#!/usr/bin/env python3
"""Independently replay final citation literals from pinned private data.

This bounded derivative replaces executable private payloads with external data:
final audit, citation receipts, original authored inputs and frozen source bytes.
No semantic judgment, canonical save or calibration approval is produced. Run
one case canary for every evidence path actually used before the full inventory.
The historical quote-bearing driver remains private and is represented by hash.
The final citation denominator comes from every final case/axis evidence binding,
not the historical round's count. Nondefault rounds explicitly identify round_id
in this config, its reviewer config, final audit and citation report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import replay_m5_round02_pairs_20261116 as pairs

ROOT = Path(__file__).absolute().parents[2]
ORIGINS = {"existing_same_case_proof_replayed_again", "new_adjudicator_literal_anchor",
           "new_adjudicator_paper_anchor"}


def read_bound(pin, expected_path=None):
    path = Path(pin["path"]).absolute()
    pairs.require(path.resolve() == path, "Pinned input traverses symlink")
    if expected_path is not None:
        pairs.require(path == expected_path.absolute(), "Pinned input path differs from required original")
    raw = path.read_bytes()
    pairs.require(pairs.sha(raw) == pin["sha256"], "Pinned private data changed")
    return raw


def expected_rows(audit, report, manifest):
    cases = {c["case_id"]: c for c in manifest["cases"]}
    pairs.require(len(cases) == len(manifest["cases"]) == 10, "Original manifest cases incomplete")
    finals = {c["case_id"]: c for c in audit["final_cases"]}
    pairs.require(len(finals) == len(audit["final_cases"]) == 10 and set(finals) == set(cases),
                  "Final audit must retain exactly ten original cases")
    expected = {}
    for cid, case in finals.items():
        pairs.require(case["occurrence_id"] == cases[cid]["occurrence_id"], "Final occurrence changed")
        axes = [a["axis"] for a in case["assessments"]]
        pairs.require(len(axes) == 6 and set(axes) == set(pairs.rounds.CATEGORIES), "Final axes incomplete")
        for axis in case["assessments"]:
            pairs.require(len(axis["evidence_ids"]) == len(set(axis["evidence_ids"])),
                          "Repeated final axis evidence binding")
            for eid in axis["evidence_ids"]:
                pairs.require(eid in cases[cid]["evidence_ids"], "Final citation outside frozen case allowlist")
                expected.setdefault((cid, eid), set()).add(axis["axis"])
    rows = {(r["case_id"], r["evidence_id"]): r for r in report["rows"]}
    pairs.require(len(rows) == len(report["rows"]) == len(expected) and rows.keys() == expected.keys(),
                  "Every final citation slot required without duplicates or omissions")
    for key, row in rows.items():
        pairs.require(len(row["final_axes"]) == len(set(row["final_axes"])) and
                      set(row["final_axes"]) == expected[key], "Final citation axis binding changed")
    return cases, [rows[k] for k in sorted(rows)]


def literal(raw, kind, proof, quote, version):
    from edgemech.literature_cache import LiteratureCache, verify_quote
    from edgemech.occurrence_review import _europepmc_abstract, _jats

    if kind == "jats":
        text, aliases = _jats(raw, proof)
        extraction = "oa_fulltext"
    elif kind == "europepmc_abstract":
        text, aliases = _europepmc_abstract(raw, proof)
        extraction = "abstract"
    else:
        pairs.require(kind == "authority" and version and proof.get("version") == version,
                      "Authority version missing or differs from frozen source")
        text, extraction = raw.decode("utf-8"), "authority_text"
        aliases = {"authority:" + proof["reference"] + "#" + version}
    document = LiteratureCache._document({"response_sha256": pairs.sha(raw)}, extraction, text)
    return verify_quote(document, quote), aliases



def source_binding(proof, frozen, case, manifest, raw, final_eid):
    """Preserve an original source identity across an explicitly verified frozen alias.

    Byte identity alone cannot establish an independent authority. Distinct paths
    or IDs additionally require both frozen authority/version bindings and unique
    primary schema id/name/version declarations in the actual source bytes.
    """
    matches = [p for p in manifest["files"] if p["path"] == proof["input"]["path"]
               and p["sha256"] == proof["input"]["sha256"]]
    pairs.require(len(matches) == 1, "Original proof path/hash not uniquely frozen")
    original = matches[0]
    declared = proof.get("manifest_evidence_id")
    if declared is None:
        choices = set(original.get("evidence_ids", [])) & set(case["evidence_ids"])
        pairs.require(len(choices) == 1, "Original source identity is absent or ambiguous for this case")
        declared = next(iter(choices))
    if declared is not None:
        pairs.require(declared in original.get("evidence_ids", []) and declared in case["evidence_ids"],
                      "Original declared identity not allowed for its exact frozen source/case")
    pairs.require(final_eid in frozen.get("evidence_ids", []) and final_eid in case["evidence_ids"],
                  "Final identity not allowed for its exact frozen source/case")
    same = original["path"] == frozen["path"] and declared in {None, final_eid}
    if same:
        return {"kind": "exact_frozen_source", "original_manifest_id": declared, "final_manifest_id": final_eid}
    pairs.require(original.get("role") == frozen.get("role") == "authority" and
                  original.get("version") == frozen.get("version") == proof.get("version") and
                  original["sha256"] == frozen["sha256"] == pairs.sha(raw),
                  "Distinct source aliases require both exact authority/version bindings")
    import yaml
    node = yaml.compose(raw, Loader=yaml.SafeLoader)
    pairs.require(isinstance(node, yaml.MappingNode), "Authority alias lacks primary schema metadata")
    metadata = {}
    for key, value in node.value:
        if key.value in {"id", "name", "version"}:
            pairs.require(key.value not in metadata and isinstance(value, yaml.ScalarNode) and
                          value.tag == "tag:yaml.org,2002:str", "Primary schema metadata repeated or nonliteral")
            metadata[key.value] = value.value
    pairs.require(set(metadata) == {"id", "name", "version"} and metadata["name"].strip() and
                  metadata["id"].startswith(("https://", "http://", "urn:")) and
                  metadata["version"] == frozen["version"], "Primary schema identity/version unavailable or mismatched")
    return {"kind": "verified_frozen_schema_alias", "original_manifest_id": declared,
            "final_manifest_id": final_eid, "original_frozen_path": original["path"],
            "final_frozen_path": frozen["path"], "primary_identity_sha256": pairs.sha(pairs.encoded(metadata)),
            "source_reference_preserved": True}


def final_authored_proof(row, frozen, case, adjudicator):
    """A changed final interpretation needs its own complete authored proof."""
    from kg_microbe_reviews import load_document

    from edgemech.occurrence_review import validate_occurrence_review

    root = Path(row["final_root"]).absolute()
    pairs.require(root.resolve() == root and root.is_dir(), "Final draft root must be canonical")
    review_path = Path(row["final_input"]["path"]).relative_to(root)
    sidecar_path = Path(row["final_sidecar"]["path"]).relative_to(root)
    review = load_document(read_bound(row["final_input"], root / review_path))
    sidecar = json.loads(read_bound(row["final_sidecar"], root / sidecar_path))
    pairs.require(isinstance(adjudicator, dict) and all(adjudicator.get(key) for key in ("id", "model", "session_id")),
                  "Actual final adjudicator identity required")
    pairs.require(review["reviewer"].get("identity") == adjudicator["id"] and
                  review["reviewer"].get("model") == adjudicator["model"] and
                  review["reviewer"].get("kind") == "agent" and
                  all(sidecar.get("reviewer", {}).get(key) == adjudicator[key]
                      for key in ("id", "model", "session_id")),
                  "Final paper proof differs from adjudicator identity/model/session")
    expected_packet = {"path": str(ROOT / case["packet_path"]),
                       "sha256": case["frozen_packet_sha256"]}
    packet_raw = read_bound(expected_packet)
    pairs.require(pairs.rounds.safe(root, case["packet_path"]).read_bytes() == packet_raw,
                  "Final draft packet differs from exact frozen original")
    checked = validate_occurrence_review(root, review, case["packet_path"], str(sidecar_path))
    pairs.require(checked["occurrence_id"] == case["occurrence_id"], "Final paper proof belongs to another occurrence")
    proofs = [p for p in sidecar["proofs"] if p["evidence_id"] == row["final_proof_id"]]
    evidence = [e for e in review["evidence"] if e["evidence_id"] == row["final_proof_id"]]
    pairs.require(len(proofs) == len(evidence) == 1, "Missing or duplicate final paper proof")
    proof, item = proofs[0], evidence[0]
    pairs.require(proof["kind"] == row["kind"] and proof["input"] == {
        "path": frozen["path"], "sha256": frozen["sha256"]}, "Final paper proof source changed")
    pins = [expected_packet, row["final_input"], row["final_sidecar"], *[
        {"path": str(root / p["path"]), "sha256": p["sha256"]} for p in review["source"]["inputs"]]]
    return proof, item, pins


def replay_one(row, frozen, case, contexts, entries, adjudicator=None):
    cid, eid = row["case_id"], row["evidence_id"]
    raw = read_bound(row["raw_input"], ROOT / frozen["path"])
    pairs.require(pairs.sha(raw) == frozen["sha256"], "Citation differs from frozen raw source")
    kind = row["kind"]
    origin = row["proof_origin"]
    input_pins = [row["raw_input"]]
    quote = None
    verified_scope, verified_support, verified_axes = None, None, []
    binding = {"kind": "new_final_authority_anchor"}
    if origin == "new_adjudicator_literal_anchor":
        pairs.require(kind == "authority" and frozen["role"] == "authority", "New anchor must be frozen authority")
        pairs.require(row["authority_version"] == frozen.get("version"), "Anchor authority version changed")
        pairs.require(row["reference"] == frozen["path"] and bool(row["inspected_extent"].strip()),
                      "Anchor source or extraction extent missing")
        quote, aliases = literal(raw, kind, {"version": frozen["version"], "reference": frozen["path"]},
                                 row["verified_quote"]["quote"], frozen["version"])
        if {"final_root", "final_input", "final_sidecar", "final_proof_id"} & row.keys():
            proof, item, final_pins = final_authored_proof(row, frozen, case, adjudicator)
            input_pins.extend(final_pins)
            pairs.require(proof["version"] == frozen["version"] and
                          proof["reference"] == item["reference"] == row["reference"] and
                          proof["inspected_extent"] == row["inspected_extent"] and
                          item["quote"] == quote["quote"] and
                          all(proof[key] == quote[key] for key in ("start", "end", "extractor", "text_sha256")),
                          "New authority anchor differs from authored final proof")
            verified_scope, verified_support, verified_axes = proof["scope"], proof["support"], proof["axes"]
            binding["authored_final_profile_validated"] = True
    elif origin == "new_adjudicator_paper_anchor":
        pairs.require(kind in {"jats", "europepmc_abstract"} and frozen["role"] == "evidence",
                      "New paper anchor must use frozen paper evidence")
        proof, item, final_pins = final_authored_proof(row, frozen, case, adjudicator)
        input_pins.extend(final_pins)
        metadata = row["paper_identity"]
        pairs.require(isinstance(metadata, dict) and set(metadata) <= {
            "title", "doi", "pmid", "pmcid", "missing_doi_reason"},
            "Paper identity must contain explicit primary metadata only")
        pairs.rounds.text(row.get("inspected_extent"), "final paper inspected extent")
        pairs.require(all(proof.get(key) == value for key, value in metadata.items()) and
                      proof["reference"] == item["reference"] == row["reference"] and
                      proof["inspected_extent"] == row["inspected_extent"] and
                      item["quote"] == row["verified_quote"]["quote"],
                      "New final paper anchor differs from authored proof")
        if kind == "europepmc_abstract":
            pairs.require(row["locator"].startswith("abstract;"),
                          "Final abstract locator must disclose inspected extent")
        quote, aliases = literal(raw, kind, proof, row["verified_quote"]["quote"], None)
        pairs.require(all(quote[key] == proof[key] for key in ("start", "end", "extractor", "text_sha256")),
                      "Final paper proof literal offsets changed")
        verified_scope, verified_support, verified_axes = proof["scope"], proof["support"], proof["axes"]
        binding = {"kind": "new_final_paper_anchor", "final_manifest_id": eid,
                   "primary_metadata_sha256": pairs.sha(pairs.encoded(metadata)),
                   "inspected_extent": row["inspected_extent"]}
    else:
        pairs.require(origin == "existing_same_case_proof_replayed_again", "Unknown final citation origin")
        prior = row["prior_proof"]
        rid = prior["reviewer_id"]
        ctx, entry = contexts[rid], entries[rid, cid]
        root = ctx["root"]
        review = json.loads(read_bound(row["original_input"], root / entry["input"]))
        sidecar = json.loads(read_bound(row["original_sidecar"], root / entry["proofs"]))
        input_pins.extend([row["original_input"], row["original_sidecar"], row["original_raw_input"]])
        matches = [p for p in sidecar["proofs"] if p["evidence_id"] == prior["proof_id"]]
        items = [e for e in review["evidence"] if e["evidence_id"] == prior["proof_id"]]
        pairs.require(len(matches) == len(items) == 1, "Missing or duplicate original proof/evidence identity")
        proof, item = matches[0], items[0]
        verified_scope, verified_support, verified_axes = proof.get("scope"), proof.get("support"), proof.get("axes", [])
        pairs.require(sidecar["occurrence_id"] == case["occurrence_id"], "Original proof belongs to another occurrence")
        pairs.require(proof["kind"] == kind and
                      proof["input"]["sha256"] == item["snapshot_sha256"] == frozen["sha256"],
                      "Original proof is not bound to final source/version")
        binding = source_binding(proof, frozen, case, ctx["manifest"], raw, eid)
        pairs.require(read_bound(row["original_raw_input"], root / proof["input"]["path"]) == raw,
                      "Original reviewer source bytes differ")
        pins = {p["path"]: p["sha256"] for p in review["source"]["inputs"]}
        pairs.require(pins.get(proof["input"]["path"]) == frozen["sha256"], "Original source not pinned by review")
        pairs.require(item["reference"] == proof["reference"] == row["reference"], "Source reference changed")
        pairs.require(row["inspected_extent"] == proof["inspected_extent"], "Extraction extent changed")
        if kind == "packet":
            from edgemech.occurrence_packet import validate_packet
            packet = json.loads(raw)
            pairs.require(frozen["path"] == case["packet_path"] and
                          packet["occurrence_id"] == case["occurrence_id"] and
                          packet["original_assertion"] == case["original_assertion"], "Original packet binding changed")
            validate_packet(packet, root=ROOT)
            pairs.require(not item.get("quote") and not row.get("verified_quote"), "Packet cannot conceal a quotation")
            aliases = {"packet:" + case["occurrence_id"]}
        else:
            quote, aliases = literal(raw, kind, proof, item["quote"], frozen.get("version"))
            pairs.require(all(quote[k] == proof[k] for k in ("start", "end", "extractor", "text_sha256")),
                          "Original quotation proof offsets changed")
            pairs.require(f"chars {quote['start']}:{quote['end']}" in item["locator"], "Original quote locator changed")
    pairs.require(set(row["verified_identities"]) == aliases, "Declared source aliases differ from primary replay")
    if quote is not None:
        pairs.require(quote == row["verified_quote"], "Final literal proof differs from independently extracted quotation")
        pairs.require(f"chars {quote['start']}:{quote['end']}" in row["locator"], "Final quotation locator changed")
    return {"case_id": cid, "evidence_id": eid, "status": "passed", "origin": origin, "kind": kind,
            "final_axes": row.get("final_axes", []),
            "scope": verified_scope, "support": verified_support, "proof_axes": verified_axes,
            "source_sha256": frozen["sha256"], "input_pins": input_pins, "source_binding": binding,
            "quote_sha256": pairs.sha(quote["quote"].encode()) if quote else None,
            "source_identity_hashes": sorted(pairs.sha(a.encode()) for a in aliases),
            "semantic_support": "not_assessed", "canonical_pair_verified": False}


def check_canary(directory, config):
    receipt = json.loads((directory / "receipt.json").read_bytes())
    pairs.require(receipt["mode"] == "canary" and receipt["helper_sha256"] == pairs.sha(Path(__file__).read_bytes())
                  and receipt["config_sha256"] == pairs.sha(pairs.encoded(config)), "Canary runtime/config changed")
    pairs.require(receipt["passed"] and len({r["case_id"] for r in receipt["rows"]}) == 1,
                  "Canary did not replay one complete case")
    expected = {p["path"] for p in receipt["artifact_pins"]}
    actual = {str(p.absolute()) for p in directory.rglob("*") if p.is_file() and p != directory / "receipt.json"}
    pairs.require(expected == actual, "Canary artifact inventory changed")
    for pin in receipt["artifact_pins"] + receipt["input_pins"]:
        read_bound(pin)
    return receipt


def check_round(config, base, audit, report, manifest):
    expected = base.get("round_id", pairs.DEFAULT_ROUND)
    pairs.rounds.text(expected, "expected final citation round")
    pairs.require(config.get("round_id", pairs.DEFAULT_ROUND) == expected and
                  audit.get("round_id", pairs.DEFAULT_ROUND) == expected and
                  report.get("round_id", pairs.DEFAULT_ROUND) == expected and
                  manifest["round_id"] == expected, "Final citation scientific round differs")
    return expected


def check_canary_origins(rows, checked):
    required = {row["proof_origin"] for row in rows}
    pairs.require(required and required <= ORIGINS, "Unknown or empty final citation evidence paths")
    actual = {r["origin"] for canary in checked for r in canary["rows"]}
    pairs.require(actual <= ORIGINS and required <= actual,
                  "Batch needs inspected canaries for every used existing-proof and new-anchor path")


def run(config, output, mode, case_id=None, canaries=()):
    pairs.require(not output.exists() and ".temp" in output.absolute().parts, "New private output directory required")
    pairs.require(not any(p.is_symlink() for p in (output, *output.absolute().parents)), "Output symlink forbidden")
    if mode == "batch":
        pairs.require(canaries, "Batch needs inspected canaries for existing-proof and new-anchor paths used")
        checked = [check_canary(c, config) for c in canaries]
    base = json.loads(read_bound(config["reviewer_config"]))
    _, entry_list = pairs.expected_entries(base)
    entries = {(e["reviewer"], e["case_id"]): e for e in entry_list}
    manifest_raw, manifest_pin = pairs.pin(ROOT, base["manifest"])
    pairs.require(manifest_pin["sha256"] == base["package_sha256"], "Coordinator package changed")
    manifest = json.loads(manifest_raw)
    pairs.verify_frozen_inputs(ROOT, manifest)
    audit, report = (json.loads(read_bound(config[k])) for k in ("final_audit", "citation_report"))
    pairs.require(audit["package_sha256"] == report["package_sha256"] == base["package_sha256"], "Final package mismatch")
    round_id = check_round(config, base, audit, report, manifest)
    cases, rows = expected_rows(audit, report, manifest)
    frozen_files = {p["path"]: p for p in manifest["files"]}
    for case in cases.values():
        case["frozen_packet_sha256"] = frozen_files[case["packet_path"]]["sha256"]
    expected_total = len(rows)
    if mode == "batch":
        check_canary_origins(rows, checked)
    if mode == "canary":
        rows = [r for r in rows if r["case_id"] == case_id]
        pairs.require(bool(rows), "Unknown or empty canary case")
    output.mkdir(mode=0o700, parents=True)
    contexts = {rid: pairs.context(base, rid, output / rid / "context") for rid in base["reviewers"]}
    pins = {eid: p for p in manifest["files"] for eid in p.get("evidence_ids", [])}
    results, input_pins = [], [config[k] for k in ("reviewer_config", "final_audit", "citation_report")]
    for ctx in contexts.values():
        for key in ("manifest", "matrix", "matrix_receipt"):
            pin = ctx["meta"][key]
            input_pins.append({"path": str(Path(pin["root"]) / pin["path"]), "sha256": pin["sha256"]})
    for module in (pairs, pairs.rounds):
        path = Path(module.__file__).absolute()
        input_pins.append({"path": str(path), "sha256": pairs.sha(path.read_bytes())})
    for row in rows:
        cid, eid = row["case_id"], row["evidence_id"]
        try:
            result = replay_one(row, pins[eid], cases[cid], contexts, entries, audit["adjudicator"])
            input_pins.extend(result["input_pins"])
        except Exception as error:
            failure = pairs.write(output / "failures" / (cid + "-" + pairs.sha(eid.encode()) + ".json"),
                                  {"error_type": type(error).__name__, "message": str(error)})
            result = {"case_id": cid, "evidence_id": eid, "status": "failed", "failure": failure,
                      "final_axes": row["final_axes"], "kind": row["kind"],
                      "origin": row.get("proof_origin"), "canonical_pair_verified": False}
        results.append(result)
        pairs.write(output / "units" / (cid + "-" + pairs.sha(eid.encode()) + ".json"), result)
    for pin in input_pins:
        read_bound(pin)
    artifacts = [{"path": str(p.absolute()), "sha256": pairs.sha(p.read_bytes())}
                 for p in sorted(output.rglob("*")) if p.is_file()]
    receipt = {"schema": "edgemech-independent-final-citation-replay/v1", "mode": mode,
               "round_id": round_id, "package_sha256": base["package_sha256"],
               "helper_sha256": pairs.sha(Path(__file__).read_bytes()), "config_sha256": pairs.sha(pairs.encoded(config)),
               "input_pins": input_pins, "artifact_pins": artifacts, "rows": results,
               "expected_total_final_citations": expected_total, "entries_retained": len(results),
               "literal_identity_passed": sum(r["status"] == "passed" for r in results),
               "passed": bool(results) and all(r["status"] == "passed" for r in results),
               "scope": "Final citation literal/identity replay only; no semantic approval or canonical pair validation",
               "canonical_pairs_verified": 0, "scientific_calibration_pass": False}
    pairs.write(output / "receipt.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("canary", "check-canary", "batch"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--canary", type=Path, action="append", default=[])
    args = parser.parse_args()
    config = json.loads(args.config.read_bytes())
    result = (check_canary(args.canary[0], config) if args.mode == "check-canary" else
              run(config, args.output, args.mode, args.case, args.canary))
    print(json.dumps({k: result[k] for k in ("passed", "entries_retained", "literal_identity_passed", "canonical_pairs_verified")}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
