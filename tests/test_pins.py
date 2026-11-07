"""Ledger and RecordReview drift must invalidate runtime verification (#5)."""

import json

import pytest

from edgemech import pins


@pytest.fixture
def pinned_copy(tmp_path, monkeypatch):
    original = pins.files
    document = json.loads(original("edgemech").joinpath("contract-pins.json").read_text())
    root = tmp_path / "edgemech"
    root.mkdir()
    (root / "contract-pins.json").write_text(json.dumps(document))
    for package, paths in document["packages"].items():
        for path in paths:
            target = tmp_path / package / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(original(package).joinpath(path).read_bytes())
    monkeypatch.setattr(pins, "files", lambda package: tmp_path / package)
    return tmp_path


@pytest.mark.parametrize("path", [
    "kg_microbe_curation/ledger.py", "kg_microbe_reviews/__init__.py",
    "kg_microbe_governance/artifacts/scripts/record_review.py",
    "kg_microbe_governance/artifacts/schema/record_review.yaml",
    "kg_microbe_governance/artifacts/__init__.py",
    "kg_microbe_governance/artifacts/scripts/__init__.py",
    "kg_microbe_governance/artifacts/scripts/check_vendored_sync.py",
])
def test_semantic_runtime_dependency_drift_fails(pinned_copy, path):
    assert pins.check_contracts()["files"] == 16
    target = pinned_copy / path
    target.write_bytes(target.read_bytes() + b"\n# drift\n")
    with pytest.raises(ValueError, match="differs from reviewed pin"):
        pins.check_contracts()
