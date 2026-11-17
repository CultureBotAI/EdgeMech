#!/usr/bin/env python3
"""Whole-bundle quote accounting and quote-free public derivatives for M5 rounds.

Runs canonical proof replay before inventory. Groups verified publication aliases
across every reviewer/case, deduplicates whitespace-equivalent excerpts, preserves
private originals, and only accepts exact regenerated public projection bytes.
Unknown files, symlinks, post-gate prose changes, incomplete batch coverage and
unreplayable metadata fail closed. Preparation itself does not publish or approve.

Round config also requires package_sha256 and reviewers keyed reviewer-a/b, each
with root, sealed matrix path and exact canonical_identity. Matrix receipts bind
the expected actual model/session and initial per-case categories.
Nondefault rounds additionally bind original-clone scientific manifests/seals and
a separately frozen publication runtime with its own valid production receipt.
The legacy v1 schema identifier is retained; outputs state the actual round and
both package identities. Valid authored verdicts never imply scientific approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
sys.dont_write_bytecode = True

from kg_microbe_governance.artifacts.scripts.record_review import (  # noqa: E402
    REPORT_ROOT,
    repository_identity,
)
from kg_microbe_reviews import load_document, read_review  # noqa: E402

from edgemech.literature_cache import LiteratureCache, verify_quote  # noqa: E402
from edgemech.occurrence_packet import validate_packet  # noqa: E402
from edgemech.occurrence_review import (  # noqa: E402
    CATEGORIES,
    _europepmc_abstract,
    _jats,
    validate_occurrence_review,
)
from edgemech.storage.parquet import safe_path  # noqa: E402

SCHEMA = "edgemech-round02-publication-gate/v1"
LEGACY_ROUND = "m5-calibration-20261116-round02"
ROUND_HELPER = "scripts/adhoc/calibration_round_20261116.py"
INITIAL_HELPER = "scripts/adhoc/seal_m5_round03_initial_20261116.py"
PUBLICATION_HELPER = "scripts/adhoc/gate_round02_publication_20261116.py"
COHORT = "artifacts/edge-calibration-20261115/cohort.json"
OCCURRENCE_HELPER = "src/edgemech/occurrence_review.py"
_VERIFICATION_DIRECTORY = None


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def text_hash(value):
    return digest(str(value).encode())


def read_pin(root, relative):
    path = Path(relative)
    require(not path.is_absolute() and ".." not in path.parts, "Input must be root relative")
    raw = safe_path(root / path).read_bytes()
    return raw, {"path": str(path), "sha256": digest(raw)}


def declared_pin(root, pin):
    require(isinstance(pin, dict) and set(pin) == {"path", "sha256"},
            "Expected an explicit root-relative path/hash pin")
    raw, actual = read_pin(root, pin["path"])
    require(actual == pin, "Declared artifact changed: " + pin["path"])
    return raw


def selected_round(config):
    round_id = config.get("round_id", LEGACY_ROUND)
    require(isinstance(round_id, str) and re.fullmatch(r"[A-Za-z0-9_.:-]+", round_id),
            "Round ID must be an explicit identifier")
    return round_id


def repository_binding(root, expected_head):
    require(root.resolve() == root, "Repository root must be canonical")
    identity = repository_identity(root)
    require(identity.casefold() == "culturebotai/edgemech", "Publication repository is not EdgeMech")
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    require(head == expected_head, "Repository HEAD differs from declared runtime")
    require(not subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
        text=True).strip(), "Tracked runtime changes must be committed")
    origin = subprocess.check_output(
        ["git", "-C", str(root), "remote", "get-url", "origin"], text=True).strip()
    return {"git_head": head, "repository_identity": identity, "repository_origin": origin}


def write_private(path, raw):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def verification_journal(stage):
    """Persist verifier attempts privately, including failures before projection exists."""
    global _VERIFICATION_DIRECTORY
    require(".temp" in stage.parts, "Verification logs must remain private under .temp")
    directory = safe_path(stage / ("verification-" + uuid.uuid4().hex), exists=False)
    directory.mkdir(mode=0o700)
    previous = _VERIFICATION_DIRECTORY
    _VERIFICATION_DIRECTORY = directory
    try:
        yield directory
    finally:
        _VERIFICATION_DIRECTORY = previous


def frozen_command(root, manifest, relative, arguments, *, module=False):
    """Run the selected clone's maintained, pinned CLI; never import newer replacements."""
    files = {item["path"]: item["sha256"] for item in manifest["files"]}
    require(len(files) == len(manifest["files"]), "Repeated frozen file path")
    _, helper = read_pin(root, relative)
    require(files.get(relative) == helper["sha256"], "Original verifier is not frozen")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(root / "src")
    environment.pop("PYTHONHOME", None)
    require(_VERIFICATION_DIRECTORY is not None, "Private verifier journal is required")
    require(not module or relative == OCCURRENCE_HELPER, "Unknown original module invocation")
    command = ([sys.executable, "-B", "-m", "edgemech.occurrence_review", *arguments]
               if module else [sys.executable, "-B", str(root / relative), "--root", str(root), *arguments])
    attempt = safe_path(_VERIFICATION_DIRECTORY / ("attempt-" + uuid.uuid4().hex), exists=False)
    attempt.mkdir(mode=0o700)
    write_private(attempt / "command.json", encoded({"command": command, "cwd": str(root),
                                                    "helper": helper, "scope": "private diagnostics"}))
    try:
        completed = subprocess.run(command, cwd=root, env=environment, capture_output=True)
    except Exception as error:
        write_private(attempt / "failure.json", encoded({"error_type": type(error).__name__,
                                                        "message": str(error)}))
        raise
    write_private(attempt / "stdout.log", completed.stdout)
    write_private(attempt / "stderr.log", completed.stderr)
    receipt = {"helper": helper, "exit_code": completed.returncode,
               "stdout_sha256": digest(completed.stdout), "stderr_sha256": digest(completed.stderr)}
    write_private(attempt / "result.json", encoded(receipt))
    require(completed.returncode == 0, "Frozen verifier failed; private diagnostics retained: " + str(attempt))
    return json.loads(completed.stdout), receipt


