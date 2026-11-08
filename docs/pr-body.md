EdgeMech preserves release occurrences and their complete decision history in
external Parquet artifacts, with bounded DuckDB queries and a verified local
reader interface. This implements storage and native-overlap infrastructure for
CultureBotAI/culturebotai-claw#766 and CultureBotAI/culturebotai-claw#767 while
keeping bulk graph data outside Git and scientific review with the native Mechs.

The shared-contract prerequisite is
[CLAW #962](https://github.com/CultureBotAI/culturebotai-claw/pull/962).
The reviewed runtime pin remains `1b5391d083ba85ac94e5279c3cba25ac4fde243c`;
all 16 imported contract files are verified. The separate infrastructure
admission in [CLAW #953](https://github.com/CultureBotAI/culturebotai-claw/pull/953)
now passes all gates while preserving historical DUF release bytes. Candidate
verification does not activate protected admission. Neither prerequisite has
been merged.

SQLite migration preserves exact occurrence IDs, raw source rows, memberships,
current decisions and historical canonical bundles. The final storage repair
independently compares SQLite and persisted Parquet hashes and row counts for
all five authoritative tables before durable manifest publication. The report
binds the pinned SQLite source and unchanged migration inputs to the persisted
proof. A real 1,000-row canary and two subsequent partition-layout measurements
preserved 999 unprocessed decisions and one deferred decision, all withheld.
The measurements do not establish a production layout or throughput.

Native adapters are in CultureBotAI/MediaIngredientMech#1147,
CultureBotAI/TraitMech#2082, CultureBotAI/HabitatMech#2313 and
CultureBotAI/TaxonMech#229. Their ten complete export surfaces contain
1,082,786 assertions: the four baseline surfaces plus three Habitat source
association inventories and three separate Taxon record-link inventories.
Transport preserves native locators, payload/evidence bindings, inherited
status and withheld scope. Supported native status does not approve a KG
occurrence; canonical packet decisions remain deferred/withheld. The real
packet canaries are explicitly native-row fixtures, not fabricated KG matches.

The full census uses the historical 20260929 KG-Microbe snapshot, manifest
`f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2`,
with 17,637,435 occurrences. Baseline and expanded representative canaries
passed through the same launcher, shell, interpreter and four-worker mode,
including independent persisted replay. The full census completed and verified
all 17,637,435 occurrences against 1,082,786 distinct native assertions. It
published 882 nonempty Parquet files totaling 1,449,552,054 bytes after native
and exact KG replay.

The verified result is 332,588 incompatible-scope occurrences, 116 whose exact
native candidates remain unassessed (unavailable reviewed evidence), and
17,304,731 unmatched occurrences; ambiguous
mapping and exact eligibility are zero. There are 332,704 endpoint candidates,
including 116 exact subject–predicate–object candidates. Missing exact native
assertion/scope bindings constrain eligibility; zero exact eligibility does not
establish zero biological overlap. No scientific approvals were created.

The run took 4,777.631 seconds including verification, with 1,484,701,696 bytes
peak parent RSS (workers excluded). Manifest:
`a2b8353349816fd067ab3a7112fd1c2f5ee9c02971591ea52f31e9b981cbdd2e`;
run receipt: `a834c68c214cf7f8d2770aa25b9d4f48d241526465bc44965c4fc12f05611fe2`.
The [full evidence](docs/validation/full-native-overlap-20261107.md) retains the
small launch/run/manifest copies. Bulk data remains outside Git.

Validation of the isolated final storage repair: 183 tests, lint, wheel/source
build, extracted-archive test collection, independent read-only review and the
runtime pin check pass. Four mutation controls show that the new source/output
and reporting guards reject otherwise valid-looking substitutions. The exact
reviewed repair was integrated after census completion; census implementation,
launcher, Parquet helpers, schemas, packets and contract pins remain unchanged.
The final read-only readiness audit also pins every PR's expected check inventory;
its missing-workflow and modified-inventory regressions pass, and a real one-PR
canary retained all five successful CLAW #962 checks at the reviewed head.
The integrated wheel/source build and complete Ruff pass succeeded; the extracted
source archive collects all 185 tests. These package checks are retained in
[the final package evidence](docs/validation/final-package-20261107.md).

Review findings were filed before repair: #1/#3/#4 publication durability and
exclusivity; #5 runtime pin closure; #6 reporting provenance; #7 source-package
closure; #8 bounded catalogue scaling; #9 native packet persistence; #10 bounded
batch tuning; #11 Arrow transaction retention; #12 bounded reader interface;
#13 milestone receipt references; #14 source/output field reconciliation;
#15 report input binding; #16 precise Trait inventory wording; #17 complete
expected CI inventory; #18 current README admission status; #19 complete test
lint coverage; #20 explicit cross-repository comment links. All repairs are included in this PR. The final CI run exercises
the complete test suite once, including both new readiness regressions.

Fixes #1. Fixes #3. Fixes #4. Fixes #5. Fixes #6. Fixes #7. Fixes #8. Fixes #9.
Fixes #10. Fixes #11. Fixes #12. Fixes #13. Fixes #14. Fixes #15. Fixes #16. Fixes #17. Fixes #18.
Fixes #19.
Fixes #20. Fixes #23. Fixes #24.

[Milestone disposition](docs/milestone-status-20261107.md) records cross-repo
dependencies and the scientific follow-ups that remain open. This PR does not
deploy a browser, publish a graph or implement the later scientific review-worker
and production queue milestones. Exact-head CI and the final readiness audit
are recorded in the PR handoff. Merging requires explicit human approval.
