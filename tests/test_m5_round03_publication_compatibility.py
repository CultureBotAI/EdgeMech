"""Publication keeps a newer runtime separate from immutable original science (#199)."""
import importlib.metadata
import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from kg_microbe_reviews import ReviewError
from kg_microbe_reviews import read_review as actual_read_review
from test_occurrence_review import case as case

from edgemech import occurrence_review

PATH = Path(__file__).parents[1] / "scripts/adhoc/gate_round02_publication_20261116.py"
SPEC = importlib.util.spec_from_file_location("round03_publication", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ROUND = "m5-calibration-20261116-round03"


def test_import_preserves_real_runtime_fingerprint_and_rejects_metadata_drift(tmp_path, monkeypatch):
    """Importing the gate must not double-count metadata already on PYTHONPATH."""
    import run_m5_review_worker_20261116 as worker

    root = tmp_path / "publication"
    source = root / "src"
    scripts = root / "scripts" / "adhoc"
    metadata = source / "m5_bootstrap_fixture-1.0.dist-info"
    metadata.mkdir(parents=True)
    scripts.mkdir(parents=True)
    (root / "uv.lock").write_text("unchanged fixture dependency lock\n")
    (metadata / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: m5-bootstrap-fixture\nVersion: 1.0\n")
    record = metadata / "RECORD"
    record.write_text("original fixture distribution record\n")
    helper = scripts / PATH.name
    helper.write_bytes(PATH.read_bytes())
    monkeypatch.syspath_prepend(str(source))
    monkeypatch.syspath_prepend(str(scripts))
    monkeypatch.setenv("PYTHONPATH", str(source))
    environment = worker.child_environment(root)
    before_paths = list(sys.path)
    before = worker.runtime_bindings(root, environment)
    spec = importlib.util.spec_from_file_location("publication_bootstrap_fixture", helper)
    imported = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imported)
    after = worker.runtime_bindings(root, environment)

    # Real metadata discovery sees the fixture exactly once, and imports do not
    # alter any same-process runtime binding or reorder the caller's import path.
    assert after == before
    assert sys.path == before_paths
    visible = [item for item in importlib.metadata.distributions()
               if item.metadata.get("Name") == "m5-bootstrap-fixture"]
    assert len(visible) == 1

    # This is not a fingerprint normalization: genuine bytes changing in the
    # actual metadata remain visible and the unchanged receipt guard rejects it.
    recorded = {key: before.get(key, "fixture-" + key) for key in worker.RUNTIME_KEYS}
    receipt = root / "receipt.json"
    receipt.write_text(json.dumps({**recorded, "schema": worker.SCHEMA,
                                  "status": "passed", "scope": worker.PRODUCTION_SCOPE}))
    record.write_text("changed fixture distribution record\n")
    changed = {**recorded, **worker.runtime_bindings(root, environment)}
    assert changed["distributions_sha256"] != recorded["distributions_sha256"]
    with pytest.raises(ValueError, match="Canary runtime changed: distributions_sha256"):
        worker.verify_receipt(receipt, changed, root, environment,
                              reviewer_package="fixture-package.json")


def pinned(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else MODULE.encoded(value))
    return {"path": relative, "sha256": MODULE.digest(path.read_bytes())}


def test_round03_does_not_silently_use_legacy_identity():
    assert MODULE.selected_round({}) == MODULE.LEGACY_ROUND
    assert MODULE.selected_round({"round_id": ROUND}) == ROUND
    with pytest.raises(ValueError, match="identifier"):
        MODULE.selected_round({"round_id": "../round03"})


@pytest.mark.parametrize("identity_field,corruption", [
    ("reviewer", None), ("reviewer", "id"), ("reviewer", "model"),
    ("reviewer", "session_id"), ("identity", None), ("missing", None),
])
def test_round03_requires_current_proof_session_identity(tmp_path, identity_field, corruption):
    reviewer = {"id": "reviewer-a", "model": "actual-model", "session_id": "actual-session"}
    axes = {axis: next(iter(values)) for axis, values in MODULE.CATEGORIES.items()}
    case = {"occurrence_id": "original", "assessments": [
        {"axis": axis, "category": value} for axis, value in axes.items()]}
    bindings = {"reviewer-a": {"root": str(tmp_path), "reviewer": reviewer,
        "canonical_identity": "reviewer-a", "cases": {"fresh-05": case},
        "proof_identity_field": "reviewer"}}
    identity = dict(reviewer)
    if corruption:
        identity[corruption] = "different"
    proofs = {} if identity_field == "missing" else {identity_field: identity}
    args = ({"root": str(tmp_path), "reviewer": "reviewer-a", "case_id": "fresh-05"},
            {"review_id": "unique", "reviewer": {"identity": "reviewer-a", "model": "actual-model"}},
            proofs, {"occurrence_id": "original", "assessments": axes}, bindings, set())
    if corruption or identity_field != "reviewer":
        with pytest.raises(ValueError, match="Proof session"):
            MODULE.bind_review(*args)
    else:
        MODULE.bind_review(*args)


@pytest.mark.parametrize("change", [None, "rationale", "proof", "packet"])
def test_publication_cannot_add_evidence_after_initial_seal(tmp_path, change):
    reviewer = {"id": "reviewer-a", "model": "actual-model", "session_id": "actual-session"}
    axes = {axis: next(iter(values)) for axis, values in MODULE.CATEGORIES.items()}
    case = {"occurrence_id": "original", "assessments": [
        {"axis": axis, "category": value} for axis, value in axes.items()]}
    review = {"review_id": "unique", "reviewer": {"identity": "reviewer-a", "model": "actual-model"},
              "summary": "Original rationale"}
    proof = {"reviewer": reviewer}
    entry = {"review": pinned(tmp_path, "draft.json", review),
             "proofs": pinned(tmp_path, "proof.json", proof),
             "packet": pinned(tmp_path, "packet.json", {"occurrence_id": "original"})}
    bindings = {"reviewer-a": {"root": str(tmp_path), "reviewer": reviewer,
        "canonical_identity": "reviewer-a", "cases": {"fresh-05": case},
        "proof_identity_field": "reviewer", "initial_entries": {"fresh-05": entry}}}
    if change == "rationale":
        review["summary"] = "Later rationale with unchanged categories"
    elif change == "proof":
        (tmp_path / "proof.json").write_text('{"reviewer":{},"later_evidence":true}')
    elif change == "packet":
        (tmp_path / "packet.json").write_text('{"occurrence_id":"original","later_input":true}')
    args = ({"root": str(tmp_path), "reviewer": "reviewer-a", "case_id": "fresh-05",
             "proofs": "proof.json", "packet": "packet.json"}, review, proof,
            {"occurrence_id": "original", "assessments": axes}, bindings, set())
    if change:
        with pytest.raises(ValueError, match="initial"):
            MODULE.bind_review(*args)
    else:
        MODULE.bind_review(*args)


def scientific_fixture(tmp_path, monkeypatch):
    coordinator, original = tmp_path / "new", tmp_path / "original"
    coordinator.mkdir()
    original.mkdir()
    for root in (coordinator, original):
        pinned(root, "uv.lock", b"same immutable dependency selection")
        pinned(root, MODULE.COHORT, b"same original cohort")
    helper = pinned(original, MODULE.ROUND_HELPER, b"old frozen helper, never executed by fixture")
    # Deliberately DIFFERENT new coordinator helper: checking old pins here is wrong.
    pinned(coordinator, MODULE.ROUND_HELPER, b"new publication helper")
    manifest = {"round_id": ROUND, "files": [helper]}
    manifest_pin = pinned(original, ".temp/science.json", manifest)
    declaration = {"git_head": "old-science-head", "manifest": manifest_pin}
    monkeypatch.setattr(MODULE, "ROOT", coordinator)
    journal = tmp_path / ".temp" / "attempts"
    journal.mkdir(parents=True)
    monkeypatch.setattr(MODULE, "_VERIFICATION_DIRECTORY", journal)
    monkeypatch.setattr(MODULE, "repository_binding",
                        lambda root, head: {"git_head": head, "repository_identity": "CultureBotAI/EdgeMech",
                                            "repository_origin": "https://github.com/CultureBotAI/EdgeMech.git"})
    return coordinator, original, declaration, manifest


@pytest.mark.parametrize("corruption", [None, "round", "manifest_hash", "helper", "lock", "cohort",
                                       "command_failure", "incomplete"])
def test_scientific_package_replays_original_clone_not_new_coordinator(tmp_path, monkeypatch, corruption):
    coordinator, original, declaration, manifest = scientific_fixture(tmp_path, monkeypatch)
    calls = []
    expected = declaration["manifest"]["sha256"]
    def run(command, **kwargs):
        calls.append((command, kwargs))
        output = {"manifest_sha256": expected, "input_hashes_verified": len(manifest["files"]),
                  "packet_replay": [{}] * (9 if corruption == "incomplete" else 10)}
        return SimpleNamespace(returncode=1 if corruption == "command_failure" else 0,
                               stdout=MODULE.encoded(output), stderr=b"retained diagnostic")
    monkeypatch.setattr(MODULE.subprocess, "run", run)
    if corruption == "round":
        manifest["round_id"] = MODULE.LEGACY_ROUND
        declaration["manifest"] = pinned(original, ".temp/science.json", manifest)
        expected = declaration["manifest"]["sha256"]
    elif corruption == "manifest_hash":
        (original / ".temp/science.json").write_text("{}")
    elif corruption == "helper":
        (original / MODULE.ROUND_HELPER).write_text("changed original verifier")
    elif corruption in {"lock", "cohort"}:
        (original / ("uv.lock" if corruption == "lock" else MODULE.COHORT)).write_text("changed")
    if corruption:
        with pytest.raises(ValueError):
            MODULE.package_binding(original, declaration, ROUND, expected)
    else:
        actual, receipt = MODULE.package_binding(original, declaration, ROUND, expected)
        assert actual == manifest
        assert receipt["manifest"] == declaration["manifest"]
        assert calls[0][0][2] == str(original / MODULE.ROUND_HELPER)
        assert calls[0][1]["cwd"] == original
        assert calls[0][1]["env"]["PYTHONPATH"] == str(original / "src")
        assert (coordinator / MODULE.ROUND_HELPER).read_bytes() != (original / MODULE.ROUND_HELPER).read_bytes()
    if corruption in {"round", "manifest_hash", "helper", "lock", "cohort"}:
        assert calls == []


@pytest.mark.parametrize("corruption", [None, "seal_hash", "manifest", "matrix", "canonical_identity",
                                       "incomplete", "receipt"])
def test_initial_binding_requires_complete_exact_original_seal(tmp_path, monkeypatch, corruption):
    helper = pinned(tmp_path, MODULE.INITIAL_HELPER, b"frozen old seal helper")
    manifest = {"files": [helper]}
    matrix = {"path": ".temp/initial/matrix.json", "sha256": "matrix-hash"}
    seal = {"manifest": ".temp/science.json", "matrix": matrix, "canonical_identity": "reviewer-a",
            "validations": [{"case_id": "case-" + str(index)} for index in range(10)]}
    if corruption in {"manifest", "canonical_identity"}:
        seal[corruption] = "changed"
    elif corruption == "matrix":
        seal["matrix"] = {**matrix, "sha256": "changed"}
    seal_pin = pinned(tmp_path, ".temp/initial/initial-seal.json", seal)
    item = {"canonical_identity": "reviewer-a",
            "scientific": {"manifest": {"path": ".temp/science.json", "sha256": "package"},
                           "initial_seal": seal_pin}}
    receipt = {"initial_seal": seal_pin}
    if corruption == "receipt":
        receipt = {"initial_seal": {**seal_pin, "sha256": "other"}}
    elif corruption == "seal_hash":
        (tmp_path / seal_pin["path"]).write_text("{}")
    calls = []
    def replay(*args):
        calls.append(args)
        return ({"status": "passed", "cases": 10, "authored_axes": 59 if corruption == "incomplete" else 60,
                 "seal": seal_pin, "matrix": matrix}, {"exit_code": 0})
    monkeypatch.setattr(MODULE, "frozen_command", replay)
    if corruption:
        with pytest.raises(ValueError):
            MODULE.initial_binding(tmp_path, item, matrix, receipt, manifest, {})
    else:
        result, entries = MODULE.initial_binding(tmp_path, item, matrix, receipt, manifest, {})
        assert len(entries) == 10 and result["initial_seal"] == seal_pin
        assert calls[0][0] == tmp_path and calls[0][2] == MODULE.INITIAL_HELPER


@pytest.mark.parametrize("round_id", [MODULE.LEGACY_ROUND, ROUND])
def test_not_assessed_is_preserved_in_bounded_derivative(tmp_path, monkeypatch, round_id):
    import copy
    case = {"case_id": "fresh-47", "occurrence_id": "original", "packet_path": "packet.json"}
    review = {"review_id": "operational", "completion": "partial", "verdict": "not_assessed",
              "scientific_review": False, "assessments": [
                  {"dimensions": [{"name": "axis", "value": axis}, {"name": "category", "value": category},
                                  {"name": "scope", "value": "Operational only"}]}
                  for axis, category in {"claim": "NOT_ASSESSABLE", "literature": "UNAVAILABLE",
                      "relation": "UNRESOLVED", "subject_node": "UNRESOLVED", "object_node": "UNRESOLVED",
                      "source_fidelity": "NOT_ASSESSABLE"}.items()]}
    pinned(tmp_path, "review.json", review)
    pinned(tmp_path, "proof.json", {"proofs": []})
    pinned(tmp_path, "packet.json", {"occurrence_id": "original"})
    config = {"mode": "canary", "round_id": round_id, "package_sha256": "original-package",
              "scientific": {"root": str(tmp_path), "manifest": pinned(
                  tmp_path, ".temp/science.json", {"cases": [case]})},
              "reviews": [{"root": str(tmp_path), "reviewer": "operational-canary",
              "case_id": "fresh-47", "review": "review.json", "proofs": "proof.json", "packet": "packet.json"}]}
    before = copy.deepcopy(review)
    monkeypatch.setattr(MODULE, "coverage", lambda config: {"cases": [case]})
    monkeypatch.setattr(MODULE, "publication_runtime", lambda config: {"runtime_id": "publication-01"})
    monkeypatch.setattr(MODULE, "canary_context", lambda config: {})
    monkeypatch.setattr(MODULE, "canonical_pair", lambda *args: {"scope": "canonical fixture"})
    monkeypatch.setattr(MODULE, "package_binding", lambda *args: ({"cases": [case]}, {}))
    monkeypatch.setattr(MODULE, "bind_original_inputs", lambda *args: None)
    monkeypatch.setattr(MODULE, "quotation_catalog", lambda *args: [])
    monkeypatch.setattr(MODULE, "review_replay", lambda *args: (
        {"occurrence_id": "original"}, {"status": "passed", "scope": "fixture profile validation"}))
    files, gate = MODULE.derive(config)
    projection = json.loads(files["operational-canary-fresh-47.json"])
    assert projection["verdict"] == "not_assessed" and projection["completion"] == "partial"
    assert not projection["calibration_rating"]
    assert projection["canonical_persistence_asserted"] == (round_id != MODULE.LEGACY_ROUND)
    assert projection["quotation_words"] == 0 and len(files) == 3
    assert projection["round_id"] == round_id
    assert projection["scientific_package_sha256"] == "original-package"
    assert "scientific" in gate["scope"].lower()
    assert json.loads((tmp_path / "review.json").read_bytes()) == before


@pytest.mark.parametrize("mismatch", ["round", "package"])
def test_round03_matrices_cannot_be_relabelled_to_fit_package(tmp_path, monkeypatch, mismatch):
    config = {"mode": "round", "round_id": ROUND, "package_sha256": "scientific-package", "reviewers": {}}
    for rid in ("reviewer-a", "reviewer-b"):
        reviewer = {"id": rid, "model": "actual-model", "session_id": rid + "-session"}
        matrix = {"round_id": MODULE.LEGACY_ROUND if mismatch == "round" else ROUND,
                  "package_sha256": "other-package" if mismatch == "package" else "scientific-package",
                  "reviewer": reviewer, "cases": []}
        pin = pinned(tmp_path, rid + ".json", matrix)
        pinned(tmp_path, rid + ".json.receipt.json", {
            "matrix_path": pin["path"], "matrix_sha256": pin["sha256"],
            "reviewer": reviewer, "package_sha256": matrix["package_sha256"]})
        config["reviewers"][rid] = {"root": str(tmp_path), "matrix": pin["path"],
                                    "canonical_identity": rid, "scientific": {}}
    monkeypatch.setattr(MODULE, "package_binding", lambda *args: ({}, {}))
    with pytest.raises(ValueError):
        MODULE.reviewer_bindings(config)

@pytest.mark.parametrize("failure", [None, "stale_parent", "missing_pin", "same_round",
                                   "same_package", "incomplete_package"])
def test_new_publication_runtime_requires_new_package_and_live_parent_replay(tmp_path, monkeypatch, failure):
    import sys
    root = tmp_path / "publication"
    root.mkdir()
    gate_pin = pinned(root, MODULE.PUBLICATION_HELPER, b"new reviewed publication helper")
    round_pin = pinned(root, MODULE.ROUND_HELPER, b"current round verifier")
    worker_pin = pinned(root, "scripts/adhoc/run_m5_review_worker_20261116.py", b"current parent launcher")
    codex_pin = pinned(root, "bin/codex", b"native fixture identity")
    manifest = {"round_id": ROUND + "-publication01", "files": [gate_pin, round_pin, worker_pin]}
    if failure == "missing_pin":
        manifest["files"] = [round_pin, worker_pin]
    if failure == "same_round":
        manifest["round_id"] = ROUND
    manifest_pin = pinned(root, ".temp/publication-package/manifest.json", manifest)
    parent_pin = pinned(root, ".temp/new-parent/canary-receipt.json",
                        {"codex_path": str(root / codex_pin["path"])})
    declaration = {"git_head": "new-publication-head", "runtime_id": manifest["round_id"],
                   "manifest": manifest_pin, "production_receipt": parent_pin}
    config = {"round_id": ROUND, "package_sha256": manifest_pin["sha256"] if failure == "same_package"
              else "original-scientific-package", "publication_runtime": declaration}
    monkeypatch.setattr(MODULE, "ROOT", root)
    monkeypatch.setattr(MODULE, "__file__", str(root / MODULE.PUBLICATION_HELPER))
    repository = {"git_head": "new-publication-head", "repository_identity": "CultureBotAI/EdgeMech",
                  "repository_origin": "https://github.com/CultureBotAI/EdgeMech.git"}
    monkeypatch.setattr(MODULE, "repository_binding", lambda *args: repository)
    package_calls, receipt_calls = [], []
    def package_check(*args):
        package_calls.append(args)
        return ({"manifest_sha256": manifest_pin["sha256"],
                 "input_hashes_verified": len(manifest["files"]),
                 "packet_replay": [{}] * (9 if failure == "incomplete_package" else 10)},
                {"exit_code": 0})
    def verify(path, bindings, selected_root, environment, *, reviewer_package):
        receipt_calls.append((path, bindings, selected_root, environment, reviewer_package))
        if failure == "stale_parent":
            raise ValueError("Canary runtime changed: helper_sha256")
        assert path == root / parent_pin["path"]
        assert reviewer_package == manifest_pin["path"]
        assert selected_root == root and bindings["git_head"] == "new-publication-head"
        return {"production_replay": {"verified": True}}
    fake_worker = SimpleNamespace(
        HELPER=root / worker_pin["path"],
        execution_inventory=lambda selected_root: [gate_pin, round_pin, worker_pin],
        digest=lambda path: MODULE.digest(Path(path).read_bytes()),
        child_environment=lambda selected_root: {"PYTHONPATH": str(selected_root / "src")},
        runtime_bindings=lambda *args: {"environment_sha256": "new-environment"},
        repository_bindings=lambda selected_root: {key: value for key, value in repository.items()
                                                   if key != "git_head"},
        verify_receipt=verify)
    monkeypatch.setitem(sys.modules, "run_m5_review_worker_20261116", fake_worker)
    monkeypatch.setattr(MODULE, "frozen_command", package_check)
    if failure:
        with pytest.raises(ValueError):
            MODULE.publication_runtime(config)
    else:
        checked = MODULE.publication_runtime(config)
        assert checked["production_receipt"] == parent_pin and len(receipt_calls) == 1
        assert checked["manifest"] == manifest_pin
        assert package_calls[0][0] == root
    if failure in {"missing_pin", "same_round", "same_package", "incomplete_package"}:
        assert receipt_calls == []


def test_nondefault_round_requires_identified_new_publication_runtime():
    with pytest.raises(KeyError, match="publication_runtime"):
        MODULE.publication_runtime({"round_id": ROUND})


def test_round03_canary_cannot_rebind_to_unfrozen_packet(tmp_path, monkeypatch):
    spec = {"root": str(tmp_path), "reviewer": "operational-canary", "case_id": "fresh-47",
            "review": "review.json", "proofs": "proofs.json", "packet": "substituted.json"}
    config = {"mode": "canary", "round_id": ROUND, "package_sha256": "original",
              "scientific": {"root": str(tmp_path)}, "reviews": [spec]}
    case = {"case_id": "fresh-47", "occurrence_id": "original", "packet_path": "original.json"}
    monkeypatch.setattr(MODULE, "publication_runtime", lambda config: {})
    monkeypatch.setattr(MODULE, "canary_context", lambda config: {})
    monkeypatch.setattr(MODULE, "coverage", lambda config: {"cases": [case]})
    monkeypatch.setattr(MODULE, "package_binding", lambda *args: ({"cases": [case]}, {}))
    with pytest.raises(ValueError, match="packet differs"):
        MODULE.derive(config)


def test_round03_reviewer_binding_uses_each_original_clone(tmp_path, monkeypatch):
    config = {"mode": "round", "round_id": ROUND, "package_sha256": "original-package", "reviewers": {}}
    calls = []
    ids = ["case-" + str(index) for index in range(10)]
    for rid in ("reviewer-a", "reviewer-b"):
        root = tmp_path / rid
        root.mkdir()
        reviewer = {"id": rid, "model": "actual-model", "session_id": rid + "-session"}
        matrix = {"round_id": ROUND, "package_sha256": "original-package", "reviewer": reviewer,
                  "cases": [{"case_id": case_id} for case_id in ids]}
        pin = pinned(root, ".temp/initial/matrix.json", matrix)
        pinned(root, pin["path"] + ".receipt.json", {
            "matrix_path": pin["path"], "matrix_sha256": pin["sha256"],
            "reviewer": reviewer, "package_sha256": "original-package"})
        config["reviewers"][rid] = {"root": str(root), "matrix": pin["path"],
                                    "canonical_identity": rid, "scientific": {"git_head": "original"}}
    def package(root, declaration, round_id, package_sha256):
        calls.append(root)
        assert declaration["git_head"] == "original" and round_id == ROUND
        assert package_sha256 == "original-package"
        return {}, {"original_root": str(root)}
    monkeypatch.setattr(MODULE, "package_binding", package)
    monkeypatch.setattr(MODULE, "initial_binding", lambda root, item, pin, receipt, manifest, package: (
        {"package": package}, {case_id: {} for case_id in ids}))
    result = MODULE.reviewer_bindings(config)
    assert calls == [tmp_path / "reviewer-a", tmp_path / "reviewer-b"]
    assert all(value["proof_identity_field"] == "reviewer" for value in result.values())
    assert result["reviewer-a"]["scientific"]["package"]["original_root"] == str(calls[0])


def test_conflicting_current_and_legacy_identity_is_rejected(tmp_path):
    reviewer = {"id": "reviewer-a", "model": "actual-model", "session_id": "actual-session"}
    bindings = {"reviewer-a": {"root": str(tmp_path), "reviewer": reviewer,
        "canonical_identity": "reviewer-a", "proof_identity_field": "reviewer"}}
    proof = {"reviewer": reviewer, "identity": {**reviewer, "session_id": "different"}}
    with pytest.raises(ValueError, match="Conflicting"):
        MODULE.bind_review({"root": str(tmp_path), "reviewer": "reviewer-a"},
                           {"review_id": "unique", "reviewer": {
                               "identity": "reviewer-a", "model": "actual-model"}},
                           proof, {}, bindings, set())


def test_failed_verifier_preserves_real_private_diagnostics_before_projection(tmp_path, monkeypatch):
    helper = pinned(tmp_path, MODULE.ROUND_HELPER, b"frozen verifier")
    manifest = {"files": [helper]}
    monkeypatch.setattr(MODULE.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(
        returncode=7, stdout=b"partial validator output", stderr=b"exact failed witness diagnostic"))
    def derive(config):
        MODULE.frozen_command(tmp_path, manifest, MODULE.ROUND_HELPER, ["verify"])
    monkeypatch.setattr(MODULE, "derive", derive)
    stage = tmp_path / ".temp" / "failed-stage"
    with pytest.raises(ValueError, match="diagnostics retained"):
        MODULE.create({}, stage)
    assert json.loads((stage / "failure.json").read_bytes())["published"] is False
    assert not (stage / "receipt.json").exists() and not (stage / "proposed-public").exists()
    attempts = list(stage.glob("verification-*/attempt-*"))
    assert len(attempts) == 1
    assert (attempts[0] / "stdout.log").read_bytes() == b"partial validator output"
    assert (attempts[0] / "stderr.log").read_bytes() == b"exact failed witness diagnostic"
    assert json.loads((attempts[0] / "result.json").read_bytes())["exit_code"] == 7
    assert MODULE._VERIFICATION_DIRECTORY is None


@pytest.mark.parametrize("damage", [None, "draft_path", "missing_markdown", "shared_mismatch",
                                    "check_failure", "changed_after_check", "wrong_occurrence"])
def test_modern_canonical_mode_requires_real_pair_and_original_cli(tmp_path, monkeypatch, damage):
    review = {"review_id": "original-review", "targets": [{"target_id": "original-occurrence"}]}
    expected = f"{MODULE.REPORT_ROOT}/original-review/review.yaml"
    pinned(tmp_path, expected, review)
    markdown = str(Path(expected).with_name("review.md"))
    pinned(tmp_path, markdown, b"matching shared Markdown fixture")
    spec = {"review": "draft.json" if damage == "draft_path" else expected,
            "packet": "packet.json", "proofs": "proofs.json"}
    calls, reads = [], []
    def read(root, path):
        reads.append((root, path))
        if damage == "missing_markdown":
            raise ValueError("Missing Markdown companion")
        if damage == "shared_mismatch" or (damage == "changed_after_check" and len(reads) == 2):
            return {**review, "changed": True}
        return dict(review)
    def command(root, manifest, helper, args, *, module):
        calls.append((root, helper, args, module))
        if damage == "check_failure":
            raise ValueError("Original canonical check failed; diagnostics retained")
        return ({"occurrence_id": "different" if damage == "wrong_occurrence" else "original-occurrence"},
                {"exit_code": 0})
    monkeypatch.setattr(MODULE, "read_review", read)
    monkeypatch.setattr(MODULE, "frozen_command", command)
    if damage:
        with pytest.raises(ValueError):
            MODULE.canonical_pair(tmp_path, review, spec, {})
    else:
        result = MODULE.canonical_pair(tmp_path, review, spec, {})
        assert result["review"]["path"] == expected and result["markdown"]["path"] == markdown
        assert calls == [(tmp_path, MODULE.OCCURRENCE_HELPER,
                          ["check", "--root", str(tmp_path), "--review", expected,
                           "--packet", "packet.json", "--proofs", "proofs.json"], True)]
        assert not any("save" == value for value in calls[0][2])
    if damage == "draft_path":
        assert reads == calls == []


def derivative_fixture(tmp_path, monkeypatch):
    cohort = json.loads((MODULE.ROOT / MODULE.COHORT).read_bytes())
    pinned(tmp_path, MODULE.COHORT, cohort)
    roots = {rid: tmp_path / rid for rid in ("reviewer-a", "reviewer-b")}
    for root in roots.values():
        root.mkdir()
    science = {"git_head": "original-head", "manifest": {"path": ".temp/science.json", "sha256": "science"}}
    base = {"mode": "round", "round_id": ROUND, "package_sha256": "science",
            "preparer": "coordinator", "source_mode": "canonical_review",
            "publication_runtime": {"runtime_id": "publication01", "manifest": {"sha256": "new"},
                                    "production_receipt": {"sha256": "new-parent"}, "git_head": "new-head"},
            "reviewers": {rid: {"root": str(root), "scientific": science, "canonical_identity": rid}
                          for rid, root in roots.items()},
            "reviews": [{"root": str(root), "reviewer": rid, "case_id": case["case_id"],
                         "review": f"reviews/{case['case_id']}.yaml"}
                        for rid, root in roots.items() for case in cohort["cases"]]}
    base_pin = pinned(tmp_path, ".temp/batch-base.json", base)
    canary = {key: base[key] for key in ("round_id", "package_sha256", "preparer",
                                       "source_mode", "publication_runtime")}
    canary.update(mode="canary", batch_config=base_pin,
                  scientific={**science, "root": str(roots["reviewer-a"])},
                  reviews=[{"root": str(roots["reviewer-a"]), "reviewer": "operational-canary",
                            "case_id": "fresh-47", "review": "reviews/operational/review.yaml"}])
    monkeypatch.setattr(MODULE, "ROOT", tmp_path)
    return base, canary


@pytest.mark.parametrize("damage", [None, "round", "package", "runtime", "parent", "original_head",
                                    "original_manifest", "other_clone", "other_case", "authored_input"])
def test_canary_context_binds_same_actual_full_batch(tmp_path, monkeypatch, damage):
    import copy
    base, canary = derivative_fixture(tmp_path, monkeypatch)
    canary = copy.deepcopy(canary)
    if damage == "round":
        canary["round_id"] = MODULE.LEGACY_ROUND
    elif damage == "package":
        canary["package_sha256"] = "other"
    elif damage in {"runtime", "parent"}:
        canary["publication_runtime"]["runtime_id" if damage == "runtime" else "production_receipt"] = "other"
    elif damage in {"original_head", "original_manifest"}:
        canary["scientific"]["git_head" if damage == "original_head" else "manifest"] = "other"
    elif damage == "other_clone":
        canary["scientific"]["root"] = str(tmp_path / "coordinator")
    elif damage == "other_case":
        canary["reviews"][0]["case_id"] = "fresh-05"
    elif damage == "authored_input":
        canary["source_mode"] = "authored_input"
    if damage:
        with pytest.raises(ValueError):
            MODULE.canary_context(canary)
    else:
        assert MODULE.canary_context(canary) == base


@pytest.mark.parametrize("source_mode", ["canonical_review", "authored_input"])
def test_full_round_cannot_bypass_derivative_canary_or_canonical_path(tmp_path, monkeypatch, source_mode):
    base, _ = derivative_fixture(tmp_path, monkeypatch)
    base["source_mode"] = source_mode
    monkeypatch.setattr(MODULE, "publication_runtime", lambda config: {})
    with pytest.raises((ValueError, KeyError)):
        MODULE.derive(base)  # No derivative_canary: must fail before opening any twenty-pair input.


@pytest.mark.parametrize("damage", [None, "changed_config", "changed_file", "stale_helper",
                                    "changed_batch", "uninspected", "same_inspector"])
def test_round_replays_actual_three_file_canary_and_exact_inspection(tmp_path, monkeypatch, damage):
    import copy
    base, canary = derivative_fixture(tmp_path, monkeypatch)
    config_pin = pinned(tmp_path, ".temp/canary-config.json", canary)
    stage_relative = ".temp/derivative-stage"
    stage = tmp_path / stage_relative
    files = {name: MODULE.encoded({"quotations": 0}) for name in (
        "operational-canary-fresh-47.json", "quote-inventory.json", "publication-gate.json")}
    for name, raw in files.items():
        pinned(stage, "proposed-public/" + name, raw)
    pins = [{"path": name, "sha256": MODULE.digest(raw)} for name, raw in sorted(files.items())]
    gate = {"passed": True}
    receipt_pin = pinned(tmp_path, stage_relative + "/receipt.json", {
        "config_sha256": MODULE.digest(MODULE.encoded(canary)),
        "helper_sha256": "old-helper" if damage == "stale_helper" else MODULE.digest(Path(MODULE.__file__).read_bytes()),
        "public_file_pins": pins, "gate": gate, "published": False})
    inspection_pin = pinned(tmp_path, ".temp/canary-inspection.json", {
        "reviewer": "coordinator" if damage == "same_inspector" else "independent-reviewer",
        "all_files_inspected": damage != "uninspected", "canonical_pair_inspected": True,
        "config": config_pin, "receipt": receipt_pin, "public_file_pins": pins})
    config = copy.deepcopy(base)
    config["derivative_canary"] = {"config": config_pin, "stage": stage_relative,
                                  "receipt": receipt_pin, "inspection": inspection_pin}
    if damage == "changed_config":
        (tmp_path / config_pin["path"]).write_bytes(MODULE.encoded(canary) + b" ")
    elif damage == "changed_file":
        (stage / "proposed-public/operational-canary-fresh-47.json").write_text("changed")
    elif damage == "changed_batch":
        config["reviews"][0]["review"] = "different-canonical.yaml"
    replayed = []
    def derive(selected):
        replayed.append(selected)
        assert selected == canary
        return files, gate
    monkeypatch.setattr(MODULE, "derive", derive)
    if damage:
        with pytest.raises(ValueError):
            MODULE.derivative_canary(config)
    else:
        result = MODULE.derivative_canary(config)
        assert replayed == [canary] and result["receipt"] == receipt_pin
        assert result["public_file_pins"] == pins


@pytest.mark.parametrize("damage", [None, "missing_markdown", "altered_markdown", "identical_draft"])
def test_real_shared_canonical_pair_boundary_preserves_or_rejects_saved_artifacts(case, monkeypatch, damage):
    """Real profile save and real shared reader; only the subsequent CLI process is mocked."""
    root, authored, _ = case
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin",
                    "https://github.com/CultureBotAI/EdgeMech.git"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty",
                    "-qm", "Synthetic canonical persistence fixture"], check=True)
    authored["source"]["git_revision"] = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    original = deepcopy(authored)
    saved = occurrence_review.save_occurrence_review(root, authored, "packet.json", "proofs.json")
    relative = saved["review"]
    yaml_path = root / relative
    markdown_path = yaml_path.with_name("review.md")
    before_yaml, before_markdown = yaml_path.read_bytes(), markdown_path.read_bytes()
    assert MODULE.read_review is actual_read_review
    assert actual_read_review(root, relative) == original
    calls = []
    def canonical_check(selected_root, manifest, helper, arguments, *, module):
        calls.append((selected_root, helper, arguments, module))
        assert selected_root == root and helper == MODULE.OCCURRENCE_HELPER and module
        assert arguments[0] == "check" and "save" not in arguments
        return ({"occurrence_id": original["targets"][0]["target_id"]}, {"exit_code": 0})
    monkeypatch.setattr(MODULE, "frozen_command", canonical_check)
    spec = {"review": relative, "packet": "packet.json", "proofs": "proofs.json"}
    if damage == "missing_markdown":
        markdown_path.unlink()
    elif damage == "altered_markdown":
        markdown_path.write_bytes(before_markdown + b"\nUnauthorized Markdown-only alteration.\n")
    elif damage == "identical_draft":
        (root / "identical-draft.json").write_bytes(MODULE.encoded(original))
        spec["review"] = "identical-draft.json"
    if damage is None:
        checked = MODULE.canonical_pair(root, authored, spec, {})
        assert len(calls) == 1 and checked["review"]["sha256"] == MODULE.digest(before_yaml)
        assert checked["markdown"]["sha256"] == MODULE.digest(before_markdown)
        assert actual_read_review(root, relative) == original
    else:
        with pytest.raises((ReviewError, ValueError, OSError)):
            MODULE.canonical_pair(root, authored, spec, {})
        assert calls == []  # Real persistence/path boundary rejects before any canonical child check.
    assert authored == original and yaml_path.read_bytes() == before_yaml
    if damage == "missing_markdown":
        assert not markdown_path.exists()
    elif damage == "altered_markdown":
        assert markdown_path.read_bytes() == before_markdown + b"\nUnauthorized Markdown-only alteration.\n"
    else:
        assert markdown_path.read_bytes() == before_markdown