def package_binding(root, declaration, round_id, package_sha256):
    """Verify immutable scientific inputs where their original runtime still exists."""
    repository = repository_binding(root, declaration["git_head"])
    raw = declared_pin(root, declaration["manifest"])
    manifest = json.loads(raw)
    require(digest(raw) == package_sha256 and manifest["round_id"] == round_id,
            "Scientific round/package differs from declared manifest")
    # The package verifier imports the original clone's source. Its shared installed
    # contracts must remain the same immutable dependency selection as this process.
    require((root / "uv.lock").read_bytes() == (ROOT / "uv.lock").read_bytes(),
            "Original scientific replay requires the same immutable dependency lock")
    require((root / COHORT).read_bytes() == (ROOT / COHORT).read_bytes(),
            "Original scientific cohort differs")
    result, receipt = frozen_command(
        root, manifest, ROUND_HELPER, ["verify", "--manifest", declaration["manifest"]["path"]])
    require(result.get("manifest_sha256") == package_sha256
            and result.get("input_hashes_verified") == len(manifest["files"])
            and len(result.get("packet_replay", [])) == 10,
            "Original package replay is incomplete")
    return manifest, {"manifest": declaration["manifest"], **repository, "verification": receipt}


def publication_runtime(config):
    """A new publication runtime gets its own package and same-path production receipt."""
    if selected_round(config) == LEGACY_ROUND and "publication_runtime" not in config:
        return None
    import run_m5_review_worker_20261116 as worker

    declaration = config["publication_runtime"]
    repository = repository_binding(ROOT, declaration["git_head"])
    raw = declared_pin(ROOT, declaration["manifest"])
    manifest = json.loads(raw)
    require(manifest["round_id"] == declaration["runtime_id"]
            and declaration["runtime_id"] != selected_round(config)
            and digest(raw) != config["package_sha256"],
            "Publication runtime/package must have a distinct identity from science")
    files = {item["path"]: item["sha256"] for item in manifest["files"]}
    require(len(files) == len(manifest["files"]), "Repeated publication runtime pin")
    for item in worker.execution_inventory(ROOT):
        require(files.get(item["path"]) == item["sha256"],
                "Unpinned current execution file: " + item["path"])
    require(files.get(PUBLICATION_HELPER) == digest(Path(__file__).read_bytes()),
            "Publication helper must be explicitly frozen")
    verified, package_check = frozen_command(
        ROOT, manifest, ROUND_HELPER, ["verify", "--manifest", declaration["manifest"]["path"]])
    require(verified.get("manifest_sha256") == digest(raw)
            and verified.get("input_hashes_verified") == len(manifest["files"])
            and len(verified.get("packet_replay", [])) == 10, "Publication package replay incomplete")
    parent = json.loads(declared_pin(ROOT, declaration["production_receipt"]))
    environment = worker.child_environment(ROOT)
    codex = Path(parent["codex_path"])
    bindings = {"git_head": repository["git_head"], "helper_sha256": worker.digest(worker.HELPER),
                "codex_path": str(codex), "codex_sha256": worker.digest(codex),
                **worker.runtime_bindings(ROOT, environment), **worker.repository_bindings(ROOT)}
    # This compares current host/Python/distributions/environment/origin/code and
    # actually rechecks the new canonical save pair, with the NEW package binding.
    worker.verify_receipt(ROOT / declaration["production_receipt"]["path"], bindings,
                          ROOT, environment, reviewer_package=declaration["manifest"]["path"])
    return {"runtime_id": declaration["runtime_id"], "manifest": declaration["manifest"],
            **repository, "package_verification": package_check,
            "production_receipt": declaration["production_receipt"],
            "runtime_bindings": bindings}


