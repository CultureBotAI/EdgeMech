"""View canaries bind the executing adapter and cannot escape through symlinks."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import stat
from pathlib import Path

import pytest
from kg_microbe_curation.identity import CurationError

from edgemech.occurrence_packet import build_packet

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/adhoc/prepare_m5_reviewer_views_20261116.py"


@pytest.fixture
def views(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("m5_views", HELPER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    root = tmp_path.resolve()
    monkeypatch.setattr(m, "ROOT", root)
    monkeypatch.setattr(m, "BASE", root / ".temp/output/cases-v2")
    for name in m.CONFIG_INPUTS:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    cohort = json.loads((ROOT / "artifacts/edge-calibration-20261115/cohort.json").read_text())
    for cid in ("fresh-47", "first-01"):
        case = next(c for c in cohort["cases"] if c["case_id"] == cid)
        edge = {**case["original_assertion"], "review_rationale": "historical authored verdict"}
        for side in ("subject", "object"):
            edge["original_" + side + "_node"] = {"id": edge[side]}
        source = {"edge": edge, "records": []}
        folder = root / ".temp/edge-calibration-20261115" / cid
        folder.mkdir(parents=True)
        descriptors = []
        for name, value in (("occurrence", edge), ("source", source)):
            p = folder / (name + ".json")
            p.write_text(json.dumps(value))
            descriptors.append({"path": str(p.relative_to(root)),
                                "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        packet = build_packet(edge, source, occurrence_input=descriptors[0],
                              source_input=descriptors[1], root=root)
        (folder / "packet.json").write_text(json.dumps(packet))
    return m, root


def test_fresh_canary_required_then_replay_and_exact_projection(views):
    m, root = views
    with pytest.raises(CurationError, match="missing artifact"):
        m.prepare("first-01")
    receipt = m.prepare("fresh-47")
    assert m.check("fresh-47") == receipt
    assert m.prepare("first-01")["case_id"] == "first-01"
    for case in ("fresh-47", "first-01"):
        folder = m.BASE / case
        view = json.loads((folder / "view.json").read_text())
        packet = json.loads((root / ".temp/edge-calibration-20261115" / case / "packet.json").read_text())
        assert view == {key: packet[key] for key in m.FIELDS}
        assert "historical authored verdict" not in json.dumps(view)
        assert stat.S_IMODE(folder.stat().st_mode) == 0o700
        for name in ("view.json", "receipt.json"):
            assert stat.S_IMODE((folder / name).stat().st_mode) == 0o600
    assert stat.S_IMODE(m.BASE.stat().st_mode) == 0o700


@pytest.mark.parametrize("input_path", [
    "src/edgemech/occurrence_packet.py", "src/edgemech/contract-pins.json",
    "docs/record-review-profile.md", "src/edgemech/storage/parquet.py", "uv.lock",
])
def test_changed_runtime_invalidates_canary(views, input_path):
    m, root = views
    m.prepare("fresh-47")
    (root / input_path).write_text("changed after canary")
    with pytest.raises(ValueError, match="configuration changed"):
        m.prepare("first-01")
    assert not (m.BASE / "first-01").exists()


def test_changed_canary_packet_bytes_invalidates_even_equivalent_json(views):
    m, root = views
    m.prepare("fresh-47")
    packet = root / ".temp/edge-calibration-20261115/fresh-47/packet.json"
    packet.write_bytes(packet.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="packet bytes changed"):
        m.prepare("first-01")


def test_changed_source_bytes_are_independently_replayed(views):
    m, root = views
    m.prepare("fresh-47")
    source = root / ".temp/edge-calibration-20261115/fresh-47/source.json"
    source.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(CurationError, match="bytes differ"):
        m.prepare("first-01")


def test_changed_canary_view_rejected(views):
    m, _ = views
    m.prepare("fresh-47")
    view = m.BASE / "fresh-47/view.json"
    view.write_bytes(view.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="replay differs"):
        m.prepare("first-01")


def test_output_parent_symlink_rejected_before_writes(views):
    m, root = views
    target = root / "outside-output"
    target.mkdir()
    link = root / "linked-output"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(CurationError, match="symlink"):
        m.prepare("fresh-47", link / "cases")
    assert list(target.iterdir()) == []


def test_direct_packet_symlink_rejected(views):
    m, root = views
    packet = root / ".temp/edge-calibration-20261115/fresh-47/packet.json"
    original = packet.with_name("original.json")
    packet.rename(original)
    packet.symlink_to(original)
    with pytest.raises(CurationError, match="symlink"):
        m.prepare("fresh-47")


def test_output_escape_rejected_and_old_preparation_preserved(views):
    m, root = views
    with pytest.raises(ValueError, match="escapes task worktree"):
        m.prepare("fresh-47", root.parent / "escape")
    old = root / ".temp/output/cases/fresh-47"
    old.mkdir(parents=True)
    receipt = old / "receipt.json"
    receipt.write_bytes(b"historical preparation is untouched")
    m.prepare("fresh-47")
    assert receipt.read_bytes() == b"historical preparation is untouched"
    with pytest.raises(FileExistsError):
        m.prepare("fresh-47")
