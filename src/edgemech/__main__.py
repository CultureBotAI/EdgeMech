"""Small JSON CLI for immutable external artifacts and inherited candidate packets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check-contracts", help="Verify installed canonical contract bytes")
    migrate = sub.add_parser("migrate-sqlite", help="Verify and migrate one frozen SQLite ledger")
    migrate.add_argument("--ledger", type=Path, required=True)
    migrate.add_argument("--export", type=Path, required=True)
    migrate.add_argument("--store", type=Path, required=True)
    migrate.add_argument("--buckets", type=int, default=16)
    migrate.add_argument("--row-group-size", type=int, default=8192)
    for command in ("verify", "stats", "lookup"):
        operation = sub.add_parser(command)
        operation.add_argument("manifest", type=Path)
        if command == "lookup":
            operation.add_argument("occurrence_id")
    census = sub.add_parser("census", help="Verify and account for a pinned source population")
    census.add_argument("--snapshot", type=Path, required=True)
    census.add_argument("--source-sha256", required=True)
    census.add_argument("--native-export", type=Path, action="append", required=True)
    census.add_argument("--native-sha256", action="append", required=True)
    census.add_argument("--output", type=Path, required=True)
    census.add_argument("--limit", type=int)
    census.add_argument("--workers", type=int, choices=range(1, 5), default=1)
    verify_census = sub.add_parser("verify-census")
    verify_census.add_argument("manifest", type=Path)
    verify_census.add_argument("--workers", type=int, choices=range(1, 5), default=1)
    args = parser.parse_args()
    from edgemech import storage

    if args.command == "check-contracts":
        from edgemech.pins import check_contracts
        result = check_contracts()
    elif args.command == "census":
        from edgemech.census import run_census
        result = {"manifest": str(run_census(
            args.snapshot, args.native_export, args.output, args.source_sha256, args.limit,
            expected_native_manifest_sha256=args.native_sha256,
            workers=args.workers,
        ))}
    elif args.command == "verify-census":
        from edgemech.census import verify_census
        result = verify_census(args.manifest, workers=args.workers)
    elif args.command == "migrate-sqlite":
        result = {"manifest": str(storage.migrate_sqlite(
            args.ledger, args.export, args.store,
            buckets=args.buckets, row_group_size=args.row_group_size,
        ))}
    elif args.command == "lookup":
        result = storage.lookup(args.manifest, args.occurrence_id)
    else:
        result = getattr(storage, args.command)(args.manifest)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