def initial_binding(root, item, matrix_pin, receipt, manifest, package):
    declaration = item["scientific"]
    seal_pin = declaration["initial_seal"]
    seal = json.loads(declared_pin(root, seal_pin))
    require(seal["manifest"] == declaration["manifest"]["path"]
            and seal["matrix"] == matrix_pin and receipt.get("initial_seal") == seal_pin
            and seal["canonical_identity"] == item["canonical_identity"],
            "Original initial seal differs from publication reviewer binding")
    checked, command = frozen_command(
        root, manifest, INITIAL_HELPER, ["check", "--seal", seal_pin["path"]])
    require(checked.get("status") == "passed" and checked.get("cases") == 10
            and checked.get("authored_axes") == 60 and checked.get("seal") == seal_pin
            and checked.get("matrix") == matrix_pin, "Complete original initial seal replay failed")
    entries = {entry["case_id"]: entry for entry in seal["validations"]}
    require(len(entries) == len(seal["validations"]) == 10, "Incomplete initial authored identities")
    return {"package": package, "initial_seal": seal_pin, "initial_check": command}, entries


def canonical_pair(root, review, spec, manifest):
    expected = f"{REPORT_ROOT}/{review['review_id']}/review.yaml"
    require(spec["review"] == expected, "Canonical publication requires the deterministic saved YAML path")
    persisted = read_review(root, expected)
    require(persisted == review, "Canonical shared readback differs from selected document")
    markdown = str(Path(expected).with_name("review.md"))
    before = {"review": read_pin(root, expected)[1], "markdown": read_pin(root, markdown)[1]}
    result, command = frozen_command(root, manifest, OCCURRENCE_HELPER, [
        "check", "--root", str(root), "--review", expected,
        "--packet", spec["packet"], "--proofs", spec["proofs"]], module=True)
    require(result.get("occurrence_id") == review["targets"][0]["target_id"],
            "Original canonical check returned another occurrence")
    require(read_review(root, expected) == persisted, "Canonical pair changed during actual check")
    require(before == {"review": read_pin(root, expected)[1], "markdown": read_pin(root, markdown)[1]},
            "Canonical pair bytes changed during actual check")
    return {**before,
            "canonical_command": command, "authored_values_checked": True,
            "scope": "Existing canonical pair read/check only; no new save or scientific approval"}


def canary_context(config):
    """The canary binds the exact pending full batch without a receipt hash cycle."""
    base_pin = config["batch_config"]
    base = json.loads(declared_pin(ROOT, base_pin))
    require(base.get("mode") == "round" and "derivative_canary" not in base,
            "Canary requires an immutable full batch proposal without its later receipt")
    coverage(base)
    for key in ("round_id", "package_sha256", "publication_runtime", "preparer"):
        require(config.get(key) == base.get(key), "Derivative canary batch context changed: " + key)
    require(isinstance(config.get("preparer"), str) and config["preparer"].strip(),
            "Actual publication preparer identity required")
    require(config.get("source_mode", "canonical_review") == "canonical_review"
            and base.get("source_mode", "canonical_review") == "canonical_review",
            "Round03 derivatives require actual canonical pairs")
    specs = config["reviews"]
    require(len(specs) == 1 and specs[0]["reviewer"] == "operational-canary"
            and specs[0]["case_id"] == "fresh-47", "Derivative canary must be the operational fresh47 unit")
    selected_root = str(Path(config["scientific"]["root"]).absolute())
    matches = [item for item in base["reviewers"].values()
               if str(Path(item["root"]).absolute()) == selected_root]
    require(len(matches) == 1 and str(Path(specs[0]["root"]).absolute()) == selected_root,
            "Derivative canary must use exactly one original A/B clone")
    for key in ("git_head", "manifest"):
        require(config["scientific"][key] == matches[0]["scientific"][key],
                "Derivative canary uses another original scientific runtime/package")
    return base


def check_stage(config, stage):
    files, gate = derive(config)
    pins = inspect_candidate(stage / "proposed-public", files)
    receipt = json.loads(safe_path(stage / "receipt.json").read_bytes())
    require(receipt["config_sha256"] == digest(encoded(config))
            and receipt["helper_sha256"] == digest(Path(__file__).read_bytes())
            and receipt["public_file_pins"] == pins and receipt["gate"] == gate
            and receipt["published"] is False, "Publication receipt changed or runtime differs")
    return {"passed": gate["passed"], "public_file_pins": pins, "published": False}


