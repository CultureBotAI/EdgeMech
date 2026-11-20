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
bindings remain private. The helper stores only structural review observations;
literal evidence, article bodies and assessment prose are not copied to its report.
Missing, nonregular, malformed and changed inputs are never silently converted
into membership. The input-list pin does not attest prior review-byte versions;
fresh document hashes must still be compared with retained earlier inventories.

The separate [source apply summary](../../scripts/adhoc/provenance/restart-source-20261120/apply-summary.json)
records one successful exclusive invocation of the exact independently reviewed
PR #232 helper. Its original private receipt is unchanged. The maintained census
replay is a separate operation; restoration does not verify census classifications
or establish science. No launcher or source mutation was rerun for this inventory.

Validation on the final candidate: 1,504 full-suite tests passed in 198.82 seconds,
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
