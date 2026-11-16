"""Reject stale/scoped sources, unsafe config placement and laundered candidate archives."""

import copy
import csv
import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[1] / "scripts/adhoc/m5_release_merge_20261116.py"


@pytest.fixture
def merge():
    """Load the standalone helper without importing KG's graph pipeline."""
    spec = importlib.util.spec_from_file_location("m5_release_merge", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_only_declared_path_placement_changes_and_existing_stats_remain(merge, tmp_path):
    """Preserve every source/semantic option and never write tracked statistics during planning."""
    kg = tmp_path / "kg"
    kg.mkdir()
    stats = kg / "merged_graph_stats.yaml"
    stats.write_bytes(b"retained historical statistics\n")
    canonical = {
        "configuration": {"output_directory": "data/merged", "checkpoint": False,
                          "preserve": ["primary_knowledge_source"]},
        "merged_graph": {
            "source": {"bactotraits": {"name": "BactoTraits", "input": {"format": "tsv", "filename": [
                "data/transformed/bactotraits/nodes.tsv", "data/transformed/bactotraits/edges.tsv"]}},
                "madin_etal": {"input": {"format": "tsv", "filename": ["data/transformed/madin_etal/edges.tsv"]}}},
            "operations": [{"name": "kgx.graph_operations.summarize_graph.generate_graph_stats", "args": {
                "filename": "merged_graph_stats.yaml", "edge_facet_properties": ["source"]}}],
            "destination": {"merged-kg-tsv": {"format": "tsv", "compression": "tar.gz", "filename": "merged-kg"}},
        },
    }
    retained = copy.deepcopy(canonical)
    output = tmp_path / "exclusive-candidate"
    configured, deltas = merge.relocated_configuration(canonical, kg, output)
    assert canonical == retained
    assert configured["merged_graph"]["destination"] == canonical["merged_graph"]["destination"]
    assert configured["configuration"]["preserve"] == ["primary_knowledge_source"]
    assert configured["merged_graph"]["operations"][0]["args"]["filename"] == str(output / stats.name)
    assert configured["merged_graph"]["operations"][0]["args"]["edge_facet_properties"] == ["source"]
    assert configured["merged_graph"]["source"]["bactotraits"]["input"]["filename"] == [
        str(kg / "data/transformed/bactotraits/nodes.tsv"), str(kg / "data/transformed/bactotraits/edges.tsv")]
    assert len(deltas) == 4
    assert stats.read_bytes() == b"retained historical statistics\n"
    assert not output.exists()


@pytest.mark.parametrize("diagnostic", [True, "false", 0, None])
def test_diagnostic_or_ambiguous_finalization_flags_never_plan(merge, tmp_path, diagnostic):
    """Only the exact false boolean or absent canonical setting can pass."""
    with pytest.raises(ValueError, match="opt-out"):
        merge.relocated_configuration({"configuration": {"allow_unfinalized_sources": diagnostic}},
                                      tmp_path, tmp_path / "out")


def source_chain(merge, root):
    """Create small whole-source contracts whose byte identities can be independently changed."""
    receipts, paths, snapshots = {}, {}, {}
    units = root / "units"
    units.mkdir()
    for source in merge.SOURCES:
        directory = root / "data/transformed" / source
        directory.mkdir(parents=True)
        names = ("ncbitaxon_nodes.tsv", "chebi_nodes.tsv") if source == "ontologies" else ("nodes.tsv", "edges.tsv")
        for name in names:
            (directory / name).write_text("id\tcategory\ntest:1\tbiolink:NamedThing\n")
        (directory / "audit.tsv").write_text("check\tstatus\nsource\tpass\n")
        finalization = {"source": source, "members": {name: merge.identity(directory / name) for name in names},
                        "audit_members": {"audit.tsv": merge.identity(directory / "audit.tsv")}}
        marker = {"version": 3, "source": source}
        (directory / "source_finalization.json").write_text(json.dumps(finalization))
        (directory / "source_fingerprint.json").write_text(json.dumps(marker))
        unit_path = units / (source + ".json")
        unit_path.write_text(json.dumps({"returncode": 0, "source": source, "git_revision": "producer-pin",
                                         "task_raw_after": {}}))
        record = {"profile": "m5-canonical-release-source-unit/v1", "returncode": 0,
                  "upstream_unchanged": True, "ancillary_preexisting_unchanged": True,
                  "plan": {"source": source, "canonical_source_directory": str(directory),
                           "git_revision": "producer-pin", "implementation_and_policy_inputs": {}, "originals": [],
                           "upstream_before": copy.deepcopy(snapshots)},
                  "canonical_source_artifacts": merge.snapshot(directory), "finalization_record": finalization,
                  "producer_fingerprint": marker, "ancillary_after": {},
                  "unit_receipt": {"path": str(unit_path), **merge.identity(unit_path)}}
        path = root / (source + "-chain.json")
        path.write_text(json.dumps(record))
        receipts[source], paths[source] = record, path
        snapshots[source] = record["canonical_source_artifacts"]
    return receipts, paths


@pytest.mark.parametrize("damage", ["scope", "source_bytes", "upstream", "failed_unit", "failed_chain"])
def test_source_chain_must_bind_complete_actual_upstreams(merge, tmp_path, damage):
    """A clean-looking latest receipt cannot launder an incomplete or changed earlier producer."""
    root = tmp_path / "kg"
    root.mkdir()
    records, paths = source_chain(merge, root)
    merge.verify_chain(root, paths)
    source = root / "data/transformed/ontologies"
    if damage == "scope":
        (source / "source_finalization.json").rename(source / "ro_source_finalization.json")
        records["ontologies"]["canonical_source_artifacts"] = merge.snapshot(source)
        paths["ontologies"].write_text(json.dumps(records["ontologies"]))
    elif damage == "source_bytes":
        (source / "ncbitaxon_nodes.tsv").write_text("tampered retained output\n")
    elif damage == "upstream":
        records["bacdive"]["plan"]["upstream_before"]["ontologies"] = {}
        paths["bacdive"].write_text(json.dumps(records["bacdive"]))
    elif damage == "failed_unit":
        unit_path = Path(records["bactotraits"]["unit_receipt"]["path"])
        unit = json.loads(unit_path.read_text())
        unit["returncode"] = 1
        unit_path.write_text(json.dumps(unit))
        records["bactotraits"]["unit_receipt"].update(merge.identity(unit_path))
        paths["bactotraits"].write_text(json.dumps(records["bactotraits"]))
    else:
        records["ontologies"]["returncode"] = 1
        paths["ontologies"].write_text(json.dumps(records["ontologies"]))
    with pytest.raises(ValueError):
        merge.verify_chain(root, paths)


def graph_archive(path, *, target=False, provider="infores:bactotraits", diagnostic=False, tamper=False, duplicate=False):
    """Write compact transport bytes with independently constructed manifest hashes."""
    obj = "METPO:1000703" if target else "METPO:9999999"
    members = {
        "merged-kg_nodes.tsv": b"id\tcategory\nNCBITaxon:1123071\tbiolink:OrganismTaxon\n",
        "merged-kg_edges.tsv": ("subject\tpredicate\tobject\tprimary_knowledge_source\n"
                                f"NCBITaxon:1123071\tbiolink:has_phenotype\t{obj}\t{provider}\n").encode(),
        "merged-kg_reference_resolution.tsv": b"check\tstatus\nendpoint_closure\tpass\n",
    }
    manifest = {"manifest_version": 1, "members": {
        name: {"sha256": hashlib.sha256(value).hexdigest(), "bytes": len(value), "rows": value.count(b"\n") - 1}
        for name, value in members.items()},
        "provenance": {"commit": "b631cacf", "python": "3.10.11", "merge_config": {"sha256": "a" * 64},
                       "source_finalization": {"required": not diagnostic, "diagnostic_opt_out": diagnostic}}}
    if tamper:
        members["merged-kg_nodes.tsv"] += b"tampered:1\tbiolink:NamedThing\n"
    with tarfile.open(path, "w:gz") as archive:
        for name, payload in [*members.items(), ("manifest.json", json.dumps(manifest).encode())]:
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        if duplicate:
            info = tarfile.TarInfo("merged-kg_edges.tsv")
            info.size = len(members[info.name])
            archive.addfile(info, io.BytesIO(members[info.name]))


def test_actual_archive_counts_hashes_and_strict_provenance_are_verified(merge, tmp_path):
    """A valid compressed candidate returns independently streamed member counts."""
    archive = tmp_path / "candidate.tar.gz"
    graph_archive(archive)
    result = merge.inspect_archive(archive, "a" * 64, "b631cacf", "3.10.11")
    assert result["members"]["merged-kg_edges.tsv"]["rows"] == 1
    assert result["members"]["merged-kg_edges.tsv"]["target_spo_occurrences"] == 0
    assert result["archive"]["sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()


@pytest.mark.parametrize("options", [
    {"target": True}, {"target": True, "provider": ""}, {"diagnostic": True}, {"tamper": True}, {"duplicate": True},
])
def test_valid_exit_or_rehashed_manifest_cannot_hide_candidate_failure(merge, tmp_path, options):
    """Reject surviving target assertions, provenance loss, diagnostics and archive tampering."""
    archive = tmp_path / "candidate.tar.gz"
    graph_archive(archive, **options)
    with pytest.raises(ValueError):
        merge.inspect_archive(archive, "a" * 64, "b631cacf", "3.10.11")


def test_changed_plan_blocks_before_output_creation_or_cli(merge, tmp_path, monkeypatch):
    """A stale plan cannot start any candidate process or reserve its output."""
    output = tmp_path / "must-stay-absent"
    planned = {"profile": "m5-strict-bactotraits-merge-plan/v1", "binding": {"output": str(output)},
               "binding_sha256": "prior"}
    plan_file = tmp_path / "old-plan.json"
    plan_file.write_text(json.dumps(planned))
    current = {**planned, "binding_sha256": "changed-inputs"}
    monkeypatch.setattr(merge.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("CLI started with stale plan"))
    with pytest.raises(ValueError, match="since --plan"):
        merge.run(current, plan_file)
    assert not output.exists()


def test_changed_protected_stats_are_a_required_failure(merge, tmp_path):
    """Even an absent historical stats path is protected from new merge side effects."""
    stats = tmp_path / "merged_graph_stats.yaml"
    binding = {"input_pins": {}, "source_trees": {}, "runtime": {}, "protected_original_outputs": {str(stats): None}}
    stats.write_text("unexpected stats written in KG checkout\n")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(merge, "runtime", lambda: {})
        with pytest.raises(ValueError, match="statistics were overwritten"):
            merge.verify_after(binding)


def quarantine_tree(merge, root, monkeypatch):
    """Use an explicitly synthetic CSV hash while preserving exact-row and complete-field contracts."""
    raw = root / "data/raw/BactoTraits_databaseV2_Jun2022.csv"
    raw.parent.mkdir(parents=True)
    row = {"strain": "fixture", "Bacdive_ID": "17851", "Full_name": "mixed identity fixture",
           "culture collection codes": "DSM 19353, JCM 14586", "uninterpreted measurement": "0.5"}
    with raw.open("w", newline="", encoding="ISO-8859-1") as stream:
        writer = csv.writer(stream, delimiter=";")
        writer.writerow(["fixture metadata1"])
        writer.writerow(["fixture metadata2"])
        writer.writerow(row)
        for _ in range(8520):
            writer.writerow(["neighbor", "7", "independent neighbor", "DSM 7", "1.0"])
        writer.writerow(row.values())
    monkeypatch.setattr(merge, "SOURCE_SHA", hashlib.sha256(raw.read_bytes()).hexdigest())
    monkeypatch.setattr(merge, "ROW_SHA", hashlib.sha256(json.dumps(row, ensure_ascii=False, indent=2,
                                                                 sort_keys=True).encode()).hexdigest())
    policy = root / "mappings/canonical/bactotraits_identity_quarantine.json"
    policy.parent.mkdir(parents=True)
    decision = {"bacdive_id": "17851", "rule_id": "fixture-mixed-row", "full_name": row["Full_name"],
                "culture_collection_codes": row["culture collection codes"], "rationale": "Fixture identity conflict",
                "evidence_urls": ["https://example.test/fixture"]}
    policy.write_text(json.dumps({"decisions": [decision]}))
    source = root / "data/transformed/bactotraits"
    source.mkdir(parents=True)
    record = {**decision, "source_data_row": "8521", "reviewed_source_data_row": "8521", "ncbitaxon_id": merge.SPO[0],
              "source_sha256": merge.SOURCE_SHA, "reviewed_source_sha256": merge.SOURCE_SHA, "row_sha256": merge.ROW_SHA,
              "disposition": "quarantine_mixed_strain_row", "raw_row_json": json.dumps(row),
              "policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest(),
              "evidence_urls": "https://example.test/fixture"}
    audit = source / merge.AUDIT

    def write_audit(records):
        with audit.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(record), delimiter="\t")
            writer.writeheader()
            writer.writerows(records)

    write_audit([record])
    for folder, filename, key, bid, taxon in (
        ("bacdive", "bacdive.tsv", "bacdive_id", "bacdive:17851", merge.SPO[0]),
        ("bactotraits", "bactotraits_mapping.tsv", "Bacdive_ID", "bacdive:17851", merge.SPO[0]),
        ("bactotraits", "bactotraits.tsv", "Bacdive_ID", "bacdive:7", "NCBITaxon:7"),
    ):
        path = root / "kg_microbe/transform_utils" / folder / "tmp" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{key}\tncbitaxon_id\n{bid}\t{taxon}\n")
    (source / "edges.tsv").write_text("subject\tpredicate\tobject\tprimary_knowledge_source\n"
                                     "NCBITaxon:7\tbiolink:has_phenotype\tMETPO:1000703\tinfores:bactotraits\n")
    return record, write_audit


@pytest.mark.parametrize("damage", ["duplicate", "omitted_field", "source_hash", "identity_column", "retained_copy", "spo_leak"])
def test_complete_audit_and_retained_joins_are_required(merge, tmp_path, monkeypatch, damage):
    """A correct ordinal/hash label alone cannot hide row truncation or a leaking retained join."""
    record, write_audit = quarantine_tree(merge, tmp_path, monkeypatch)
    result = merge.verify_quarantine(tmp_path)
    assert result["audit"]["rows"] == 1
    assert result["source_edges"]["rows"] == 1  # Neighboring row remains present.
    if damage == "duplicate":
        write_audit([record, record])
    elif damage == "omitted_field":
        raw_row = json.loads(record["raw_row_json"])
        del raw_row["uninterpreted measurement"]
        write_audit([{**record, "raw_row_json": json.dumps(raw_row)}])
    elif damage == "source_hash":
        write_audit([{**record, "source_sha256": "0" * 64}])
    elif damage == "identity_column":
        write_audit([{**record, "full_name": "silent replacement identity"}])
    elif damage == "retained_copy":
        path = tmp_path / "kg_microbe/transform_utils/bactotraits/tmp/bactotraits.tsv"
        with path.open("a") as stream:
            stream.write(f"bacdive:17851\t{merge.SPO[0]}\n")
    else:
        path = tmp_path / "data/transformed/bactotraits/edges.tsv"
        with path.open("a") as stream:
            stream.write("\t".join((*merge.SPO, "infores:bactotraits")) + "\n")
    with pytest.raises(ValueError):
        merge.verify_quarantine(tmp_path)