def derivative_canary(config):
    declaration = config["derivative_canary"]
    canary = json.loads(declared_pin(ROOT, declaration["config"]))
    require(canary.get("mode") == "canary", "Expected an actual bounded derivative canary")
    base = canary_context(canary)
    require(base == {key: value for key, value in config.items() if key != "derivative_canary"},
            "Derivative canary does not bind the exact current full batch")
    stage_relative = Path(declaration["stage"])
    require(not stage_relative.is_absolute() and stage_relative.parts
            and stage_relative.parts[0] == ".temp" and ".." not in stage_relative.parts,
            "Derivative canary stage must remain private")
    stage = safe_path(ROOT / stage_relative)
    require(declaration["receipt"]["path"] == str(stage_relative / "receipt.json"),
            "Derivative canary receipt belongs to another stage")
    declared_pin(ROOT, declaration["receipt"])
    checked = check_stage(canary, stage)  # Actual pair replay plus exact regeneration of all three files.
    require(checked["passed"] and len(checked["public_file_pins"]) == 3,
            "Complete bounded derivative canary failed")
    inspected = json.loads(declared_pin(ROOT, declaration["inspection"]))
    require(isinstance(inspected.get("reviewer"), str) and inspected["reviewer"].strip()
            and inspected["reviewer"].strip() != config["preparer"].strip()
            and inspected.get("all_files_inspected") is True
            and inspected.get("canonical_pair_inspected") is True
            and inspected.get("config") == declaration["config"]
            and inspected.get("receipt") == declaration["receipt"]
            and inspected.get("public_file_pins") == checked["public_file_pins"],
            "Independent inspection must bind the exact actual canary files and pair")
    # Recheck private pins after potentially long literal/source replay.
    for key in ("config", "receipt", "inspection"):
        declared_pin(ROOT, declaration[key])
    return {key: declaration[key] for key in ("config", "receipt", "inspection")} | {
        "stage": str(stage_relative), "public_file_pins": checked["public_file_pins"],
        "scope": "Actual inspected derivative canary replay; not scientific approval"}


def add_quote(groups, aliases, quote, origin):
    """Union metadata-verified aliases, including transitive DOI/PMID/PMCID bridges."""
    aliases = set(aliases)
    require(bool(aliases), "Quote lacks verified source identity")
    quote = " ".join(quote.split())
    require(bool(quote), "Empty quoted excerpt")
    joined = [g for g in groups if g["aliases"] & aliases]
    quotes = {quote: [origin]}
    for group in joined:
        aliases |= group["aliases"]
        for prior, locations in group["quotes"].items():
            quotes.setdefault(prior, []).extend(locations)
        groups.remove(group)
    # Earlier groups can become connected by aliases collected from a later one.
    while True:
        joined = [g for g in groups if g["aliases"] & aliases]
        if not joined:
            break
        for group in joined:
            aliases |= group["aliases"]
            for prior, locations in group["quotes"].items():
                quotes.setdefault(prior, []).extend(locations)
            groups.remove(group)
    groups.append({"aliases": aliases, "quotes": quotes})


def public_aliases(aliases):
    """Authority version prose is private; publication identifiers remain usable."""
    return sorted("authority-sha256:" + text_hash(a) if a.startswith("authority:") else a
                  for a in aliases)


def quote_inventory(groups):
    result = []
    for group in groups:
        excerpts = [{"quote_sha256": text_hash(q), "words": len(q.split()),
                     "occurrences": sorted(locations, key=lambda x: json.dumps(x, sort_keys=True))}
                    for q, locations in group["quotes"].items()]
        words = sum(item["words"] for item in excerpts)
        result.append({"source_identities": public_aliases(group["aliases"]),
                       "deduplicated_quote_words": words, "maximum_words": 25,
                       "within_budget": words <= 25,
                       "excerpts": sorted(excerpts, key=lambda x: x["quote_sha256"])})
    return sorted(result, key=lambda x: x["source_identities"])


