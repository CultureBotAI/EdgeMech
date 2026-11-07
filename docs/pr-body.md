EdgeMech stores release occurrences and their complete decision history in
external Parquet artifacts and queries them with DuckDB. This implements the
storage and native-overlap infrastructure for
CultureBotAI/culturebotai-claw#766 and CultureBotAI/culturebotai-claw#767 while keeping bulk
graph data outside Git and preserving native scientific ownership.

Shared-contract prerequisite: [CLAW #962](https://github.com/CultureBotAI/culturebotai-claw/pull/962).
The immutable reviewed runtime pin remains
`1b5391d083ba85ac94e5279c3cba25ac4fde243c`; all 16 imported contract files are
verified. Fleet admission is separately staged in
CultureBotAI/culturebotai-claw#953 and blocked by the immutable-release
transition recorded in CultureBotAI/culturebotai-claw#960.

SQLite migration preserves exact occurrence IDs, source bytes, memberships,
current decisions and historical bundles. Complete canonical replay and
physical/logical hash reconciliation precede durable manifest publication.
The real 1,000-row canary and three partition-layout measurements are recorded
in [validation evidence](docs/validation/20261107.md).

Native adapters are in CultureBotAI/MediaIngredientMech#1147,
CultureBotAI/TraitMech#2082, CultureBotAI/HabitatMech#2313 and
CultureBotAI/TaxonMech#229. Their complete declared surfaces contain
327,941 assertions with inherited supported, withheld or unassessed status.
Exact inherited-scope conformance is separate from scientific approval;
canonical candidate decisions remain deferred/withheld. The real native packet
round-trip is a clearly labeled native-row fixture, not a fabricated KG match.

Validation: 153 tests, lint, wheel/source build, extracted-archive test
collection, independent read-only review and the final runtime pin check pass.
Four-worker validation uses bounded ordered batches and bulk SQL; on the same
1,000 native rows, measured catalogue construction changed from about 10.19 to
5.64 seconds. That prefix measurement does not predict full-run throughput.

The combined four-adapter canary and full census use the historical 20260929
KG-Microbe snapshot, manifest
`f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2`.
The canary is currently running; full-population receipt publication follows
its persisted artifact verification. Neither an overlap rate nor full-run
completion is claimed before that receipt exists.

Review findings are filed and repaired: #1/#3/#4 publication durability and
exclusivity; #5 runtime pin closure; #6 receipt-bound reporting; #7 source-package
provenance; #8 bounded catalogue scaling; #9 real native packet conformance.
Fixes #1. Fixes #3. Fixes #4. Fixes #5. Fixes #6. Fixes #7. Fixes #8. Fixes #9.

This PR remains draft. Merging requires explicit approval.
