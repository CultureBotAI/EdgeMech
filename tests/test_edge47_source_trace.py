"""PR107 issues109/110: exercise the source-trace path with adversarial provenance."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "edge47_source_trace", ROOT / "scripts/adhoc/trace_edge47_source_20261115.py"
)
trace_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(trace_module)

CONCENTRATION = "BacDive_Salt_concentration"
UNIT = "BacDive_Salt_concentration_unit"
REFERENCE = {
    "@id": 119830,
    "authors": "Synthetic catalogue curators",
    "catalogue": "Synthetic catalogue (CIP 103005)",
    "doi/url": "https://example.invalid/catalogue/CIP103005",
    "extra": {"retained": "exact reference object"},
}


def inputs(tmp_path, *, columns=(CONCENTRATION, UNIT), reference_field="Reference",
           references=None, mismatched_binding=None, mismatched_subject=None):
    """Create real CSV/JSON/TSV files, including the fixed source row20904."""
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    transformed = tmp_path / "transformed/microbedecoder"
    transformed.mkdir(parents=True)
    output = tmp_path / "output"
    output.mkdir()
    record = {"LPSN_ID": "783091", "BacDive_ID": "6845",
              CONCENTRATION: "0-10", UNIT: "%"}
    csv_path = raw_root / "database.csv"
    with csv_path.open("w", encoding="latin1", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(record))
        writer.writeheader()
        writer.writerows({} for _ in range(20903))
        writer.writerow(record)
    bacdive = {
        "General": {"BacDive-ID": 6845},
        "Physiology and metabolism": {"halophily": {
            "@ref": 119830, "concentration": "0-10 %", "growth": "positive",
            "salt": "NaCl", "tested relation": "growth",
        }},
        reference_field: [REFERENCE] if references is None else references,
    }
    (raw_root / "bacdive_strains.json").write_text(json.dumps([bacdive]))
    selected = []
    for name, locator, value in (("database.csv", "CSV data row 20904", record),
                                 ("bacdive_strains.json", "6845", bacdive)):
        text = trace_module.canonical(value)
        selected.append({"source_relative_path": name, "locator": locator,
                         "text": text, "text_sha256": trace_module.digest(text.encode())})
    packet = tmp_path / "packet.json"
    packet.write_text(json.dumps({trace_module.OCCURRENCE: {
        "edge": {"occurrence_id": trace_module.OCCURRENCE}, "records": selected,
    }}))
    binding = "sha256:" + trace_module.file_digest(csv_path) + "#record=20904"
    with (transformed / "edges.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=[
            "subject", "source_column", "source_record", "value",
        ])
        writer.writeheader()
        for index, column in enumerate(columns):
            writer.writerow({
                "subject": "lpsn:999999" if index == mismatched_subject else "lpsn:783091",
                "source_column": column,
                "source_record": "sha256:wrong#record=20904" if index == mismatched_binding else binding,
                "value": record[column],
            })
    return packet, raw_root, output


def test_full_trace_preserves_real_reference_field_and_exact_pair(tmp_path):
    packet, raw_root, output = inputs(tmp_path)
    trace_module.trace(packet, raw_root, output)
    result = json.loads((output / "source-trace.json").read_text())
    assert result["bacdive"]["matching_references"] == [REFERENCE]
    assert result["bacdive"]["all_reference_records"] == [REFERENCE]
    assert {row["source_column"] for row in result["current_transformed_sibling_rows"]} == {
        CONCENTRATION, UNIT,
    }
    assert result["microbedecoder"]["frozen_matches_current_raw"] is True
    assert result["bacdive"]["frozen_matches_current_raw"] is True


@pytest.mark.parametrize("columns", [
    (CONCENTRATION, CONCENTRATION), (UNIT, UNIT), (CONCENTRATION,), (UNIT,), (),
    (CONCENTRATION, UNIT, UNIT),
])
def test_full_trace_rejects_duplicate_or_missing_columns(tmp_path, columns):
    packet, raw_root, output = inputs(tmp_path, columns=columns)
    with pytest.raises(ValueError, match="exactly one concentration and one unit"):
        trace_module.trace(packet, raw_root, output)
    assert not (output / "source-trace.json").exists()


@pytest.mark.parametrize("index", [0, 1])
def test_full_trace_rejects_wrong_source_record_for_either_sibling(tmp_path, index):
    packet, raw_root, output = inputs(tmp_path, mismatched_binding=index)
    with pytest.raises(ValueError, match="exact CSV source record"):
        trace_module.trace(packet, raw_root, output)
    assert not (output / "source-trace.json").exists()


@pytest.mark.parametrize("index", [0, 1])
def test_full_trace_rejects_wrong_subject_for_either_sibling(tmp_path, index):
    packet, raw_root, output = inputs(tmp_path, mismatched_subject=index)
    with pytest.raises(ValueError, match="exactly one concentration and one unit"):
        trace_module.trace(packet, raw_root, output)
    assert not (output / "source-trace.json").exists()


@pytest.mark.parametrize(("field", "references"), [
    ("references", [REFERENCE]),
    ("Reference", []),
    ("Reference", [{"@id": 111111, "catalogue": "Unrelated synthetic catalogue"}]),
    ("Reference", [REFERENCE, REFERENCE]),
    ("Reference", [REFERENCE, {"@id": "119830", "catalogue": "Conflicting catalogue"}]),
    ("Reference", [{"id": 119830, "catalogue": "Wrong identifier field"}]),
])
def test_full_trace_rejects_missing_or_ambiguous_halophily_reference(tmp_path, field, references):
    packet, raw_root, output = inputs(tmp_path, reference_field=field, references=references)
    with pytest.raises(ValueError, match="exactly one matching BacDive Reference"):
        trace_module.trace(packet, raw_root, output)
    assert not (output / "source-trace.json").exists()
