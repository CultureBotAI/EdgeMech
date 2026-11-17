"""Adversarial guards for the one-case round03 owner replay, 2026-11-16."""
import copy
import importlib.util
import os
import stat
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "first30_replay", Path(__file__).parents[1] / "scripts/adhoc/replay_first30_salinity_20261116.py")
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)


def source_record():
    return {"tax_name": replay.TAXON, "summaries": [
        {"name": name, "is_discrete": False, "num_observations": 27, "unique_databases": 1,
         "majority_label": label, "percentages": {}} for name, label in replay.FIELDS.items()]}


@pytest.mark.parametrize("mutation", ["taxon", "unit", "value", "duplicate", "missing", "discrete"])
def test_rejects_changed_source_semantics(mutation):
    record = source_record()
    if mutation == "taxon":
        record["tax_name"] = "another species"
    elif mutation in ("unit", "value"):
        record["summaries"][-1]["majority_label"] = (
            "Median: 1.8 M NaCl" if mutation == "unit" else "Median: 2.8 % NaCl (w/v)")
    elif mutation == "duplicate":
        record["summaries"].append(copy.deepcopy(record["summaries"][-1]))
    elif mutation == "missing":
        record["summaries"].pop()
    else:
        record["summaries"][-1]["is_discrete"] = True
    with pytest.raises(ValueError):
        replay.selected_summaries(record)


def test_exact_source_fields_kept_distinct():
    result = replay.selected_summaries(source_record())
    assert result["salinity maximum"]["majority_label"].startswith("Median: 1.8")
    assert result["salinity growth"]["majority_label"].startswith("Median: 0.0")


def test_checksum_guards_actual_bytes(tmp_path):
    path = tmp_path / "source"
    path.write_bytes(b"pinned")
    assert replay.check_file(path, replay.sha(b"pinned"))["bytes"] == 6
    path.write_bytes(b"mutated")
    with pytest.raises(ValueError, match="Pinned file mismatch"):
        replay.check_file(path, replay.sha(b"pinned"))


def test_private_outputs_under_permissive_umask_without_changing_ancestor(tmp_path):
    """Issue #188: actual persisted modes must not depend on the launcher's umask."""
    tmp_path.chmod(0o755)
    output = tmp_path / "new-parent" / "new-output"
    previous_umask = os.umask(0)
    try:
        replay.create_private_output_dir(output)
        path = output / "source-record.json"
        pin = replay.save_private(path, b"private evidence\n")
    finally:
        os.umask(previous_umask)
    assert stat.S_IMODE(tmp_path.stat().st_mode) == 0o755
    assert stat.S_IMODE(output.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert path.read_bytes() == b"private evidence\n"
    assert pin["sha256"] == replay.sha(path.read_bytes())
    with pytest.raises(ValueError, match="fresh directory"):
        replay.create_private_output_dir(output)
    with pytest.raises(FileExistsError):
        replay.save_private(path, b"replacement")
    assert path.read_bytes() == b"private evidence\n"


def test_source_record_pin_cannot_be_recomputed_to_accept_mutation():
    text = '{"tax_name":"another species"}'
    wrapper = {"text": text, "text_sha256": replay.sha(text.encode())}
    with pytest.raises(ValueError, match="record pin mismatch"):
        replay.verify_record(text.encode(), wrapper)


def compiled_method(path, source):
    namespace = {"__name__": replay.MODULE}
    exec(compile(source, str(path), "exec", dont_inherit=True), namespace)
    return namespace["MetaTraitsTransform"]._classify_salinity_phenotypes


def test_same_named_stub_fails_actual_owner_code_check(tmp_path):
    path = tmp_path / "owner.py"
    source = "class MetaTraitsTransform:\n    def _classify_salinity_phenotypes(self, low, high):\n        return [high]\n"
    owner = compiled_method(path, source)
    assert replay.verify_method(owner, path, source)["method"] == "_classify_salinity_phenotypes"
    stub = compiled_method(path, source.replace("return [high]", "return ['invented']"))
    with pytest.raises(ValueError, match="differs from pinned owner"):
        replay.verify_method(stub, path, source)
    wrong_path = compiled_method(tmp_path / "installed-copy.py", source)
    with pytest.raises(ValueError, match="source path mismatch"):
        replay.verify_method(wrong_path, path, source)


def occurrence_inputs():
    assertion = {"subject": replay.SUBJECT, "predicate": "biolink:has_phenotype", "object": replay.OBJECT,
                 "relation": "RO:0002200", "origin_transform": "metatraits_gtdb/edges.tsv",
                 "occurrence_id": replay.OCCURRENCE, "transform_row_number": replay.EDGE_ROW}
    row = {k: assertion[k] for k in ("subject", "predicate", "object", "relation")}
    row.update(value="1.8", unit="%NaCl(w/v)")
    packet = {"original_assertion": assertion.copy(), "occurrence_id": replay.OCCURRENCE,
              "endpoints": {"subject": {"label": replay.TAXON}}}
    source = {"edge": {**assertion, "curated_source_record": row.copy()}}
    return packet, source, assertion.copy(), row


@pytest.mark.parametrize("field,value", [("subject", "GTDB:other"), ("unit", "M"), ("value", "0.0")])
def test_retained_edge_mutation_rejected(field, value):
    packet, source, occurrence, row = occurrence_inputs()
    replay.verify_occurrence(packet, source, occurrence, row)
    row[field] = value
    with pytest.raises(ValueError):
        replay.verify_occurrence(packet, source, occurrence, row)


def test_occurrence_ordinal_identity_rejected():
    packet, source, occurrence, row = occurrence_inputs()
    occurrence["transform_row_number"] += 1
    with pytest.raises(ValueError, match="Frozen occurrence mismatch"):
        replay.verify_occurrence(packet, source, occurrence, row)


def test_definition_mismatch_cannot_be_hidden_by_correct_label():
    node = {"id": "https://w3id.org/metpo/1000625", "type": "CLASS", "lbl": "slightly halophilic",
            "meta": {"definition": {"val": "optimal growth"}}}
    ontology = {"graphs": [{"nodes": [node]}]}
    packet = {"endpoints": {"object": {"label": node["lbl"], "id": replay.OBJECT,
                                       "record": {"description": "optimal growth"}}}}
    output = {"curie": replay.OBJECT, "name": node["lbl"]}
    mapping = {node["lbl"]: output}
    assert replay.verify_ontology(ontology, packet, output, mapping) == node
    node["meta"]["definition"]["val"] = "maximum tolerance"
    with pytest.raises(ValueError, match="definition differs"):
        replay.verify_ontology(ontology, packet, output, mapping)
