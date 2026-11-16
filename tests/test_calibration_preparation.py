"""Calibration preparation preserves provenance and enforces an unchanged live canary."""

from __future__ import annotations

import importlib.util
import json
import shutil
import stat
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[1] / "scripts/adhoc/prepare_calibration_20261115.py"


@pytest.fixture
def preparation(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("calibration_preparation", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root, archive = tmp_path / "repo", tmp_path / "archive"
    root.mkdir()
    archive.mkdir()
    (root / "artifacts").mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text(".temp/\n")
    real_root = HELPER.parents[2]
    for relative in module.CODE_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(real_root / relative, target)
    monkeypatch.setattr(module, "SELECTION", (
        ("first", 1, "Retained observation context"),
        ("fresh", 47, "Canary retained context"),
    ))

    def edge(ordinal, name):
        return {
            "occurrence_id": "urn:kg-microbe:occurrence:v1:" + name,
            "canary_ordinal": ordinal, "subject": "taxon:" + name,
            "predicate": "biolink:has_phenotype", "object": "trait:" + name,
            "origin_transform": "fixture/edges.tsv", "transform_row_number": ordinal,
            "relation": "RO:0002200", "subject_label": name, "object_label": name,
            "subject_category": "biolink:OrganismTaxon", "object_category": "biolink:PhenotypicQuality",
            "original_subject_node": {"id": "taxon:" + name, "description": "private context"},
            "original_object_node": {"id": "trait:" + name, "description": "private context"},
        }

    first, fresh = edge(1, "first"), edge(47, "fresh")
    public = {}
    for name, value in (("first", first), ("fresh", fresh)):
        projection = deepcopy(value)
        del projection["original_subject_node"]["description"]
        del projection["original_object_node"]["description"]
        relative = f"artifacts/{name}.jsonl"
        raw = json.dumps(projection).encode() + b"\n"
        (root / relative).write_bytes(raw)
        public[name] = (relative, module.digest(raw))
    monkeypatch.setattr(module, "PUBLIC", public)
    source_text = '{"kept": "literal source text", "unit": "%"}'
    wrapper = {"source_path": str(module.RAW_ROOT / "fixture.json"),
               "locator": "record 1", "text": source_text,
               "text_sha256": module.digest(source_text.encode()), "retained_extra": "unchanged"}
    first_inputs = {}
    for relative, raw in (
        ("sample/private-provenance/canary.jsonl", json.dumps(first).encode() + b"\n"),
        ("source/source-records-50.json", module.encoded({first["occurrence_id"]: [wrapper]})),
    ):
        path = archive / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        first_inputs[relative] = module.digest(raw)
    monkeypatch.setattr(module, "FIRST_INPUTS", first_inputs)
    fresh_source = {"edge": fresh, "records": [{**wrapper, "source_relative_path": "fixture.json"}],
                    "resolved_names": ["retained extra source field"]}
    fresh_path = archive / "phase2/source/packets/47.json"
    fresh_path.parent.mkdir(parents=True)
    fresh_path.write_bytes(module.encoded(fresh_source))
    (root / module.BASE).mkdir(parents=True)
    (root / module.PROTOCOL).write_bytes(module.encoded({
        "profile": "edgemech-calibration-protocol/v1", "cohort_id": module.COHORT_ID,
        "canary_case_id": module.CANARY,
        "selection": {"first": [1], "fresh": [47]},
    }))
    (root / module.COHORT).write_bytes(module.encoded(module.cohort_document(root, archive)))
    return module, root, archive


def test_canary_then_first_case_persist_and_replay_without_altering_archives(preparation):
    module, root, archive = preparation
    original = {path: path.read_bytes() for path in archive.rglob("*") if path.is_file()}
    with pytest.raises(Exception, match="missing artifact"):
        module.prepare(root, archive, "first-01")
    assert not (root / module.PRIVATE / "first-01").exists()
    receipt = module.prepare(root, archive, module.CANARY)
    assert receipt["scientific_status"] == "unassessed"
    assert receipt["native_capability_enabled"] is False
    assert receipt["validation"]["endpoint_records_verified"] == 2
    assert module.check_case(root, archive, module.CANARY) == receipt
    first = module.prepare(root, archive, "first-01")
    assert first["canary_receipt"] == module.pin(root, module.PRIVATE / module.CANARY / "receipt.json")
    source = json.loads((root / module.PRIVATE / "first-01/source.json").read_bytes())
    old_wrapper = json.loads(original[archive / "source/source-records-50.json"])[
        first["occurrence_id"]][0]
    new_wrapper = source["records"][0]
    assert new_wrapper == {**old_wrapper, "source_relative_path": "fixture.json"}
    assert all(path.read_bytes() == raw for path, raw in original.items())
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600
               for path in (root / module.PRIVATE / "first-01").iterdir())
    with pytest.raises(FileExistsError):
        module.prepare(root, archive, module.CANARY)


@pytest.mark.parametrize("changed", ["protocol", "cohort", "code"])
def test_changed_configuration_requires_new_canary_before_other_case(preparation, changed):
    module, root, archive = preparation
    module.prepare(root, archive, module.CANARY)
    path = {"protocol": module.PROTOCOL, "cohort": module.COHORT,
            "code": module.CODE_PATHS[1]}[changed]
    with (root / path).open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError, match="configuration changed"):
        module.prepare(root, archive, "first-01")
    assert not (root / module.PRIVATE / "first-01").exists()


