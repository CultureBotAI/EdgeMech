"""Regression checks for fixed-input publication paths escaping through symlinks."""
import importlib.util
from pathlib import Path

import pytest


def load(name):
    path = Path(__file__).resolve().parents[1] / "scripts/adhoc" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("operation", ["read", "pin", "write"])
def test_publication_rejects_ancestor_redirect_before_access(tmp_path, monkeypatch, operation):
    module = load("publish_m5_results_20261116.py")
    root, external = tmp_path / "root", tmp_path / "external"
    root.mkdir()
    external.mkdir()
    (external / "artifact").write_bytes(b"outside")
    (root / "redirect").symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(module, "ROOT", root)
    target = root / "redirect/artifact"
    with pytest.raises(ValueError, match="Symlink"):
        if operation == "read":
            module.raw(target)
        elif operation == "pin":
            module.pin(target)
        else:
            module.publish(target, b"replacement")
    assert (external / "artifact").read_bytes() == b"outside"


def test_evidence_export_rejects_redirect_before_json_read(tmp_path, monkeypatch):
    module = load("export_m5_evidence_index_20261116.py")
    root, external = tmp_path / "root", tmp_path / "external"
    root.mkdir()
    external.mkdir()
    (external / "manifest.json").write_bytes(b"not JSON: must not reach parser")
    (root / "redirect").symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(module, "ROOT", root)
    monkeypatch.setattr(module, "MANIFEST", root / "redirect/manifest.json")
    with pytest.raises(ValueError, match="Symlink"):
        module.payload()


def test_changed_published_bytes_are_never_replaced(tmp_path, monkeypatch):
    module = load("publish_m5_results_20261116.py")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    target = tmp_path / "artifact.json"
    module.publish(target, b"first")
    module.publish(target, b"first")
    with pytest.raises(ValueError, match="changed publication"):
        module.publish(target, b"second")
    assert target.read_bytes() == b"first"
