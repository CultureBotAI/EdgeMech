# Expected PR checks: independent review, 2026-11-07

The final read-only audit uses
[`check_pr_readiness_20261107.py`](../../scripts/adhoc/check_pr_readiness_20261107.py)
and the separately pinned
[expected-check inventory](../validation/pr-readiness-expected-checks-20261107.json).
Two independent reviewers compared that inventory with the frozen PR workflow
definitions and actual changed paths, rather than deriving expected checks from
the response being tested. Neither pass edited source, policy or output, nor
retriggered a workflow. No inventory omission was found.

| PR | Reviewed workflow head | Expected checks |
| --- | --- | ---: |
| CLAW #962 | `6031604c3b24a1a47a0b15a1ec1d46db47d73e1e` | 5 |
| CLAW #953 | `85a69ee2164a3c9e70e0ffd8a9c33038ab84d716` | 5 |
| CLAW #987 | `326bdff8c285301d7b626fb7a001f41ce15700fa` | 6 |
| Site #541 | `1642cf7c416c9120d3980aeb9069faeb1fc6d29e` | 1 |
| MIM #1147 | `8ec80235d41154e398238459d914c9fa3052a1d8` | 17 |
| Trait #2082 | `39bc45b6fbcfbef56cf3b9ea7150d19d26b095e9` | 9 |
| Habitat #2313 | `73eed5f64fe550b6d6b7c640d53384c72e13abff` | 5 |
| Taxon #229 | `9495d5939df1135f0c71e28c9d5194a12d2e0f9c` | 3 |
| EdgeMech #2 | `ea2503df9ffdbf9cb6b6ae82b3c0ba32d272f3d2` | 1 |

All listed jobs have applicable unfiltered `pull_request` triggers. Path filters
in the native workflows are under `push`, so they do not suppress these PR
checks. The expected sets include the authoritative full tests/QC, mandatory
native contract jobs, vendored checks and applicable reusable label jobs.
All four native contract jobs explicitly pin CLAW
`1b5391d083ba85ac94e5279c3cba25ac4fde243c` and require contract imports before
running exporter, publication and expansion tests. The MIM/Trait reusable label
job names agree with the pinned CLAW `label-correspondence` child workflow.

Excluded jobs are main-only, scheduled/manual, or reusable without an applicable
caller: CLAW cross-repo validation, knowledge-gap scan, progress Pages and
admission/integrity; native Pages/integrity and manual shepherd/admission;
Trait main/manual check-presence and its disabled automatic Claude review;
EdgeMech manual shepherd and scheduled/manual admission. Site refresh steps
are conditional schedule/manual steps inside `validate`, not additional PR jobs.

The inventory SHA-256 is
`f122463d877629b86e2145eafd7f1ce29ecf7b1d849c2e32ebd0a6516fe59486`.
The helper SHA-256 is
`3f0ef8ad291672c0c4e592e7bc2b167675694104f0b4707110a131076c163b13`.
EdgeMech #17 records the missing-workflow finding; both its missing-check and
weakened-policy regressions pass. The one-PR live canary was independently
rehashed and inspected, including the exact expected five checks and unchanged
CLAW #962 head. Its retained receipt SHA-256 is
`d699d8294c0fd90773bc15c8ab44a37c70a1824c94c09a410a808d88ca68b4d8`.

These are expected workflow inventories, not a claim that every job had finished
at this review time. The final audit must supply the final reviewed EdgeMech
head after its integration and CI. EdgeMech #19 subsequently expands Ruff to
the complete test directory, preserving the reviewed `test` job and PR triggers.
The audit
records a point-in-time GitHub snapshot and does not grant permission to merge
or replace the separate adversarial review.

The first nine-PR audit did not certify readiness: GitHub initially returned
unknown merge states for three CLAW PRs. Refresh confirmed #962/#987 clean but
#953 conflicting with newly advanced main `081e9c8f44c5ce28849e162b7fecac1b3ba17ad7`.
CLAW #997 records that integration finding. Independent read-only comparison
confirmed that main changed no workflow from the prior base `c7485ddb`; the five
CLAW #953 jobs and their unfiltered PR triggers remain identical. The #997/#1004
policy and public-sync repairs, tests and consumer canary add no workflow job.
The pinned expected-check inventory therefore remains unchanged. The final
audit must pin the new reviewed CLAW #953 head, along with the final EdgeMech
documentation head, rather than reuse the earlier successful CI heads.

The final refresh also exposed stale Taxon #229 test-merge metadata while
GitHub reported `CLEAN` / `MERGEABLE`. This is not evidence that the clean
result was false. An isolated Git check of actual main `5d69e8f` and reviewed
head `9495d593` confirmed a conflict-free merge without changing the feature
branch or rerunning CI. The [retained proof and API limitation](pr-readiness-stale-merge-base-20261108.md)
record the immutable inputs, unique merge base and output hashes. EdgeMech
#22 remains open as nonblocking future receipt-observability work; it adds no
up-to-date-branch or fresh test-merge requirement. The audit continues to
report a point-in-time status, not CI validation of every newly composed tree
or permission to merge.