@pytest.mark.parametrize("name", ["occurrence.json", "source.json", "packet.json"])
def test_changed_private_bytes_fail_replay(preparation, name):
    module, root, archive = preparation
    module.prepare(root, archive, module.CANARY)
    with (root / module.PRIVATE / module.CANARY / name).open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="Prepared artifact changed"):
        module.check_case(root, archive, module.CANARY)


def test_modified_upstream_source_fails_frozen_binding(preparation):
    module, root, archive = preparation
    module.prepare(root, archive, module.CANARY)
    with (archive / "phase2/source/packets/47.json").open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="Frozen case or retained inputs changed"):
        module.check_case(root, archive, module.CANARY)


def test_recomputed_artifact_hash_cannot_hide_changed_source(preparation):
    module, root, archive = preparation
    module.prepare(root, archive, module.CANARY)
    directory = root / module.PRIVATE / module.CANARY
    source = json.loads((directory / "source.json").read_bytes())
    source["edge"]["subject_category"] = "biolink:ChemicalEntity"
    (directory / "source.json").write_bytes(module.encoded(source))
    receipt = json.loads((directory / "receipt.json").read_bytes())
    receipt["artifacts"]["source.json"] = module.pin(root, module.PRIVATE / module.CANARY / "source.json")
    (directory / "receipt.json").write_bytes(module.encoded(receipt))
    with pytest.raises(ValueError, match="differs from retained derivation"):
        module.check_case(root, archive, module.CANARY)


def test_nonignored_staging_and_symlink_ancestors_are_refused(preparation, tmp_path):
    module, root, archive = preparation
    (root / ".gitignore").write_text("")
    with pytest.raises(ValueError, match="not gitignored"):
        module.prepare(root, archive, module.CANARY)
    (root / ".gitignore").write_text(".temp/\n")
    external = tmp_path / "external"
    external.mkdir()
    (root / ".temp").symlink_to(external, target_is_directory=True)
    with pytest.raises(Exception, match="symlink"):
        module.prepare(root, archive, module.CANARY)
    assert not list(external.iterdir())


def test_public_projection_tampering_and_duplicate_ordinal_are_rejected(preparation, monkeypatch):
    module, root, archive = preparation
    relative, _ = module.PUBLIC["first"]
    path = root / relative
    row = json.loads(path.read_bytes())
    row["subject_category"] = "biolink:ChemicalEntity"
    path.write_bytes((json.dumps(row) + "\n").encode())
    monkeypatch.setitem(module.PUBLIC, "first", (relative, module.digest(path.read_bytes())))
    with pytest.raises(ValueError, match="differs from retained private edge"):
        module.cohort_document(root, archive)
    row["subject_category"] = "biolink:OrganismTaxon"
    raw = (json.dumps(row) + "\n").encode() * 2
    path.write_bytes(raw)
    monkeypatch.setitem(module.PUBLIC, "first", (relative, module.digest(raw)))
    with pytest.raises(ValueError, match="one exact ordinal"):
        module.cohort_document(root, archive)


def test_exclusive_manifest_write_and_path_traversal_guard(preparation):
    module, root, _ = preparation
    old = (root / module.COHORT).read_bytes()
    with pytest.raises(FileExistsError):
        module.write_new(root / module.COHORT, b"replacement")
    assert (root / module.COHORT).read_bytes() == old
    with pytest.raises(Exception, match="traversal"):
        module.write_new(root / ".." / "escaped.json", b"no")
