# Adversarial review and correction of PRs 33 and 38

The read-only review covered PR33 at `68e4cbb` and PR38 at `baeb623`.
Separate passes examined preparation, retrieval/provenance and adjudication.
PR33 had no new blocking findings and merged as `c205b78`. PR38 was retargeted
to main. Every new finding was filed before implementation.

| Issue | Finding | Resolution |
|---|---|---|
| [42](https://github.com/CultureBotAI/EdgeMech/issues/42) | Full-text paragraph/cell concatenation could invent contiguous quote text | v2 preserves block boundaries and inline chemistry; v1 full text is audit-only |
| [43](https://github.com/CultureBotAI/EdgeMech/issues/43) | Deferred OA fetch counted complete | Both retrieval stages affect completion and stop the queue |
| [44](https://github.com/CultureBotAI/EdgeMech/issues/44) | Short Retry-After bypassed minimum interval | Preserve the greater limiter/server deadline |
| [45](https://github.com/CultureBotAI/EdgeMech/issues/45) | Absolute response paths escaped the cache | Require canonical SHA-256 response basename |
| [46](https://github.com/CultureBotAI/EdgeMech/issues/46) | Mixed reviews could mark unsupported evidence supported | Require supporting quotes per supported assessment |
| [47](https://github.com/CultureBotAI/EdgeMech/issues/47) | Refuting evidence recorded as no conflict | Explicit refutation produces unresolved conflict |
| [48](https://github.com/CultureBotAI/EdgeMech/issues/48) | Python optimization removed judgment binding assertions | Explicit errors, tested under python -O |
| [49](https://github.com/CultureBotAI/EdgeMech/issues/49) | One malformed metadata response broke unrelated replay | Revalidate and isolate explicitly invalid entries; reject fabricated evidence |

All eight fixes are in `8572e30`, with regression coverage. Local validation:
**265 tests passed in 41.78 seconds**, repository-wide Ruff passed, and all 16
pinned CLAW contract files verified. No shared contract was changed.

## Persisted validation

The original 463-occurrence cohort, retrieval and ten-assessment pilot passed
fresh raw-response reconstruction, canonical bundle validation and all ten quote
proof checks. Its original quote-proof SHA-256 remains
`dbf91bc266850c6f9aa33d3bdcbc075001804f076a371e7ccd138c2e99894e4b`.

A fresh one-identifier retrieval canary wrote nonempty artifacts and passed
source reconstruction before the complete 33-identifier cached replay ran.
The replay completed all 33 identifiers, with 33 metadata cache hits, text for
29 papers and no deferred identifiers. The persisted provider attempt count
remained 35 before and after: no new provider requests were made. New text
derivatives use v2; their `documents.json` SHA-256 is
`6639f0c57578f77ee0d4833ea351c18c3ceb64057f3073baee26b7fadc4235de`.

The unchanged ten judgments were also regenerated through the corrected
adjudication path using their original pinned abstract evidence. Results remain
four supported and six unknown, 453 deferred, and zero KG admissions. The new
bundle SHA-256 is
`8c03e3bb306cce3fdccfb71763528e1b489d61937912571bd319d1be35268e13`.
This is a workflow revalidation, not a new independent scientific assessment.

The committed helper `scripts/adhoc/verify_literature_review_fixes_20261110.py`
produced `workspace/literature-review-original-validation-20261110.json` and
`workspace/literature-review-revalidated-20261110.json`. Retrieval artifacts:
`workspace/literature-retrieval-v2-canary-20261110` and
`workspace/literature-retrieval-v2-full-20261110`. Revalidated adjudication:
`workspace/literature-adjudication-revalidated-20261110`. Prior artifacts remain
intact. Legacy full-text derivatives may be replayed for audit, but new scientific
quotes from them are rejected until retrieval is regenerated from retained bytes.

Scientific uncertainties in #41, individual review of the remaining occurrences,
bibliographic resolution, legacy coverage correction (#35) and upstream node
metadata repair (#36) remain follow-ups. None is represented as completed here.

## Cleanup scope

Git's worktree inventory lists only the primary EdgeMech checkout. There is no
dedicated linked worktree to remove. Cleanup is limited to the two merged feature
branches locally and remotely. The primary checkout, protected workspace and
temporary evidence, environment, unrelated branches and caches are preserved.
The cleanup inventory included ignored paths; its reference scan hit its cap,
so it is not evidence that unscanned data is unreferenced. No files are selected
for deletion.