def coverage(config):
    require(config["mode"] in {"canary", "round"}, "Unknown publication mode")
    specs = config["reviews"]
    require(isinstance(specs, list), "Reviews must be a list")
    keys = [(s["reviewer"], s["case_id"]) for s in specs]
    require(len(keys) == len(set(keys)), "Repeated reviewer/case")
    cohort = json.loads((ROOT / "artifacts/edge-calibration-20261115/cohort.json").read_text())
    expected = {case["case_id"] for case in cohort["cases"]}
    require(all(cid in expected for _, cid in keys), "Unknown original cohort case")
    if config["mode"] == "round":
        require(set(keys) == {(r, c) for r in ("reviewer-a", "reviewer-b") for c in expected},
                "Round publication requires both reviewers and all ten cases")
    else:
        require(len(specs) == 1 and keys[0][0] == "operational-canary",
                "Canary must contain one operational unit, excluded from scoring")
    canonical_pairs = [(str(Path(spec["root"]).resolve()),
                        str((Path(spec["root"]) / spec["review"]).resolve())) for spec in specs]
    require(len(canonical_pairs) == len(set(canonical_pairs)),
            "Repeated canonical root/review pair across reviewer/case labels")
    return cohort


def reviewer_bindings(config):
    if config["mode"] == "canary":
        return {}
    declared = config.get("reviewers", {})
    require(set(declared) == {"reviewer-a", "reviewer-b"},
            "Round requires expected reviewer bindings from sealed matrices")
    bindings = {}
    round_id = selected_round(config)
    for rid, item in declared.items():
        root = safe_path(Path(item["root"]).absolute())
        manifest, package = None, None
        if round_id != LEGACY_ROUND:
            manifest, package = package_binding(
                root, item["scientific"], round_id, config["package_sha256"])
        raw, pin = read_pin(root, item["matrix"])
        receipt_raw, receipt_pin = read_pin(root, item["matrix"] + ".receipt.json")
        matrix, receipt = json.loads(raw), json.loads(receipt_raw)
        reviewer = matrix["reviewer"]
        require(receipt["matrix_path"] == item["matrix"] and
                receipt["matrix_sha256"] == pin["sha256"] and
                receipt["reviewer"] == reviewer and
                receipt["package_sha256"] == matrix["package_sha256"] == config["package_sha256"],
                "Sealed reviewer matrix/receipt/package binding differs")
        require(matrix["round_id"] == round_id and
                reviewer["id"] == rid and reviewer.get("session_id") and
                reviewer.get("model") not in {None, "", "unknown", "configured_default"},
                "Expected actual reviewer identity/model/session unavailable")
        require(all(isinstance(reviewer[key], str) and
                    re.fullmatch(r"[A-Za-z0-9_.:-]+", reviewer[key])
                    for key in ("model", "session_id")), "Actual reviewer metadata must be identifiers")
        require(item.get("canonical_identity"), "Expected canonical reviewer identity missing")
        cases = {case["case_id"]: case for case in matrix["cases"]}
        require(len(cases) == len(matrix["cases"]), "Repeated sealed matrix case")
        bindings[rid] = {"root": str(root.resolve()), "reviewer": reviewer,
                         "canonical_identity": item["canonical_identity"], "cases": cases,
                         "matrix": pin, "matrix_receipt": receipt_pin}
        if round_id != LEGACY_ROUND:
            scientific, entries = initial_binding(
                root, item, pin, receipt, manifest, package)
            require(set(entries) == set(cases), "Initial seal and matrix cases differ")
            bindings[rid].update(scientific=scientific, initial_entries=entries,
                                 proof_identity_field="reviewer")
    require(len({b["reviewer"]["session_id"] for b in bindings.values()}) == 2 and
            len({b["canonical_identity"] for b in bindings.values()}) == 2,
            "The two reviewer labels must bind distinct sessions and canonical identities")
    return bindings


def bind_review(spec, review, proofs, replay, bindings, seen_ids):
    require(review["review_id"] not in seen_ids, "Repeated canonical review_id")
    seen_ids.add(review["review_id"])
    if not bindings:
        return
    bound = bindings[spec["reviewer"]]
    require(str(Path(spec["root"]).resolve()) == bound["root"], "Review root differs from reviewer binding")
    require(review["reviewer"]["identity"] == bound["canonical_identity"] and
            review["reviewer"].get("model") == bound["reviewer"]["model"],
            "Canonical reviewer identity/model differs from sealed reviewer binding")
    field = bound.get("proof_identity_field", "identity")
    if field == "reviewer" or field in proofs:
        require(isinstance(proofs.get(field), dict)
                and all(proofs[field].get(key) == bound["reviewer"][key]
                    for key in ("id", "model", "session_id")),
                "Proof session identity differs from sealed reviewer binding")
    if field == "reviewer" and "identity" in proofs:
        require(isinstance(proofs["identity"], dict)
                and all(proofs["identity"].get(key) == bound["reviewer"][key]
                        for key in ("id", "model", "session_id")),
                "Conflicting legacy/current proof session identity")
    if "initial_entries" in bound:
        root = Path(bound["root"])
        entry = bound["initial_entries"][spec["case_id"]]
        require(review == load_document(declared_pin(root, entry["review"])),
                "Published authored values differ from complete initial review")
        require(read_pin(root, spec["proofs"])[1] == entry["proofs"]
                and read_pin(root, spec["packet"])[1] == entry["packet"],
                "Published proof or packet differs from initial evidence")
    initial = bound["cases"][spec["case_id"]]
    initial_axes = {a["axis"]: a["category"] for a in initial["assessments"]}
    require(initial["occurrence_id"] == replay["occurrence_id"] and
            len(initial["assessments"]) == 6 and set(initial_axes) == set(CATEGORIES) and
            initial_axes == replay["assessments"],
            "Canonical case/categories differ from the sealed initial matrix")



