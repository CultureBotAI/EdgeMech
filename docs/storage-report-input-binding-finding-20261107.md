# Bind migration reports to the pinned source SQLite

Independent root review of the EdgeMech #14 repair found a remaining report
boundary related to #6 and CultureBotAI/culturebotai-claw#951. The production
source/output comparison is independent, but `check_storage` checks only the
outer receipt's claimed SQLite hash. It does not require the artifact manifest's
`source.sqlite_sha256` to agree. The report also ignores the migration receipt's
before/after input hashes.

A substituted, internally consistent migration from another ledger could pass
the report's source check after resetting just the outer SQLite claim to the
expected hash and updating the output digests. The initial positive report test
also omits the manifest's SQLite digest, hiding this distinction.

Acceptance: require the manifest and outer receipt to name the same pinned
SQLite digest; expose the original source SQLite path in the outer receipt so
the exact migration input map entry can be checked; require complete before/after
map equality and valid input digests, including the exact pinned ledger entry.
Add a rehashed substitute-manifest negative and rehashed migration-input-map
negatives. These checks authenticate consistency of retained experiment
evidence; the report does not rerun the migration or reauthenticate a publisher.
