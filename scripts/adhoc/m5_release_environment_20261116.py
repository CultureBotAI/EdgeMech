#!/usr/bin/env python3
"""Inventory and install the M5 KG lock from its read-only Poetry artifact cache.

Provenance: the November 16 release worker has a fresh Python 3.10 KG venv,
but online Poetry installation failed DNS. This helper selects main/dev lock
records using the TARGET interpreter's markers and wheel tags. Published
wheels must match poetry.lock SHA256. A locally built cached wheel is accepted
only with an explicit flag, a hash-matched co-located locked source archive,
and a separately recorded wheel hash; co-location is not a build attestation.
Run --plan first. Installation uses only the recorded local wheel paths,
--no-index, --no-deps and --require-hashes, followed by pip check.

The planner needs Python 3.11+ with packaging, independently of the target
Python 3.10-3.12 environment. It neither downloads nor edits the shared cache.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from packaging.markers import Marker
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name, parse_wheel_filename


def sha256(path: Path) -> str:
    """Hash bytes without loading large wheels at once."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def target_runtime(python: Path) -> dict:
    """Ask the target's pip-vendored packaging for its actual platform."""
    program = (
        "import json,sys; from pip._vendor.packaging.markers import default_environment; "
        "from pip._vendor.packaging.tags import sys_tags; "
        "print(json.dumps({'executable':sys.executable,'version':sys.version,"
        "'markers':default_environment(),'tags':[str(t) for t in sys_tags()]}))"
    )
    result = subprocess.run([str(python), "-c", program], check=True, capture_output=True, text=True)
    runtime = json.loads(result.stdout)
    version = runtime["markers"]["python_version"]
    if version not in {"3.10", "3.11", "3.12"}:
        raise ValueError(f"Unsupported KG target Python: {version}")
    runtime["resolved_executable"] = str(python.resolve())
    runtime["executable_sha256"] = sha256(python.resolve())
    return runtime


def selected(package: dict, groups: set[str], environment: dict) -> bool:
    """Respect per-group lock markers as well as Python version constraints."""
    active_groups = set(package["groups"]) & groups
    if not active_groups:
        return False
    constraint = package.get("python-versions", "*")
    if constraint != "*" and not SpecifierSet(constraint).contains(environment["python_full_version"]):
        return False
    markers = package.get("markers")
    if isinstance(markers, dict):
        return any(group not in markers or Marker(markers[group]).evaluate(environment) for group in active_groups)
    return not markers or Marker(markers).evaluate(environment)


def write_json(path: Path, value: dict) -> None:
    """Keep each new record exclusive rather than overwriting old receipts."""
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def plan(args: argparse.Namespace) -> int:
    """Inventory compatible cache bytes without installing anything."""
    args.output.mkdir(parents=True, exist_ok=False)
    runtime = target_runtime(args.python)
    lock_path = args.kg_root / "poetry.lock"
    lock = tomllib.loads(lock_path.read_text())
    groups = set(args.groups.split(","))
    packages = [p for p in lock["package"] if selected(p, groups, runtime["markers"])]
    cache_files = sorted(path for path in args.cache.rglob("*") if path.is_file())
    wheel_index: dict[tuple[str, str], list[Path]] = {}
    for path in cache_files:
        if path.suffix != ".whl":
            continue
        name, version, _, tags = parse_wheel_filename(path.name)
        if set(map(str, tags)) & set(runtime["tags"]):
            wheel_index.setdefault((canonicalize_name(name), str(version)), []).append(path)
    records = []
    missing = []
    for package in packages:
        name, version = package["name"], package["version"]
        locked_files = {entry["file"]: entry["hash"].removeprefix("sha256:") for entry in package["files"]}
        candidates = wheel_index.get((canonicalize_name(name), version), [])
        choices = []
        for path in candidates:
            digest = sha256(path)
            record = {"name": name, "version": version, "path": str(path), "sha256": digest}
            if locked_files.get(path.name) == digest:
                record["status"] = "lock_matched_wheel"
                choices.append(record)
                continue
            sources = []
            for source_name, source_digest in locked_files.items():
                source = path.parent / source_name
                if source.suffix != ".whl" and source.is_file() and sha256(source) == source_digest:
                    sources.append({"path": str(source), "sha256": source_digest})
            if sources and args.allow_cached_built_wheels:
                record.update(status="cached_built_wheel", locked_sources=sources,
                              provenance_limit="Co-located pinned source; cached build not independently attested.")
                choices.append(record)
        if choices:
            choices.sort(key=lambda record: (record["status"] != "lock_matched_wheel", record["path"]))
            records.append(choices[0])
        else:
            missing.append({"name": name, "version": version, "compatible_cached_wheels": list(map(str, candidates)),
                            "locked_filenames": list(locked_files)})
    names = [canonicalize_name(record["name"]) for record in records]
    if len(names) != len(set(names)):
        raise ValueError("Multiple selected lock versions for a package; refuse ambiguous installation")
    requirements = "".join(f"{Path(r['path']).as_uri()} --hash=sha256:{r['sha256']}\n" for r in records)
    requirements_path = args.output / "requirements.txt"
    with requirements_path.open("x") as handle:
        handle.write(requirements)
    inventory = {
        "created_at": datetime.now(timezone.utc).isoformat(), "mode": "offline_inventory",
        "planner_python": sys.version, "target": runtime, "groups": sorted(groups),
        "kg_root": str(args.kg_root), "lock_path": str(lock_path), "lock_sha256": sha256(lock_path),
        "helper_sha256": sha256(Path(__file__)), "cache": str(args.cache),
        "cache_files_enumerated": len(cache_files), "selected_lock_packages": len(packages),
        "requirements_sha256": sha256(requirements_path), "packages": records, "missing": missing,
        "allow_cached_built_wheels": args.allow_cached_built_wheels,
    }
    write_json(args.output / "inventory.json", inventory)
    print(json.dumps({"output": str(args.output), "selected": len(packages), "available": len(records),
                      "cached_built": [r["name"] for r in records if r["status"] == "cached_built_wheel"],
                      "missing": [{"name": p["name"], "version": p["version"]} for p in missing]}, indent=2))
    return 2 if missing else 0


