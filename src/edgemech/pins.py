"""Verify installed canonical contract bytes against the reviewed package pin."""

import hashlib
import json
from importlib.resources import files


def check_contracts() -> dict:
    pins = json.loads(files("edgemech").joinpath("contract-pins.json").read_text())
    package = files(pins["package"])
    for path, digest in pins["files"].items():
        if hashlib.sha256(package.joinpath(path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Installed canonical contract differs from reviewed pin: {path}")
    return {"verified": True, "claw_commit": pins["commit"], "files": len(pins["files"])}
