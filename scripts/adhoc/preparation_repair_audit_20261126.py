#!/usr/bin/env python3
"""Retain later native producer sources and emit new offline repair audit records.

Purpose: issue228 provenance successor for the reviewed #236/#237/#238 repairs.
Inputs: explicit native history/cutoff, local command argv, tracked working bytes,
or existing repair logs. Outputs: exclusive private archives, build snapshots,
command receipts and review handoffs below
the owned repair tree. UTC date: 2026-11-26. Publication requires separate review.
This parameterized successor is NOT a historical execution or recovery replay.
Archived producer text is inert evidence; it is never imported or executed.
No old receipt is restamped, no canary runs, and no canonical pair is regenerated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from preparation_receipt_20261126 import ROOT, checked_path, directory, read_regular

WORK = ROOT / ".temp/preparation-repairs-236-238-20261126"
CALLS = {"custom_tool_call", "function_call"}
OUTPUTS = {"custom_tool_call_output", "function_call_output"}


def utc():
    return datetime.now(timezone.utc).isoformat()


def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() != timezone.utc.utcoffset(result):
        raise ValueError("Explicit UTC timestamp required")
    return result


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    raw = read_regular(path)
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": digest(raw)}


@contextmanager
def new_stream(path):
    path = checked_path(path, "file", base=WORK, absent=True)
    with directory(path.parent) as parent:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
        with os.fdopen(fd, "wb") as stream:
            yield stream
            stream.flush()
            os.fsync(stream.fileno())


def save(path, raw):
    with new_stream(path) as stream:
        stream.write(raw)
    if read_regular(path) != raw:
        raise ValueError("Audit readback differs")
    return pin(path)


def save_json(path, data):
    return save(path, (json.dumps(data, indent=2) + "\n").encode())


def reserve(path):
    path = checked_path(path, "directory", base=WORK, absent=True)
    with directory(path.parent, create=True) as parent:
        os.mkdir(path.name, mode=0o700, dir_fd=parent)
    return path


def select_history(path, after, until):
    """Capture exact complete native records; allow only explicit regular history input."""
    selected = []
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    fd = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("History must be a regular file")
        stream = os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise
    with stream:
        for number, raw in enumerate(stream, 1):
            if not raw.endswith(b"\n"):
                break  # The active native log may have an unfinished final record.
            item = json.loads(raw)
            if item.get("type") != "response_item":
                continue
            payload = item.get("payload", {})
            if payload.get("type") not in CALLS | OUTPUTS:
                continue
            if after < stamp(item["timestamp"]) <= until:
                selected.append((number, raw, item))
    return selected


def archive(history, after, output, until=None):
    boundary = utc() if until is None else until
    beginning, ending = stamp(after), stamp(boundary)
    if beginning >= ending:
        raise ValueError("Empty or reversed history interval")
    checked_path(output, "directory", base=WORK, absent=True)
    records = select_history(history, beginning, ending)
    output = reserve(output)
    raw_pin = save(output / "native-tool-records.jsonl", b"".join(r[1] for r in records))
    returned = {d["payload"].get("call_id") for _, _, d in records
                if d["payload"]["type"] in OUTPUTS}
    calls = []
    for number, raw, item in records:
        payload = item["payload"]
        if payload["type"] not in CALLS:
            continue
        source = payload.get("input", payload.get("arguments"))
        if not isinstance(source, str):
            raise ValueError("Unexpected native tool source representation")
        source_pin = save(output / f"producer-{len(calls):04d}.original.txt", source.encode())
        calls.append({"original_timestamp": item["timestamp"], "native_line": number,
                      "native_line_sha256": digest(raw), "tool": payload.get("name"),
                      "call_id": payload.get("call_id"), "source": source_pin,
                      "execution_evidence": "paired_native_output" if payload.get("call_id")
                      in returned else "output_not_in_snapshot"})
    return save_json(output / "manifest.json", {
        "classification": "PRIVATE_HISTORICAL_PRODUCER_SOURCE_ARCHIVE",
        "capture_at_utc": utc(), "after_exclusive": after, "until_inclusive": boundary,
        "history_path": str(history), "raw_records": raw_pin, "calls": calls,
        "source_record_count": len(records), "producer_call_count": len(calls),
        "capturing_successor": pin(Path(__file__)), "historical_executions_replayed": False,
        "limit": "Exact native input/argument text plus paired outputs when present; captured "
                 "calls are not approved replay programs or a reconstructed interpreter state.",
    })


def run(command, output):
    if not command:
        raise ValueError("Explicit nonempty local command required")
    checked_path(output, "directory", base=WORK, absent=True)
    caches = {"TMPDIR": "tmp", "PYTHONPYCACHEPREFIX": "pycache", "UV_CACHE_DIR": "uv-cache",
              "RUFF_CACHE_DIR": "ruff-cache", "XDG_CACHE_HOME": "cache"}
    for name in caches.values():
        checked_path(WORK / name, "directory", base=WORK)
    output = reserve(output)
    env = os.environ.copy()
    env.update({"UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"})
    for key, name in caches.items():
        with directory(WORK / name, create=True):
            pass
        env[key] = str(WORK / name)
    start, tick = utc(), time.monotonic()
    error = None
    with new_stream(output / "stdout") as stdout, new_stream(output / "stderr") as stderr:
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                    stdout=stdout, stderr=stderr, timeout=1800, check=False)
            code = result.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            code, error = None, f"{type(exc).__name__}: {exc}"
    receipt = save_json(output / "receipt.json", {
        "classification": "OFFLINE_ENGINEERING_REPAIR_COMMAND_NOT_CANARY",
        "started_at_utc": start, "finished_at_utc": utc(), "elapsed_seconds": time.monotonic()-tick,
        "command": command, "cwd": str(ROOT), "exit_code": code, "error": error,
        "producer": pin(Path(__file__)), "stdout": pin(output / "stdout"),
        "stderr": pin(output / "stderr"), "scientific_review_coverage": 0,
    })
    return code, receipt


def snapshot(output):
    """Copy current index-listed working bytes for an isolated offline build only."""
    checked_path(output, "directory", base=WORK, absent=True)
    listing = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    paths = [Path(os.fsdecode(name)) for name in listing.split(b"\0") if name]
    if len(paths) != len(set(paths)) or not paths:
        raise ValueError("Expected unique tracked file paths")
    originals = {}
    for path in paths:
        if path.is_absolute() or ".." in path.parts or path.parts[0] in {".git", ".temp"}:
            raise ValueError("Unsafe tracked build path")
        checked_path(ROOT / path, "file", base=ROOT, required=True)
        originals[path] = read_regular(ROOT / path)
    output = reserve(output)
    pins = []
    for path, raw in originals.items():
        destination = output / "source" / path
        with directory(destination.parent, create=True):
            pass
        pins.append(save(destination, raw))
    if any(read_regular(ROOT / path) != raw for path, raw in originals.items()):
        raise ValueError("Working inputs changed while copying build snapshot")
    return save_json(output / "manifest.json", {
        "classification": "PRIVATE_CURRENT_WORKING_BUILD_SNAPSHOT_NOT_SOURCE_RESTORATION",
        "producer": pin(Path(__file__)), "files": pins, "source_files": len(pins),
        "tracked_listing_sha256": digest(listing), "originals_unchanged": True,
        "limit": "Contains held canonical files; private build staging, not publication clearance"})


def handoff(output):
    """New private report only; existing canary and repair records are never replaced."""
    checked_path(output, "directory", base=WORK, absent=True)
    paths = [ROOT / p for p in (
        "scripts/adhoc/preparation_receipt_20261126.py",
        "scripts/adhoc/preparation_readback_20261126.py",
        "scripts/adhoc/preparation_public_projection_20261126.py",
        "scripts/adhoc/preparation_repair_audit_20261126.py",
        "scripts/adhoc/preparation_privacy_mutation_20261126.py",
        "tests/test_preparation_helpers_20261126.py",
        "tests/test_preparation_public_projection_20261126.py",
        "tests/test_preparation_repair_audit_20261126.py",
        "tests/test_preparation_privacy_mutation_20261126.py",
        "docs/validation/preparation-canary-20261126.md")]
    paths += sorted((ROOT / "artifacts/preparation-canary-20261126").glob("*.json"))
    paths += sorted((ROOT / "reviews/structured/20261126T031443Z-excluded-preparation-canary")
                    .glob("review.*"))
    paths += sorted((WORK / "commands").rglob("stdout"))
    paths += sorted((WORK / "commands").rglob("stderr"))
    paths += sorted((WORK / "commands").rglob("receipt.json"))
    paths += sorted((WORK / "commands").rglob("exit-code"))
    paths += sorted((WORK / "producer-archives").rglob("manifest.json"))
    paths += sorted((ROOT / ".temp/fulltext/preparation-repairs-236-238")
                    .glob("privacy-mutation-*/result.json"))
    paths += sorted((WORK / "build-snapshots").glob("*/manifest.json"))
    paths += sorted((WORK / "dist-final-02").glob("*"))
    for name in ("ACCEPTANCE.json", "preservation.sha256", "candidate-files.sha256",
                 "public-projection-mapping.json", "CANONICAL-WITHDRAWAL-PROPOSAL.md",
                 "canonical-withdrawal-NOT-APPLIED.patch", "proposed-working-tree.patch"):
        paths.append(WORK / name)
    pins = [pin(path) for path in paths]
    outcomes = []
    for receipt_path in sorted((WORK / "commands").rglob("receipt.json")):
        receipt = json.loads(read_regular(receipt_path))
        outcomes.append({"attempt": str(receipt_path.parent.relative_to(WORK)),
                         "exit_code": receipt["exit_code"], "receipt": pin(receipt_path)})
    test_lines = {}
    for path in sorted((WORK / "commands").rglob("stdout")):
        matches = re.findall(r"^.*\b(?:passed|failed|errors)\b.* in [0-9.]+s.*$",
                             read_regular(path).decode(errors="replace"), re.M)
        if matches:
            test_lines[str(path.parent.relative_to(WORK))] = matches[-1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result = {"classification": "BOUNDED_ENGINEERING_REPAIR_NOT_A_SECOND_CANARY",
              "status": "PREPARED_FOR_INDEPENDENT_REVIEW_PUBLICATION_HELD", "recorded_at_utc": utc(),
              "head": head, "scientific_review_coverage": 0, "occurrence": None,
              "A_count": None, "B_count": None, "baseline_cutoff": None, "A_B_attempt": False,
              "new_provider_requests": 0, "new_agents": 0, "new_actual_canary_runs": 0,
              "new_canonical_saves": 0, "producer": pin(Path(__file__)), "artifacts": pins,
              "command_outcomes": outcomes, "test_summaries": test_lines,
              "canonical_pair": "Exact tracked pair unchanged; private copies preserved; removal NOT applied",
              "holds": ["Independent final helper/source/privacy review",
                        "Separate reviewed owner disposition of canonical append-only/publication conflict",
                        "No final commit/push/PR or exact-head publication until those decisions"],
              "historical_producers": "Private native-source archives; original timestamps/bytes, no replay or restamping",
              "scope_limit": "Helpers guard their own I/O endpoints; explicit child commands remain trusted, not sandboxed."}
    output = reserve(output)
    report = ["# Offline preparation repairs: review handoff", "",
              "Prepared for independent review; publication remains held. This is not a second canary.",
              "Scientific coverage0; occurrence/A/B counts/cutoff null; no A/B attempt.", "",
              "## Repairs", "",
              "- #236: traversal/resolved containment and symlink/nonregular endpoint preflight; descriptor-relative no-follow/exclusive I/O.",
              "- #237: strict MCP error/envelope/text/paper/metadata types; every present structuredContent is validated and must agree, including falsey values.",
              "- #238: fixed allowlisted public digest/status projections; original operational records preserved privately and in history.",
              "- Issue228: further producers use this tracked parameterized successor; historical tool input sources are retained separately and never rerun or restamped.",
              "", "## Validation and pre-fix evidence", ""]
    report += [f"- `{name}`: {line}" for name, line in test_lines.items()]
    report += ["", "Full command receipts, exact source/evidence hashes and current HEAD are in completion.json.",
               "Pre-fix suites run original preserved helper bytes in fresh pytest processes on synthetic copies; all test fixtures are under durable fulltext staging. No actual retained library/canonical evidence is exercised by the regressions.",
               "", "## Publication and canonical-pair hold", "",
               "The two tracked canonical files remain byte-identical. See CANONICAL-WITHDRAWAL-PROPOSAL.md and the separate NOT-APPLIED patch in the repair root. The append-only checker/base is unchanged; its conflict requires a separate reviewed owner disposition.",
               "The current tree is NOT cleared for publication: the held pair still contains prior operational bindings. No final commit, push, PR, history erasure, provider/canary/canonical-save/source/census rerun or merge is performed by this repair handoff.",
               "Census attribution, PR233, full A/B freeze, W5/W6, issue220, identity/lineage, correction/resource and supported fulltext/native-proof gates remain unchanged.",
               "", "## Candidate source hashes", ""]
    report += [f"- `{p['path']}`: `{p['sha256']}`" for p in pins
               if p["path"].startswith(("scripts/adhoc/", "tests/"))]
    save_json(output / "completion.json", result)
    save(output / "REPORT.md", ("\n".join(report) + "\n").encode())
    return save_json(output / "readback.json", {"producer": pin(Path(__file__)),
                     "report": pin(output / "REPORT.md"), "completion": pin(output / "completion.json")})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    archival = commands.add_parser("archive")
    archival.add_argument("--history", type=Path, required=True)
    archival.add_argument("--after", required=True)
    archival.add_argument("--until")
    archival.add_argument("--output", type=Path, required=True)
    runner = commands.add_parser("run")
    runner.add_argument("--output", type=Path, required=True)
    runner.add_argument("command", nargs=argparse.REMAINDER)
    reporter = commands.add_parser("handoff")
    reporter.add_argument("--output", type=Path, required=True)
    copier = commands.add_parser("snapshot")
    copier.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    if args.action == "archive":
        receipt = archive(args.history, args.after, args.output, args.until)
    elif args.action == "run":
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        code, receipt = run(command, args.output)
        print(json.dumps(receipt))
        return code if code is not None and 0 <= code <= 255 else 1
    elif args.action == "snapshot":
        receipt = snapshot(args.output)
    else:
        receipt = handoff(args.output)
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
