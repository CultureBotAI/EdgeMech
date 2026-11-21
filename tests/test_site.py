"""Publication boundaries and scientific-identity regressions for the sample browser."""

import copy
import csv
import io
import json
from pathlib import Path

import pytest

from edgemech import site

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def inputs():
    revision = site.git(ROOT, "rev-parse", "HEAD").decode().strip()
    values, provenance = site.read_inputs(ROOT, revision)
    return values, provenance, revision


def test_public_scope_and_independent_assessment_axes(inputs):
    data = site.project(*inputs)
    assert data["counts"]["public_sample"] == 10000
    assert data["counts"]["retained"] == 8500
    assert data["counts"]["omitted"] == 1500
    assert sum("review" in row for row in data["records"]) == 100
    first = data["records"][0]
    assert first["content_accuracy_verdict"] == "accurate_direct_evidence"
    assert first["review"]["source_fidelity"]["verdict"] == "NOT_ASSESSABLE"
    assert first["review"]["scientific_support"]["verdict"] == "NOT_ASSESSABLE"
    assert data["census"]["counts"]["exact_eligible"] == 0
    assert data["census"]["occurrences"] == 17637435


def test_original_claim_is_not_replaced_by_curated_change(inputs):
    data = site.project(*inputs)
    changed = next(row for row in data["records"] if "curated_change" in row)
    assert changed["predicate"] == "biolink:close_match"
    assert changed["curated_change"]["predicate"] == "biolink:same_as"
    assert changed["occurrence_id"] in {row["occurrence_id"] for row in inputs[0][site.SAMPLE]}


def test_public_projection_excludes_quotes_private_paths_and_source_rows(inputs):
    raw = site.encode(site.project(*inputs))
    assert b'"quote"' not in raw
    assert b"/Users/" not in raw
    assert b'"curated_source_record"' not in raw
    assert b'"source_snapshot_date":"2026-09-29"' in raw


@pytest.mark.parametrize("mutation,message", [
    ("duplicate", "duplicate occurrence"),
    ("outside", "outside the public sample"),
    ("axis", "assessment axes differ"),
    ("nested", "different occurrence"),
    ("claim", "claim differs"),
    ("census", "do not reconcile"),
])
def test_reject_inconsistent_bindings(inputs, mutation, message):
    values, provenance, revision = inputs
    values = copy.deepcopy(values)
    if mutation == "duplicate":
        values[site.SAMPLE].append(values[site.SAMPLE][0])
    elif mutation == "outside":
        values[site.FIRST][0]["occurrence_id"] = "urn:kg-microbe:occurrence:v1:" + "a" * 64
    elif mutation == "axis":
        values[site.SCIENCE].pop()
    elif mutation == "nested":
        values[site.FIRST][0]["source_fidelity"]["occurrence_id"] = "wrong"
    elif mutation == "claim":
        values[site.FIRST][0]["predicate"] = "wrong"
    else:
        values[site.CENSUS]["counts"]["exact_eligible"] += 1
    with pytest.raises(ValueError, match=message):
        site.project(values, provenance, revision)


def test_reject_uncommitted_source_bytes(inputs, monkeypatch):
    monkeypatch.setattr(site, "git", lambda *_args: b"mismatched")
    with pytest.raises(ValueError, match="uncommitted or mismatched"):
        site.read_inputs(ROOT, inputs[2])


def test_csv_neutralizes_formula_cells_and_preserves_multiline_text(inputs):
    row = site.project(*inputs, canary=True)["records"][0]
    row["subject_label"] = ' =HYPERLINK("https://example.invalid")\nnext line'
    rows = list(csv.DictReader(io.StringIO(site.csv_bytes([row]).decode())))
    assert rows[0]["subject_label"] == "'" + row["subject_label"]
    assert rows[0]["occurrence_id"] == row["occurrence_id"]
    assert rows[0]["source_fidelity"] == "NOT_ASSESSABLE"


def test_canary_build_persists_one_real_record_and_is_reproducible(inputs, tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    one = site.build(ROOT, first, inputs[2], canary=True)
    two = site.build(ROOT, second, inputs[2], canary=True)
    assert one == two
    data = json.loads((first / "sample.json").read_bytes())
    assert data["canary"] is True and len(data["records"]) == 1
    assert data["records"][0]["review"]["source_fidelity"]
    assert (first / "catalogue/1.html").stat().st_size > 0
    assert "ONE-RECORD CANARY" in (first / "index.html").read_text()
    with pytest.raises(ValueError, match="output already exists"):
        site.build(ROOT, first, inputs[2])


def test_static_catalogue_escapes_untrusted_labels(inputs, tmp_path):
    data = site.project(*inputs, canary=True)
    data["records"][0]["subject_label"] = '<img src=x onerror="alert(1)">'
    site.catalogue(data, tmp_path)
    html = (tmp_path / "catalogue/1.html").read_text()
    assert "&lt;img" in html and "<img" not in html


def test_large_manifest_provenance_uses_raw_file_with_visible_line_and_hash(inputs, tmp_path):
    data = site.project(*inputs, canary=True)
    source = next(item for item in data["provenance"] if item["path"] == site.SAMPLE)
    assert source["bytes"] > 7_000_000  # Too large for a GitHub blob line view.
    assert source["download_url"] == f"{site.RAW_REPOSITORY}/{inputs[2]}/{site.SAMPLE}"
    row = data["records"][0]
    assert inputs[0][site.SAMPLE][row["source_line"] - 1]["occurrence_id"] == row["occurrence_id"]
    site.catalogue(data, tmp_path)
    html = (tmp_path / "catalogue/1.html").read_text()
    assert f'href="{source["download_url"]}"' in html
    assert f'Source line {row["source_line"]} (1-based)' in html
    assert source["sha256"] in html
    assert "Exact source row" not in html and "#L" not in html
