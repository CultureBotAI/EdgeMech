#!/usr/bin/env python3
"""Replay one NEW fresh-05 #152 transport canary; never an independent rating.

Historical inputs are read-only. New bytes, production CLI receipts and complete
assessment parity are retained privately. No service calls or graph admissions.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import run_abstract_canary_20261115 as base  # noqa: E402
from kg_microbe_governance.artifacts.scripts.record_review import (  # noqa: E402
    inspect_source,
)
from kg_microbe_reviews import read_review  # noqa: E402

from edgemech.occurrence_review import CATEGORIES  # noqa: E402

OLD = Path("/Users/marcin/agent-work/EdgeMech/m5-calibration-20261116")
OLD_RUN = OLD / ".temp/m5-worker-run-20261116"
DEFAULT_STAGE = ".temp/m5-round02-worker-20261116/acceptance/canary-01"
AXES = {
    "claim": "SUPPORTED_AS_STATED", "literature": "SUPPORTS", "relation": "INCORRECT",
    "subject_node": "UNRESOLVED", "object_node": "UNRESOLVED",
    "source_fidelity": "NOT_ASSESSABLE",
}
AUTHORITY = {
    "ncbi": ("evidence/literature/new-fresh05-ncbi1123071/response.xml",
             "e3c3c74d3106e779e9f4864c782c58b5a2f91cd7f5260817776c38059e630772",
             "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1123071",
             "NCBI UpdateDate=2014/05/01 13:16:02; retained retrieval 2026-11-16",
             "<TaxId>1123071</TaxId>\n    <ScientificName>Rubritalea squalenifaciens DSM 18772</ScientificName>",
             ["claim", "subject_node"], "context_only", "context"),
    "metpo": ("evidence/fresh14/metpo.owl",
              "8b6f8fe0510a698579e532658c8ace05da2550093365df9ca83feb0741778415",
              "https://w3id.org/metpo/releases/2026-06-12/metpo.owl", "2026-06-12",
              "A motility in which an organism lacks the ability to move independently under its own power.",
              ["claim", "object_node"], "context_only", "context"),
    "biolink": ("evidence/fresh14/biolink-model-4.4.0.yaml",
                "4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb",
                "https://github.com/biolink/biolink-model/blob/v4.4.0/biolink-model.yaml",
                "4.4.0", "domain: biological entity\n    range: phenotypic feature",
                ["relation"], "refutes", "exact"),
}
PROPOSITION = (
    "Original NCBITaxon:1123071 (Rubritalea squalenifaciens DSM 18772) "
    "biolink:has_phenotype METPO:1000703 (non motile): its literal descriptive content "
    "is the named strain's inability to move independently under its own power, as "
    "reported for HOact23(T)=DSM18772(T) in the primary abstract. This is bounded to "
    "that observation, not every organism or condition. Original identifiers, predicate "
    "and direct negative endpoint definition are retained. Support for this content "
    "does not certify the formal ontology conjunction: METPO's inherited motility "
    "definition conflicts, strict Biolink categories fail, and source accessions conflict. "
    "No motility is inferred from that inconsistency; no corrected relation is substituted."
)


def stage_path(relative):
    path = Path(relative)
    base.require(not path.is_absolute() and path.parts[:1] == (".temp",)
                 and ".." not in path.parts, "Stage must be private repository-relative .temp")
    target = base.safe_path(ROOT / path, exists=False)
    base.require(not target.exists(), "Exclusive canary directory already exists")
    check = subprocess.run(["git", "check-ignore", "--quiet", "--no-index", str(path)],
                           cwd=ROOT, check=False)
    base.require(check.returncode == 0, "Stage must be gitignored")
    return target


def historical_inventory():
    result = []
    for reviewer in ("reviewer-a", "reviewer-b"):
        for name in ("review-input.json", "proofs.json"):
            path = OLD_RUN / reviewer / "fresh-05" / name
            raw = path.read_bytes()
            result.append({"path": str(path), "sha256": base.digest(raw)})
    path = OLD_RUN / "reviewer-a/fresh-05/save-command.json"
    raw = path.read_bytes()
    failure = json.loads(raw)
    base.require(failure["exit_status"] == 1 and
                 "Supported-as-stated cannot conceal incorrect/unassessed original modeling"
                 in failure["stderr"], "Historical failure is not the expected #152 boundary")
    result.append({"path": str(path), "sha256": base.digest(raw)})
    return result


def check_parity(authored, persisted, receipt, packet):
    base.require(authored["assessments"] == persisted["assessments"],
                 "Persisted authored assessments changed")
    for field in ("targets", "completion", "verdict", "review_id"):
        base.require(authored[field] == persisted[field], f"Persisted {field} changed")
    base.require(packet["occurrence_id"] == receipt["occurrence_id"] == base.OCCURRENCE,
                 "Original occurrence binding changed")
    base.require(receipt["assessments"] == AXES, "Six-axis receipt differs")
    base.require(persisted["completion"] == "partial" and
                 persisted["verdict"] == "needs_curation", "Aggregate disposition changed")
    base.require(receipt["kg_admissions"] == 0, "Canary cannot admit graph records")
    return True


def set_assessment(review, axis, summary, details, evidence_ids):
    assessment = next(a for a in review["assessments"]
                      if any(d["name"] == "axis" and d["value"] == axis
                             for d in a["dimensions"]))
    assessment["summary"] = summary
    assessment["outcome"] = CATEGORIES[axis][AXES[axis]]
    assessment["evidence_ids"] = evidence_ids
    values = {"axis": axis, "category": AXES[axis],
              "scope": "Original fresh-05 occurrence; operational #152 canary excluded from scoring",
              **details}
    assessment["dimensions"] = [
        {"name": k, "value": v, "definition": "Authored bounded canary dimension: " + k,
         "evidence_ids": evidence_ids} for k, v in values.items()]


def command(stage, name, action, review, packet, proofs):
    argv = [sys.executable, "-B", "-m", "edgemech.occurrence_review", action,
            "--review", review, "--packet", packet, "--proofs", proofs]
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                            env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, check=False)
    base.write_json(stage / (name + ".json"), {
        "argv": argv, "exit_code": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr})
    base.require(result.returncode == 0, name + " failed; inspect immutable command receipt")
    return json.loads(result.stdout)


def run(relative):
    started = base.utc_now()
    historical = historical_inventory()
    raws, occurrence, source, paper_raw, spans = base.load_inputs(base.RETAINED, base.PAPER)
    base.check_contracts()
    stage = stage_path(relative)
    stage.mkdir(mode=0o700, parents=True)
    for name in ("occurrence.json", "source.json"):
        base.write_new(stage / name, raws[name])
    base.write_new(stage / "prepared-packet.json", raws["packet.json"])
    base.write_new(stage / "abstract.json", paper_raw)
    occurrence_pin, source_pin = base.pin(stage / "occurrence.json"), base.pin(stage / "source.json")
    packet = base.build_packet(occurrence, source, occurrence_input=occurrence_pin,
                               source_input=source_pin, root=ROOT)
    base.write_json(stage / "packet.json", packet)
    base.validate_packet(packet, root=ROOT)
    packet_pin, paper_pin = base.pin(stage / "packet.json"), base.pin(stage / "abstract.json")
    proofs = [{"evidence_id": "packet-source", "kind": "packet", "input": packet_pin,
               "reference": packet_pin["path"], "support": "context_only", "scope": "exact",
               "scope_rationale": "Exact original source rows remain conflicting; not biological proof.",
               "inspected_extent": "Complete original packet and all source rows.",
               "axes": ["source_fidelity", "subject_node", "object_node"]}]
    for eid, span in spans.items():
        proofs.append({**base.paper_identity(), "evidence_id": eid, "input": paper_pin,
                       "support": "supports", "scope": "exact", "scope_rationale": PROPOSITION,
                       "axes": ["claim", "literature"],
                       **{k: span[k] for k in ("text_sha256", "start", "end", "extractor")}})
    authority_evidence, copied_pins = [], [occurrence_pin, source_pin, paper_pin,
                                         base.pin(stage / "prepared-packet.json")]
    for eid, (old_path, sha, reference, version, quote, axes, role, scope) in AUTHORITY.items():
        raw = base.checked_input(OLD_RUN / old_path, sha)
        base.write_new(stage / (eid + ".txt"), raw)
        pin = base.pin(stage / (eid + ".txt"))
        copied_pins.append(pin)
        span = base.verify_quote(base.LiteratureCache._document(
            {"response_sha256": sha}, "authority_text", raw.decode()), quote)
        proofs.append({"evidence_id": eid, "kind": "authority", "input": pin,
                       "reference": reference, "version": version, "support": role,
                       "scope": scope, "scope_rationale": PROPOSITION if eid != "biolink" else
                       "Strict declared has_phenotype domain and range fail for original "
                       "OrganismTaxon and PhenotypicQuality categories under Biolink 4.4.0; "
                       "full class ancestors and predicate description inspected. This is "
                       "version-scoped and does not establish the sampled ontology version.",
                       "inspected_extent": "Exact term definitions and inherited constraints in retained authority.",
                       "axes": axes,
                       **{k: span[k] for k in ("text_sha256", "start", "end", "extractor")}})
        authority_evidence.append({"evidence_id": eid, "kind": "authority",
            "reference": reference, "support": role, "quote": quote,
            "locator": f"version {version}; chars {span['start']}:{span['end']}",
            "snapshot_sha256": sha, "accessed_at": started,
            "summary": "Versioned authority retained for scoped identity/meaning or strict relation check."})
    base.write_json(stage / "proofs.json", {"profile": base.PROFILE,
                    "occurrence_id": base.OCCURRENCE, "proofs": proofs})
    proofs_pin = base.pin(stage / "proofs.json")
    review = base.review_document(packet_pin, proofs_pin, copied_pins, spans, started,
                                  base.utc_now(), ("git check-ignore --quiet --no-index " + relative, 0))
    review.update(review_id=base.utc_now().replace("-", "").replace(":", "") + "-round02-152-canary",
                  title="Round02 scoped content and incorrect modeling acceptance canary",
                  summary="New operational #152 save/check reproduction of one retained fresh-05 "
                  "occurrence. Literal nonmotility content is supported, strict relation modeling "
                  "is incorrect under Biolink 4.4.0, remaining modeling and source fidelity unresolved.")
    for item in review["evidence"]:
        if item["kind"] == "primary_source":
            item.update(support="supports", summary=PROPOSITION)
    review["evidence"].extend(authority_evidence)
    set_assessment(review, "claim", PROPOSITION, {"assertion_scope": PROPOSITION},
                   [*base.PAPER_IDS, "ncbi", "metpo"])
    set_assessment(review, "literature", "The exact primary abstract reports the bounded named "
                   "strain observation. No full text or measurement conditions are claimed.",
                   {"search_scope": "Retained complete Europe PMC core abstract PMID17625207; "
                    "DOI/title/PMID verified. No new search or provider calls; abstract only."}, base.PAPER_IDS)
    set_assessment(review, "relation", "Strict Biolink 4.4.0 original declared category "
                   "fit fails. This does not refute the independently observed biological content.",
                   {"direction": "Original taxon to phenotype direction retained.",
                    "domain_range": "has phenotype requires biological entity to phenotypic feature; "
                    "OrganismTaxon derives from named thing and PhenotypicQuality from organism "
                    "attribute, not those required classes. Full ancestors were inspected.",
                    "specificity": "Original predicate describes phenotype bearing; no replacement used.",
                    "qualifiers": "Biolink 4.4.0 version-scoped assessment; sampled-version identity "
                    "not established by this canary. No universal condition interpretation."}, ["biolink"])
    set_assessment(review, "subject_node", "NCBI binds the nominal original strain identifier, "
                   "but complete category and historical model validation remain unresolved.",
                   {"identity": "NCBITaxon:1123071 matches NCBI DSM18772 record.",
                    "label": "Original Rubritalea squalenifaciens DSM 18772 retained.",
                    "category_fit": "OrganismTaxon retained; complete historical category review unavailable.",
                    "rank_or_type": "NCBI retained record states strain.",
                    "definition": "Taxonomic concept identifies named strain; not an individual cell.",
                    "authority_version": AUTHORITY["ncbi"][3]}, ["packet-source", "ncbi"])
    set_assessment(review, "object_node", "Direct negative definition is retained, but inherited "
                   "motility definition conflicts. Formal modeling remains unresolved; no motility inferred.",
                   {"identity": "METPO:1000703 retained.", "label": "non motile retained.",
                    "category_fit": "PhenotypicQuality retained without a full correctness claim.",
                    "rank_or_type": "Phenotype class with unresolved inherited constraints.",
                    "definition": "Direct definition lacks self-powered motion, while parent1000701 "
                    "requires capability to move. This semantic conflict prevents CORRECT.",
                    "authority_version": "METPO2026-06-12 retained; original production binding unresolved."},
                   ["packet-source", "metpo"])
    review["limitations"] = [PROPOSITION,
        "Operational self-review only; both historical failed inputs were inspected. Excluded "
        "from calibration and expert validation. No current repair changes historical edge verdict.",
        "Required source-identity and full versioned-modeling checks unavailable; partial needs_curation.",
        "Zero provider calls; retained response bodies and source rows remain private."]
    review["source"] = inspect_source(ROOT, review["targets"],
        [i["path"] for i in review["source"]["inputs"]] +
        ["scripts/adhoc/run_round02_acceptance_canary_20261116.py", "uv.lock"])["source"]
    base.write_json(stage / "authored-review.json", review)
    base.write_json(stage / "historical-inputs.json", historical)
    saved = command(stage, "save-command", "save", str((stage / "authored-review.json").relative_to(ROOT)),
                    packet_pin["path"], proofs_pin["path"])
    checked = command(stage, "check-command", "check", saved["review"],
                      packet_pin["path"], proofs_pin["path"])
    persisted = read_review(ROOT, saved["review"])
    check_parity(review, persisted, checked, packet)
    yaml_path = ROOT / saved["review"]
    markdown_path = yaml_path.with_suffix(".md")
    base.require(yaml_path.stat().st_size > 0 and markdown_path.stat().st_size > 0,
                 "Canonical YAML/Markdown bytes must both exist")
    base.require(historical_inventory() == historical, "Historical inputs changed")
    receipt = {**saved, "check": checked, "aggregate": {"completion": "partial", "verdict": "needs_curation"},
               "assessment_byte_equivalent_values": True, "historical_inputs_unchanged": True,
               "pair": [base.pin(yaml_path), base.pin(markdown_path)],
               "calibration_rating": False, "provider_calls": 0,
               "publication_status": "private_candidate_until_whole_bundle_quote_gate",
               "packet": packet_pin, "proofs": proofs_pin}
    base.write_json(stage / "receipt.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", default=DEFAULT_STAGE)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.plan:
        stage_path(args.staging)
        historical_inventory()
        base.load_inputs(base.RETAINED, base.PAPER)
        for old_path, sha, *_ in AUTHORITY.values():
            base.checked_input(OLD_RUN / old_path, sha)
        result = {"staging": args.staging, "writes": 0, "provider_calls": 0,
                  "assessments": AXES, "calibration_rating": False}
    else:
        result = run(args.staging)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