def quotation_catalog(root, review, proofs):
    """Replay quotation bytes/metadata even when a draft's semantic validation fails.

    This only establishes literal source accounting. It neither changes support
    roles nor treats a source report as independent scientific support.
    """
    evidence = {item["evidence_id"]: item for item in review["evidence"]}
    require(len(evidence) == len(review["evidence"]), "Repeated evidence identity")
    proof_ids = [p["evidence_id"] for p in proofs["proofs"]]
    require(len(proof_ids) == len(set(proof_ids)) and set(proof_ids) == set(evidence),
            "Quotation inventory requires every cited/provided proof exactly once")
    inputs = {item["path"]: item["sha256"] for item in review["source"]["inputs"]}
    result = []
    for proof in proofs["proofs"]:
        item = evidence[proof["evidence_id"]]
        if proof["kind"] == "packet":
            require(not item.get("quote"), "Packet proof cannot conceal a quotation")
            continue
        raw, pin = read_pin(root, proof["input"]["path"])
        require(inputs.get(pin["path"]) == pin["sha256"] == proof["input"]["sha256"] ==
                item["snapshot_sha256"], "Quoted source bytes are not exactly bound")
        require(item["reference"] == proof["reference"], "Quotation reference differs")
        if proof["kind"] == "europepmc_abstract":
            text, aliases = _europepmc_abstract(raw, proof)
            kind = "abstract"
        elif proof["kind"] == "jats":
            text, aliases = _jats(raw, proof)
            kind = "oa_fulltext"
        else:
            require(proof["kind"] == "authority" and proof.get("version"), "Unknown quoted source")
            text, kind = raw.decode("utf-8"), "authority_text"
            aliases = {"authority:" + proof["reference"] + "#" + proof["version"],
                       "authority-raw-sha256:" + digest(raw)}
        document = LiteratureCache._document({"response_sha256": digest(raw)}, kind, text)
        quotation = verify_quote(document, item.get("quote"))
        require(all(proof.get(key) == quotation[key] for key in ("text_sha256", "start", "end", "extractor")),
                "Quotation offsets or extractor differ")
        require(f"chars {quotation['start']}:{quotation['end']}" in item["locator"],
                "Quotation locator does not bind verified offsets")
        quote = " ".join(quotation["quote"].split())
        result.append({"quote": quote, "aliases": aliases, "sha256": text_hash(quote),
                       "evidence_id": item["evidence_id"], "raw_sha256": digest(raw)})
    return result



def bind_original_inputs(root, review, proofs, packet, spec, original_occurrence):
    """Bind original bytes and occurrence even if semantic input validation fails."""
    inputs = {item["path"]: item["sha256"] for item in review["source"]["inputs"]}
    require(len(inputs) == len(review["source"]["inputs"]), "Duplicate authored source input")
    for path, expected in inputs.items():
        _, actual = read_pin(root, path)
        require(actual["sha256"] == expected, "Authored source input changed")
    for path in (spec["packet"], spec["proofs"]):
        _, actual = read_pin(root, path)
        require(inputs.get(path) == actual["sha256"], "Packet/proof sidecar is not bound to authored input")
    require(packet["occurrence_id"] == proofs["occurrence_id"] == original_occurrence,
            "Packet/proof occurrence differs from original cohort")
    require(len(review["targets"]) == 1, "Exactly one original occurrence target required")
    target = review["targets"][0]
    require(target["target_id"] == original_occurrence and target["path"] == spec["packet"] and
            target.get("selector") == "occurrence_id=" + original_occurrence,
            "Authored target path/selector differs from original packet occurrence")
    validate_packet(packet, root=root)


