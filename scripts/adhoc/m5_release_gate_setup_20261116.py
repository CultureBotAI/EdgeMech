#!/usr/bin/env python3
"""Prepare isolated offline KG PR gates from retained M5 package bytes.

Provenance: use the November 16 environment inventory for all KG lock wheels.
The two unpinned tox-only tools are reconstructed from the canonical checkout's
installed pure-Python distributions, verifying each retained file against its
installed RECORD. Reconstructed hashes are local artifact hashes, not claimed
PyPI wheel hashes. Original environments and caches are read-only.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    """Hash a local file without changing it."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def repack(source: Path, wheelhouse: Path) -> dict:
    """Reconstruct a pure-Python wheel from RECORD-verified installed files."""
    package = source.parent
    wheel_text = (source / "WHEEL").read_text()
    if "Root-Is-Purelib: true" not in wheel_text or "Tag: py3-none-any" not in wheel_text:
        raise ValueError(f"Unsupported retained tool wheel: {source.name}")
    stem = source.name.removesuffix(".dist-info")
    destination = wheelhouse / f"{stem}-py3-none-any.whl"
    retained = []
    excluded = []
    for relative, recorded_hash, size in csv.reader((source / "RECORD").read_text().splitlines()):
        path = Path(relative)
        if ".." in path.parts or path.suffix == ".pyc" or path.name in {"RECORD", "INSTALLER", "REQUESTED"}:
            excluded.append(relative)
            continue
        if path.is_absolute() or not recorded_hash.startswith("sha256="):
            raise ValueError(f"Unverifiable retained file: {relative}")
        resolved = (package / path).resolve()
        if not resolved.is_relative_to(package.resolve()):
            raise ValueError(f"Retained file escapes site-packages: {relative}")
        content = resolved.read_bytes()
        actual = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
        if recorded_hash != "sha256=" + actual or int(size) != len(content):
            raise ValueError(f"Installed RECORD mismatch: {relative}")
        retained.append((relative, content, recorded_hash))
    record_path = f"{source.name}/RECORD"
    record = io.StringIO(newline="")
    writer = csv.writer(record, lineterminator="\n")
    for name, content, hash_value in sorted(retained):
        writer.writerow([name, hash_value, len(content)])
    writer.writerow([record_path, "", ""])
    retained.append((record_path, record.getvalue().encode(), ""))
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as wheel:
        for name, content, _ in sorted(retained):
            member = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o644 << 16
            wheel.writestr(member, content)
    return {"path": str(destination), "sha256": digest(destination), "source_dist_info": str(source),
            "source_record_sha256": digest(source / "RECORD"), "verified_source_files": len(retained) - 1,
            "excluded_installer_files": excluded, "provenance": "Reconstructed from installed RECORD-verified files"}


