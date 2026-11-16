"""Issue #105: complete packets reject unrelated measurements and replay actual bytes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from kg_microbe_curation.identity import CurationError

from edgemech.occurrence_packet import build_packet, validate_packet


@pytest.fixture
def inputs(tmp_path):
    subject, object_id = "lpsn:783091", "kgmicrobe.source_attribute:salt"
    edge = {
        "occurrence_id": "urn:kg-microbe:occurrence:v1:fixture",
        "subject": subject, "predicate": "biolink:has_attribute", "object": object_id,
        "origin_transform": "microbedecoder/edges.tsv", "transform_row_number": 241764,
        "relation": "SIO:000008", "subject_label": "Fixture organism",
        "object_label": "reported Salt concentration: 0-10 (source value)",
        "subject_category": "biolink:OrganismTaxon", "object_category": "biolink:Attribute",
        "original_subject_node": {"id": subject, "description": "Retained taxonomic record"},
        "original_object_node": {"id": object_id, "description": "A source attribute"},
    }
    edge["omitted_source_record"] = {
        **{k: edge[k] for k in ("occurrence_id", "subject", "predicate", "object", "origin_transform")},
        "source_column": "BacDive_Salt_concentration", "value": "0-10",
    }
    source = {"edge": edge, "records": []}
    records = [
        ("database.csv", "CSV data row 20904", {
            "LPSN_ID": "783091", "BacDive_ID": "6845",
            "BacDive_Salt_concentration": "0-10", "BacDive_Salt_concentration_unit": "%",
            "Strain": "UNRELATED CROSSWALK STRAIN", "NCBI_ID": "999999",
        }),
        ("bacdive_strains.json", "6845", {
            "General": {"BacDive-ID": 6845},
            "Name and taxonomic classification": {"strain designation": "DSM 20190"},
            "External links": {"culture collection no.": "CIP 103005, DSM 20190"},
            "Physiology and metabolism": {"halophily": {
                "salt": "NaCl", "concentration": "0-10 %", "tested relation": "growth",
                "growth": "positive", "@ref": 119830,
            }},
            "Culture and growth conditions": {"temperature": "30", "medium": "Unlinked medium"},
            "Reference": [{"@id": 119830, "catalogue": "Fixture catalogue", "extra": "kept"}],
        }),
    ]
    for path, locator, record in records:
        text = json.dumps(record, sort_keys=True)
        source["records"].append({
            "source_relative_path": path, "locator": locator, "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        })
    return tmp_path, source


def persist(root, source, occurrence=None):
    occurrence = deepcopy(source["edge"]) if occurrence is None else occurrence
    (root / "source.json").write_text(json.dumps(source))
    (root / "occurrence.json").write_text(json.dumps(occurrence))
    descriptors = [{"path": name, "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}
                   for name in ("occurrence.json", "source.json")]
    return build_packet(occurrence, source, occurrence_input=descriptors[0],
                        source_input=descriptors[1], root=root)


def alter_record(source, index, mutate):
    wrapper = source["records"][index]
    record = json.loads(wrapper["text"])
    mutate(record)
    wrapper["text"] = json.dumps(record, sort_keys=True)
    wrapper["text_sha256"] = hashlib.sha256(wrapper["text"].encode()).hexdigest()


def test_complete_context_keeps_exact_strain_reference_and_unknowns(inputs):
    root, source = inputs
    packet = persist(root, source)
    context = packet["measurement_context"]
    assert [context[k] for k in ("substance", "literal_concentration", "recorded_unit",
                                "tested_relation", "growth_result")] == [
        "NaCl", "0-10", "%", "growth", "positive",
    ]
    assert context["organism_scope"]["strain_designation"] == "DSM 20190"
    assert "UNRELATED" not in json.dumps(context)
    assert context["percent_basis"] is context["assay_conditions"] is None
    assert context["reference"]["extra"] == "kept"
    assert context["source_bindings"][0]["locator"] == "CSV data row 20904"
    assert packet["endpoints"]["object"]["record"]["description"] == "A source attribute"
    assert packet["endpoints"]["subject"]["authority_status"] == "unassessed"
    assert packet["native_admission"] is False
    assert validate_packet(packet, root=root)["measurement_status"] == "source_bound"


@pytest.mark.parametrize("mutation", [
    lambda r: r.update(LPSN_ID="999"),
    lambda r: r.update(BacDive_ID="999"),
    lambda r: r.update(BacDive_Salt_concentration_unit="g/L"),
    lambda r: r.update(BacDive_Salt_concentration="0-11"),
])
def test_refuses_unrelated_source_unit_strain_or_value(inputs, mutation):
    root, source = inputs
    alter_record(source, 0, mutation)
    with pytest.raises(CurationError):
        persist(root, source)


@pytest.mark.parametrize("mutation", [
    lambda r: r["General"].update({"BacDive-ID": 999}),
    lambda r: r["Reference"][0].update({"@id": 111}),
    lambda r: r["Reference"].append(deepcopy(r["Reference"][0])),
    lambda r: r["Physiology and metabolism"]["halophily"].update(concentration="0-10 g/L"),
    lambda r: r["Physiology and metabolism"].update(halophily=[
        r["Physiology and metabolism"]["halophily"], r["Physiology and metabolism"]["halophily"]]),
])
def test_refuses_unrelated_or_ambiguous_bacdive_observation(inputs, mutation):
    root, source = inputs
    alter_record(source, 1, mutation)
    with pytest.raises(CurationError):
        persist(root, source)


def test_refuses_duplicate_exact_source_record(inputs):
    root, source = inputs
    source["records"].append(deepcopy(source["records"][0]))
    with pytest.raises(CurationError, match="one exact MicrobeDecoder"):
        persist(root, source)


def test_retained_input_mutation_and_self_authored_context_are_rejected(inputs):
    root, source = inputs
    packet = persist(root, source)
    altered = deepcopy(packet)
    altered["measurement_context"]["percent_basis"] = "w/v"
    with pytest.raises(CurationError, match="differs from replayed"):
        validate_packet(altered, root=root)
    (root / "source.json").write_text(json.dumps(source) + " ")
    with pytest.raises(CurationError, match="bytes differ"):
        validate_packet(packet, root=root)


@pytest.mark.parametrize("field", ["subject", "object"])
def test_endpoint_snapshots_cannot_be_swapped(inputs, field):
    root, source = inputs
    source["edge"]["original_" + field + "_node"]["id"] = "other:identifier"
    with pytest.raises(CurationError, match="node does not bind"):
        persist(root, source)


def test_public_projection_can_omit_private_description_but_cannot_alter_node(inputs):
    root, source = inputs
    public = deepcopy(source["edge"])
    del public["original_subject_node"]["description"]
    packet = persist(root, source, public)
    assert packet["endpoints"]["subject"]["record"]["description"] == "Retained taxonomic record"
    public["subject_category"] = "biolink:ChemicalEntity"
    with pytest.raises(CurationError, match="differs from its retained"):
        persist(root, source, public)


def test_unsupported_measurement_is_explicitly_unresolved(inputs):
    root, source = inputs
    source["edge"]["origin_transform"] = "other/edges.tsv"
    packet = persist(root, source)
    assert packet["measurement_context"]["status"] == "unresolved"
    assert packet["endpoints"]["object"]["category"] == "biolink:Attribute"


def test_replay_refuses_absolute_traversing_and_symlink_input_paths(inputs):
    root, source = inputs
    packet = persist(root, source)
    for path in (str(root / "source.json"), "../source.json"):
        bad = deepcopy(packet)
        bad["inputs"]["source"]["path"] = path
        with pytest.raises(CurationError, match="repository-relative"):
            validate_packet(bad, root=root)
    (root / "alias.json").symlink_to(root / "source.json")
    packet["inputs"]["source"]["path"] = "alias.json"
    with pytest.raises(CurationError, match="symlink"):
        validate_packet(packet, root=root)


def test_packet_display_includes_joined_context_before_literature(inputs, capsys):
    root, source = inputs
    packet = persist(root, source)
    directory = Path(__file__).resolve().parents[1] / "scripts/adhoc/edge_recanary_20261113"
    sys.path.insert(0, str(directory))
    try:
        spec = importlib.util.spec_from_file_location("complete_review_packet", directory / "review_packet.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.display({"primary": [], "fallback": []}, occurrence_packet=packet)
    finally:
        sys.path.remove(str(directory))
    output = capsys.readouterr().out
    first = json.loads(output.splitlines()[0])
    assert first["measurement_context"]["substance"] == "NaCl"
    assert first["measurement_context"]["recorded_unit"] == "%"
    assert first["endpoints"]["subject"]["id"] == "lpsn:783091"


@pytest.mark.parametrize("damage", ["changed", "deleted"])
def test_timed_review_refuses_context_changed_after_begin(tmp_path, damage):
    path = Path(__file__).resolve().parents[1] / "scripts/adhoc/edge_recanary_20261113/review_clock.py"
    spec = importlib.util.spec_from_file_location("bound_review_clock", path)
    clock = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(clock)
    packet, context = tmp_path / "literature.json", tmp_path / "context.json"
    packet.write_text('{"primary": []}')
    context.write_text('{"measurement": "original"}')
    receipt = clock.begin_review(tmp_path / "reviews", "scientific", "47", packet,
                                 bound_inputs=[context])
    assert receipt["timer"]["bound_inputs"][0]["sha256"] == hashlib.sha256(context.read_bytes()).hexdigest()
    if damage == "changed":
        context.write_text('{"measurement": "replacement"}')
    else:
        context.unlink()
    with pytest.raises(ValueError, match="Bound review input changed"):
        clock.finish_review(tmp_path / "reviews", "scientific", "47", {"decision": "unknown"})
    assert not (tmp_path / "reviews/decisions/scientific/47.json").exists()
