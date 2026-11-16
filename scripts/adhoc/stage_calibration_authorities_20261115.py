#!/usr/bin/env python3
"""2026-11-15: retain two pinned authorities for the ten-case calibration PR.

Inputs: unchanged TraitMech METPO and Biolink snapshots, pinned below.
Outputs: private raw copies and replayable receipts under EdgeMech .temp/.
This is evidence preparation, not authority adjudication or a scientific score.
Run --plan, stage/check metpo as the canary, then stage/check biolink separately.
No network, graph mutation, batch mode, or overwrite is supported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).absolute().parents[2]
HELPER = Path(__file__).absolute()
DESTINATION = ROOT / ".temp/edge-calibration-authorities-20261115"
SOURCE_ROOT = Path("/Users/marcin/Documents/VIMSS/ontology/Mechs/TraitMech/data/raw")
PROFILE = "edgemech-calibration-authority-staging/v1"
AUTHORITIES = {
    "metpo": {
        "file": "metpo.owl",
        "version": "2026-06-12",
        "reference": "https://w3id.org/metpo/releases/2026-06-12/metpo.owl",
        "sha256": "8b6f8fe0510a698579e532658c8ace05da2550093365df9ca83feb0741778415",
    },
    "biolink": {
        "file": "biolink-model.yaml",
        "version": "4.4.0",
        "reference": "https://w3id.org/biolink/vocab/",
        "sha256": "4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb",
    },
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def no_symlinks(path):
    for part in (path, *path.parents):
        require(not part.is_symlink(), f"Symlink is not permitted: {part}")


def read_regular(path):
    no_symlinks(path)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), f"Not a regular file: {path}")
        return stream.read()


def verify_authority(name, raw):
    expected = AUTHORITIES[name]
    require(digest(raw) == expected["sha256"], f"Authority hash mismatch: {name}")
    if name == "metpo":
        namespaces = {"owl": "http://www.w3.org/2002/07/owl#"}
        ontology = ET.fromstring(raw).find("owl:Ontology", namespaces)
        require(ontology is not None, "METPO ontology metadata is absent")
        versions = ontology.findall("owl:versionInfo", namespaces)
        iris = ontology.findall("owl:versionIRI", namespaces)
        require(len(versions) == len(iris) == 1, "METPO version metadata is ambiguous")
        require(versions[0].text == expected["version"], "METPO version differs")
        require(iris[0].get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource")
                == expected["reference"], "METPO version IRI differs")
    else:
        # Exact pinned bytes use one unquoted top-level version and id. Do not
        # introduce a generalized YAML interpretation for these fixed inputs.
        lines = raw.decode("utf-8").splitlines()
        require([line for line in lines if line.startswith("version:")]
                == ["version: " + expected["version"]], "Biolink version differs")
        require([line for line in lines if line.startswith("id:")]
                == ["id: " + expected["reference"]], "Biolink identity differs")


def source(name):
    raw = read_regular(SOURCE_ROOT / AUTHORITIES[name]["file"])
    verify_authority(name, raw)
    return raw


def private_directory(path, *, create=False):
    no_symlinks(path)
    if create and not path.exists():
        path.mkdir(mode=0o700)
    info = path.stat()
    require(stat.S_ISDIR(info.st_mode), f"Not a directory: {path}")
    require(stat.S_IMODE(info.st_mode) == 0o700, f"Directory must have mode 0700: {path}")


def write_new(path, raw):
    no_symlinks(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    require(read_regular(path) == raw, f"Persisted bytes differ: {path}")


def expected_receipt(name, raw, canary):
    authority = AUTHORITIES[name]
    return {
        "profile": PROFILE,
        "authority": name,
        "source_path": str(SOURCE_ROOT / authority["file"]),
        "staged_path": str((DESTINATION / name / authority["file"]).relative_to(ROOT)),
        "source_sha256": authority["sha256"],
        "staged_sha256": digest(raw),
        "bytes": len(raw),
        "version": authority["version"],
        "reference": authority["reference"],
        "helper_sha256": digest(read_regular(HELPER)),
        "verified_canary": canary,
        "status": "copied_and_replayed",
        "scientific_assessment": "not_performed",
        "limitation": "Pinning proves byte identity and version, not semantic fitness for an edge.",
    }


def check(name):
    private_directory(ROOT / ".temp")
    private_directory(DESTINATION)
    directory = DESTINATION / name
    private_directory(directory)
    raw = source(name)
    copy = read_regular(directory / AUTHORITIES[name]["file"])
    verify_authority(name, copy)
    require(copy == raw, f"Source and retained authority differ: {name}")
    canary = None
    if name == "biolink":
        check("metpo")
        canary = digest(read_regular(DESTINATION / "metpo/receipt.json"))
    receipt = json.loads(read_regular(directory / "receipt.json"))
    timestamp = receipt.pop("staged_at")
    require(isinstance(timestamp, str) and timestamp.endswith("+00:00"), "Invalid receipt time")
    datetime.fromisoformat(timestamp)
    require(receipt == expected_receipt(name, raw, canary), "Receipt or helper identity differs")
    return {"authority": name, "status": "replay_passed", "sha256": digest(copy)}


def stage(name):
    raw = source(name)
    canary = None
    if name == "biolink":
        check("metpo")
        canary = digest(read_regular(DESTINATION / "metpo/receipt.json"))
    private_directory(ROOT / ".temp", create=True)
    private_directory(DESTINATION, create=True)
    directory = DESTINATION / name
    no_symlinks(directory)
    directory.mkdir(mode=0o700)  # Exclusive unit: a partial attempt cannot be overwritten.
    private_directory(directory)
    write_new(directory / AUTHORITIES[name]["file"], raw)
    require(source(name) == raw, "Authority source changed while staging")
    receipt = expected_receipt(name, raw, canary)
    receipt["staged_at"] = datetime.now(timezone.utc).isoformat()
    write_new(directory / "receipt.json", (json.dumps(receipt, indent=2) + "\n").encode())
    return check(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", action="store_true")
    action.add_argument("--stage", choices=AUTHORITIES)
    action.add_argument("--check", choices=AUTHORITIES)
    args = parser.parse_args()
    if args.plan:
        result = {"status": "plan_only", "authorities": [
            {"authority": name, **authority, "source_path": str(SOURCE_ROOT / authority["file"]),
             "bytes": len(source(name)), "status": "source_hash_and_version_verified",
             "planned_directory": str((DESTINATION / name).relative_to(ROOT))}
            for name, authority in AUTHORITIES.items()
        ], "sequence": ["stage metpo", "check metpo", "stage biolink", "check biolink"]}
    else:
        result = stage(args.stage) if args.stage else check(args.check)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