def setup(args: argparse.Namespace) -> int:
    """Prepare an exclusive wheelhouse, environment record and read-only probes."""
    args.output.mkdir(parents=True, exist_ok=False)
    setup_root = args.kg_root / "data/validation/pr-gates/m5-setup"
    setup_root.mkdir(parents=True, exist_ok=False)
    wheelhouse = setup_root / "wheelhouse"
    wheelhouse.mkdir()
    inventory = json.loads(args.inventory.read_text())
    if inventory["missing"]:
        raise ValueError("KG lock inventory is incomplete")
    copied = []
    for item in inventory["packages"]:
        source = Path(item["path"])
        if digest(source) != item["sha256"]:
            raise ValueError(f"Cached wheel changed: {source.name}")
        destination = wheelhouse / source.name
        if destination.exists():
            raise FileExistsError(destination)
        shutil.copyfile(source, destination)
        if digest(destination) != item["sha256"]:
            raise ValueError(f"Copied wheel mismatch: {source.name}")
        copied.append({"path": str(destination), "sha256": item["sha256"], "source": str(source)})
    canonical = args.canonical_root / ".tox"
    repacked = [repack(canonical / "codespell/lib/python3.10/site-packages/codespell-2.4.3.dist-info", wheelhouse),
                repack(canonical / "docstr-coverage/lib/python3.10/site-packages/docstr_coverage-2.3.2.dist-info", wheelhouse)]
    constraints = setup_root / "constraints.txt"
    constraints.write_text("".join(f"{item['name']}=={item['version']}\n" for item in inventory["packages"])
                           + "codespell==2.4.3\ndocstr-coverage==2.3.2\n")
    # The final runner intentionally strips TOX* selectors. A private .tox link
    # keeps its standard unmodified command's physical output under data/.
    tox_link = args.kg_root / ".tox"
    if os.path.lexists(tox_link):
        raise FileExistsError(f"Preserve pre-existing tox output: {tox_link}")
    tox_output = setup_root / "tox"
    tox_output.mkdir()
    tox_link.symlink_to(tox_output, target_is_directory=True)
    for name in ("tmp", "pip-cache", "virtualenv", "poetry-cache", "xdg-cache", "matplotlib"):
        (setup_root / name).mkdir()
    environment = {
        "VIRTUAL_ENV": str(args.kg_root / ".venv310"),
        "PATH": str(args.kg_root / ".venv310/bin") + ":/opt/homebrew/bin:/usr/bin:/bin",
        "PIP_NO_INDEX": "1", "PIP_FIND_LINKS": str(wheelhouse), "PIP_CONSTRAINT": str(constraints),
        "PIP_CACHE_DIR": str(setup_root / "pip-cache"), "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "VIRTUALENV_OVERRIDE_APP_DATA": str(setup_root / "virtualenv"),
        "VIRTUALENV_NO_PERIODIC_UPDATE": "1", "VIRTUALENV_DOWNLOAD": "0",
        "POETRY_CACHE_DIR": str(setup_root / "poetry-cache"), "TMPDIR": str(setup_root / "tmp"),
        "XDG_CACHE_HOME": str(setup_root / "xdg-cache"), "MPLCONFIGDIR": str(setup_root / "matplotlib"),
    }
    unset = ["CONDA_DEFAULT_ENV", "CONDA_PREFIX", "PYTEST_ADDOPTS", "POETRY_VIRTUALENVS_IN_PROJECT"]
    effective = dict(os.environ)
    for key in list(effective):
        if key in unset or key.startswith("TOX"):
            effective.pop(key)
    effective.update(environment)
    with (args.output / "environment.json").open("x") as handle:
        json.dump({"set": environment, "unset": unset, "unset_prefixes": ["TOX"]}, handle, indent=2)
        handle.write("\n")
    commands = [
        ["poetry", "run", "python", "-c", "import sys; print(sys.version); print(sys.executable)"],
        ["poetry", "env", "info", "--path"],
        ["poetry", "run", "tox", "--version"],
        ["poetry", "run", "tox", "c", "-e", "codespell", "-k", "pass_env"],
        ["poetry", "run", "python", "scripts/run_pr_gates.py", "m5-final-pending", "--dry-run"],
    ]
    results = []
    for index, command in enumerate(commands):
        result = subprocess.run(command, cwd=args.kg_root, env=effective, capture_output=True, text=True)
        log = args.output / f"probe-{index + 1}.log"
        with log.open("x") as handle:
            handle.write(result.stdout + result.stderr)
        results.append({"command": command, "returncode": result.returncode, "log": str(log), "sha256": digest(log)})
    receipt = {"completed_at": datetime.now(timezone.utc).isoformat(), "helper_sha256": digest(Path(__file__)),
               "inventory_sha256": digest(args.inventory), "setup_root": str(setup_root),
               "copied_wheels": copied, "reconstructed_tool_wheels": repacked,
               "constraints_sha256": digest(constraints), "probes": results,
               "scope": "Environment preparation only; no source formatting or full test suite executed."}
    with (args.output / "setup-receipt.json").open("x") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"setup_root": str(setup_root), "copied_wheels": len(copied),
                      "reconstructed_tools": repacked, "probes": results}, indent=2))
    return int(any(result["returncode"] for result in results))


def main() -> int:
    """Parse explicit task-only setup paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("kg-root", "canonical-root", "inventory", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    return setup(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
