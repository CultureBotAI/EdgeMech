# Candidate membership preparation validation — 2026-11-26

This is engineering preparation for issues #224/#228. Neither the new membership
scan nor the timing-wrapper probe has been executed against campaign inputs.
Scientific coverage remains0; A/B remain null. Independent source review and
exact publication readback remain gates before actual use.

## Boundary 2 successor repairs

The independently reviewed 16-file candidate was held for B2-EXIT-01 and
B2-PATH-02. Findings were filed as #241 and #242 before source changes. The
original patch remains retained at
`5e9ecf00ff343bf380fa7a019ccff60323c9e5758e6c0a38fa942df4557fc52b`.
The validation and source tables later in this document describe that historical
candidate and its predecessors, not the repaired successor.

The timing helper now returns nonzero when the timed control alone times out or
cannot launch, while retaining both outcomes. A completed current wrapper with
a different observed exit remains a separate observation. Neither outcome can
recover the original census child's exit.

Both helpers use the new `restart_private_attempt_20261126.py` for output.
It retains a no-follow directory-descriptor chain through attempt creation,
exclusive files, progress, results, failure receipts, readback and fsync. It
checks directory and file identities and releases descriptors on errors. Failed
attempts remain preserved; symlink replacement cannot redirect later path-following
writes because those writes now use retained descriptors. Each result also binds
the shared output helper's source hash.

Final successor validation: **1746 passed in164.75s**, exit0; **91 focused tests
passed in1.13s**;16 contracts, full CI Ruff and offline sdist/wheel builds passed.
All six repaired/new source/test pins remained unchanged through the full suite.
The full log SHA256 is
`8baf4627ef9a26432dd41512d81009b4df7392a0900d4aa46000d7cc6794e1a1`.

A separate fresh pytest process used exact preserved original helper bytes with
the new regression tests. It produced **10 expected assertion failures**: two
timed-only missing-terminal cases and eight redirected-output cases, including
failure receipts. The first negative run's8 failures/2 passes is also preserved.
Its two passing fixtures lacked a reachable redirected child directory; that
fixture gap was filed before correction. The corrected final run verifies the
requested ancestor-at-open distinction rather than a missing-directory error.
No original source was rewritten and no actual campaign operation was repeated.

The exact successor still requires independent changed-source/result review and
publication readback before actual membership or timing-helper use. The owner's
Boundary4 hold remains: no branch transition, worker publication or separate-branch
selection. Boundary3's final privacy-source PASS does not lift that hold. A/B,
census disposition and all scientific gates remain unchanged.

Sanitized source, validation and negative-result pins are retained in
`scripts/adhoc/provenance/restart-native-inventory-20261120/boundary2-repair-20261126.json`.

## Historical candidate validation

The preparation branch starts at ae065236952b231fb315d137292b1cc95b153b96. Its
candidate now includes all seven exact reviewed repair files from PR233
head7510827b2f21df1603e1f6697456ffb0d4f45a09, applied as source changes on the
existing branch. Branch history and the root's clean reviewed checkout remain
unchanged. The earlier1576-test result below applies to preparation before this
integration; its files and patch remain retained. Relevant maintained census code
is unchanged, SHA2562b90886fb21d1f42d3d718d936e1a09e37c935b1b23d5ff6cf4b266abfa73793.

The earlier integrated candidate completed **1709 passed in168.82s**, observed terminal
exit0. Its full log SHA256 is
9d8e01e351bb58c3955ae1b3919ef9fecc85b124c4f0f2ca3108e15e041cd7f4.
This combines the accepted1637-test repair inventory with the72 new timing and
membership tests. All16 contracts, full CI Ruff and final offline sdist/wheel
builds passed on the integrated source. The integrated build log SHA256 is
b0d56b1d3e4b23ffeac7eee00f081c2ade3f81b5db10f42de1a373ac10c5d9d1.

