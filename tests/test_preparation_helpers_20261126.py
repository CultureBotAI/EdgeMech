"""Offline #236/#237 regressions; every invocation uses synthetic checkout copies.

Set PREPARATION_HELPER_SOURCE to preserved executed helper bytes for fresh-process
regression runs. No retained library or canonical evidence is loaded or mutated.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
TITLE = ("Rubritalea squalenifaciens sp. nov., a squalene-producing marine bacterium "
         "belonging to subdivision 1 of the phylum 'Verrucomicrobia'.")
JOURNAL = "International journal of systematic and evolutionary microbiology. 2007;57(Pt 7):1630-1634"


def envelope():
    data = {"paper_id": "17625207", "query_type": "paper_by_id", "found": True,
            "warnings": [], "paper": {
                "id": "17625207", "base_id": "17625207", "doi": "10.1099/ijs.0.65010-0",
                "title": TITLE, "source": "pubmed", "journal_ref": JOURNAL,
                "url": "https://pubmed.ncbi.nlm.nih.gov/17625207/",
                "abstract": "Synthetic fixture: was a non-motile, rod-shaped marker.",
            }, "_meta": {"request_id": "synthetic-request", "tool": "get_paper_by_id",
                         "duration_ms": 1, "server_version": "fixture"}}
    return {"isError": False, "content": [{"type": "text", "text": json.dumps(data)}],
            "structuredContent": copy.deepcopy(data)}


@pytest.fixture
def sample(tmp_path):
    root = tmp_path / "synthetic-checkout"
    scripts = root / "scripts/adhoc"
    scripts.mkdir(parents=True)
    source = Path(os.environ.get("PREPARATION_HELPER_SOURCE", REPO / "scripts/adhoc"))
    for name in ("preparation_receipt_20261126.py", "preparation_readback_20261126.py"):
        shutil.copyfile(source / name, scripts / name)
    base = root / ".temp/restart-preparation-01"
    (base / "library").mkdir(parents=True)
    (base / "library/request-01.json").write_text('{"synthetic":true}\n')
    (base / "library/response-01.json").write_text(json.dumps(envelope()))
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "retained").write_bytes(b"outside bytes must remain identical")
    return root, base, outside


def invoke(sample, name, args):
    root, base, outside = sample
    logs = root.parent / "invocations"
    logs.mkdir(exist_ok=True)
    attempt = logs / f"attempt-{len(list(logs.iterdir())):02d}"
    attempt.mkdir()
    env = {"PATH": os.defpath, "TMPDIR": str(root.parent),
           "PYTHONPYCACHEPREFIX": str(root.parent / "pycache")}
    command = [sys.executable, str(root / "scripts/adhoc" / name), *map(str, args)]
    try:
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=8)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
    (attempt / "stdout").write_bytes(stdout)
    (attempt / "stderr").write_bytes(stderr)
    (attempt / "outcome.json").write_text(json.dumps({"command": command, "exit_code": code}))
    return code


def readback(sample, output=None):
    return invoke(sample, "preparation_readback_20261126.py",
                  ["library", "--output", output or sample[1] / "result.json"])


def recorder(sample, label="fixture"):
    return invoke(sample, "preparation_receipt_20261126.py", [label, "--", sys.executable,
        "-c", "import os,pathlib;pathlib.Path('command-ran').write_text('synthetic');"
        "(pathlib.Path(os.environ['TMPDIR'])/'child-marker').write_text('synthetic')"])


def assert_rejected(sample, code, *, recorder_mode=False):
    root, base, outside = sample
    assert code is not None, "Refusal must not block on a nonregular endpoint"
    assert code != 0
    assert (outside / "retained").read_bytes() == b"outside bytes must remain identical"
    assert not (outside / "child-marker").exists()
    if recorder_mode:
        assert not (root / "command-ran").exists(), "Command ran before endpoint validation"
        assert not (base / "commands/fixture").exists(), "Preflight must precede output creation"
    else:
        assert not (base / "library/abstract-01.txt").exists(), "Invalid input derived an artifact"
        assert not (base / "result.json").exists()


def test_confinement_traversal_rejected_before_derivation(sample):
    root, base, outside = sample
    target = base / ".." / ".." / ".." / "outside" / "leaked.json"
    assert_rejected(sample, readback(sample, target))
    assert not (outside / "leaked.json").exists()


@pytest.mark.parametrize("kind", ["symlink", "dangling_symlink", "directory", "fifo"])
def test_confinement_output_leaf_rejected_before_derivation(sample, kind):
    root, base, outside = sample
    output = base / "result.json"
    if kind == "symlink":
        output.symlink_to(outside / "retained")
    elif kind == "dangling_symlink":
        output.symlink_to(outside / "absent")
    elif kind == "directory":
        output.mkdir()
    else:
        os.mkfifo(output)
    code = readback(sample)
    assert code is not None and code != 0
    assert (outside / "retained").read_bytes() == b"outside bytes must remain identical"
    assert not (outside / "absent").exists()
    assert not (base / "library/abstract-01.txt").exists()


def test_confinement_existing_destination_preserved_before_derivation(sample):
    output = sample[1] / "result.json"
    output.write_bytes(b"existing receipt")
    assert readback(sample) != 0
    assert output.read_bytes() == b"existing receipt"
    assert not (sample[1] / "library/abstract-01.txt").exists()


@pytest.mark.parametrize("leaf", ["command-outcomes.jsonl", "tmp", "uv-cache", "cache",
                                    "pycache", "ruff-cache", "python", "venv", "commands"])
def test_confinement_recorder_symlink_preflight(sample, leaf):
    root, base, outside = sample
    (base / leaf).symlink_to(outside / "retained" if leaf.endswith("jsonl") else outside)
    code = recorder(sample)
    assert code is not None and code != 0
    assert not (root / "command-ran").exists()
    assert (outside / "retained").read_bytes() == b"outside bytes must remain identical"
    assert not (outside / "fixture").exists()
    assert not (outside / "child-marker").exists()
    if leaf != "commands":
        assert not (base / "commands/fixture").exists()


@pytest.mark.parametrize("leaf,kind", [("command-outcomes.jsonl", "directory"),
                                       ("command-outcomes.jsonl", "fifo"),
                                       ("tmp", "file"), ("venv", "fifo")])
def test_confinement_recorder_nonregular_preflight(sample, leaf, kind):
    target = sample[1] / leaf
    if kind == "directory":
        target.mkdir()
    elif kind == "fifo":
        os.mkfifo(target)
    else:
        target.write_bytes(b"existing file")
    assert_rejected(sample, recorder(sample), recorder_mode=True)


def test_confinement_existing_command_attempt_is_preserved(sample):
    attempt = sample[1] / "commands/fixture"
    attempt.mkdir(parents=True)
    (attempt / "receipt.json").write_bytes(b"prior attempt")
    assert recorder(sample) != 0
    assert (attempt / "receipt.json").read_bytes() == b"prior attempt"
    assert not (sample[0] / "command-ran").exists()


def test_confinement_intermediate_symlink_rejected(sample):
    root, base, outside = sample
    moved = outside / "moved-library"
    (base / "library").rename(moved)
    (base / "library").symlink_to(moved)
    assert readback(sample) != 0
    assert not (moved / "abstract-01.txt").exists()
    assert not (base / "result.json").exists()


@pytest.mark.parametrize("case", ["isError", "error_type", "structured_empty", "structured_null",
    "structured_false", "structured_zero", "structured_list", "structured_string", "contradictory",
    "root_list", "content_string", "content_nonmapping", "text_nonstring", "text_nonjson",
    "multiple_text", "nontext", "data_list", "found_integer", "paper_list", "id_integer",
    "title_list", "abstract_list", "journal_list", "url_integer", "url_wrong", "base_id_wrong",
    "missing_request_id", "request_id_list", "duration_boolean", "warnings_string"])
def test_mcp_envelope_refuses_before_success_artifacts(sample, case):
    response = envelope()
    data = json.loads(response["content"][0]["text"])
    if case == "isError":
        response["isError"] = True
    elif case == "error_type":
        response["isError"] = 1
    elif case.startswith("structured_"):
        response["structuredContent"] = {
            "empty": {}, "null": None, "false": False, "zero": 0, "list": [], "string": "bad",
        }[case.removeprefix("structured_")]
    elif case == "contradictory":
        response["structuredContent"]["found"] = False
    elif case == "root_list":
        response = []
    elif case == "content_string":
        response["content"] = "bad"
    elif case == "content_nonmapping":
        response["content"] = [None]
    elif case == "text_nonstring":
        response["content"][0]["text"] = []
    elif case == "text_nonjson":
        response["content"][0]["text"] = "{bad"
    elif case == "multiple_text":
        response["content"] *= 2
    elif case == "nontext":
        response["content"].append({"type": "image", "data": "synthetic"})
    else:
        if case == "data_list":
            data = []
        elif case == "found_integer":
            data["found"] = 1
        elif case == "paper_list":
            data["paper"] = []
        elif case == "missing_request_id":
            del data["_meta"]["request_id"]
        elif case == "request_id_list":
            data["_meta"]["request_id"] = []
        elif case == "duration_boolean":
            data["_meta"]["duration_ms"] = True
        elif case == "warnings_string":
            data["warnings"] = "bad"
        else:
            field, value = {"id_integer": ("id", 17625207), "title_list": ("title", [TITLE]),
                "abstract_list": ("abstract", ["was a non-motile, rod-shaped"]),
                "journal_list": ("journal_ref", ["2007;57(Pt 7):1630-1634"]),
                "url_integer": ("url", 1), "url_wrong": ("url", "https://example.invalid/private"),
                "base_id_wrong": ("base_id", "wrong")}[case]
            data["paper"][field] = value
        response["content"][0]["text"] = json.dumps(data)
        response["structuredContent"] = copy.deepcopy(data)
    (sample[1] / "library/response-01.json").write_text(json.dumps(response))
    assert_rejected(sample, readback(sample))


def test_mcp_positive_retained_shape_synthetic_body(sample):
    assert readback(sample) == 0
    result = json.loads((sample[1] / "result.json").read_bytes())
    assert result["literal_replay"] == "passed"
    assert result["scientific_review_coverage"] == 0
    assert result["body_read"] is False
    assert (sample[1] / "library/abstract-01.txt").read_text().startswith("Synthetic fixture:")


def test_confinement_positive_synthetic_command(sample):
    assert recorder(sample) == 0
    receipt = json.loads((sample[1] / "commands/fixture/receipt.json").read_bytes())
    assert receipt["exit_code"] == 0
    assert receipt["scientific_review_coverage"] == 0
    assert (sample[0] / "command-ran").read_text() == "synthetic"
