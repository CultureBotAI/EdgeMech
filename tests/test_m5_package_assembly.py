"""Private evidence assembly must reject paths before any read/write occurs."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "m5_assembly", Path(__file__).parents[1] / "scripts/adhoc/assemble_m5_package_20261116.py")
assembly = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assembly)


def test_reject_redirected_output_and_input(tmp_path, monkeypatch):
    root = tmp_path / "root"
    external = tmp_path / "external"
    root.mkdir()
    external.mkdir()
    (external / "source.json").write_text("{}")
    (root / "redirect").symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(assembly, "ROOT", root)
    with pytest.raises(ValueError):
        assembly.write(Path("redirect/output.json"), {"private": True})
    with pytest.raises(ValueError):
        assembly.load("redirect/source.json")
    assert not (external / "output.json").exists()


@pytest.mark.parametrize("path", ["../external/secret.json", "/external/secret.json"])
def test_reject_escaping_inputs_before_read(tmp_path, monkeypatch, path):
    monkeypatch.setattr(assembly, "ROOT", tmp_path)
    with pytest.raises(ValueError):
        assembly.load(path)


def test_private_exclusive_persistence(tmp_path, monkeypatch):
    monkeypatch.setattr(assembly, "ROOT", tmp_path)
    path = Path("private/input.json")
    assembly.write(path, {"value": 1})
    assert assembly.load(path) == {"value": 1}
    assert (tmp_path / path).stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        assembly.write(path, {"value": 2})
    assert assembly.load(path) == {"value": 1}
