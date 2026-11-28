#!/usr/bin/env python3
"""Prepare exactly one excluded first-32 native draft, never save canonically.

Purpose: issues228/220 tracked producer for exposed, partial native proof drafts.
Inputs: explicitly pinned retained occurrence/source/authority files, actual
native session metadata and interpreter/dependency/source bindings.
Outputs: append-only private acceptance, draft inputs/proofs and validation
receipts exclusively below .temp/first32-worker-20261128. UTC date: 2026-11-28.
Provenance: new parameterized preparation producer; no historical replay,
provider requests, population credit, calibration agreement or canonical SAVE.
Source and exact artifacts require independent review before any publication/save.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / ".temp/first32-worker-20261128"
OCCURRENCE = "urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b"
OWNED_SOURCE = {"scripts/adhoc/prepare_first32_native_20261128.py",
                "tests/test_prepare_first32_native_20261128.py"}


def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Regular nonsymlink input required: {path}")
    return path.read_bytes()


def pin(path):
    raw = read(path)
    return {"path": str(path), "bytes": len(raw), "sha256": digest(raw)}


def checked(path, *, absent=False):
    path = Path(path)
    if ".." in path.parts:
        raise ValueError("Traversal forbidden")
    path = path.absolute()
    path.relative_to(OUTPUT)
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("Symlink output component")
        if current.exists() and current != path and not current.is_dir():
            raise ValueError("Nondirectory output component")
    path.resolve().relative_to(OUTPUT.resolve())
    if absent and path.exists():
        raise FileExistsError(path)
    return path


def reserve(path):
    path = checked(path, absent=True)
    path.mkdir(parents=True, mode=0o700)
    return path


def save(path, raw):
    path = checked(path, absent=True)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if read(path) != raw:
        raise ValueError("Written-byte readback mismatch")
    return pin(path)


def save_json(path, data):
    return save(path, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode())


def git(*args, root=ROOT):
    return subprocess.check_output(["git", *args], cwd=root)


def state(root):
    listing = git("ls-files", "-z", root=root)
    return {"root": str(root), "head": git("rev-parse", "HEAD", root=root).decode().strip(),
            "branch": git("branch", "--show-current", root=root).decode().strip(),
            "status": git("status", "--porcelain=v1", root=root).decode(),
            "work_diff_sha256": digest(git("diff", "--binary", root=root)),
            "index_diff_sha256": digest(git("diff", "--cached", "--binary", root=root)),
            "tracked": [pin(root / os.fsdecode(name)) for name in listing.split(b"\0")
                        if name and os.fsdecode(name) not in OWNED_SOURCE]}


def native_metadata(history):
    session = context = None
    with Path(history).open("rb") as stream:
        for line in stream:
            if not line.endswith(b"\n"):
                continue
            item = json.loads(line)
            if item.get("type") == "session_meta":
                session = item
            elif item.get("type") == "turn_context":
                context = item
    if session is None or context is None:
        raise ValueError("Actual native session/turn metadata unavailable")
    return {"history": str(history), "session_meta": session, "turn_context": context}


def runtime():
    modules = {}
    for name in ("edgemech.occurrence_packet", "edgemech.occurrence_review", "edgemech.pins",
                 "kg_microbe_reviews", "kg_microbe_governance.artifacts.scripts.record_review"):
        module = importlib.import_module(name)
        modules[name] = pin(Path(module.__file__).resolve())
    if not all(Path(modules[name]["path"]).is_relative_to(ROOT / "src")
               for name in modules if name.startswith("edgemech.")):
        raise ValueError("EdgeMech import is not bound to science checkout src")
    return {"observed_at_utc": utc(), "pid": os.getpid(), "parent_pid": os.getppid(),
            "interpreter": sys.executable, "resolved_interpreter": str(Path(sys.executable).resolve()),
            "python_version": sys.version, "platform": platform.platform(), "cwd": str(Path.cwd()),
            "sys_path": sys.path, "explicit_pythonpath": os.environ.get("PYTHONPATH"),
            "modules": modules, "distributions": sorted(
                [{"name": d.metadata["Name"], "version": d.version}
                 for d in importlib.metadata.distributions()], key=lambda d: str(d["name"]))}


def accept(args):
    output = reserve(args.output)
    native = native_metadata(args.history)
    original = state(args.original_root)
    bound = state(ROOT)
    observed = runtime()
    save(output / "producer.py.original", read(Path(__file__)))
    save_json(output / "native-metadata.json", native)
    save_json(output / "original-checkout-state.json", original)
    save_json(output / "science-checkout-state.json", bound)
    result = {"recorded_at_utc": utc(), "classification": "EXCLUDED_EXPOSED_FIRST32_DRAFT_PREPARATION",
              "occurrence_id": OCCURRENCE, "scientific_production_coverage": 0,
              "A_count": None, "B_count": None, "baseline_cutoff": None,
              "unobserved_candidates_retained": 694, "historical_census_outer": "FAILED1",
              "historical_census_child": "UNKNOWN", "canonical_save_authorized": False,
              "native_session": native, "runtime": observed, "source_binding": bound,
              "original_checkout_head": original["head"], "producer": pin(Path(__file__)),
              "new_provider_requests": 0, "exposed_preparation": True,
              "readiness_limit": "Preparation bindings only; separate exact-artifact/runtime admissibility review required before one SAVE",
              "durable_output_root": str(OUTPUT)}
    return save_json(output / "ACCEPTANCE.json", result)


INPUT_PINS = {
    "occurrence.json": (".temp/edge-calibration-20261115/first-32/occurrence.json", "d80216b91e94eec7e6fe6f8feaf070539286ab7f4601f056562b99b9a2e81c3a"),
    "source.json": (".temp/edge-calibration-20261115/first-32/source.json", "5c1d2f4d001642bc136718e7ddd67d231d9ca0589b6c406a5d110dd6a6dcdc1e"),
    "retained-packet.json": (".temp/edge-calibration-20261115/first-32/packet.json", "32cb804b4f6e0f678f01faf3ecf351146101d1beb0abe6e77ecbffedd470ded2"),
    "biolink.txt": (".temp/m5-round03-worker-20261116/round03-package/evidence/r03-evidence-001.txt", "4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb"),
    "ncbi.txt": (".temp/m5-round03-worker-20261116/round03-package/evidence/r03-evidence-015.txt", "37433381f5915338ee3e342a85ea15e8417fcf7b9bb7f08871cac084f958490d"),
    "lpsn.txt": (".temp/m5-round03-worker-20261116/round03-package/evidence/r03-evidence-023.txt", "b0d4c227cf90f01256edd978d913821d8ad38dc1d15b6850b0ca9d2abb445875"),
    "retained-manifest.json": (".temp/m5-round03-worker-20261116/round03-package/manifest.json", "3928396bf4c089620ec0209fdcb986c14f36969259ed01ab563c6807037ee298"),
    "lpsn-view-receipt.json": (".temp/m5-round03-worker-20261116/round03-package/receipts/r03-evidence-023.json", "e5d2609642ebf70e9f49aa4534d59fb155a77aaa7ef8fe03405f0f82e4b3c6d3"),
}
AUTHORITY = {
    "biolink": {"eid": "r03-evidence-001", "version": "4.4.0",
                "reference": "https://raw.githubusercontent.com/biolink/biolink-model/v4.4.0/biolink-model.yaml",
                "extent": "Inspected close match, related to at concept level, related to and organism taxon sections; full document retained, not claimed completely read",
                "retrieved_at": None, "update_time": None},
    "ncbi": {"eid": "r03-evidence-015",
             "version": "NCBI record UpdateDate=2013/01/11 12:14:10; retrieved=2026-11-16T20:38:28.005741+00:00",
             "reference": "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1281099",
             "extent": "Complete retained 2389-byte NCBI XML; identifier, name, parent, rank, lineage and dates",
             "retrieved_at": "2026-11-16T20:38:28.005741+00:00", "update_time": "2013/01/11 12:14:10"},
    "lpsn": {"eid": "r03-evidence-023", "version": "provider snapshot2026-11-16",
             "reference": "https://lpsn.dsmz.de/species/methanomethylophilus-alvi",
             "extent": "Complete retained 3796-byte LPSN view; whole-native-document receipt checked; record, name, rank, lineage and nomenclature",
             "retrieved_at": None, "snapshot_date": "2026-11-16", "update_time": None},
}
CATEGORIES = {"claim": "CONTRADICTED_AS_STATED", "literature": "NOT_APPLICABLE",
              "relation": "INCORRECT", "subject_node": "CORRECT", "object_node": "CORRECT",
              "source_fidelity": "NOT_ASSESSABLE"}
LIMIT = "Exposed first-32 preparation only; no production, Queue A/B, blinded calibration or paper-access credit."
LINEAGE = "Exact source-row co-occurrence is replayed, but the original producer's version-specific field-to-close_match semantics and full emission lineage are not established."


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative_pin(path):
    return {"path": str(Path(path).absolute().relative_to(ROOT)), "sha256": pin(path)["sha256"]}


def proof_specs():
    specs = []
    snippets = {
        "lpsn": [("name-rank", "Species Methanomethylophilus alvi"),
                 ("identifier", "Record number: 46511"), ("lineage", "Archaea Methanobacteriati")],
        "ncbi": [("identifier-name", "<TaxId>1281099</TaxId>\n    <ScientificName>Escherichia coli HVH 169 (4-1075578)</ScientificName>"),
                 ("rank-lineage", "<Rank>strain</Rank>\n    <Division>Bacteria</Division>")],
    }
    for authority, pieces in snippets.items():
        node = "subject_node" if authority == "lpsn" else "object_node"
        for role, axes in (("supports", [node]), ("refutes", ["claim", "relation"])):
            for suffix, quote in pieces:
                specs.append({"evidence_id": f"{authority}-{suffix}-{role}",
                    "manifest_evidence_id": AUTHORITY[authority]["eid"], "kind": "authority",
                    "scope": "exact", "support": role, "axes": axes,
                    "scope_rationale": ("The authority identifies the encoded endpoint in its retained version."
                        if role == "supports" else
                        "Read together with the other endpoint and Biolink definition, this retained taxon meaning refutes the original crosswalk; it does not invalidate either identifier."),
                    "inspected_extent": AUTHORITY[authority]["extent"],
                    "version": AUTHORITY[authority]["version"], "reference": AUTHORITY[authority]["reference"],
                    "quote": quote, "locator": f"{authority} retained native document; {suffix}",
                    "summary": "Endpoint identity evidence" if role == "supports" else "Version-scoped crosswalk counterevidence"})
    for eid, quote, axes, role in (
        ("biolink-relation", "semantically similar but not strictly equivalent", ["relation"], "refutes"),
        ("biolink-taxon", "classification of a set of organisms.", ["subject_node", "object_node"], "supports"),
        ("biolink-strain", "strains or subspecies.", ["object_node"], "supports"),
    ):
        specs.append({"evidence_id": eid, "manifest_evidence_id": "r03-evidence-001",
            "kind": "authority", "scope": "exact", "support": role, "axes": axes,
            "scope_rationale": "Biolink4.4.0 criterion applied to the retained endpoint meanings; original build model-version lineage is not established",
            "inspected_extent": AUTHORITY["biolink"]["extent"], "version": "4.4.0",
            "reference": AUTHORITY["biolink"]["reference"], "quote": quote,
            "locator": "Biolink4.4.0 close match or organism taxon definition",
            "summary": "Crosswalk fails semantic-similarity criterion" if role == "refutes" else "OrganismTaxon category applicability"})
    specs.append({"evidence_id": "source-packet", "manifest_evidence_id": "new-packet",
        "kind": "packet", "scope": "partial", "support": "context_only", "axes": ["source_fidelity"],
        "scope_rationale": LINEAGE, "inspected_extent": "Entire retained occurrence/source/packet and exact database.csv record10743",
        "reference": "packet-placeholder", "locator": "original_assertion; source_records[0]; CSV data row10743",
        "summary": "Exact row co-occurrence and packet replay, not complete generation fidelity"})
    return specs


def quote_budget(specs):
    groups = {}
    for item in specs:
        if item["kind"] != "authority":
            continue
        key = item["manifest_evidence_id"]
        group = groups.setdefault(key, {"proof_words": 0, "axis_weighted_words": 0, "proof_ids": []})
        words = len(item["quote"].split())
        group["proof_words"] += words
        group["axis_weighted_words"] += words * len(item["axes"])
        group["proof_ids"].append(item["evidence_id"])
    require(all(g["axis_weighted_words"] <= 25 for g in groups.values()),
            "Aggregate authority quote budget exceeds25 including repeated roles/axes")
    return groups


def assessments(specs):
    shared_scope = "Original lpsn:46511 biolink:close_match / skos:closeMatch NCBITaxon:1281099 assertion; authority versions retained November16, evaluated in exposed preparation."
    details = {
        "claim": {"assertion_scope": shared_scope + " This is semantic correspondence between taxon concepts, not a source-report reinterpretation or an experimental phenotype claim."},
        "literature": {"search_scope": "Classified the exact retained assertion and source row as an identifier crosswalk. Used retained taxonomic definitions and Biolink semantics; no paper search/retrieval or paper proof. Embedded DOI/PMID enrichments are source context, not experimental crosswalk support or paper-access credit."},
        "relation": {"direction": "Biolink4.4.0 close match is symmetric and exactly maps to skos:closeMatch; reversing endpoints cannot repair the taxon mismatch.",
            "domain_range": "The inspected close match -> related to at concept level -> related to hierarchy permits named things; two OrganismTaxon instances satisfy broad category compatibility but this does not establish conceptual similarity.",
            "specificity": "An archaeal species and an Escherichia coli bacterial strain do not express the same general taxon concept under the inspected model semantics.",
            "qualifiers": "No qualifier repairs the crosswalk. Exact generating-graph model version is unavailable; judgment is explicitly version-scoped."},
        "subject_node": {"identity": "Retained LPSN view explicitly identifies record46511 as Methanomethylophilus alvi.",
            "label": "The encoded subject label matches the retained LPSN species name.",
            "category_fit": "Biolink4.4.0 OrganismTaxon describes a classification of organisms, fitting this species; this does not certify strict prefix-policy conformance or generating-version admissibility.",
            "rank_or_type": "Species in retained LPSN snapshot; archaeal lineage.",
            "definition": "Taxon concept defined by the full retained name/rank/lineage record; distinct from the bacterial object strain.",
            "authority_version": "LPSN provider snapshot2026-11-16; Biolink4.4.0. Exact LPSN retrieval time and update time are not supplied; neither is fabricated or equated to current nomenclature."},
        "object_node": {"identity": "NCBI TaxId1281099 identifies Escherichia coli HVH169(4-1075578); full XML parent is562.",
            "label": "The encoded Escherichia coli HVH 169 (4-1075578) label matches the retained ScientificName.",
            "category_fit": "Biolink4.4.0 OrganismTaxon explicitly includes strains; category fit does not validate the mapping.",
            "rank_or_type": "Strain, parent562, bacterial lineage in the retained full XML.",
            "definition": "The specific E.coli strain concept, not Methanomethylophilus alvi; no corrected replacement identifier is proposed.",
            "authority_version": "NCBI retrieved2026-11-16T20:38:28.005741+00:00; UpdateDate2013/01/11 12:14:10 is record metadata, not a 2013 snapshot. Biolink4.4.0."},
        "source_fidelity": {"source_binding": "microbedecoder/edges.tsv row85111; database.csv CSV data row10743 contains LPSN_ID46511 and NCBI_Taxonomy_ID1281099 with divergent lineages. " + LINEAGE},
    }
    rationales = {
        "claim": "The retained authorities identify an archaeal species and a bacterial E.coli strain, contradicting the asserted semantic taxon correspondence within these versions.",
        "literature": "Experimental literature is inapplicable to this structural crosswalk. Taxonomic definitions and mapping semantics govern; no experimental-paper/fulltext credit is claimed.",
        "relation": "The original close_match relation fails semantic similarity, despite valid broad endpoint categories and symmetry.",
        "subject_node": "The subject identifier, label, species rank and organism-taxon meaning are correct within the retained authority scope.",
        "object_node": "The object identifier, label, strain rank and organism-taxon meaning are correct within the retained authority scope.",
        "source_fidelity": LINEAGE,
    }
    return [{"axis": axis, "category": CATEGORIES[axis], "scope": shared_scope,
             "rationale": rationales[axis], "dimensions": details[axis],
             "evidence_ids": [p["evidence_id"] for p in specs if axis in p["axes"]]}
            for axis in CATEGORIES]


def validate_limits(review, sidecar):
    require(review["completion"] == "partial", "Required lineage limit must remain partial")
    axes = {next(d["value"] for d in a["dimensions"] if d["name"] == "axis"):
            next(d["value"] for d in a["dimensions"] if d["name"] == "category")
            for a in review["assessments"]}
    require(axes == CATEGORIES, "Excluded first32 draft categories/limits changed")
    require(all(p["kind"] in {"authority", "packet"} for p in sidecar["proofs"]), "Unexpected paper proof")
    require(not any("literature" in p["axes"] for p in sidecar["proofs"]), "No literature proof allowed")
    require(review["targets"][0]["target_id"] == OCCURRENCE and len(review["targets"]) == 1,
            "Only the exact first32 occurrence is authorized")


def prepare(args):
    import copy
    import xml.etree.ElementTree as ET
    from importlib.resources import files

    import author_m5_review_data_20261116 as mechanical
    from kg_microbe_governance.artifacts.scripts.record_review import SCHEMA_PATH, render_markdown
    from kg_microbe_reviews import load_document, validate_review

    from edgemech.occurrence_packet import build_packet, validate_packet
    from edgemech.occurrence_review import PROFILE, validate_occurrence_review
    from edgemech.pins import check_contracts

    started = utc()
    acceptance = json.loads(read(args.acceptance / "ACCEPTANCE.json"))
    binding = json.loads(read(checked(args.expected_binding)))
    changes = json.loads(read(checked(args.coordinator_changes)))
    actual_native = native_metadata(Path(binding["native_history"]))
    check_identity(acceptance, binding)
    check_identity({"native_session": actual_native}, binding)
    before = verify_preservation(args.acceptance, changes)
    output = reserve(args.output)
    save(output / "producer.py.original", read(Path(__file__)))
    save_json(output / "current-native-metadata.json", actual_native)
    save(output / "expected-native.json", read(args.expected_binding))
    save(output / "coordinator-changes.json", read(args.coordinator_changes))
    retained = {}
    input_manifest = []
    for name, (path, checksum) in INPUT_PINS.items():
        original = args.retained_root / path
        raw = read(original)
        require(digest(raw) == checksum, f"Retained input hash mismatch: {name}")
        destination = output / "inputs" / name
        save(destination, raw)
        input_manifest.append({"original": pin(original), "private_copy": pin(destination)})
        retained[name] = destination
    for index, path in enumerate(args.authority):
        destination = output / "authority" / f"instruction-{index:02d}.md"
        save(destination, read(path))
        input_manifest.append({"original": pin(path), "private_copy": pin(destination)})
    for name in ("occurrence.json", "source.json", "retained-packet.json", "retained-manifest.json"):
        retained[name] = json.loads(read(retained[name]))
    source, occurrence = retained["source.json"], retained["occurrence.json"]
    require(occurrence["occurrence_id"] == OCCURRENCE, "Wrong occurrence")
    require((occurrence["subject"], occurrence["predicate"], occurrence["object"], occurrence["relation"])
            == ("lpsn:46511", "biolink:close_match", "NCBITaxon:1281099", "skos:closeMatch"), "Original assertion mismatch")
    source_record = json.loads(source["records"][0]["text"])
    require(len(source["records"]) == 1 and source["records"][0]["locator"] == "CSV data row 10743"
            and source_record["LPSN_ID"] == "46511" and source_record["NCBI_Taxonomy_ID"] == "1281099",
            "Exact source-row binding differs")
    original_packet = retained["retained-packet.json"]
    original_replay = validate_packet(original_packet, root=args.retained_root)
    packet = build_packet(occurrence, source,
        occurrence_input=relative_pin(output / "inputs/occurrence.json"),
        source_input=relative_pin(output / "inputs/source.json"), root=ROOT)
    rebound = copy.deepcopy(packet)
    rebound["inputs"] = original_packet["inputs"]
    require(rebound == original_packet, "New packet changes retained content beyond copied input paths")
    save_json(output / "packet.json", packet)
    packet_pin = relative_pin(output / "packet.json")
    manifest = {"classification": "ONE_CASE_EXCLUDED_INPUT_BUNDLE_NOT_A_CALIBRATION_ROUND",
                "scientific_status": "draft_preparation_only", "cases": [], "files": []}
    manifest["files"].append({**packet_pin, "role": "packet", "evidence_ids": ["new-packet"]})
    old_files = retained["retained-manifest.json"]["files"]
    for name, metadata in AUTHORITY.items():
        checksum = pin(output / "inputs" / (name + ".txt"))["sha256"]
        matches = [p for p in old_files if metadata["eid"] in p.get("evidence_ids", [])]
        require(len(matches) == 1 and matches[0]["sha256"] == checksum
                and matches[0]["version"] == metadata["version"], "Authority version/manifest binding mismatch")
        manifest["files"].append({**relative_pin(output / "inputs" / (name + ".txt")),
            "role": "authority", "evidence_ids": [metadata["eid"]], **metadata})
    xml = ET.fromstring(read(output / "inputs/ncbi.txt"))
    require(xml.findtext("./Taxon/UpdateDate") == AUTHORITY["ncbi"]["update_time"], "NCBI update metadata differs")
    receipt = json.loads(read(output / "inputs/lpsn-view-receipt.json"))
    lpsn_hash = INPUT_PINS["lpsn.txt"][1]
    require(receipt["policy"] == "whole_native_document" and receipt["source_sha256"] == lpsn_hash
            and receipt["view_sha256"] == lpsn_hash and receipt["spans"][0]["source_byte_end"] == 3796,
            "LPSN whole-view receipt differs")
    case = {"case_id": "first-32", "occurrence_id": OCCURRENCE, "packet_path": packet_pin["path"],
            "evidence_ids": ["new-packet", *[a["eid"] for a in AUTHORITY.values()]]}
    manifest["cases"] = [case]
    save_json(output / "input-bundle.json", manifest)
    observed = runtime()
    contracts = check_contracts()
    contract_description = json.loads(read(ROOT / "src/edgemech/contract-pins.json"))
    contract_pins = []
    for package, items in contract_description["packages"].items():
        for name, checksum in items.items():
            path = Path(str(files(package).joinpath(name)))
            require(pin(path)["sha256"] == checksum, "Installed contract drift")
            destination = output / "runtime/contracts" / package / name
            save(destination, read(path))
            contract_pins.append({"installed": pin(path), "copy": relative_pin(destination)})
    require(pin(SCHEMA_PATH)["sha256"] == pin(ROOT / "schema/record_review.yaml")["sha256"], "Schema copies differ")
    code_paths = ["src/edgemech/occurrence_packet.py", "src/edgemech/occurrence_review.py",
        "src/edgemech/literature_cache.py", "src/edgemech/storage/parquet.py", "src/edgemech/pins.py",
        "src/edgemech/contract-pins.json", "schema/record_review.yaml", "pyproject.toml", "uv.lock",
        "docs/record-review-profile.md", "scripts/adhoc/author_m5_review_data_20261116.py",
        "scripts/adhoc/calibration_round_20261116.py", *sorted(OWNED_SOURCE)]
    observed.update({"contracts": contracts, "contract_files": contract_pins,
                     "code": [pin(ROOT / p) for p in code_paths],
                     "source_state": "working_tree", "base": git("rev-parse", "HEAD").decode().strip(),
                     "limitation": "Existing interpreter with explicit science src; pinned16 contracts pass. This new draft/producer and exact runtime await independent admissibility review; no new eligible ten-case package claimed."})
    save_json(output / "runtime-manifest.json", observed)
    save_json(output / "identity-binding.json", {"canonical_reviewer": binding["canonical_reviewer"], "expected_binding": relative_pin(output / "expected-native.json"), "actual_native_metadata": relative_pin(output / "current-native-metadata.json"), "actual_thread": actual_native["session_meta"]["payload"]["id"], "actual_model": actual_native["turn_context"]["payload"]["model"], "actual_effort": actual_native["turn_context"]["payload"]["effort"], "runtime": relative_pin(output / "runtime-manifest.json"), "observed_at_utc": utc(), "actual_pid": observed["pid"], "exposed_self_review": True})
    save_json(output / "input-manifest.json", {"captured_at_utc": utc(), "inputs": input_manifest})
    specs = proof_specs()
    specs[-1]["reference"] = packet_pin["path"]
    budget = quote_budget(specs)
    authored = assessments(specs)
    accessed_at = utc()
    save_json(output / "authored-spec.json", {"recorded_at_utc": accessed_at, "proofs": specs,
        "assessments": authored, "scope": LIMIT, "newly_authored": True,
        "historical_exposure": "Coordinator narrative and retained row contain historical judgments; this task is explicitly exposed. Historical adjudication proofs were not used as authored verdicts."})
    proofs, evidence = mechanical.make_evidence(ROOT, manifest, case, specs, accessed_at)
    literal_replay = []
    for proof, item in zip(proofs, evidence, strict=True):
        if proof["kind"] == "packet":
            continue
        raw = read(ROOT / proof["input"]["path"])
        text = raw.decode()
        quote = item["quote"]
        start, end = proof["start"], proof["end"]
        require(text[start:end] == quote, "Literal character replay failed")
        bstart, bend = len(text[:start].encode()), len(text[:end].encode())
        require(raw[bstart:bend] == quote.encode(), "Literal byte replay failed")
        literal_replay.append({"evidence_id": proof["evidence_id"], "quote_sha256": digest(quote.encode()),
            "character_start": start, "character_end": end, "utf8_byte_start": bstart,
            "utf8_byte_end": bend, "input_sha256": digest(raw), "words": len(quote.split())})
    sidecar = {"profile": PROFILE, "occurrence_id": OCCURRENCE, "proofs": proofs}
    save_json(output / "proofs.json", sidecar)
    save_json(output / "literal-replay.json", {"quotes": literal_replay, "aggregate_budget": budget,
        "budget_method": "Every proof counted, and conservatively each axis counted even for one shared proof; no deduplication across repeated roles"})
    finished = datetime.now(timezone.utc)
    finished_at = finished.isoformat().replace("+00:00", "Z")
    started_at = datetime.fromisoformat(started).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    checks = [{"check_id": "retained-replay", "name": "Exact input and native packet replay", "status": "passed",
               "required": True, "target_ids": [OCCURRENCE], "summary": "Pinned original bytes and rebuilt packet replay passed; only private-copy paths changed."},
              {"check_id": "quote-replay", "name": "Literal authority offset and budget replay", "status": "passed",
               "required": True, "target_ids": [OCCURRENCE], "summary": "Exact native character and UTF8 byte spans replayed, with conservative repeated-role budgets <=25 per authority."},
              {"check_id": "original-generation", "name": "Original version-specific emission lineage", "status": "unavailable",
               "required": True, "target_ids": [OCCURRENCE], "summary": LINEAGE},
              {"check_id": "experimental-paper", "name": "Experimental literature for structural crosswalk", "status": "not_applicable",
               "required": False, "target_ids": [OCCURRENCE], "summary": "Identifier definitions and relation semantics govern this assertion; no paper-access credit."}]
    claim_eids = [p["evidence_id"] for p in specs if "claim" in p["axes"]]
    ownership = "The upstream MicrobeDecoder crosswalk producer/source-field owner must establish original-version lineage before any correction; frozen occurrence bytes are not edited."
    review = {"schema_version": "1.0.0", "review_id": finished.strftime("%Y%m%dT%H%M%SZ") + "-excluded-first32-draft",
        "kind": "record", "repository": "CultureBotAI/EdgeMech", "skill": PROFILE,
        "title": "Exposed partial first-32 taxon crosswalk assessment draft", "started_at": started_at, "finished_at": finished_at,
        "reviewer": {"identity": binding["canonical_reviewer"],
            "kind": "agent", "model": "gpt-6-astra", "independence": "self_review",
            "independence_basis": "Explicitly exposed retained fixed case; read coordinator narrative and historical annotations in source. New judgments from inspected source/authorities; not blinded agreement."},
        "completion": "partial", "verdict": "needs_curation", "scientific_review": True,
        "summary": "Retained-version authorities contradict the crosswalk while validating both individual endpoint meanings; original generation fidelity remains not assessable. " + LIMIT,
        "source": {"git_revision": observed["base"], "state": "working_tree", "inputs": []},
        "scope": {"description": LIMIT, "selection": "Exactly one user-designated exposed first-32 occurrence; not Queue A/B or a replacement ten-case round.",
                  "coverage": "partial", "population_size": 1, "reviewed_target_ids": [OCCURRENCE]},
        "targets": [{"target_id": OCCURRENCE, "path": packet_pin["path"], "selector": "occurrence_id=" + OCCURRENCE,
                     "label": "first-32 original crosswalk", "kind": "snapshot_row", "ownership_note": ownership}],
        "checks": checks, "evidence": evidence, "assessments": mechanical.make_assessments(authored, OCCURRENCE),
        "findings": [{"finding_id": "crosswalk-mismatch", "issue_key": "first32-crosswalk-mismatch", "category": "identity",
            "severity": "major", "status": "open", "certainty": "confirmed", "title": "Crosswalk links distinct taxon concepts",
            "description": "Version-scoped archaeal species versus bacterial E.coli strain mismatch; this finding does not invalidate the individual IDs or propose a replacement ID.",
            "target_ids": [OCCURRENCE], "evidence_ids": claim_eids, "ownership_note": ownership}],
        "actions": [{"action_id": "trace-crosswalk", "description": "Request owner review of original-version source field and crosswalk emission; preserve exact occurrence and seek evidence before proposing any identifier correction.",
            "finding_ids": ["crosswalk-mismatch"], "target_ids": [OCCURRENCE], "ownership_note": ownership,
            "acceptance_checks": ["Establish original-generation lineage and field semantics", "Independently review retained endpoint meanings and relation applicability", "Do not invent a corrected ID or edit frozen source bytes"]}],
        "limitations": [LINEAGE, LIMIT, "No current authority refresh or historical snapshot reconstruction. Retrieval and update dates remain distinct.",
            "Generic packet measurement_context remains unresolved; experimental measurements, units and conditions are inapplicable to this structural claim.",
            "Draft validation is transport/provenance validation, not scientific approval, canonical persistence or exact-runtime admission.",
            "Biolink OrganismTaxon semantic applicability does not certify LPSN prefix-policy conformance; no original-generating-model version recovered."],
        "notes": ["Production scientific coverage0; A/B and cutoff null; all694 candidates retained; historical census outerFAILED1/childUNKNOWN unchanged.",
                  "Complete private authority contexts retained; only bounded literal excerpts used as proof quotes."]}
    paths = [p for p in output.rglob("*") if p.is_file()]
    paths += [ROOT / p for p in code_paths]
    paths.append(args.acceptance / "ACCEPTANCE.json")
    review["source"]["inputs"] = [{**relative_pin(p), "role": "Exact private draft/source/runtime input"}
                                      for p in sorted(set(paths))]
    validate_limits(review, sidecar)
    save_json(output / "review.json", review)
    save(output / "review.yaml", serialize_draft(review))
    validate_review(review)
    native = validate_occurrence_review(ROOT, review, packet_pin["path"], str((output / "proofs.json").relative_to(ROOT)))
    require(load_document(read(output / "review.yaml")) == review, "YAML readback differs")
    save(output / "review.md", render_markdown(review).encode())
    privacy = scan_public_draft(read(output / "review.yaml"), read(output / "review.md"), binding)
    save_json(output / "public-privacy-scan.json", privacy)
    validate_occurrence_review(ROOT, json.loads(read(output / "review.json")),
                               packet_pin["path"], str((output / "proofs.json").relative_to(ROOT)))
    after = verify_preservation(args.acceptance, changes)
    require(before == after, "Preservation state changed")
    for item in input_manifest:
        require(pin(Path(item["original"]["path"])) == item["original"], "Retained original changed")
    result = {"status": "VALIDATED_DRAFT_ONLY_AWAITING_INDEPENDENT_ADMISSIBILITY_REVIEW",
        "recorded_at_utc": utc(), "original_packet_validation": original_replay,
        "new_packet_validation": validate_packet(packet, root=ROOT), "native_validation": native,
        "canonical_schema": pin(SCHEMA_PATH), "contracts": contracts, "quotes": literal_replay, "private_identity_binding": pin(output / "identity-binding.json"), "private_expected_binding": pin(output / "expected-native.json"), "coordinator_change_binding": pin(output / "coordinator-changes.json"), "public_privacy_scan": pin(output / "public-privacy-scan.json"),
        "quote_budget": budget, "preservation": after, "canonical_save_attempts": 0,
        "provider_requests": 0, "scientific_production_coverage": 0, "A_count": None, "B_count": None,
        "baseline_cutoff": None, "all694_retained": True, "historical_census": {"outer": "FAILED1", "child": "UNKNOWN"},
        "artifacts": [pin(p) for p in sorted(output.rglob("*")) if p.is_file()]}
    return save_json(output / "draft-receipt.json", result)


def command(args):
    output = reserve(args.output)
    save(output / "producer.py.original", read(Path(__file__)))
    env = os.environ.copy()
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT / "src"),
                "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"})
    for key, leaf in {"TMPDIR": "tmp", "XDG_CACHE_HOME": "cache", "UV_CACHE_DIR": "uv-cache",
                      "RUFF_CACHE_DIR": "ruff-cache"}.items():
        target = checked(output / leaf, absent=True)
        target.mkdir(mode=0o700)
        env[key] = str(target)
    argv = args.command[1:] if args.command[:1] == ["--"] else args.command
    require(bool(argv), "Explicit command required")
    started = utc()
    result = subprocess.run(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                            capture_output=True, timeout=1800, check=False)
    save(output / "stdout", result.stdout)
    save(output / "stderr", result.stderr)
    receipt = save_json(output / "receipt.json", {"started_at_utc": started, "finished_at_utc": utc(),
        "argv": argv, "cwd": str(ROOT), "exit_code": result.returncode,
        "producer": pin(output / "producer.py.original"), "stdout": pin(output / "stdout"), "stderr": pin(output / "stderr")})
    return receipt, result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    acceptance = commands.add_parser("accept")
    acceptance.add_argument("--history", type=Path, required=True)
    acceptance.add_argument("--original-root", type=Path, required=True)
    draft = commands.add_parser("draft")
    draft.add_argument("--acceptance", type=Path, required=True)
    draft.add_argument("--expected-binding", type=Path, required=True)
    draft.add_argument("--coordinator-changes", type=Path, required=True)
    draft.add_argument("--retained-root", type=Path, required=True)
    draft.add_argument("--authority", type=Path, action="append", default=[])
    runner = commands.add_parser("run")
    runner.add_argument("command", nargs=argparse.REMAINDER)
    for sub in (acceptance, draft, runner):
        sub.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    require(Path.cwd() == ROOT, "Explicit science-checkout cwd required")
    checked(args.output, absent=True)
    try:
        if args.action == "accept":
            result, code = accept(args), 0
        elif args.action == "draft":
            result, code = prepare(args), 0
        else:
            result, code = command(args)
    except Exception as exc:
        import traceback
        if args.output.exists() and not (args.output / "failure.json").exists():
            save_json(args.output / "failure.json", {"recorded_at_utc": utc(),
                "exception": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(),
                "producer": pin(Path(__file__)), "canonical_save_attempts": 0})
        raise
    print(json.dumps(result))
    return code


def serialize_draft(review):
    """Use the pinned canonical serializer/strict loader without persistence."""
    from kg_microbe_governance.artifacts.scripts.record_review import _dump_document, load_document
    raw = _dump_document(review).encode()
    require(load_document(raw) == review, "Canonical YAML serialization readback differs")
    return raw


def check_identity(acceptance, binding):
    require(set(binding) == {"expected_thread_id", "expected_model", "expected_effort", "canonical_reviewer", "native_history"}, "Private identity binding fields differ")
    require(all(isinstance(value, str) and value.strip() for value in binding.values()), "Empty private identity binding")
    require(binding["canonical_reviewer"] == "edgemech-native-reviewer-01", "Unstable canonical pseudonym")
    native = acceptance["native_session"]
    require(native["session_meta"]["payload"]["id"] == binding["expected_thread_id"], "Unexpected native thread")
    context = native["turn_context"]["payload"]
    require(context["model"] == binding["expected_model"] == "gpt-6-astra"
            and context["effort"] == binding["expected_effort"] == "ultra", "Unexpected native model/effort")
    require(git("rev-parse", "HEAD").decode().strip() == "5d470683823323e2dd8d72e08c49ade138229dc6", "Science base changed")
    require(git("branch", "--show-current").decode().strip() == "campaign/lbnl-occurrence-preparation-20261128", "Science branch changed")


def approved_changes(manifest):
    import re
    require(set(manifest) == {"format", "changes"} and manifest["format"] == "first32-authorized-disjoint-change/v1", "Unexpected coordinator change manifest")
    require(isinstance(manifest["changes"], list) and len(manifest["changes"]) == 1, "Exactly one named coordinator change required")
    change = manifest["changes"][0]
    require(set(change) == {"path", "before_sha256", "after_sha256", "reviewed_intermediate_sha256", "finding"}, "Coordinator change fields differ")
    require(change["path"] == "scripts/adhoc/dispatch_restart_preparation_task_20261128.sh", "Change outside coordinator dispatch path")
    for key in ("before_sha256", "after_sha256", "reviewed_intermediate_sha256"):
        require(isinstance(change[key], str) and re.fullmatch(r"[a-f0-9]{64}", change[key]), "Invalid coordinator digest")
    finding = change["finding"]
    require(set(finding) == {"path", "sha256"} and pin(Path(finding["path"]))["sha256"] == finding["sha256"], "Coordinator finding pin mismatch")
    return {change["path"]: change}


def verify_preservation(acceptance_dir, changes):
    allowed = approved_changes(changes)
    results, seen = [], set()
    for name in ("original-checkout-state.json", "science-checkout-state.json"):
        prior = json.loads(read(acceptance_dir / name))
        unchanged = 0
        for item in prior["tracked"]:
            current = pin(Path(item["path"]))
            relative = Path(item["path"]).relative_to(Path(prior["root"])).as_posix()
            if name == "science-checkout-state.json" and relative in allowed:
                change = allowed[relative]
                require(item["sha256"] == change["before_sha256"] and current["sha256"] == change["after_sha256"], "Unapproved coordinator before/after digest")
                results.append({"classification": "AUTHORIZED_DISJOINT_COORDINATOR_CHANGE",
                    "path": relative, "before": item, "after": current, "authorization": change})
                seen.add(relative)
            else:
                require(current == item, "Preexisting tracked bytes changed: " + item["path"])
                unchanged += 1
        require(git("rev-parse", "HEAD", root=Path(prior["root"])).decode().strip() == prior["head"], "Preexisting head changed")
        results.append({"root": prior["root"], "head": prior["head"], "tracked_files_unchanged": unchanged,
                        "whole_tree_unchanged_claimed": name == "original-checkout-state.json"})
    require(seen == set(allowed), "Authorized coordinator change not observed")
    return results


def scan_public_draft(yaml_bytes, markdown_bytes, binding):
    import re

    from kg_microbe_reviews import load_document
    review = load_document(yaml_bytes)
    require(review["reviewer"]["identity"] == "edgemech-native-reviewer-01", "Canonical operational identity is forbidden")
    patterns = [re.escape(binding["expected_thread_id"]), r"/Users/", r"/private/", r"/dev/tty", r"tmux-[0-9]",
                r"(?im)^\s*(?:thread_id|session_id|pid|ppid|parent_pid|cwd|tty|pane|socket)\s*:"]
    for raw in (yaml_bytes, markdown_bytes):
        text = raw.decode()
        require(not any(re.search(pattern, text) for pattern in patterns), "Prospective public operational binding found")
    for item in review["source"]["inputs"]:
        path = Path(item["path"])
        require(not path.is_absolute() and ".." not in path.parts, "Public input path is not relative")
    return {"status": "passed", "scope": "Complete prospective YAML and Markdown including source inputs",
            "canonical_pseudonym": review["reviewer"]["identity"], "yaml_sha256": digest(yaml_bytes),
            "markdown_sha256": digest(markdown_bytes), "private_expected_thread_sha256": digest(binding["expected_thread_id"].encode()),
            "limitations": "Local artifact privacy scan, not public release or scientific approval"}


if __name__ == "__main__":
    raise SystemExit(main())
