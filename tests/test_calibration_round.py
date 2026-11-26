"""Initial agreement cannot grant a scientific pass or conceal changed input bytes."""

from __future__ import annotations

import importlib.util
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest
from kg_microbe_curation.identity import sha256_json

from edgemech.occurrence_packet import build_packet

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/adhoc/calibration_round_20261116.py"


@pytest.fixture
def round_inputs(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("calibration_round", HELPER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.original_baseline = m.baseline
    root = tmp_path.resolve()

    def put(path, value):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value))

    protocol = json.loads((ROOT / m.PROTOCOL).read_text())
    cohort = json.loads((ROOT / m.COHORT).read_text())
    files = []
    for path, role, extra in [
        ("instructions.md", "instructions", {}),
        ("adapter.py", "proof_adapter", {}),
        ("authority.txt", "authority", {"version": "fixture-1", "evidence_ids": ["authority"]}),
        ("evidence.txt", "evidence", {"evidence_ids": ["paper"]}),
    ]:
        (root / path).write_text("synthetic fixture, not scientific evidence\n")
        files.append({"path": path, "role": role, **extra})
    for path in sorted(m.RUNTIME_PATHS):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, root / path)
        files.append({"path": path, "role": "proof_adapter"})
    cases = []
    for case in cohort["cases"]:
        cid = case["case_id"]
        edge = deepcopy(case["original_assertion"])
        for side in ("subject", "object"):
            node = {"id": edge[side]}
            edge["original_" + side + "_node"] = node
            case["endpoints"][side]["private_record_sha256"] = sha256_json(node)
        # This fixture exercises packet provenance; its empty rows are not evidence.
        source = {"edge": edge, "records": []}
        op, sp, pp = (f"cases/{cid}/{name}.json" for name in ("occurrence", "source", "packet"))
        put(op, edge)
        put(sp, source)
        packet = build_packet(edge, source,
                              occurrence_input={"path": op, "sha256": m.digest((root / op).read_bytes())},
                              source_input={"path": sp, "sha256": m.digest((root / sp).read_bytes())},
                              root=root)
        put(pp, packet)
        vp = f"cases/{cid}/view.json"
        put(vp, {key: packet[key] for key in m.VIEW_FIELDS})
        files.extend({"path": path, "role": role} for path, role in
                     ((op, "occurrence"), (sp, "source"), (pp, "packet"), (vp, "view")))
        cases.append({"case_id": cid, "packet_path": pp, "reviewer_view_path": vp,
                      "evidence_ids": ["paper", "authority"]})
    put(m.PROTOCOL, protocol)
    put(m.COHORT, cohort)
    for path in ("docs/record-review-profile.md", "scripts/adhoc/calibration_round_20261116.py"):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, root / path)
    monkeypatch.setattr(m, "baseline", lambda r: (protocol, cohort))
    config = {"round_id": "test-round", "files": files, "cases": cases}
    put("config.json", config)
    m.freeze(root, "config.json", "manifest.json")
    return m, root, protocol, cohort, config, put


def matrix_fixture(m, root, cohort, rid="a", resolved=False):
    selected = {"claim": "SUPPORTED_AS_STATED", "literature": "SUPPORTS",
                "relation": "CORRECT", "subject_node": "CORRECT", "object_node": "INCORRECT",
                "source_fidelity": "SUPPORTED"} if resolved else {
                    "claim": "INSUFFICIENT_EVIDENCE", "literature": "UNAVAILABLE",
                    "relation": "UNRESOLVED", "subject_node": "UNRESOLVED",
                    "object_node": "UNRESOLVED", "source_fidelity": "NOT_ASSESSABLE"}
    return {"round_id": "test-round", "package_sha256": m.digest((root / "manifest.json").read_bytes()),
            "reviewer": {"id": rid, "model": "fixture-model", "session_id": "session-" + rid,
                         "historical_exposure": "synthetic test only"},
            "cases": [{"case_id": c["case_id"], "occurrence_id": c["occurrence_id"],
                       "assessments": [{"axis": axis, "category": category,
                                        "scope": "exact original fixture occurrence",
                                        "rationale": "synthetic test rationale",
                                        "evidence_ids": ["paper"] if resolved else [],
                                        "dimensions": {key: "explicit fixture limit" for key in m.DETAILS[axis]}}
                                       for axis, category in selected.items()]} for c in cohort["cases"]]}


