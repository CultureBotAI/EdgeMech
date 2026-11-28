"""Issue238: synthetic privacy canaries for a strict public digest/status view."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts/adhoc"
MARKER = "SYNTHETIC_PRIVATE_BINDING_MUST_NOT_ESCAPE"


@pytest.fixture
def projection(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "public_projection_fixture", SCRIPTS / "preparation_public_projection_20261126.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def snapshot(name="retained"):
    return {"path": f"/synthetic/{MARKER}/{name}", "sha256": "a" * 64, "bytes": 12,
            "extra": {"thread_id": MARKER, "argv": [MARKER]}}


def fixture(kind):
    value = {"scientific_review_coverage": 0, "cwd": f"/synthetic/{MARKER}",
             "thread_id": MARKER, "pid": 987654321, "command": [MARKER],
             "unknown": {"nested": [MARKER]}}
    if kind == "commands":
        value["commands"] = [{**value, "exit_code": 0, "label": MARKER, "error": MARKER,
                              "helper": snapshot(), "stdout": snapshot(), "stderr": snapshot()}]
    elif kind == "library":
        value.update({"provider": "valency", "provider_request_count": 1,
                      "request_id": MARKER, "provider_metadata": {"private": MARKER},
                      "identity_verified": True, "body_read": False, "tables_read": False,
                      "figures_read": False, "fulltext_ready": False,
                      "native_scientific_proof_admitted": False, "literal_replay": "passed",
                      "request": snapshot(), "response": snapshot(), "abstract": snapshot(),
                      "quote": MARKER, "quote_sha256": "b" * 64, "quote_words": 4})
    elif kind == "canonical":
        value.update({"canonical_read_review": "passed", "input_hash_replay": "passed",
                      "contracts": {"verified": True, "files": 16, "claw_commit": "c" * 40},
                      "artifacts": [snapshot("review.yaml"), snapshot("review.md")],
                      "source_provenance": {"reason": MARKER}})
    else:
        value.update({"occurrence": None, "A_B_attempt": False, "A_count": None,
                      "B_count": None, "baseline_cutoff": None,
                      "validation": {"contracts": 16, "focused": {"passed": 1},
                        "full_suite": {"passed": 1, "failed": 0, "errors": 0, "exit_code": 0},
                        "ruff_exit": 0, "package_build_exit": 0, "extra": MARKER},
                      "readiness": {"shared_canonical_engineering": True,
                        "actual_worker_metadata_abstract_access": True, "fulltext": False,
                        "native_occurrence_production": False, "calibration": False,
                        "extra": MARKER}})
    return value


@pytest.mark.parametrize("kind", ["commands", "library", "canonical", "summary"])
def test_allowlist_omits_all_operational_and_unknown_bindings(projection, kind):
    raw = json.dumps(fixture(kind)).encode()
    result = projection.project(raw, kind)
    text = json.dumps(result)
    assert MARKER not in text
    assert "/synthetic/" not in text
    assert "987654321" not in text
    assert all(f'"{key}"' not in text for key in (
        "argv", "command", "cwd", "thread_id", "pid", "path", "label", "error",
        "request_id", "provider_metadata", "source_provenance", "quote", "extra", "unknown"))
    assert result["source_artifact_sha256"] == projection.hashlib.sha256(raw).hexdigest()
    assert result["scientific_review_coverage"] == 0


def test_command_projection_exact_allowlist(projection):
    result = projection.project(json.dumps(fixture("commands")).encode(), "commands")
    assert set(result) == {"format", "kind", "source_artifact_sha256",
                           "scientific_review_coverage", "commands", "command_count"}
    assert set(result["commands"][0]) == {
        "record_sha256", "exit_code", "status", "helper_sha256", "stdout", "stderr"}
    assert set(result["commands"][0]["stdout"]) == {"sha256", "bytes"}


@pytest.mark.parametrize("bad", [MARKER, {"private": MARKER}, True, 999999])
def test_private_values_cannot_enter_typed_status_fields(projection, bad):
    source = fixture("commands")
    source["commands"][0]["exit_code"] = bad
    with pytest.raises(ValueError):
        projection.project(json.dumps(source).encode(), "commands")


@pytest.mark.parametrize("kind,field", [("library", "literal_replay"),
    ("library", "quote_sha256"), ("library", "identity_verified"),
    ("canonical", "canonical_read_review"), ("summary", "scientific_review_coverage")])
def test_allowlisted_scalars_cannot_smuggle_private_text(projection, kind, field):
    source = fixture(kind)
    source[field] = MARKER
    with pytest.raises(ValueError):
        projection.project(json.dumps(source).encode(), kind)


def test_original_source_unchanged_and_hash_sensitive(projection):
    source = fixture("library")
    raw = json.dumps(source).encode()
    first = projection.project(raw, "library")
    assert raw == json.dumps(source).encode()
    source["unknown"]["nested"].append("another synthetic binding")
    second = projection.project(json.dumps(source).encode(), "library")
    assert first.pop("source_artifact_sha256") != second.pop("source_artifact_sha256")
    assert first == second


@pytest.mark.parametrize("bad_output", ["existing", "symlink", "traversal", "fifo", "valid"])
def test_projection_cli_synthetic_destinations_only(tmp_path, bad_output):
    root = tmp_path / "synthetic-checkout"
    scripts = root / "scripts/adhoc"
    scripts.mkdir(parents=True)
    for name in ("preparation_receipt_20261126.py", "preparation_readback_20261126.py",
                 "preparation_public_projection_20261126.py"):
        shutil.copyfile(SCRIPTS / name, scripts / name)
    proposal = root / ".temp/preparation-repairs-236-238-20261126/public-proposal"
    proposal.mkdir(parents=True)
    source = root / "synthetic.json"
    original = json.dumps(fixture("library")).encode()
    source.write_bytes(original)
    outside = tmp_path / "outside"
    outside.write_bytes(b"retain outside")
    output = proposal / "view.json"
    if bad_output == "existing":
        output.write_bytes(b"prior projection")
    elif bad_output == "symlink":
        output.symlink_to(outside)
    elif bad_output == "traversal":
        output = proposal / ".." / ".." / ".." / "leaked.json"
    elif bad_output == "fifo":
        os.mkfifo(output)
    result = subprocess.run([sys.executable, str(scripts / "preparation_public_projection_20261126.py"),
        "library", "--source", str(source), "--output", str(output)], cwd=root,
        env={"PATH": os.defpath, "TMPDIR": str(tmp_path),
             "PYTHONPYCACHEPREFIX": str(tmp_path / "pycache")},
        capture_output=True, timeout=8)
    (tmp_path / "stdout").write_bytes(result.stdout)
    (tmp_path / "stderr").write_bytes(result.stderr)
    assert source.read_bytes() == original
    assert outside.read_bytes() == b"retain outside"
    if bad_output == "valid":
        assert result.returncode == 0
        assert MARKER not in output.read_text()
    else:
        assert result.returncode != 0
        if bad_output == "existing":
            assert output.read_bytes() == b"prior projection"
        assert not (root / "leaked.json").exists()
