# Round02 acceptance fix and bootstrap validation — 2026-11-16

[PR #167](https://github.com/CultureBotAI/EdgeMech/pull/167) follows the immutable
failed round01 at `d197474`. Candidate `455b0766cefe5c58d39b9973db9de69fbb24f732`
removes EdgeMech's blanket rejection of supported claims alongside incorrect or
unassessed modeling. Pinned CLAW `0ca25b8` already permits mixed individual
assessment outcomes while enforcing aggregate verdict and completion rules;
the shared dependency and contract pins are unchanged.

The candidate retains exact-scope literature requirements, versioned authority
for resolved modeling judgments, opposing-proof guards and the strict aggregate
pass check. A saved partial review remains neither approval nor KG admission.
The scientific scope of any fresh-05 claim still requires independent review;
the transport repair does not supply that verdict.

## Verified engineering checks

- Local focused `tests/test_occurrence_review.py`: 111 passed, including 13 new
  regressions covering all three modeling axes and preserved save/readback.
- Isolated M5 Python 3.14.7 locked environment: `python -m pytest -q` completed
  with **843 passed in 44.03 seconds**. Persisted output:
  `.temp/round02-initial-full-tests.log`.
- All 16 pinned CLAW contracts verified; full Ruff scope passed. Persisted
  outputs: `.temp/round02-initial-contracts.log` and
  `.temp/round02-initial-ruff.log`.
- Offline source and wheel builds succeeded; both nonempty artifacts were
  inspected under `.temp/round02-initial-build/` (approximately 412 and 85 KiB).
- Separate read-only whole-PR review of `455b076` against `d197474` found no new
  material defects. Earlier prompt/status findings were filed as #164/#165 and
  their repairs were independently verified. The possible assay-definition
  defect is separately recorded in #166; its biological consequences are not
  inferred.

## Runtime and scientific boundary

M5's isolated worktree is
`/Users/marcin/agent-work/EdgeMech/m5-calibration-round02-20261116`; it has its own
locked virtual environment. The original calibration and release workers have
exited and their artifacts remain intact. The pinned fleet manifest still
disables EdgeMech's native record-review capability; this work uses the existing
local occurrence profile and does not enable a native fleet capability.

At this report's commit, the new bootstrap and production fresh-05 save/check
canaries have not run, no round02 package is frozen and no fresh reviewer has
started. The coordinator must satisfy those prerequisites, then record actual
processes, package hashes, service usage and all original gate results under
its new private output directory. This report certifies the bounded code/test
milestone only. Round01 remains failed; retained90 and9900 remain gated.
