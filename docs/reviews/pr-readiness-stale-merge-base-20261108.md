# Record current-base provenance in readiness receipts

EdgeMech issue [22](https://github.com/CultureBotAI/EdgeMech/issues/22) remains
open for future API-freshness and receipt-observability work. It is nonblocking
for the reviewed TaxonMech PR 229: an isolated Git check proves its unchanged
head merges cleanly with the actual current main. This finding does not
establish that GitHub's `CLEAN` result was false, require an up-to-date branch,
or invalidate the successful head checks. The initial proposal to require fresh
test-merge parents as a readiness gate is withdrawn.

## Observed API limitation

The final read-only nine-PR readiness refresh initially returned an unknown
merge state for TaxonMech PR 229. Subsequent REST and GraphQL reads returned
`CLEAN` / `MERGEABLE`, with all three head checks successful, while exposing
different base identities:

- Reviewed head: `9495d5939df1135f0c71e28c9d5194a12d2e0f9c`.
- Actual `defaultBranchRef.target.oid` and `pullRequest.baseRef.target.oid`:
  `5d69e8fddfec18941993abd779b7d600b0ccad14`.
- Cached `pullRequest.baseRefOid` and REST base:
  `ab35a0d0a0a2b47d250145db0c15b414fccbfdb8`.
- `potentialMergeCommit.oid`: `53859406e96467c3906f565591f3c06939aca800`,
  whose actual parents are that old base and the reviewed head.

REST GETs with `Cache-Control: no-cache` at `2026-11-08T02:47:11Z` and
`2026-11-08T02:47:57Z` still returned the old pair and a clean result. GitHub's
[mergeability guide](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-your-git-database#checking-mergeability-of-pull-requests)
warns that merge refs can become outdated and prescribes a pull-request GET
followed by polling. Its
[GraphQL descriptions](https://docs.github.com/en/graphql/reference/pulls#pullrequest)
describe `potentialMergeCommit` as the generated test merge and `mergeable` as
the conflict assessment. These API fields alone do not establish a conflict
with the actual current base, nor prove that `CLEAN` is incorrect.

## Concrete current-base compatibility proof

The proof used Git `2.50.1 (Apple Git-155)` in a new isolated shared clone:

```text
/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/culturebotai-claw-edgemech-20261107/.temp/taxon-mergeability-20261108
```

The parent worktree ignores this `.temp` path. A shared, no-checkout clone of
the local Taxon feature worktree reused its existing objects read-only; a fetch
of immutable current main `5d69e8f` wrote only to the isolated repository.
No Taxon branch, index, working file or remote ref was changed.

The exact inspection commands inside that isolated repository were:

```sh
git fetch --no-tags https://github.com/CultureBotAI/TaxonMech.git 5d69e8fddfec18941993abd779b7d600b0ccad14
git merge-base --all 5d69e8fddfec18941993abd779b7d600b0ccad14 9495d5939df1135f0c71e28c9d5194a12d2e0f9c
git merge-tree ab35a0d0a0a2b47d250145db0c15b414fccbfdb8 5d69e8fddfec18941993abd779b7d600b0ccad14 9495d5939df1135f0c71e28c9d5194a12d2e0f9c > merge-tree-three-way.txt
git merge-tree --write-tree 5d69e8fddfec18941993abd779b7d600b0ccad14 9495d5939df1135f0c71e28c9d5194a12d2e0f9c
```

Results:

- The unique merge base is `ab35a0d0a0a2b47d250145db0c15b414fccbfdb8`.
- The three-argument read-only check completed with no conflict or
  changed-in-both markers. Its retained `merge-tree-three-way.txt` contains
  1,693 lines / 77,226 bytes and SHA-256
  `6ea75386dd196097a7c147a79a83793011e5fac055855019b7305555f7c6be57`.
- The modern merge-tree check exited `0` and created result tree
  `c9092ce788bb1fca5dc7fcbf8c5fe92e059430d3` only in the isolated object
  database. It made no commit and updated no branch.
- The resulting tree differs from current main only by the feature's 13 added
  paths. It differs from the reviewed feature head only by main's 13 changed
  paths. There is no overlapping path between those two changesets.
- Actual main advanced through `7aceacf89bf91511b1b4222086dce25a4bea8a86`
  (committed `2026-11-07T21:53:27Z`, parent `ab35a0d0`) to `5d69e8f`
  (committed `2026-11-08T00:40:18Z`, parent `7aceacf8`).
- The original Taxon worktree remained clean at the reviewed head. No workflow,
  native export, census replay, rebase or PR update was triggered by this proof.

This establishes conflict-free Git composition for those immutable inputs.
It does not claim that CI executed on the newly composed tree or establish
semantic compatibility beyond the reviewed changes and existing validation.

## Triage

The readiness helper remains a point-in-time GitHub status and exact-head CI
inventory check with `merge_permission: false`. No runtime, test policy or
expected-check inventory changes are needed for this case. A future receipt
improvement may record live base targets, generated test-merge parents and
their observed mismatch explicitly, without treating stale test-merge
metadata as proof of conflict or introducing an automatic rebase requirement.
Merging remains the user's decision.
