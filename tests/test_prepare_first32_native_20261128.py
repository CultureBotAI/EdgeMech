"""Issues228/220: synthetic confinement, quote budgets and native draft limits."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from kg_microbe_reviews import ReviewError

from edgemech.occurrence_packet import build_packet
from edgemech.occurrence_review import validate_occurrence_review

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/adhoc/prepare_first32_native_20261128.py"


@pytest.fixture
def module(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("first32_fixture", SCRIPT)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_quote_budget_counts_repeated_proofs_and_axes(module):
    specs = module.proof_specs()
    budget = module.quote_budget(specs)
    assert {k: v["axis_weighted_words"] for k, v in budget.items()} == {
        "r03-evidence-023": 24, "r03-evidence-015": 24, "r03-evidence-001": 21}
    specs.append(copy.deepcopy(specs[0]))
    with pytest.raises(ValueError, match="budget"):
        module.quote_budget(specs)


@pytest.mark.parametrize("kind", ["existing", "symlink", "traversal", "fifo"])
def test_output_guard_preserves_destinations(tmp_path, monkeypatch, module, kind):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    base = tmp_path / ".temp/first32-worker-20261128"
    monkeypatch.setattr(module, "OUTPUT", base)
    base.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.write_bytes(b"retain")
    destination = base / "attempt"
    if kind == "existing":
        destination.mkdir()
        (destination / "retained").write_bytes(b"prior")
    elif kind == "symlink":
        destination.symlink_to(outside)
    elif kind == "traversal":
        destination = base / ".." / "escaped"
    else:
        os.mkfifo(destination)
    with pytest.raises((ValueError, FileExistsError)):
        module.reserve(destination)
    assert outside.read_bytes() == b"retain"
    assert not (base.parent / "escaped").exists()
    if kind == "existing":
        assert list(destination.iterdir()) == [destination / "retained"]
        assert (destination / "retained").read_bytes() == b"prior"


def synthetic_case(module, tmp_path):
    import author_m5_review_data_20261116 as mechanical
    oid = module.OCCURRENCE
    edge = {"occurrence_id": oid, "subject": "lpsn:46511", "object": "NCBITaxon:1281099",
            "predicate": "biolink:close_match", "relation": "skos:closeMatch",
            "origin_transform": "synthetic/edges.tsv", "transform_row_number": 1,
            "subject_label": "synthetic subject", "object_label": "synthetic object",
            "subject_category": "biolink:OrganismTaxon", "object_category": "biolink:OrganismTaxon",
            "original_subject_node": {"id": "lpsn:46511"},
            "original_object_node": {"id": "NCBITaxon:1281099"}}
    def write(name, value):
        raw = json.dumps(value).encode()
        (tmp_path / name).write_bytes(raw)
        return {"path": name, "sha256": module.digest(raw)}
    source = {"edge": edge, "records": []}
    sp = write("source.json", source)
    packet = build_packet(edge, source, occurrence_input=sp, source_input=sp, root=tmp_path)
    pp = write("packet.json", packet)
    specs = module.proof_specs()
    specs[-1]["reference"] = "packet.json"
    manifest = {"files": [{**pp, "role": "packet", "evidence_ids": ["new-packet"]}]}
    for authority in module.AUTHORITY.values():
        eid = authority["eid"]
        quotes = dict.fromkeys(s["quote"] for s in specs if s["manifest_evidence_id"] == eid)
        raw = ("SYNTHETIC TEST DOCUMENT, NOT RETAINED EVIDENCE\n" + "\n".join(quotes)).encode()
        name = eid + ".txt"
        (tmp_path / name).write_bytes(raw)
        manifest["files"].append({"path": name, "sha256": module.digest(raw),
            "role": "authority", "version": authority["version"], "evidence_ids": [eid]})
    case = {"packet_path": "packet.json", "evidence_ids": ["new-packet", *[a["eid"] for a in module.AUTHORITY.values()]]}
    proofs, evidence = mechanical.make_evidence(tmp_path, manifest, case, specs, "2000-01-01T00:00:00Z")
    sidecar = {"profile": "edgemech-occurrence-review/v1", "occurrence_id": oid, "proofs": proofs}
    side = write("proofs.json", sidecar)
    review = {"schema_version": "1.0.0", "review_id": "20000101T000000Z-synthetic", "kind": "record",
        "repository": "CultureBotAI/EdgeMech", "skill": "edgemech-occurrence-review/v1", "title": "Synthetic only",
        "started_at": "2000-01-01T00:00:00Z", "finished_at": "2000-01-01T00:00:00Z",
        "reviewer": {"identity": "synthetic", "kind": "agent", "independence": "self_review", "independence_basis": "Synthetic test"},
        "completion": "partial", "verdict": "needs_curation", "scientific_review": True, "summary": "Synthetic test",
        "source": {"git_revision": "a" * 40, "state": "working_tree", "inputs": [
            {"path": p["path"], "sha256": p["sha256"], "role": "synthetic"}
            for p in [sp, side, *manifest["files"]]]},
        "scope": {"description": "synthetic", "selection": "synthetic", "coverage": "partial", "population_size": 1, "reviewed_target_ids": [oid]},
        "targets": [{"target_id": oid, "path": "packet.json", "selector": "occurrence_id=" + oid,
                     "label": "synthetic", "kind": "snapshot_row", "ownership_note": "Synthetic fixture"}],
        "checks": [{"check_id": "lineage", "name": "Synthetic missing lineage", "status": "unavailable", "required": True,
                    "target_ids": [oid], "summary": "Synthetic unavailable check"}],
        "evidence": evidence, "assessments": mechanical.make_assessments(module.assessments(specs), oid),
        "findings": [], "actions": [], "limitations": ["Synthetic fixture, no scientific evidence"]}
    return review, sidecar


@pytest.mark.parametrize("mutation", ["none", "completion", "fidelity", "quote", "input", "paper"])
def test_native_draft_replay_and_negative_controls(module, tmp_path, mutation):
    review, sidecar = synthetic_case(module, tmp_path)
    if mutation == "completion":
        review["completion"] = "completed"
    elif mutation == "fidelity":
        target = review["assessments"][-1]
        target["outcome"] = "supported"
        next(d for d in target["dimensions"] if d["name"] == "category")["value"] = "SUPPORTED"
    elif mutation == "quote":
        review["evidence"][0]["quote"] = "NOT IN SYNTHETIC DOCUMENT"
    elif mutation == "input":
        (tmp_path / "r03-evidence-001.txt").write_text("tampered")
    elif mutation == "paper":
        sidecar["proofs"][0]["kind"] = "jats"
    if mutation == "none":
        module.validate_limits(review, sidecar)
        result = validate_occurrence_review(tmp_path, review, "packet.json", "proofs.json")
        assert result["verified_evidence"] == 14
        assert result["verified_quotes"] == 13
        assert result["kg_admissions"] == 0
        assert not (tmp_path / "reviews").exists()
    elif mutation in {"completion", "fidelity", "paper"}:
        with pytest.raises(ValueError):
            module.validate_limits(review, sidecar)
    else:
        with pytest.raises((ValueError, ReviewError)):
            validate_occurrence_review(tmp_path, review, "packet.json", "proofs.json")


def test_existing_attempt_cli_cannot_append_failure(tmp_path):
    scripts = tmp_path / "scripts/adhoc"
    scripts.mkdir(parents=True)
    target = scripts / SCRIPT.name
    target.write_bytes(SCRIPT.read_bytes())
    output = tmp_path / ".temp/first32-worker-20261128/attempt"
    output.mkdir(parents=True)
    (output / "retained").write_bytes(b"prior")
    result = subprocess.run([sys.executable, str(target), "run", "--output", str(output), "--", "true"],
        cwd=tmp_path, capture_output=True, env={"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
    (tmp_path / "stdout").write_bytes(result.stdout)
    (tmp_path / "stderr").write_bytes(result.stderr)
    assert result.returncode != 0
    assert list(output.iterdir()) == [output / "retained"]
    assert (output / "retained").read_bytes() == b"prior"


def test_relative_input_pin_binds_explicit_checkout(module, monkeypatch, tmp_path):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    path = Path("acceptance.json")
    path.write_bytes(b"synthetic acceptance")
    result = module.relative_pin(path)
    assert result == {"path": "acceptance.json", "sha256": module.digest(path.read_bytes())}


def test_actual_clock_uses_pinned_canonical_timestamp_format(module):
    import re
    from datetime import datetime, timezone

    import yaml
    from kg_microbe_governance.artifacts.scripts.record_review import SCHEMA_PATH

    pattern = yaml.safe_load(SCHEMA_PATH.read_text())["types"]["UTCTimestamp"]["pattern"]
    value = module.utc()
    assert re.fullmatch(pattern, value)
    assert abs((datetime.now(timezone.utc) - datetime.fromisoformat(value)).total_seconds()) < 2


def test_canonical_serializer_replays_shared_lists_without_yaml_aliases(module):
    from kg_microbe_reviews import load_document
    shared = ["synthetic-evidence"]
    value = {"first": shared, "second": shared}
    raw = module.serialize_draft(value)
    assert b"&id" not in raw and b"*id" not in raw
    assert load_document(raw) == value


def test_command_receipt_pins_retained_executed_producer(tmp_path, module):
    scripts = tmp_path / "scripts/adhoc"
    scripts.mkdir(parents=True)
    target = scripts / SCRIPT.name
    original = SCRIPT.read_bytes()
    target.write_bytes(original)
    output = tmp_path / ".temp/first32-worker-20261128/run"
    result = subprocess.run([sys.executable, str(target), "run", "--output", str(output), "--",
        sys.executable, "-c", "print('synthetic offline command')"], cwd=tmp_path,
        capture_output=True, env={"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
    (tmp_path / "stdout").write_bytes(result.stdout)
    (tmp_path / "stderr").write_bytes(result.stderr)
    assert result.returncode == 0, result.stderr.decode()
    receipt = json.loads((output / "receipt.json").read_bytes())
    assert receipt["producer"]["path"] == str(output / "producer.py.original")
    assert receipt["producer"]["sha256"] == module.digest(original)
    assert (output / "producer.py.original").read_bytes() == original


def preservation_case(module, monkeypatch, tmp_path):
    science, original = tmp_path / "science", tmp_path / "original"
    science.mkdir()
    original.mkdir()
    monkeypatch.setattr(module, "ROOT", science)
    monkeypatch.setattr(module, "git", lambda *args, **kwargs: b"a" * 40)
    paths = {"dispatch": science / "scripts/adhoc/dispatch_restart_preparation_task_20261128.sh",
             "protected": science / "src/native.py",
             "imported": science / "artifacts/preparation-canary-20261126/summary.json",
             "canonical": science / "reviews/structured/synthetic/review.yaml",
             "unlisted": science / "OTHER.md", "original_worker": original / "preserved"}
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"before")
    acceptance = tmp_path / "acceptance"
    acceptance.mkdir()
    for name, root, selected in (("original", original, [paths["original_worker"]]),
        ("science", science, [p for k, p in paths.items() if k != "original_worker"])):
        (acceptance / f"{name}-checkout-state.json").write_text(json.dumps({
            "root": str(root), "head": "a" * 40, "tracked": [module.pin(p) for p in selected]}))
    finding = tmp_path / "finding.md"
    finding.write_bytes(b"Synthetic filed finding")
    manifest = {"format": "first32-authorized-disjoint-change/v1", "changes": [{
        "path": "scripts/adhoc/dispatch_restart_preparation_task_20261128.sh",
        "before_sha256": module.digest(b"before"), "after_sha256": module.digest(b"authorized after"),
        "reviewed_intermediate_sha256": module.digest(b"intermediate"),
        "finding": {"path": str(finding), "sha256": module.digest(finding.read_bytes())}}]}
    paths["dispatch"].write_bytes(b"authorized after")
    return acceptance, manifest, paths


@pytest.mark.parametrize("change", ["allowed", "unknown_after", "wrong_before", "wrong_path", "finding",
                                    "protected", "imported", "canonical", "unlisted", "original_worker"])
def test_exact_disjoint_change_and_protected_refusals(module, monkeypatch, tmp_path, change):
    acceptance, manifest, paths = preservation_case(module, monkeypatch, tmp_path)
    if change == "unknown_after":
        paths["dispatch"].write_bytes(b"unauthorized successor")
    elif change == "wrong_before":
        manifest["changes"][0]["before_sha256"] = "f" * 64
    elif change == "wrong_path":
        manifest["changes"][0]["path"] = "src/native.py"
    elif change == "finding":
        Path(manifest["changes"][0]["finding"]["path"]).write_bytes(b"changed finding")
    elif change != "allowed":
        paths[change].write_bytes(b"unauthorized protected change")
    if change == "allowed":
        result = module.verify_preservation(acceptance, manifest)
        delta = next(item for item in result if "classification" in item)
        assert delta["before"]["sha256"] == module.digest(b"before")
        assert delta["after"]["sha256"] == module.digest(b"authorized after")
        assert result[-1]["tracked_files_unchanged"] == 4
        assert result[-1]["whole_tree_unchanged_claimed"] is False
        assert result[0]["whole_tree_unchanged_claimed"] is True
    else:
        with pytest.raises(ValueError):
            module.verify_preservation(acceptance, manifest)


def identity_fixture():
    binding = {"expected_thread_id": "synthetic-private-thread", "expected_model": "gpt-6-astra",
               "expected_effort": "ultra", "canonical_reviewer": "edgemech-native-reviewer-01",
               "native_history": "/synthetic/private/history.jsonl"}
    actual = {"native_session": {"session_meta": {"payload": {"id": binding["expected_thread_id"]}},
              "turn_context": {"payload": {"model": "gpt-6-astra", "effort": "ultra"}}}}
    return binding, actual


@pytest.mark.parametrize("bad", [None, "thread", "model", "effort", "pseudonym", "missing"])
def test_private_expected_identity_is_exactly_compared(module, monkeypatch, bad):
    binding, actual = identity_fixture()
    monkeypatch.setattr(module, "git", lambda *args, **kwargs:
        b"5d470683823323e2dd8d72e08c49ade138229dc6" if args[0] == "rev-parse"
        else b"campaign/lbnl-occurrence-preparation-20261128")
    if bad == "thread":
        actual["native_session"]["session_meta"]["payload"]["id"] = "other synthetic thread"
    elif bad in {"model", "effort"}:
        actual["native_session"]["turn_context"]["payload"][bad] = "different"
    elif bad == "pseudonym":
        binding["canonical_reviewer"] = binding["expected_thread_id"]
    elif bad == "missing":
        del binding["expected_thread_id"]
    if bad is None:
        module.check_identity(actual, binding)
    else:
        with pytest.raises(ValueError):
            module.check_identity(actual, binding)


@pytest.mark.parametrize("bad", [None, "identity", "yaml_thread", "md_thread", "absolute_input", "md_path", "pid", "socket", "tty"])
def test_prospective_public_artifact_privacy(module, bad):
    binding, _ = identity_fixture()
    review = {"reviewer": {"identity": binding["canonical_reviewer"]},
              "source": {"inputs": [{"path": ".temp/synthetic/identity-binding.json"}]}, "notes": []}
    markdown = "Synthetic canonical draft\n"
    if bad == "identity":
        review["reviewer"]["identity"] = binding["expected_thread_id"]
    elif bad == "yaml_thread":
        review["notes"].append(binding["expected_thread_id"])
    elif bad == "md_thread":
        markdown += binding["expected_thread_id"]
    elif bad == "absolute_input":
        review["source"]["inputs"][0]["path"] = "/Users/synthetic/private/input.json"
    elif bad == "md_path":
        markdown += "/Users/synthetic/private/runtime"
    elif bad == "pid":
        markdown += "pid: 987654321\n"
    elif bad == "socket":
        markdown += "/private/synthetic/socket\n"
    elif bad == "tty":
        markdown += "/dev/ttys999\n"
    raw = module.serialize_draft(review)
    if bad is None:
        result = module.scan_public_draft(raw, markdown.encode(), binding)
        assert result["status"] == "passed"
        assert result["private_expected_thread_sha256"] == module.digest(binding["expected_thread_id"].encode())
    else:
        with pytest.raises(ValueError):
            module.scan_public_draft(raw, markdown.encode(), binding)