def review_replay(root, review, proofs, spec, source_mode):
    require(source_mode in {"canonical_review", "authored_input"}, "Unknown publication source mode")
    try:
        result = validate_occurrence_review(root, review, spec["packet"], spec["proofs"])
        return result, {"status": "passed", "scope": "Production input validation; not persistence"}
    except Exception as error:
        if source_mode != "authored_input":
            raise
        axes = {}
        for assessment in review["assessments"]:
            dims = {d["name"]: d["value"] for d in assessment["dimensions"]}
            require(dims["axis"] not in axes, "Duplicate authored assessment axis")
            axes[dims["axis"]] = dims["category"]
        require(len(review["targets"]) == 1, "Draft requires one original occurrence target")
        return {"occurrence_id": review["targets"][0]["target_id"], "assessments": axes}, {
            "status": "failed", "scope": "Original authored input; failure preserved without correction",
            "error_type": type(error).__name__, "error_sha256": text_hash(str(error))}


def derive(config):
    cohort = coverage(config)
    runtime = publication_runtime(config)
    round_id = selected_round(config)
    canary_science = None
    if round_id != LEGACY_ROUND and config["mode"] == "canary":
        canary_context(config)
        declared = config["scientific"]
        root = safe_path(Path(declared["root"]).absolute())
        require(all(str(Path(spec["root"]).absolute()) == str(root) for spec in config["reviews"]),
                "Operational derivative must use its original scientific clone")
        canary_manifest, canary_science = package_binding(
            root, declared, round_id, config["package_sha256"])
        cases = {case["case_id"]: case for case in canary_manifest["cases"]}
        for spec in config["reviews"]:
            require(spec["packet"] == cases[spec["case_id"]]["packet_path"],
                    "Operational derivative packet differs from frozen science")
    identities = {"round_id": round_id, "scientific_package_sha256": config.get("package_sha256"),
                  "publication_runtime": runtime}
    source_mode = config.get("source_mode", "canonical_review")
    checked_canary = None
    if round_id != LEGACY_ROUND:
        require(source_mode == "canonical_review", "Round03 derivatives require actual canonical pairs")
        if config["mode"] == "round":
            checked_canary = derivative_canary(config)
    originals = {case["case_id"]: case["occurrence_id"] for case in cohort["cases"]}
    groups, files, sources = [], {}, []
    bindings, seen_ids = reviewer_bindings(config), set()
    for spec in sorted(config["reviews"], key=lambda s: (s["reviewer"], s["case_id"])):
        root = safe_path(Path(spec["root"]).absolute())
        review_raw, review_pin = read_pin(root, spec["review"])
        proof_raw, proof_pin = read_pin(root, spec["proofs"])
        packet_raw, packet_pin = read_pin(root, spec["packet"])
        review, proofs, packet = load_document(review_raw), json.loads(proof_raw), json.loads(packet_raw)
        bind_original_inputs(root, review, proofs, packet, spec, originals[spec["case_id"]])
        canonical = None
        if round_id != LEGACY_ROUND:
            declaration = (config["scientific"] if config["mode"] == "canary"
                           else config["reviewers"][spec["reviewer"]]["scientific"])
            original_manifest = json.loads(declared_pin(root, declaration["manifest"]))
            canonical = canonical_pair(root, review, spec, original_manifest)
        replay, validation = review_replay(root, review, proofs, spec, source_mode)
        require(replay["occurrence_id"] == originals[spec["case_id"]], "Wrong original occurrence")
        bind_review(spec, review, proofs, replay, bindings, seen_ids)
        evidence_index = []
        for quotation in quotation_catalog(root, review, proofs):
            origin = {"reviewer": spec["reviewer"], "case_id": spec["case_id"],
                      "evidence_id_sha256": text_hash(quotation["evidence_id"])}
            add_quote(groups, quotation["aliases"], quotation["quote"], origin)
            evidence_index.append({"source_identities": public_aliases(quotation["aliases"]),
                                   "quote_sha256": quotation["sha256"],
                                   "raw_sha256": quotation["raw_sha256"]})
        assessments = []
        for assessment in review["assessments"]:
            dims = {d["name"]: d["value"] for d in assessment["dimensions"]}
            axis, category = dims["axis"], dims["category"]
            require(axis in CATEGORIES and category in CATEGORIES[axis], "Unrecognized categories")
            assessments.append({"axis": axis, "category": category,
                                "scope_sha256": text_hash(dims["scope"]),
                                "authored_assessment_sha256": digest(encoded(assessment))})
        require(review["completion"] in {"partial", "completed", "blocked", "aborted"},
                "Unknown completion status")
        require(review["verdict"] in {"pass", "pass_with_notes", "needs_curation", "blocked", "fail",
                                     "not_assessed"},
                "Unknown aggregate verdict")
        source = {"reviewer": spec["reviewer"], "case_id": spec["case_id"],
                  "review": review_pin, "proofs": proof_pin, "packet": packet_pin}
        sources.append(source)
        projection = {"schema": SCHEMA, **identities, "mode": config["mode"], "reviewer": spec["reviewer"],
                      "case_id": spec["case_id"], "occurrence_id": packet["occurrence_id"],
                      "assessments": sorted(assessments, key=lambda a: a["axis"]),
                      "completion": review["completion"], "verdict": review["verdict"],
                      "private_inputs": source, "source_mode": source_mode,
                      "production_input_validation": validation,
                      "canonical_persistence_asserted": canonical is not None,
                      "canonical_pair": canonical,
                      "source_evidence": evidence_index, "quotation_words": 0,
                      "canonical_review": False, "kg_admissions": 0,
                      "calibration_rating": config["mode"] == "round"}
        files[f"{spec['reviewer']}-{spec['case_id']}.json"] = encoded(projection)
    inventory = quote_inventory(groups)
    inventory_document = {"schema": SCHEMA, **identities, "coverage": {"mode": config["mode"],
                          "reviews": len(sources), "expected": 20 if config["mode"] == "round" else 1},
                          "scope": "All evidence excerpts in every specified private review or authored draft; "
                          "public derivative files contain hashes and categorical fields only.",
                          "private_source_inventory": inventory,
                          "private_originals_within_budget": all(g["within_budget"] for g in inventory),
                          "private_originals_modified": False,
                          "public_derivative_quote_words": 0}
    files["quote-inventory.json"] = encoded(inventory_document)
    gate = {"schema": SCHEMA, **identities, "mode": config["mode"], "passed": True,
            "public_quotes": "zero_by_exact_schema_projection",
            "self_file": "publication-gate.json",
            "self_hash_location": "private receipt.json public_file_pins",
            "all_proposed_public_files": [{"path": name, "sha256": digest(raw)}
                                          for name, raw in sorted(files.items())],
            "source_coverage": sources, "private_originals_published": False, "source_mode": source_mode,
            "sealed_reviewer_bindings": {rid: {
                "reviewer": {key: bound["reviewer"][key] for key in ("id", "model", "session_id")},
                "matrix": bound["matrix"], "matrix_receipt": bound["matrix_receipt"],
                "scientific": bound.get("scientific")}
                for rid, bound in bindings.items()},
            "operational_scientific_package": canary_science,
            "verified_derivative_canary": checked_canary,
            "private_originals_within_budget": inventory_document["private_originals_within_budget"],
            "private_over_budget_source_count": sum(not g["within_budget"] for g in inventory),
            "scope": "Publication quotation gate only; no scientific or calibration approval."}
    # Gate itself is generated from enumerations, paths, hashes and verified IDs.
    files["publication-gate.json"] = encoded(gate)
    return files, gate


