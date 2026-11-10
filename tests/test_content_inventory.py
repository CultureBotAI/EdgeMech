"""Preparation must preserve duplicates and must never manufacture scientific support."""
import hashlib
import json

import pyarrow.parquet as pq
import pytest
from kg_microbe_curation.identity import CurationError, canonical_json
from test_census import export_native, snapshot

from edgemech.census import run_census
from edgemech.content_inventory import prepare_inventory
from edgemech.storage.parquet import file_hash


def fixture(tmp_path, *, duplicate_nodes=False):
    source, _ = snapshot(tmp_path / "source", [
        ("Fixture:1", "biolink:related_to", "Fixture:2", "infores:fixture", "DOI:10.1/example"),
        ("Fixture:1", "biolink:related_to", "Fixture:2", "infores:fixture", "DOI:10.1/example"),
        ("Fixture:1", "biolink:related_to", "Fixture:missing", "infores:fixture", ""),
    ], header=("subject", "predicate", "object", "primary_knowledge_source", "publications"))
    nodes = b"id\tname\tcategory\nFixture:1\tOne\tbiolink:NamedThing\nFixture:2\t\t\n"
    if duplicate_nodes:
        nodes += b"Fixture:1\tDifferent\tbiolink:NamedThing\n"
    (source / "merged-kg_nodes.tsv").write_bytes(nodes)
    manifest = json.loads((source / "manifest.json").read_bytes())
    manifest["members"]["merged-kg_nodes.tsv"] = {
        "rows": len(nodes.splitlines()) - 1, "bytes": len(nodes),
        "sha256": hashlib.sha256(nodes).hexdigest(),
    }
    (source / "manifest.json").write_bytes(canonical_json(manifest))
    native = export_native(tmp_path / "native", [])
    census = run_census(source, [native], tmp_path / "census", file_hash(source / "manifest.json"),
                        expected_native_manifest_sha256=[file_hash(native / "manifest.json")])
    return census


def test_duplicate_occurrences_missing_nodes_and_no_fabricated_support(tmp_path):
    census = fixture(tmp_path)
    output = tmp_path / "output"
    result = prepare_inventory(census, file_hash(census), output, reserve_bytes=0)
    rows = pq.read_table(output / result["partitions"][0]["path"]).to_pylist()
    assert result["rows"] == 3
    assert result["profile"][0]["distinct_spo"] == 2
    assert result["profile"][0]["inline_evidence_occurrences"] == 2
    assert len({row["occurrence_id"] for row in rows}) == 3
    assert [row["endpoint_status"] for row in rows] == [
        "missing_label_or_category", "missing_label_or_category", "missing_node"
    ]
    assert all(row["content_status"] == "unassessed" for row in rows)
    assert result["scientific_reviews"] == result["scientific_approvals"] == 0
    assert json.loads((output / "manifest.json").read_bytes())["complete_population"]
    with pytest.raises(FileExistsError):
        prepare_inventory(census, file_hash(census), output, reserve_bytes=0)


@pytest.mark.parametrize("damage", ["pin", "partition", "nodes", "identity", "coverage"])
def test_corruption_never_publishes(tmp_path, damage):
    census = fixture(tmp_path)
    manifest = json.loads(census.read_bytes())
    pin = file_hash(census)
    if damage == "pin":
        pin = "0" * 64
    elif damage == "nodes":
        (tmp_path / "source" / "merged-kg_nodes.tsv").write_bytes(b"wrong")
    elif damage in {"partition", "identity"}:
        path = census.parent / manifest["partitions"][0]["path"]
        if damage == "partition":
            path.write_bytes(b"wrong")
        else:
            table = pq.read_table(path)
            rows = table.to_pylist()
            rows[0]["occurrence_id"] = rows[1]["occurrence_id"]
            import pyarrow as pa
            pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), path)
            manifest["partitions"][0].update(bytes=path.stat().st_size, sha256=file_hash(path))
            census.write_bytes(canonical_json(manifest))
            pin = file_hash(census)
    else:
        manifest["partitions"][0]["first_row"] = 2
        census.write_bytes(canonical_json(manifest))
        pin = file_hash(census)
    output = tmp_path / "output"
    with pytest.raises(CurationError):
        prepare_inventory(census, pin, output, reserve_bytes=0)
    assert not (output / "manifest.json").exists()


def test_duplicate_node_ids_rejected(tmp_path):
    census = fixture(tmp_path, duplicate_nodes=True)
    with pytest.raises(CurationError, match="unique"):
        prepare_inventory(census, file_hash(census), tmp_path / "output", reserve_bytes=0)
    assert not (tmp_path / "output" / "manifest.json").exists()


def test_disk_reserve(tmp_path):
    census = fixture(tmp_path)
    with pytest.raises(CurationError, match="reserve"):
        prepare_inventory(census, file_hash(census), tmp_path / "output", reserve_bytes=10**20)
    assert not (tmp_path / "output").exists()


def test_partial_and_full_cross_partition_duplicate_counts(tmp_path, monkeypatch):
    import edgemech.census as census_module

    monkeypatch.setattr(census_module, "BATCH_ROWS", 1)
    census = fixture(tmp_path)
    partial = prepare_inventory(census, file_hash(census), tmp_path / "partial", reserve_bytes=0)
    assert partial["rows"] == 1
    assert partial["complete_population"] is False
    full = prepare_inventory(census, file_hash(census), tmp_path / "full",
                             partition_limit=None, reserve_bytes=0)
    assert full["rows"] == 3
    assert len(full["partitions"]) == 3
    assert full["profile"][0]["distinct_spo"] == 2
    assert full["complete_population"] is True
    assert full["selected_source_sha256"] == full["source"]["edge_member_sha256"]


def test_failed_publication_has_no_completion_marker(tmp_path, monkeypatch):
    import edgemech.content_inventory as inventory

    census = fixture(tmp_path)

    def interrupted(*args):
        raise OSError("Injected publication interruption")

    monkeypatch.setattr(inventory.os, "link", interrupted)
    with pytest.raises(OSError, match="Injected"):
        prepare_inventory(census, file_hash(census), tmp_path / "output", reserve_bytes=0)
    assert not (tmp_path / "output" / "manifest.json").exists()
    assert (tmp_path / "output" / "manifest.pending").stat().st_size > 0


def test_atomic_manifest_refuses_replacement(tmp_path):
    from edgemech.content_inventory import _write_json

    path = tmp_path / "manifest.json"
    path.write_text("original")
    with pytest.raises(FileExistsError):
        _write_json(path, {"replacement": True})
    assert path.read_text() == "original"
