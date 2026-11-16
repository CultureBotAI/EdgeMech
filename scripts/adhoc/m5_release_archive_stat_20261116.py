#!/usr/bin/env python3
"""Preserve exact archive stat integers after review found JS precision loss.

2026-11-16: this read-only observation supplements, never rewrites, the original
publication receipt. A nanosecond rounding difference is not a byte mutation.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ARCHIVE = Path(
    "/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe/"
    "data/merged/merged-kg.tar.gz"
)


def main():
    """Hash the preserved archive and serialize exact stat values directly in Python."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    before = ARCHIVE.stat()
    digest = hashlib.sha256()
    with ARCHIVE.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = ARCHIVE.stat()
    fields = ("st_size", "st_mtime_ns", "st_ctime_ns", "st_dev", "st_ino")
    assert all(getattr(before, key) == getattr(after, key) for key in fields)
    result = {
        "path": str(ARCHIVE), "sha256": digest.hexdigest(),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "stat": {key: getattr(after, key) for key in fields},
        "helper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "note": "Original publication stat lost 24ns in JS integer rounding; archive bytes match.",
        "published_release_verified": False,
    }
    assert result["sha256"] == "3d529dd0024843f9278ecfbfc8703413061ef9c4c7474805ecec03aa8cfdfd4c"
    with args.output.open("x") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    print(result["sha256"])


if __name__ == "__main__":
    main()