| Candidate | SHA256 |
| --- | --- |
| Membership helper | 865ebf20c67a1427f3677fd4b2c9db8815133be26abdd8ce0d6099dbbbdccaf3 |
| Membership tests | 51bf6f126ab0c283d83dfc0c9737951f20f66da26054baf564bf8298d7254201 |
| Timing-wrapper helper | 303759c49327ab7ddc399ae2de854ce5ab9a029befce7ce4ef5318a8a6be41b0 |
| Timing-wrapper tests | 82a1378bf70642166e0886015c044a818bc3b3874beb90a8aa1a321030c2b5b9 |

The55 membership tests passed in2.00s. They distinguish identical raw/SPO rows at
different positions, other source versions, incomplete scans, forged row/hash
identities, schema/count mismatches, malformed pins/JSON, symlink/FIFO input,
invalid time budgets, output escape, existing attempts and preserved failures.
Focused log SHA256f4677acf293e2974a609225b1b72e1fb25fc3bcdf564cfb232f68cc080e7bfd7.

The earlier expanded suite, including the unchanged17 timing-wrapper tests, completed
**1576 passed in164.58s**, observed terminal exit0. Full log SHA256
d24409803082c889d75136f83d079719f260d09a2648c8393710cffc6e800e3b.
All16 pinned contracts, full CI-scope Ruff and offline sdist/wheel builds passed.
Build log SHA256b32e59384113cc81d6b086a836ef72e74d90d818c0de7412c2775afeeacf018c.
Source/test pins remained unchanged after validation. The original unexecuted
membership draft is privately retained at SHA256
5fd65c87566c107b552bcee3ef2b4a7ab48d61763c1686caf3a4a1c86281ab33.

Fresh repaired structural observations from the already-reviewed PR233 helper
are bound separately in its sanitized provenance companion. They reproduce the
two historical locator/document outputs exactly; they do not qualify baseline
membership. Original census FAILED outer exit1 and unobserved child exit remain
unchanged. Canonical publication treatment and worker producer review are
separate pending decisions, with no new provider/canonical operation performed.

## Bounded fixture-content extension

The retained fixture-extension candidate added a read-only inspector and18 offline tests.
Its expanded suite completed **1727 passed in174.77s**, observed terminal
exit0; log SHA256
7838cd9cef0506b69278c9cbadde09d66c085f4e0331d66d111d06a0d0bb0f54.
All16 contracts, CI-scope Ruff and offline sdist/wheel builds passed. This is a
new scope after the earlier1709-test validation, whose evidence remains retained.
Its exact source/test bytes were preserved after that run; the Boundary2 repairs
above are a separately validated successor.

The inspector reuses the accepted audit's pinned document/locator projections
and guarded regular-file reads. It reads only the four explicitly selected
fixture-family groups, checks every selected copy against its retained hash,
and reports fixed content predicates per byte variant. Duplicate identities,
missing variants, changed copies, malformed metadata, unsafe file types and
budget failures refuse success. Unknown outcomes and nonscientific flags alone
do not produce an exclusion. Outputs contain hashes, fixed checks and counts;
private paths, review prose and runtime bindings remain outside public provenance.

The actual bounded read completed with command exit0 and empty stderr. It read
563 pinned locators representing503 variants: one canonical stub at42 locators,
222 occurrence-fixture variants at241 locators, and140 readiness variants for
each synthetic reviewer. All selected content predicates matched. The original
619-variant audit remains unchanged;116 other variants are outside this content
inspection. No record or target ID was removed from a baseline ledger.

Source, test, input, result and validation digests accompany the helper in
`scripts/adhoc/provenance/restart-native-inventory-20261120/fixture-content-observations-20261126.json`.
The new source was tracked before use and its exact pre-execution bytes remain
private. This observed content match is a candidate fixture disposition requiring
independent source/result review. Historical test execution has not been reconstructed.
It is not a canonical replay or scientific decision. The membership scan,
timing-wrapper probe, worker publication treatment and full A/B freeze remain
separately held; the original census outer exit1/child-unknown evidence is unchanged.
