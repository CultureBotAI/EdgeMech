"""2026-11-13 PR76: classify scientific applicability before evidence searches.

Inputs: original edge transform, predicate and object identifier only. Outputs:
written ordered applicability rules and per-edge decisions; no scientific verdicts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "artifacts/edge-recanary-20261113"
TABLE = Path(__file__).with_name("APPLICABILITY.md")
APPLICABLE = "APPLICABLE"
NOT_APPLICABLE = "NOT_APPLICABLE"
TRAIT_TRANSFORMS = tuple(name + "/edges.tsv" for name in (
    "bacdive", "bactotraits", "madin_etal", "metatraits", "metatraits_gtdb", "microbedecoder"))
METABOLIC_PREDICATES = tuple("METPO:" + identifier for identifier in (
    "2000002", "2000003", "2000006", "2000008", "2000010", "2000011", "2000012",
    "2000013", "2000015", "2000016", "2000017", "2000027", "2000028", "2000030",
    "2000031", "2000033", "2000034", "2000037", "2000038", "2000039", "2000041",
    "2000042", "2000044", "2000046", "2000065", "2000202", "2000222", "2000602",
    "2000604", "2000606"))
BIOLOGICAL_SOURCE_FIELDS = (
    "antibiotic_resistance", "antibiotic_sensitivity", "cell_length", "cell_shape",
    "cell_width", "colony_size", "enzyme_activity", "flagellum_arrangement",
    "gram_stain", "incubation_period", "indole_test", "isolation_category_1",
    "isolation_category_2", "isolation_category_3", "metabolite_production",
    "metabolite_utilization", "motility", "oxygen_tolerance", "ph_for_growth",
    "salt_concentration", "spore_formation", "temperature_for_growth", "voges_proskauer")


def rule(identifier, transforms, predicates, prefixes, status, reason):
    return {"rule_id": identifier, "transforms": transforms, "predicates": predicates,
            "object_prefixes": prefixes, "status": status, "reason": reason}


RULES = (
    rule("identity_taxonomy", ("*",), (
        "biolink:same_as", "biolink:close_match", "biolink:exact_match", "biolink:broad_match",
        "biolink:narrow_match", "biolink:subclass_of", "biolink:in_taxon"), ("*",),
        NOT_APPLICABLE, "Identity, taxonomy or crosswalk assertion; no organism-level biological claim."),
    rule("reaction_scaffolding", ("rhea_mappings/edges.tsv",), ("*",), ("*",),
         NOT_APPLICABLE, "Reaction participants, directions or reaction identity; outside organism-claim science axis."),
    rule("recipe_composition", ("mediadive/edges.tsv",), ("biolink:has_part",), ("*",),
         NOT_APPLICABLE, "Recipe composition does not assert organism growth or a phenotype."),
    rule("related_identity", ("gold/edges.tsv", "microbedecoder/edges.tsv"),
         ("biolink:related_to",), ("NCBITaxon:", "gold:"), NOT_APPLICABLE,
         "This transform/predicate class links organism records or identifiers."),
    rule("source_units", ("microbedecoder/edges.tsv",), ("biolink:has_attribute",),
         ("kgmicrobe.source_attribute:microbedecoder_bacdive_salt_concentration_unit_",),
         NOT_APPLICABLE, "A unit token alone is metadata, not a biological measurement."),
    rule("unmapped_bergey_other", ("microbedecoder/edges.tsv",), ("biolink:has_attribute",),
         ("kgmicrobe.source_attribute:microbedecoder_bergey_type_of_metabolism_daa2ea51fd2269f0b2c931a54b3607f04c2766422c11814a29abf4b3d73c579a",),
         NOT_APPLICABLE, "The exact source-value class Other has no resolved metabolic proposition."),
    rule("phenotype", TRAIT_TRANSFORMS, ("biolink:has_phenotype",), ("METPO:",),
         APPLICABLE, "Explicit organism phenotype or growth-condition assertion."),
    rule("biological_measurement", ("bactotraits/edges.tsv", "metatraits/edges.tsv", "metatraits_gtdb/edges.tsv"),
         ("biolink:has_attribute",), ("METPO:",), APPLICABLE,
         "Trait-table class carries a biological measurement, including genomic composition."),
    rule("metabolic_substrate", TRAIT_TRANSFORMS, METABOLIC_PREDICATES,
         ("CHEBI:", "NCIT:", "FOODON:", "ENVO:", "kgmicrobe.carbon_substrate:"),
         APPLICABLE, "Enumerated metabolic/substrate relation; preserve its positive or negative polarity."),
    rule("metabolic_process", TRAIT_TRANSFORMS,
         ("biolink:capable_of", "METPO:2000102", "METPO:2000103", "METPO:2000302", "METPO:2000303"),
         ("GO:", "EC:", "METPO:", "kgmicrobe.pathway:", "kgmicrobe.activity:", "kgmicrobe.assay:"),
         APPLICABLE, "Metabolic process, enzyme activity or assay phenotype; original qualifiers remain binding."),
    rule("assay_observation", ("bacdive/edges.tsv",), ("METPO:2000511",), ("kgmicrobe.assay:",),
         APPLICABLE, "Assay observation can carry a biological claim; polarity must be resolved from the asserting record."),
    rule("product_consumption", TRAIT_TRANSFORMS, ("biolink:produces", "biolink:consumes"),
         ("CHEBI:", "kgmicrobe.compound:", "kgmicrobe.ingredient:"), APPLICABLE,
         "Organism product or consumption assertion."),
    rule("susceptibility", ("bacdive/edges.tsv",),
         ("biolink:associated_with_resistance_to", "biolink:associated_with_sensitivity_to"),
         ("CHEBI:",), APPLICABLE, "Organism susceptibility phenotype."),
    rule("medium_growth", ("mediadive/edges.tsv", "metatraits/edges.tsv", "metatraits_gtdb/edges.tsv"),
         ("METPO:2000517",), ("mediadive.medium:", "kgmicrobe.medium:"), APPLICABLE,
         "Organism growth on a specified medium; recipe identity must be retained."),
    rule("habitat_forward", ("gold/edges.tsv",), ("biolink:located_in",), ("gold.ecosystem:",),
         APPLICABLE, "Organism environment or habitat assertion."),
    rule("habitat_inverse", ("prego_habitat/edges.tsv", "madin_etal/edges.tsv", "bacdive/edges.tsv"),
         ("biolink:location_of",), ("NCBITaxon:", "kgmicrobe.strain:"), APPLICABLE,
         "Inverse environment/body-site location assertion; original direction is retained."),
    rule("biological_source_field", ("microbedecoder/edges.tsv",), ("biolink:has_attribute",),
         tuple("kgmicrobe.source_attribute:microbedecoder_bacdive_" + field + "_"
               for field in BIOLOGICAL_SOURCE_FIELDS)
         + ("kgmicrobe.source_attribute:microbedecoder_faprotax_type_of_metabolism_",
            "kgmicrobe.source_attribute:microbedecoder_bergey_type_of_metabolism_"),
         APPLICABLE, "Named source field carries a biological phenotype, metabolism or growth claim; this does not establish its truth or scientific resolution."),
    rule("unresolved_class", ("*",), ("*",), ("*",), NOT_APPLICABLE,
         "No explicit biological class rule matches; conservatively excluded before searching. Requires a separately reviewed rule change, not evidence-driven relabeling."),
)


def classify(row):
    """First matching written rule wins; labels, verdicts and evidence are ignored."""
    for item in RULES:
        transform_ok = "*" in item["transforms"] or row["origin_transform"] in item["transforms"]
        predicate_ok = "*" in item["predicates"] or row["predicate"] in item["predicates"]
        object_ok = "*" in item["object_prefixes"] or any(
            row["object"].startswith(prefix) for prefix in item["object_prefixes"])
        if transform_ok and predicate_ok and object_ok:
            return {"scientific_applicability": item["status"], "applicability_rule": item["rule_id"],
                    "applicability_reason": item["reason"]}
    raise AssertionError("Missing conservative fallback")


def table_text():
    lines = ["# Scientific applicability before retrieval — fresh recanary", "",
             "PR76, 2026-11-13. Rules use only the original transform, predicate and object identifier. "
             "They run in table order; the first match wins. Object prefixes are literal CURIE namespaces "
             "or explicit source-field stems, with `*` meaning any value. Comma-separated entries mean OR. "
             "No name, inherited verdict, paper result or search success changes applicability.", "",
             "Source fidelity applies to all 50 edges. Scientific retrieval runs only for APPLICABLE rows. "
             "NOT_APPLICABLE rows remain separate and are excluded from scientific support-rate denominators. "
             "Applicable claims with unresolved names, units or polarity may later be NOT_ASSESSABLE; "
             "applicability alone does not approve a claim. Source-field metadata-only and unmapped Other "
             "classes are explicitly excluded before the broader biological-field rule.", "",
             "| Rule | Transform | Predicate | Object prefix | Scientific applicability | Reason |",
             "|---|---|---|---|---|---|"]
    for item in RULES:
        lines.append("| " + " | ".join((item["rule_id"], ", ".join(item["transforms"]),
            ", ".join(item["predicates"]), ", ".join(item["object_prefixes"]),
            item["status"], item["reason"])) + " |")
    lines += ["", "Reproduce after selecting the cohort:", "",
              "```sh", "python scripts/adhoc/edge_recanary_20261113/applicability.py --write", "```", "",
              "The sidecar pins the cohort, table and classifier hashes. The sample retains original "
              "10k-manifest weights; its purposive class coverage does not yield a population accuracy estimate.", ""]
    return "\n".join(lines)


def self_test():
    def edge(transform, predicate, obj):
        return {"origin_transform": transform + "/edges.tsv", "predicate": predicate, "object": obj}
    cases = [
        (edge("bacdive", "biolink:close_match", "kgmicrobe.strain:DSM-1"), NOT_APPLICABLE),
        (edge("bactotraits", "biolink:has_phenotype", "METPO:1000703"), APPLICABLE),
        (edge("gold", "biolink:related_to", "NCBITaxon:1"), NOT_APPLICABLE),
        (edge("mediadive", "biolink:has_part", "CHEBI:1"), NOT_APPLICABLE),
        (edge("mediadive", "METPO:2000517", "mediadive.medium:1"), APPLICABLE),
        (edge("rhea_mappings", "biolink:has_output", "CHEBI:1"), NOT_APPLICABLE),
        (edge("metatraits", "METPO:2000034", "CHEBI:1"), APPLICABLE),
        (edge("prego_habitat", "biolink:location_of", "NCBITaxon:1"), APPLICABLE),
        (edge("microbedecoder", "biolink:has_attribute",
              "kgmicrobe.source_attribute:microbedecoder_bacdive_salt_concentration_unit_hash"), NOT_APPLICABLE),
        (edge("microbedecoder", "biolink:has_attribute",
              "kgmicrobe.source_attribute:microbedecoder_bacdive_salt_concentration_hash"), APPLICABLE),
        (edge("microbedecoder", "biolink:has_attribute", RULES[5]["object_prefixes"][0]), NOT_APPLICABLE),
        (edge("unknown", "METPO:2000006", "CHEBI:1"), NOT_APPLICABLE),
        (edge("metatraits", "METPO:9999999", "CHEBI:1"), NOT_APPLICABLE),
    ]
    for row, expected in cases:
        result = classify(row)
        assert result["scientific_applicability"] == expected, row
        assert result == classify({**row, "object_label": "untrusted changed label",
                                  "content_accuracy_verdict": "SUPPORTED"})
    assert len({r["rule_id"] for r in RULES}) == len(RULES)
    print(json.dumps({"class_cases_passed": len(cases), "rules": len(RULES)}))


def write():
    table = table_text()
    path = OUT / "applicability.jsonl"
    metadata_path = OUT / "applicability-metadata.json"
    if path.exists() or metadata_path.exists():
        raise FileExistsError("Refusing to replace frozen applicability decisions")
    TABLE.write_text(table)
    canary = OUT / "canary.jsonl"
    rows = [json.loads(line) for line in canary.read_text().splitlines()]
    if len(rows) != 50 or len({row["occurrence_id"] for row in rows}) != 50:
        raise ValueError("Require exactly 50 recanary rows")
    decisions = [{"canary_ordinal": row["canary_ordinal"], "occurrence_id": row["occurrence_id"],
                  "origin_transform": row["origin_transform"], "predicate": row["predicate"],
                  "object": row["object"], **classify(row)} for row in rows]
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in decisions))
    metadata = {"classified_at": datetime.now(timezone.utc).isoformat(),
                "classification_precedes_scientific_retrieval": True,
                "counts": dict(Counter(row["scientific_applicability"] for row in decisions)),
                "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (TABLE, Path(__file__), canary, path)}}
    metadata_path.write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n")
    print(json.dumps(metadata["counts"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.write:
        write()
