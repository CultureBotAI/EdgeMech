"""Private authority capture preserves original bytes and requires a canary."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    'capture_relations', Path(__file__).parents[1] / 'scripts/adhoc/capture_m5_relation_authorities_20261116.py')
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_capture_replay_immutability(tmp_path, monkeypatch):
    monkeypatch.setattr(MOD, 'source', lambda unit: (b'original\n', {'version': 'v1'}))
    receipt = MOD.capture('biolink-4.4.0', tmp_path)
    assert MOD.check('biolink-4.4.0', tmp_path) == receipt
    with pytest.raises(FileExistsError):
        MOD.capture('biolink-4.4.0', tmp_path)
    (tmp_path / 'biolink-4.4.0/source.txt').write_bytes(b'changed')
    with pytest.raises(ValueError, match='bytes changed'):
        MOD.check('biolink-4.4.0', tmp_path)


def test_other_unit_requires_verified_canary(tmp_path, monkeypatch):
    monkeypatch.setattr(MOD, 'source', lambda unit: (b'original', {'version': 'v1'}))
    with pytest.raises(FileNotFoundError):
        MOD.capture('metpo-classes-maintained', tmp_path)
    assert not (tmp_path / 'metpo-classes-maintained').exists()
