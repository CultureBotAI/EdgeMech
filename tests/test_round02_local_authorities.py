"""Meaningful immutability and retained function extraction guards."""
import ast
import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).parents[1] / "scripts/adhoc/capture_round02_local_authorities_20261116.py"
SPEC = importlib.util.spec_from_file_location("local_authorities", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_snapshot_never_overwrites(tmp_path):
    path = tmp_path / "snapshot"
    MODULE.write(path, b"original")
    with pytest.raises(FileExistsError):
        MODULE.write(path, b"replacement")
    assert path.read_bytes() == b"original"


def test_owner_function_requires_unique_definition():
    with pytest.raises(ValueError):
        MODULE.function(ast.parse("def x(): pass\ndef x(): pass"), "x")
    with pytest.raises(ValueError):
        MODULE.function(ast.parse("def y(): pass"), "x")
