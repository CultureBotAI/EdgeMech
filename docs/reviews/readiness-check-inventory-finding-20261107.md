Read-only review of scripts/adhoc/check_pr_readiness_20261107.py found a fail-open completeness gap in its readiness calculation.

The helper requires a nonempty statusCheckRollup and checks that every reported entry succeeds, but it has no expected check inventory. A same-head, open, non-draft PR with mergeStateStatus CLEAN and only one successful optional check can therefore produce ready=true even if its authoritative quality gate never appears. Branches without required-check protection make this consequential; CLEAN alone is not a substitute for the intended CI inventory.

Require a reviewed expected check inventory for every pinned PR, retain that policy in the receipt, and reject missing expected checks while continuing to reject pending, failed and unknown check types. Do not infer the expected inventory from the same live response being tested. Add a focused negative that removes one authoritative expected check from an otherwise successful response and requires ready=false; preserve exact-head and read-only behavior.

No source or audit output was changed during this review. The Trait milestone wording repair for issue #16 was also inspected and is accurate against its persisted instance-level inventory.
