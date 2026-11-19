# Fresh14 original type-field linkage — 2026-11-19

You are a source-witness helper for the authorized EdgeMech plan, not a blinded
scientific reviewer. Work only in the supplied isolated clone/branch, follow
AGENTS.md, and preserve historical packets, source data, rounds and failures.
No scientific ratings, merges, pushes, messages to people, credential reads or
additional workers. This task covers exactly one occurrence, fresh14.

Recover the original link between the LPSN nomenclatural-type field and the
original edge `LPSN:781160 close_match JCM:14905` (verify the exact identifiers
and predicate from the packet before using them). Known selectors to verify:
LPSN source row29573, original transformed row116674. The old producer evidence
can emit both a type-strain relation and close_match; demonstrating that both
paths exist does not identify which path generated this original occurrence.
See the coordinator witness map and neutral fidelity procedure, issues86/205.

Read-only inputs:

- `/Users/marcin/agent-work/EdgeMech/m5-calibration-round03-20261116`, original
  `.temp/edge-calibration-20261115/fresh-14` packet and manifest-bound evidence.
- `/Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe`, retained
  raw/finalized source inputs and actual owner code/history.

For actual owner imports, the first43 canary successfully used Python3.10.11 at
`/Users/marcin/agent-work/EdgeMech/pr1871-cleanup-20261119/preserved-worktree-artifacts/payload/.venv310/bin/python`.
The EdgeMech 3.14 environment lacks `kghub_downloader`; owner `.venv-kgm` lacks
the needed downloader API. Check compatibility for this LPSN path rather than
assuming first43 proves every dependency. Preserve failures; no owner environment
may be repaired in place. See the first43 helper/report in the sibling
`content-review-workers-20261119/metatraits` clone for the bounded I/O strategy.

Trace the exact source field, original subject/object identity, selected lookup
and emission branch. Distinguish source coassignment/type assertion from the
semantics of the original mapping relation and the species-versus-strain roles.
Pin the original source row, packet, transformed row, owner code, mapping inputs
and relevant definition/version evidence. Current code or a later source version
must not silently stand in for the original. Unknown historical dirty state
remains an explicit limit.

Implement any required analysis/replay only in
`scripts/adhoc/replay_lpsn_type_link_20261119.py`, written before execution, with
meaningful focused tests in `tests/test_lpsn_type_link_20261119.py`. No inline
analysis programs. Use the actual owner implementation when safely replayable,
never a handwritten copy of its mapping rule. Avoid full dataset transforms,
constructors that write to the owner, and all owner-data mutations. If exact
execution cannot be safely recovered, persist the established source/field
bindings and the precise remaining dependency instead of simulating a pass.

Use a new private `.temp/content-review-20261119/fresh14-<attempt>/` for each
attempt, explicit0700 directories/0600 files and exclusive writes. Free checks
first, then exactly one real source unit through the retained helper. Inspect
and independently re-read its nonempty outputs, original occurrence linkage,
hashes and all qualifiers. Preserve failures and re-canary after fixes. No
further cases or provider sweep. An evidence gap is an acceptable task result
but not a resolved scientific category.

Write REPORT.md in the launcher output directory, separate from final.md. Include
exact commands/interpreters, inspected scope, artifact hashes, what is established
versus missing, original/current version distinctions, and any candidate owner
change that requires separate review. Run focused tests and Ruff; report unrelated
failures without silently fixing them. You may commit only the two named helper
and test files after verification. The coordinator will collect them into the
active PR and push the same day. Include the commit ID in REPORT.md.
