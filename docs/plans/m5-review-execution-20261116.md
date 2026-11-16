# M5 review execution — 2026-11-16

The user authorized M5 synchronization, ten-case independent calibration,
reassessment of the retained 100, expansion only after the established gates,
and verification of the merged BactoTraits correction in a regenerated graph.

The reviewed EdgeMech baseline is `f841b1dff874e78d1a14075413be6a92c90f1378`.
KG-Microbe's merged correction is `2d94ed094167d94402f21400a9ad7dc4f7f20438`.
The M5 host is `marcins-MacBook-Pro-3.local`; its main EdgeMech checkout has
been fast-forwarded from `47bcaec` without changing the old worker worktrees.

## Execution order and durable state

1. Copy retained inputs to the same private locations on M5, checking one real
   transferred file before the rest and comparing checksums after copying.
2. Install the locked environment in the isolated launch worktree. Run a single
   Codex worker through the same launcher/environment/tmux path as subsequent
   workers. Verify its persisted packet-replay artifact and receipt.
3. Start a calibration coordinator and a separate release-verification worker.
   They work on task branches, publish progress under their private output
   directories, and open PRs for reviewable changes. New PR merges and release
   publication remain separate human decisions.
4. The coordinator prepares a new evidence round, then starts two fresh review
   sessions against the same pinned package. Freeze both initial matrices before
   comparison. Record model identities and old-label exposure; same-model
   sessions do not establish independent expert validation.
5. Evaluate the original preregistered thresholds. Failure preserves the failed
   round and triggers evidence/rubric repair in a separately identified round;
   thresholds must not be relaxed. Passing permits review of the remaining 90.
6. Expansion beyond 100 requires all-100 accounting, evidence/modeling gates and
   independently verified correction bytes. Use a new end-to-end canary for any
   new batch or retrieval path, followed by bounded batches, never an immediate
   9,900-item fan-out.

The tracked worker prompts are under `scripts/adhoc/m5_review_20261116/`.
`scripts/adhoc/run_m5_review_worker_20261116.py` records process state, logs,
final output and canary validation in exclusive private directories. A launcher
receipt proves operational execution only; it does not pass scientific gates.
Use the actual PID/session and persisted output when reporting progress.

## Evidence and authority constraints

The retained 100-case archive is at
`/Users/marcin/agent-work/EdgeMech/edge-sample-review-20261112-data`.
Canonical EdgeMech `.temp/` holds the ten historical packet sets, staged
authorities, edge47 full-paper proof and fresh05 identity proof. Historical
receipts pin older profile bytes and must remain intact; new execution uses new
receipts in fresh worktrees. Do not overwrite TraitMech ontology snapshots to
satisfy an old authority-staging receipt.

Every final assessment separates claim, literature, relation, subject node,
object node and source fidelity. Evidence must preserve organism/strain scope,
source measurements and units, DOI identity, short literal excerpts, authority
version and exact original occurrence. Missing evidence is unresolved, not false.
The frozen graph and maintained producer may use different ontology versions.

Use the LBNL literature workflow and retained provenance before fresh requests.
Record the services actually called; skill availability is not service usage.
Use anonymous public APIs and existing CBORG read-only tools. Do not expose
credentials, email addresses or copyrighted paper bodies. Authenticated general
full-text retrieval remains dependent on separately reviewed/merged PR #102.
No paid deep-research jobs, messages, mentions or automatic new-PR merges.

## Release-verification boundary

The existing BactoTraits v3 replay proves an exact-row pre-finalization producer
quarantine. A new release check must bind corrected producer code, frozen source
bytes, finalization and merged graph outputs. Do not relabel the old release as
corrected or publish a release without permission. A local corrected candidate,
an inspected published release and an unavailable publication are distinct
statuses. Preserve all existing source/graph outputs and quarantine audits.
