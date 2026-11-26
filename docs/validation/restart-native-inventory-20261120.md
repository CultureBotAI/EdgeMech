# Retained native-review inventory, 2026-11-20

The earlier filename shortlist omitted retained synthetic artifacts. The bounded
audit helper now records every supplied native-review path, preserves copied and
changed bytes separately, and reports direct assessment-to-target bindings using
the pinned CLAW document loader. It does not assign baseline membership or validate
scientific judgments. Issues #224 and #228 govern accounting and provenance.

An ignored-inclusive two-root search retained 413,624 file locators, including
7,073 archive candidates and 871 `review.yaml` locators. Git internals, explicitly
named environment/cache directories and node_modules were excluded; symbolic
links were not followed. Retained test outputs were included. This filename
inventory does not establish complete archive coverage. Archive containers,
additional artifact formats, source/version bindings and baseline dispositions
remain to be reconciled.

The actual bounded audit read and parsed all 871 supplied locators into 619 byte
variants with 120 declared review IDs. It flags 222 variants with explicit fixture
content, without automatically excluding them. A further 280 variants use two
historical readiness-review IDs and need test-provenance disposition; one minimal
document lacks declared timing. Counts describe retained files, not assessed
occurrences. A/B counts remain null, and new scientific coverage remains zero.

Public [summary](../../scripts/adhoc/provenance/restart-native-inventory-20261120/summary.json)
binds the executed helper, private input list, per-locator readbacks and document
observations by SHA-256. Actual source bodies, source-input paths and invocation
bindings remain private. The original helper intended to store only structural
review observations. Independent review later demonstrated that malformed nested
projected fields could copy prose; original results remain retained and
unqualified. The repaired helper bounds and type-checks each projected field
before producing observations.
Missing, nonregular, malformed and changed inputs are never silently converted
into membership. The input-list pin does not attest prior review-byte versions;
fresh document hashes must still be compared with retained earlier inventories.

The separate [source apply summary](../../scripts/adhoc/provenance/restart-source-20261120/apply-summary.json)
records one successful exclusive invocation of the exact independently reviewed
PR #232 helper. Its original private receipt is unchanged. The maintained census
replay is a separate operation; restoration does not verify census classifications
or establish science. No launcher or source mutation was rerun for this inventory.

Validation on the original candidate: 1,504 full-suite tests passed in 198.82 seconds,
15 focused tests passed in 1.77 seconds, all 16 pinned contracts and CI-scope Ruff
passed, and offline source/wheel builds succeeded. Tests cover retained byte variants, partial engineering
judgments, prose-only mentions, orphan target bindings, fixture markers, cutoff
ambiguity, missing and malformed files, symlinks, input pins, failure readback and
refusal to overwrite results. Full-suite log SHA-256 is
`cf855a157f8d301580909d1424df3be2b741044066f7d25672340b036f109cd7`.
Two unsuccessful test invocations remain private: one used the wrong fulltext
fixture prefix, and the next omitted its parent directory. The corrected run used
a fresh durable fixture root; no code or live mutation changed for those repairs.
Independent engineering/publication review remains pending. This record grants
no scientific dispatch gate.

## Independent review repairs, 2026-11-26

Issues #234 and #235 were filed before fixes. More than six fractional timestamp
digits are now rejected instead of silently truncated; such review timing stays
unresolved. Projected IDs, categories, source-input fields and target fields must
have bounded scalar shapes. Invalid documents retain their locator and exact hash
with `unresolved_parse_or_shape`, without copying the malformed values. Missing
optional declarations remain unknown. These checks do not constitute canonical
schema validation or baseline qualification.

All 129 focused tests passed on Python 3.14.7. In a fresh process using the exact
original helper, five selected regressions failed meaningfully: two submicrosecond
timing cases and three persisted nested-value cases. The repaired inventory passed
1,618 full tests in 176.93 seconds, 16 contracts, CI-scope Ruff and offline builds.
Original helper and result hashes are unchanged; no original audit or live canary
was rerun to manufacture these results.

The new `checkpoint_restart_20261126.py` preserves previous state bytes and records
its own producer hash. It is a parameterized successor, not the producer of the
historical recovery checkpoints. It was added after the 1,618-test collection and
was not covered by that run. Independent review identified a writer race before
any live use; issue #239 was filed before repair. A maintained per-state
`LockManager.lock` context now covers comparison, snapshot and replacement.
Nineteen focused tests cover stale state, concurrent writers, failure release,
duplicate JSON keys, confinement and refusal to promote scientific counters.
The concurrency regression fails against the pre-lock source in a fresh process.
The combined final suite passed 1,637 tests in 182.80 seconds, including the
checkpoint helper. Its log SHA-256 is
`48cdbd5a19c3018f7c1902ab5f3fa728af1e9ee1a0b8b147a47a1cdcc93c9cdb`.
All 16 contracts, CI-scope Ruff and offline builds passed. Independent source and
focused-regression review passed for the four exact helper/test hashes in the
[repair provenance](../../scripts/adhoc/provenance/restart-native-inventory-20261120/repair-20261126.json).
The independent terminal addendum also verified the combined suite, provenance
and census plan. Exact committed/publication readback remains pending; the
checkpoint helper has not been used on live state.

The retained census command completed with outer exit 1 despite a complete JSON
result equal to the pinned manifest. The timing-wrapper warning supports an error
attribution but does not supply a separately observed child exit. That validation
status remains under review; no verification or source restore was repeated.
All A/B and scientific gates remain unchanged.
