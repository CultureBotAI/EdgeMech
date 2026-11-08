# Compare source and persisted logical tables before migration publication

Final acceptance review for CultureBotAI/culturebotai-claw#951 at EdgeMech
`1b1837a79e25241b3bd3dfb850fe8baa9687f64c` found a missing production boundary.
`migrate_sqlite` replays and validates the source SQLite, writes Parquet tables,
then independently verifies the output's internal identities/history/projections.
It does not compare the source's complete logical table hashes and row counts
with the persisted tables before publishing `CURRENT`.

The existing round-trip test compares every field, but that check is not run by
the production migrator. A writer defect that changes `metadata.header` to a
different same-width header can remain internally consistent: output hashes
describe the changed metadata, and verification copies that retained metadata
into its replay baseline. This loses original source fields while retaining the
original SQLite and export file digests in the artifact.

Acceptance: within the read-only source transaction, compute independent
complete-field logical hashes and row counts for all five authoritative tables;
compare them against persisted Parquet readback before publication and retain
both sides in the migration receipt. An injected same-width-header corruption
must fail even when the altered output's physical/logical hashes are valid.
Preserve all earlier replay, source-ID, immutability and atomic-publication
guards. Prove the regression fails with this new comparison removed, then rerun
the real 1,000-row storage canary using an isolated worktree and new output.

The active full census and its frozen source checkout are outside this repair.
