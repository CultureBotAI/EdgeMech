EdgeMech's fleet registration exposed an assumption that every admitted repository must have a numeric corpus card, graph node, historical statistics and website audit. This change represents curation infrastructure explicitly: EdgeMech gets its repository description, membership badge and canonical capability row while the fourteen-corpus census and all its existing evidence remain intact.

The membership snapshot and CLAW-only audit row use `64cd157ecd37cbd5a1550465d89eb804c5b59409`, including EdgeMech's corrected not-applicable inventory declaration. The existing record counts, graph, overlap assets, November 4 source pins, website verdicts and historical PR totals do not change. EdgeMech has no published Pages site or scientific corpus represented by this audit; native-review transport does not imply independent scientific approval.

Closes #540. Depends on [CLAW #953](https://github.com/CultureBotAI/culturebotai-claw/pull/953); please keep this PR unmerged until that registration is approved. Merging this repository deploys the site, and remains the user's decision.

Validation: 252 unit tests passed; generated-page check, canonical-manifest semantic check against the reviewed CLAW feature checkout, and `git diff --check` passed. New tests reject fabricated corpus/site entries, hidden corpus members, missing infrastructure representation and conflicting repository identities. A separate read-only adversarial review found no additional blocking issue after #540 was addressed. The membership refresh helper and review record are retained in this PR; the lease helper is retained in CLAW.

The PR workflow runs local tests and the generated-page check. Its nightly/manual live-main manifest check still compares against CLAW main, so that comparison remains dependent on the prerequisite merge; no check was weakened. No fresh corpus scan or live fourteen-site feature audit was performed for this membership-only update.

Worktree: `/Users/marcin/Documents/VIMSS/ontology/Mechs/CultureBotAI-site-edgemech-20261107`. No corpus snapshot was created or removed.

Final read-only review confirmed exact head
`1642cf7c416c9120d3980aeb9069faeb1fc6d29e`, with no additional finding.
The head's Fleet page CI check is green. The generated-page check and semantic
manifest check were repeated against the admission worktree and passed: fifteen
fleet members, with the existing fourteen-corpus census preserved. CLAW's later
explicit unverified serialization declaration does not change the fields used by
the site projection, so the site's original immutable source pin is retained.
Issue #540 is addressed in this PR. CLAW #953 must be approved and merged before
this dependent site change; neither PR is merged by this review.

