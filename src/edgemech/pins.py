"""Verify installed canonical contract bytes against the reviewed package pin."""

import hashlib
import json
from importlib.resources import files


def check_contracts() -> dict:
    pins = json.loads(files("edgemech").joinpath("contract-pins.json").read_text())
    if pins.get("format") != "edgemech-contract-pins/v2":
        raise ValueError("Unsupported contract pin format")
    count = 0
    for name, checksums in pins["packages"].items():
        package = files(name)
        for path, digest in checksums.items():
            if hashlib.sha256(package.joinpath(path).read_bytes()).hexdigest() != digest:
                raise ValueError(f"Installed canonical contract differs from reviewed pin: {name}/{path}")
            count += 1
    return {"verified": True, "claw_commit": pins["commit"], "files": count}
