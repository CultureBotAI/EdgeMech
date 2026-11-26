Execute the user-authorized M5 BactoTraits graph-release verification track.
Do not stop at a plan. Read AGENTS.md in both EdgeMech and KG-Microbe and the
EdgeMech docs/plans/m5-review-execution-20261116.md. The other worker owns
ten-case calibration/reassessment; do not edit its worktree or ratings.

The exact-row correction is merged in KG-Microbe PR #1867, merge commit
2d94ed094167d94402f21400a9ad7dc4f7f20438, reviewed head
a86c63e778ebf8a646abb9d4d9e0718dfd49f5a0. EdgeMech PR #135 contains the evidence
record at f841b1d. Inspect current source and frozen provenance before acting.
The quarantined complete original row is BactoTraits row8521/BacDive17851 with
conflicting organism name and DSM19353/JCM14586 accessions. Do not quarantine
neighboring rows without independently establishing their identities.

Retained independently verified evidence is on M5 at
/Users/marcin/agent-work/EdgeMech/retained-pr135-pr1867-20261116/kg-candidate/data/validation-bactotraits-130/
under baseline-v3-20261116 and candidate-v3-20261116. Preserve every nested cache
file and old receipt. The old baseline emitted21edges/22nodes and candidate0/0
plus one complete quarantine audit. This demonstrates PRE-FINALIZATION only.

Start by verifying current published release metadata and local graph provenance.
As of the parent's check, GitHub latest release was2025-03-07, while the old M5
canonical merged-kg.tar.gz was datedOct18,2026. Neither can demonstrate a Nov16
correction. Do not overwrite them or claim publication is complete. Record a
precise unmet publication dependency if there is still no corrected release.

Work in the supplied isolated KG task worktree using corrected merged code:
/Users/marcin/agent-work/EdgeMech/m5-kg-bactotraits-release-20261116.
The baseline worktree is
/Users/marcin/agent-work/EdgeMech/m5-kg-bactotraits-baseline-20261116
at ef27b97a0b450767da54235c6105b5250c178adc. The raw input root is the original
/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe.
Use a pinned Python3.10-3.12 KG environment, not EdgeMech's Python3.14 environment.
M5 has raw BactoTraitsCSV, BacDive lookup, METPO tables, NCBITaxonDB and OWL gzip;
validate the actual inputs. The helper must run a NEW M5 baseline/candidate pair
with identical shared inputs/interpreter and a new --baseline-receipt; historical
v3 receipts cannot substitute for the new baseline. Use --plan before each run.

Before a full build, inspect the current release_preflight and dependency chain:
BactoTraits depends on completed BacDive, which depends on completed ontologies.
Old October transform fingerprints do not satisfy current producer freshness.
Never disable freshness or use allow_unfinalized_sources to call a candidate a
release. Open upstream issue#887 concerns retired kg-hub download URLs; verify
its current status before assuming automated publication works. Other sources
may independently emit the same SPO; trace the quarantined source lineage rather
than requiring unconditional absence of that SPO from the entire graph.

Never commit directly to master/main. Locate retained source inputs and pinned
ontology/prefix/cache requirements without broad downloads or broad scans of
ignored data. Use scripts/adhoc/replay_bactotraits_identity_130_20261115.py for
the smallest actual producer canary and inspect its persisted row audit, output
counts, hashes and runtime provenance. New M5 execution needs new receipts;
do not edit old receipt paths or Python versions. Reuse existing receipt-bound
inputs read-only and keep output roots exclusive.

Then run the smallest adequate finalization/merge candidate path that can verify
the correction survives into graph outputs. Inspect dependencies and free disk
before a large build. Run exactly one real unit through the SAME launcher,
environment, output placement and concurrency mode as any later batch; verify
on-disk side effects, not exit code. If full-snapshot rebuilding is infeasible
with current inputs, complete a bounded candidate verification and explain the
precise full-release blocker instead of relabeling a source fixture as a release.
Do not start unrelated expensive downloads or use all32workers.

Bind producer commit, rawsource bytes, authorities, configuration, finalization
implementation and output hashes. Check the quarantined assertion cannot leak
through another retained copy/join, and identify any equivalent independent
provenance separately. Do not infer trait falsity, replacement identity or a
graph-wide validation from this one correction. Candidate verification and
published-release verification are distinct statuses.

Record findings as owned-repository issues without mentions. Implement necessary
fixes on task branches, keep helpers in scripts/adhoc/ with provenance comments,
open PRs, run required checks and separate read-only adversarial review, file
each finding and triage/fix it. Merging new PRs and publishing releases require
separate human approval; don't ask prematurely before concrete reviewable work.
Push commits the same day. No other messages, mentions, email disclosure,
mail-adjacent helpers, credentials in logs, destructive cleanup, /tmp state or
sandbox bypass. Leave unrelated repositories/outputs and historical evidence
unchanged. Keep .temp/m5-release-progress.json and .temp/M5_RELEASE_PROGRESS.md
current with actual process, phase, commands, hashes, results and blockers.
