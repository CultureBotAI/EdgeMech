"""2026-11-13 PR76: validate timed decisions and publish short scientific proofs.

Inputs: pinned private canary, applicability sidecar, retrieval packets/raw bytes,
and review_clock decisions/receipts. Outputs: public 50-row scientific ledger.
Citation paper indices are within packet.primary entries for the named retrieval
stage (primary/fallback); document indices are within that entry's documents.
No network requests or automatic directional scientific judgments are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/edge-recanary-20261113"
sys.path.insert(0, str(ROOT / "src"))
from edgemech.literature_cache import LiteratureCache  # noqa: E402

SPEC = importlib.util.spec_from_file_location("recanary_retrieval", Path(__file__).with_name("retrieve_targeted.py"))
RETRIEVAL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RETRIEVAL
SPEC.loader.exec_module(RETRIEVAL)
VERDICTS = {"SUPPORTED", "CONTRADICTED", "NOT_FOUND", "NOT_ASSESSABLE"}
MODEL = "GPT-6 (runtime variant not exposed)"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def validate_inputs(manifest, applicability, sampling_metadata, applicability_metadata):
    # Issue #84: CLI paths may be relative; provenance keys remain repository-relative.
    manifest, applicability, sampling_metadata, applicability_metadata = (
        Path(path).resolve() for path in
        (manifest, applicability, sampling_metadata, applicability_metadata))
    sample = json.loads(sampling_metadata.read_text())
    manifest_hash = sha(manifest.read_bytes())
    if sample["private_original_canary"]["sha256"] != manifest_hash:
        raise ValueError("Original canary differs from pinned sampling metadata")
    rows = load_lines(manifest)
    applied = load_lines(applicability)
    if len(rows) != 50 or len({r["occurrence_id"] for r in rows}) != 50:
        raise ValueError("Require exactly 50 unique original recanary claims")
    if len(applied) != 50 or {r["occurrence_id"] for r in applied} != {r["occurrence_id"] for r in rows}:
        raise ValueError("Applicability does not cover exactly the recanary")
    pins = json.loads(applicability_metadata.read_text())["hashes"]
    for relative, expected in pins.items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Applicability provenance path must remain repository-relative")
        path = ROOT / path
        if not path.resolve().is_relative_to(ROOT.resolve()) or sha(path.read_bytes()) != expected:
            raise ValueError("Applicability provenance differs from its frozen hash")
    if pins.get(str(applicability.relative_to(ROOT))) != sha(applicability.read_bytes()):
        raise ValueError("Applicability decisions lack their frozen hash")
    by_id = {row["occurrence_id"]: row for row in rows}
    for row in applied:
        claim = by_id[row["occurrence_id"]]
        if any(row[key] != claim[key] for key in ("canary_ordinal", "origin_transform", "predicate", "object")):
            raise ValueError("Applicability is attached to a changed claim")
        if row["scientific_applicability"] not in {"APPLICABLE", "NOT_APPLICABLE"}:
            raise ValueError("Invalid applicability")
    return rows, {row["occurrence_id"]: row for row in applied}, manifest_hash


def timed_decisions(reviews, axis="scientific"):
    """Verify actual start/finish and immutable packet/decision bindings."""
    result = {}
    for path in sorted((reviews / "decisions" / axis).glob("*.json")):
        decision = json.loads(path.read_text())
        receipt_path = reviews / "timing" / axis / path.name
        receipt = json.loads(receipt_path.read_text())
        if receipt.get("axis") != axis or receipt.get("status") != "finished":
            raise ValueError("Missing completed adjudication timer")
        if receipt["edge_id"] != path.stem or sha(path.read_bytes()) != receipt["decision_sha256"]:
            raise ValueError("Timed decision identity/hash mismatch")
        if Path(receipt["decision_path"]).resolve() != path.resolve():
            raise ValueError("Timing receipt points to a different decision")
        packet_path = Path(receipt["packet_path"])
        if sha(packet_path.read_bytes()) != receipt["packet_sha256"]:
            raise ValueError("Packet changed after timed adjudication")
        seconds = receipt["elapsed_seconds"]
        elapsed = (receipt["stopped_monotonic_ns"] - receipt["started_monotonic_ns"]) / 1e9
        if not math.isfinite(seconds) or seconds < 0 or not math.isclose(seconds, elapsed, abs_tol=1e-8):
            raise ValueError("Invalid measured adjudication duration")
        oid = decision["occurrence_id"]
        stage = "primary" if path.stem.endswith("-primary") else "final"
        expected_name = str(decision["canary_ordinal"]) + ("-primary" if stage == "primary" else "")
        if path.stem != expected_name:
            raise ValueError("Timed decision stage/ordinal mismatch")
        if stage in result.setdefault(oid, {}):
            raise ValueError("Duplicate timed decision stage")
        result[oid][stage] = (decision, {
            key: receipt[key] for key in ("started_at", "stopped_at", "elapsed_seconds",
                                         "packet_sha256", "decision_sha256")}, packet_path)
    return result


def validate_packet(packet, row, manifest_hash, applicability):
    if packet["occurrence_id"] != row["occurrence_id"] or packet["manifest_sha256"] != manifest_hash:
        raise ValueError("Packet identity/manifest mismatch")
    if packet["claim_sha256"] != sha(json.dumps(row, sort_keys=True).encode()):
        raise ValueError("Packet claim hash mismatch")
    if packet["applicability"] != applicability:
        raise ValueError("Packet changed scientific applicability")
    for stage in packet.get("stages", []):
        if stage["wall_seconds"] < 0 or stage["api_attempts"] != sum(stage["api_attempts_by_service"].values()):
            raise ValueError("Inconsistent retrieval telemetry")


def validate_not_found(packet):
    """A technical failure or an unexecuted search cannot become NOT_FOUND."""
    if not packet["primary"] and not packet["fallback"]:
        raise ValueError("NOT_FOUND requires completed bounded retrieval")
    for search in packet["fallback"]:
        if search["response"]["status"] != "retrieved":
            raise ValueError("Failed search requires NOT_ASSESSABLE")
    for item in packet["primary"]:
        result = item["result"]
        if result["metadata"]["status"] != "retrieved" or result.get("status") == "invalid_metadata":
            raise ValueError("Unsuccessful citation retrieval requires NOT_ASSESSABLE")
        if result.get("identity_lookup_failure"):
            raise ValueError("Failed citation identity lookup requires NOT_ASSESSABLE")
        full = any(doc["kind"] in {"oa_fulltext", "publisher_fulltext"} for doc in result["documents"])
        if not full:
            if (result.get("fulltext_status") or
                    result.get("fulltext_retrieval", {}).get("status", "retrieved") != "retrieved"):
                raise ValueError("Failed full-text retrieval requires NOT_ASSESSABLE")
            normal = {"not_found", "not_found_or_unconfigured", "no_doi_for_targeted_ladder", "verified_fulltext"}
            if any(item["status"] not in normal for item in result.get("ladder_attempts", [])):
                raise ValueError("Failed full-text ladder requires NOT_ASSESSABLE")
    plans = [stage["targeting_plan"] for stage in packet.get("stages", [])]
    if plans and plans[-1].get("general_queries") and not packet["fallback"]:
        raise ValueError("NOT_FOUND requires completion of the planned fallback queries")


def exact_proof(document, quote):
    if not isinstance(quote, str) or not quote.strip() or len(quote) > 600 or len(quote.split()) > 100:
        raise ValueError("Evidence must be a nonempty short quote (at most 600 characters/100 words)")
    text = document["text"]
    if sha(text.encode()) != document["text_sha256"]:
        raise ValueError("Rebuilt text hash mismatch")
    start = text.find(quote)
    if start < 0:
        raise ValueError("Quote is not an exact substring of rebuilt text")
    return {"quote": quote, "start": start, "end": start + len(quote),
            "text_sha256": document["text_sha256"],
            "response_sha256": document["response"]["response_sha256"],
            "extractor": document["extractor"], "kind": document["kind"]}


def finalize(manifest, applicability, retrieval, reviews, output,
             sampling_metadata=ART / "sampling-metadata.json",
             applicability_metadata=ART / "applicability-metadata.json", edge=None):
    rows, applied, manifest_hash = validate_inputs(manifest, applicability, sampling_metadata, applicability_metadata)
    if edge is not None:
        selected = [row for row in rows if row["canary_ordinal"] == edge]
        if len(selected) != 1:
            raise ValueError("Single-unit verification must select one frozen canary ordinal")
        rows = selected
        applied = {row["occurrence_id"]: applied[row["occurrence_id"]] for row in rows}
    decisions = timed_decisions(reviews)
    if edge is not None:
        decisions = {oid: value for oid, value in decisions.items() if oid in applied}
    applicable_ids = {oid for oid, item in applied.items() if item["scientific_applicability"] == "APPLICABLE"}
    if set(decisions) != applicable_ids:
        raise ValueError("Require exactly one timed decision per applicable edge and none for excluded edges")
    results = []
    with LiteratureCache(retrieval / "cache") as cache:
        for row in rows:
            oid = row["occurrence_id"]
            app = applied[oid]
            packet_path = retrieval / "packets" / (sha(oid.encode()) + ".json")
            result = {key: row[key] for key in ("canary_ordinal", "occurrence_id", "origin_transform")}
            result.update({key: app[key] for key in ("scientific_applicability", "applicability_rule", "applicability_reason")})
            result.update(manifest_sha256=manifest_hash, evidence=[], retrieval_seconds=0,
                          api_attempts=0, api_attempts_by_service={}, adjudication_timing=None)
            if app["scientific_applicability"] == "NOT_APPLICABLE":
                if packet_path.exists():
                    packet = json.loads(packet_path.read_text())
                    validate_packet(packet, row, manifest_hash, "NOT_APPLICABLE")
                    if packet["primary"] or packet["fallback"] or any(s["api_attempts"] for s in packet["stages"]):
                        raise ValueError("Excluded edge was searched")
                result.update(verdict="NOT_APPLICABLE", rationale=app["applicability_reason"],
                              adjudicating_model="deterministic pre-search applicability rule")
                results.append(result)
                continue
            if "final" not in decisions[oid]:
                raise ValueError("Applicable edge lacks final timed adjudication")
            decision, timing, timed_packet_path = decisions[oid]["final"]
            if sha(timed_packet_path.read_bytes()) != sha(packet_path.read_bytes()):
                raise ValueError("Final adjudication snapshot differs from the final retrieval packet")
            packet = json.loads(packet_path.read_text())
            validate_packet(packet, row, manifest_hash, "APPLICABLE")
            segments = []
            if "primary" in decisions[oid]:
                primary_decision, primary_timing, primary_path = decisions[oid]["primary"]
                primary_packet = json.loads(primary_path.read_text())
                validate_packet(primary_packet, row, manifest_hash, "APPLICABLE")
                if primary_packet["fallback"] or any(s["stage"] != "primary" for s in primary_packet["stages"]):
                    raise ValueError("Primary sufficiency snapshot already contains fallback retrieval")
                if "fallback_reason" not in primary_decision or not isinstance(primary_decision["fallback_reason"], str):
                    raise ValueError("Primary sufficiency decision must state whether fallback is needed")
                if packet["fallback"] and not primary_decision["fallback_reason"].strip():
                    raise ValueError("Fallback retrieval needs an authored primary-insufficiency reason")
                segments.append({"review_stage": "primary_sufficiency", **primary_timing})
            segments.append({"review_stage": "final_adjudication", **timing})
            total_timing = {"elapsed_seconds": sum(item["elapsed_seconds"] for item in segments),
                            "segments": segments,
                            "measurement": "Sum of timed reading/judgment intervals; excludes intervening retrieval"}
            if decision["canary_ordinal"] != row["canary_ordinal"]:
                raise ValueError("Decision ordinal mismatch")
            if decision["verdict"] not in VERDICTS or not str(decision.get("rationale", "")).strip():
                raise ValueError("Invalid authored verdict or empty rationale")
            if decision["verdict"] == "NOT_FOUND":
                validate_not_found(packet)
            citations = decision.get("citations", [])
            if decision["verdict"] in {"SUPPORTED", "CONTRADICTED"} and not citations:
                raise ValueError("Directional verdict requires verified quoted evidence")
            services = {}
            for stage in packet["stages"]:
                for service, count in stage["api_attempts_by_service"].items():
                    services[service] = services.get(service, 0) + count
            result.update(verdict=decision["verdict"], rationale=decision["rationale"],
                          adjudicating_model=decision.get("adjudicating_model", MODEL),
                          adjudication_timing=total_timing,
                          retrieval_seconds=sum(s["wall_seconds"] for s in packet["stages"]),
                          api_attempts=sum(services.values()), api_attempts_by_service=services,
                          packet_sha256=timing["packet_sha256"])
            for citation in citations:
                stage = citation.get("stage", "primary")
                if stage not in {"primary", "fallback"}:
                    raise ValueError("Unknown citation retrieval stage")
                papers = [item for item in packet["primary"] if item["retrieval_stage"] == stage]
                paper, document_index = citation["paper"], citation["document"]
                if type(paper) is not int or type(document_index) is not int or paper < 0 or document_index < 0:
                    raise ValueError("Citation indices must be nonnegative integers")
                item = papers[paper]["result"]
                document = item["documents"][document_index]
                rebuilt = RETRIEVAL.replay_document(item, document, cache)
                if not rebuilt.get("doi") and not rebuilt.get("pmid"):
                    raise ValueError("Scientific evidence needs raw-bound DOI/PMID")
                proof = exact_proof(rebuilt, citation["quote"])
                result["evidence"].append({**proof, "doi": rebuilt.get("doi"),
                    "pmid": rebuilt.get("pmid"), "pmcid": rebuilt.get("pmcid"),
                    "title": rebuilt.get("title"), "retrieval_url": rebuilt["response"]["url"],
                    "retrieval_stage": stage, "paper": paper, "document": document_index})
            results.append(result)
    serialized = "".join(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n" for result in results)
    if re.search(r"/(?:[Uu]sers|home)/|Mac[Bb]ook|\.[l]ocal\b|ttys\d+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|BEGIN [A-Z ]*PRIVATE KEY", serialized):
        raise ValueError("Public ledger contains a private identifier")
    output.write_text(serialized)
    print(json.dumps({"ledger_rows": len(results), "applicable": len(applicable_ids),
                      "quotes_verified": sum(len(row["evidence"]) for row in results)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "applicability", "retrieval", "reviews", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--edge", type=int, help="Verify one frozen ordinal for the first live end-to-end unit")
    args = parser.parse_args()
    finalize(args.manifest, args.applicability, args.retrieval, args.reviews, args.output, edge=args.edge)