def seal_pair(data, mutate=None, resolved=False):
    m, root, _, cohort, _, put = data
    a = matrix_fixture(m, root, cohort, "a", resolved)
    b = matrix_fixture(m, root, cohort, "b", resolved)
    if mutate:
        mutate(b)
    for rid, matrix in (("a", a), ("b", b)):
        put(rid + "-draft.json", matrix)
        m.save_matrix(root, "manifest.json", rid + "-draft.json", rid + ".json")
    return m.compare(root, "manifest.json", "a.json", "b.json")


def test_canary_replays_one_case_and_full_verify_replays_all(round_inputs):
    m, root, *_ = round_inputs
    assert len(m.verify(root, "manifest.json", "fresh-47")["packet_replay"]) == 1
    assert len(m.verify(root, "manifest.json")["packet_replay"]) == 10


def test_changed_pin_and_changed_preregistered_baseline_fail(round_inputs):
    m, root, *_ = round_inputs
    (root / "authority.txt").write_text("changed")
    with pytest.raises(ValueError, match="Pinned input changed"):
        m.verify(root, "manifest.json")
    with pytest.raises(ValueError, match="Preregistered baseline changed"):
        m.original_baseline(root)
    assert m.original_baseline(ROOT)[0]["thresholds"]["initial_exact_category_agreement"]["minimum"] == 54


@pytest.mark.parametrize("missing_path", [
    "src/edgemech/occurrence_packet.py", "src/edgemech/occurrence_review.py",
    "src/edgemech/literature_cache.py", "src/edgemech/contract-pins.json",
    "src/edgemech/storage/parquet.py", "src/edgemech/pins.py", "uv.lock",
    "schema/record_review.yaml",
])
def test_every_runtime_pin_required_at_freeze_and_verify(round_inputs, missing_path):
    m, root, _, _, config, put = round_inputs
    config["files"] = [item for item in config["files"] if item["path"] != missing_path]
    put("missing-runtime.json", config)
    with pytest.raises(ValueError, match="Missing required adapter/runtime pins"):
        m.freeze(root, "missing-runtime.json", "invalid-manifest.json")
    assert not (root / "invalid-manifest.json").exists()
    # A hand-authored manifest must not bypass the freeze guard.
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["files"] = [item for item in manifest["files"] if item["path"] != missing_path]
    put("missing-runtime-manifest.json", manifest)
    with pytest.raises(ValueError, match="Missing required adapter/runtime pins"):
        m.verify(root, "missing-runtime-manifest.json")


@pytest.mark.parametrize("changed_path", [
    "src/edgemech/occurrence_packet.py", "src/edgemech/occurrence_review.py",
    "src/edgemech/literature_cache.py", "src/edgemech/contract-pins.json",
    "src/edgemech/storage/parquet.py", "src/edgemech/pins.py", "uv.lock",
    "schema/record_review.yaml",
])
def test_changed_adapter_or_runtime_bytes_fail_replay(round_inputs, changed_path):
    m, root, *_ = round_inputs
    path = root / changed_path
    path.write_bytes(path.read_bytes() + b"\nchanged after freeze\n")
    with pytest.raises(ValueError, match="Pinned input changed"):
        m.verify(root, "manifest.json", "fresh-47")