def inspect_candidate(destination, expected):
    require(destination.is_dir() and not destination.is_symlink(), "Candidate directory invalid")
    entries = list(destination.rglob("*"))
    require(all(not path.is_symlink() for path in entries), "Candidate includes symlink")
    actual = {str(path.relative_to(destination)) for path in entries if path.is_file()}
    require(actual == set(expected), "Public file inventory incomplete or has unaccounted files")
    for name, raw in expected.items():
        require((destination / name).read_bytes() == raw,
                f"Proposed public bytes differ from quote-free projection: {name}")
    return [{"path": name, "sha256": digest(raw)} for name, raw in sorted(expected.items())]


def create(config, stage):
    require(not stage.exists(), "Publication stage must be new")
    stage.mkdir(mode=0o700, parents=True)
    try:
        with verification_journal(stage):
            files, gate = derive(config)
    except Exception as error:
        write_private(stage / "failure.json", encoded({"error_type": type(error).__name__,
            "message": str(error), "config_sha256": digest(encoded(config)),
            "helper_sha256": digest(Path(__file__).read_bytes()), "published": False}))
        raise
    public = stage / "proposed-public"
    public.mkdir(mode=0o700)
    for name, raw in files.items():
        with (public / name).open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    pins = inspect_candidate(public, files)
    receipt = {"schema": SCHEMA, "config_sha256": digest(encoded(config)),
               "helper_sha256": digest(Path(__file__).read_bytes()), "public_file_pins": pins,
               "gate": gate, "published": False}
    with (stage / "receipt.json").open("xb") as stream:
        stream.write(encoded(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "check"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(safe_path(args.config.absolute()).read_text())
    stage = safe_path(args.stage.absolute(), exists=args.action == "check")
    require(".temp" in stage.parts, "Stage must remain in private .temp until reviewed")
    if args.action == "prepare":
        result = create(config, stage)
    else:
        with verification_journal(stage):
            checked = check_stage(config, stage)
        result = {"passed": checked["passed"],
                  "public_files_verified": len(checked["public_file_pins"]), "published": False}
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