def install(args: argparse.Namespace) -> int:
    """Install only a complete, unchanged, previously inspected inventory."""
    inventory_path = args.output / "inventory.json"
    inventory = json.loads(inventory_path.read_text())
    if inventory["missing"]:
        raise ValueError("Inventory incomplete; installation is blocked")
    runtime = target_runtime(args.python)
    if runtime != inventory["target"]:
        raise ValueError("Target interpreter changed after planning")
    if sha256(Path(inventory["lock_path"])) != inventory["lock_sha256"]:
        raise ValueError("Lock changed after planning")
    requirements = args.output / "requirements.txt"
    if sha256(requirements) != inventory["requirements_sha256"]:
        raise ValueError("Requirements changed after planning")
    for record in inventory["packages"]:
        if sha256(Path(record["path"])) != record["sha256"]:
            raise ValueError(f"Wheel changed after planning: {record['name']}")
        for source in record.get("locked_sources", []):
            if sha256(Path(source["path"])) != source["sha256"]:
                raise ValueError(f"Locked source changed: {record['name']}")
    scratch = args.output / "pip-scratch"
    scratch.mkdir(exist_ok=False)
    environment = dict(os.environ, TMPDIR=str(scratch))
    command = [str(args.python), "-m", "pip", "--isolated", "--disable-pip-version-check", "install",
               "--no-index", "--no-cache-dir", "--no-deps", "--require-hashes", "-r", str(requirements)]
    with (args.output / "install.log").open("x") as log:
        process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=environment)
    check = subprocess.run([str(args.python), "-m", "pip", "--isolated", "check"], capture_output=True, text=True)
    installed = subprocess.run([str(args.python), "-m", "pip", "--isolated", "list", "--format=json"],
                               check=True, capture_output=True, text=True)
    receipt = {"completed_at": datetime.now(timezone.utc).isoformat(), "command": command,
               "inventory_sha256": sha256(inventory_path), "returncode": process.returncode,
               "pip_check_returncode": check.returncode, "pip_check": check.stdout + check.stderr,
               "installed": json.loads(installed.stdout), "install_log_sha256": sha256(args.output / "install.log")}
    write_json(args.output / "install-receipt.json", receipt)
    print(json.dumps({key: value for key, value in receipt.items() if key != "installed"}, indent=2))
    return process.returncode or check.returncode


def main() -> int:
    """Keep planning and mutation explicit and separate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kg-root", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--groups", default="main,dev")
    parser.add_argument("--allow-cached-built-wheels", action="store_true")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--install", action="store_true")
    args = parser.parse_args()
    for name in ("kg_root", "python", "cache", "output"):
        setattr(args, name, getattr(args, name).absolute())
    return plan(args) if args.plan else install(args)


if __name__ == "__main__":
    raise SystemExit(main())