@pytest.mark.parametrize("mutation", [
    lambda d: d["cases"].pop(),
    lambda d: d["cases"].append(d["cases"][0]),
    lambda d: d["cases"][0]["assessments"].pop(),
    lambda d: d["cases"][0]["assessments"].append(d["cases"][0]["assessments"][0]),
    lambda d: d["cases"][0]["assessments"][0].update(category="UNASSESSED"),
    lambda d: d["cases"][0]["assessments"][0].update(dimensions={}),
    lambda d: d["cases"][0]["assessments"][0].update(evidence_ids=["not-pinned"]),
    lambda d: d["cases"][0]["assessments"][0].update(category="SUPPORTED_AS_STATED"),
    lambda d: d["reviewer"].update(model="configured_default"),
])
def test_incomplete_or_unbound_matrix_rejected(round_inputs, mutation):
    m, root, _, cohort, *_ = round_inputs
    matrix = matrix_fixture(m, root, cohort)
    mutation(matrix)
    with pytest.raises(ValueError):
        m.validate_matrix(root, "manifest.json", matrix)


def test_unresolved_agreement_never_satisfies_resolution_or_critical_audit(round_inputs):
    result = seal_pair(round_inputs)
    assert result["initial_gates"]["initial_exact_category_agreement"]["numerator"] == 60
    assert all(count["numerator"] == 0 for count in result["initial_resolution_counts_not_final_gates"]["a"].values())
    assert all(item["status"] == "untested_label_class" for item in result["critical_errors"].values())
    assert result["status"] == "pending_adjudication"
    assert result["scientific_calibration_passed"] is False


def test_resolved_agreement_never_turns_unsupported_claims_into_pass(round_inputs):
    result = seal_pair(round_inputs, resolved=True)
    claim = result["critical_errors"]["unsupported SUPPORTED_AS_STATED"]
    assert claim["emitted_labels"] == 20 and claim["unsupported_labels"] is None
    assert result["remaining_gates"]["evidence_replay"]["status"].startswith("pending")
    assert result["scientific_calibration_passed"] is False


@pytest.mark.parametrize("claim_differences,expected", [(1, True), (2, False)])
def test_claim_threshold_preserved_and_disagreements_retained(round_inputs, claim_differences, expected):
    def mutate(matrix):
        for case in matrix["cases"][:claim_differences]:
            case["assessments"][0]["category"] = "NOT_ASSESSABLE"
    result = seal_pair(round_inputs, mutate)
    assert result["initial_gates"]["initial_claim_agreement"]["passed"] is expected
    assert len(result["disagreements"]) == claim_differences
    assert sum(cell["count"] for cell in result["initial_confusion_tables"]["claim"]) == 10
    if not expected:
        assert result["status"] == "failed_initial_gate"


def test_immutable_matrix_bytes_cannot_be_replaced(round_inputs):
    m, root, *_ = round_inputs
    seal_pair(round_inputs)
    with pytest.raises(ValueError, match="Receipt already exists"):
        m.save_matrix(root, "manifest.json", "a-draft.json", "a.json")
    (root / "a.json").chmod(0o600)
    (root / "a.json").write_text("{}")
    with pytest.raises(ValueError, match="changed after saving"):
        m.compare(root, "manifest.json", "a.json", "b.json")


def test_projection_cannot_include_historical_judgments(round_inputs):
    m, root, _, _, config, put = round_inputs
    view_path = config["cases"][0]["reviewer_view_path"]
    view = json.loads((root / view_path).read_text())
    view["historical_verdict"] = "do not leak this to reviewers"
    put(view_path, view)
    with pytest.raises(ValueError, match="allowlisted"):
        m.freeze(root, "config.json", "another.json")


@pytest.mark.parametrize("path", ["../outside", "/absolute/path"])
def test_unsafe_paths_rejected(round_inputs, path):
    m, root, *_ = round_inputs
    with pytest.raises(ValueError, match="Unsafe relative"):
        m.safe(root, path, exists=False)


def test_symlink_inputs_rejected(round_inputs):
    m, root, *_ = round_inputs
    (root / "link").symlink_to(root / "evidence.txt")
    with pytest.raises(ValueError, match="Symlink"):
        m.safe(root, "link")
