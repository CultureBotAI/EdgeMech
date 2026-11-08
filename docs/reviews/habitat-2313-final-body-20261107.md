This adds native HabitatMech exports for EdgeMech while preserving exact source locators, payloads and native decision scope. The existing 1,831-row decision export contains 424 inherited native ITEM decisions and 1,407 unassessed rows. The completed association exports cover all 13,266 committed selected source rows: 3,081 BacDive, 8,807 PREGO and 1,378 Madin associations. Every added association remains unassessed.

Source concepts and the native `habitatmech:characteristic_taxa` slot stay explicitly unprojected. Complete association and owner rows retain strain-count units, taxon candidate pools, PREGO ranking/scores/direct flags/channels and Madin's unranked selection scope. Habitat grounding review does not review these associations. No characteristicness, growth, preference, causal claim or KG approval is inferred.

The shared contract prerequisite is [CLAW #962](https://github.com/CultureBotAI/culturebotai-claw/pull/962), pinned at `1b5391d083ba85ac94e5279c3cba25ac4fde243c`. [#2311](https://github.com/CultureBotAI/HabitatMech/issues/2311) is advanced by the completed source transport and stays open for exact assertion evidence/reviews and reviewed KG projections. Existing outputs remain immutable.

All three real four-worker canaries were independently verified before full export. Every generated envelope validates, and persisted bytes, ordered membership and counters reconcile before durable manifest-last publication. The full files were independently rehashed after publication. Exact commands, manifest/payload hashes, sizes and limitations are retained in [the source-association guide](https://github.com/CultureBotAI/HabitatMech/blob/73eed5f64fe550b6d6b7c640d53384c72e13abff/docs/edge-source-associations-20261107.md).

All five CI checks passed on reviewed head `73eed5f64fe550b6d6b7c640d53384c72e13abff`. The authoritative quality gate reports 1,235 passed and 27 skipped; its separate structured-review contract tier passed four tests. The mandatory pinned-contract adapter tier passed 28 tests without skipped feature tests. Ruff passed. Independent read-only implementation and exact-head reviews found no new blocking issue.

Fixes #2312. That review finding required persisted binary hashes and ordered identity/source-position reconciliation; valid-row reversal and duplication regression tests verify refusal before publication. Earlier publisher collision and directory-durability safeguards remain in place.

Ready for human review and an explicit merge decision. No merge has been authorized or performed.
