# Chemical scope and upstream node metadata follow-up

This change addresses EdgeMech #41/#55 and continues #36 on top of PR #58.
The original release, source occurrences and earlier assessments remain immutable.

1. Check primary chemical ontology definitions and existing producer policies.
   Separate the reported analyte, the original source-table token and the graph
   object. Define a bounded adjudication policy before revising the three chemical
   assessments. A reporting convention must not assert charge-state equivalence.
2. Diagnose missing labels against current KG-Microbe code and pinned local inputs.
   Prioritize the ten BacDive-linked nodes and publication metadata. Use existing
   source labels or verbatim source citations with explicit provenance; do not
   fabricate titles, genome names or sequence names from identifiers.
3. Implement producer fixes in an isolated KG-Microbe branch. Run one source-record
   canary, inspect the persisted output, and only then run a bounded replay.
   Carry unresolved source gaps forward with exact identifiers and repair routes.
4. Generate new chemical assessments and a verified coverage view with retained
   inputs, quotation proofs and policy provenance. Test restrictive cases that
   could turn a family-level observation into an exact chemical approval.
5. Open separate PRs, perform read-only adversarial review, file every finding,
   address in-scope findings and run each repository's required final checks.
   Merge awaits approval for these PRs. Release regeneration follows upstream
   integration; a local canary is not a repaired published release.

Implementation uses current upstream KG-Microbe commit `333c0edc8` in a separate
worktree. The existing KG-Microbe checkout contains unrelated work and remains
untouched. EdgeMech's parent PR #58 is still open.
