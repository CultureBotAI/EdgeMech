# Content-review implementation on M5 — 2026-11-19

This is the execution record for the upgraded
[content-review plan](../plans/content-review-20261109.md) and plan finding
[#213](https://github.com/CultureBotAI/EdgeMech/issues/213).

## Starting state and dispatch

Implementation branch: `implement/content-review-20261119`, based on reviewed,
unmerged PR #211 at `27be00ddc57688b3e9edbca60175a84aba91961c`. Main remains
`f841b1dff874e78d1a14075413be6a92c90f1378`. PRs #211/#190/#167/#150 and shared
CLAW #1289 remain open; the protected full-text helper PR #102 remains open.
No merge has been performed or newly authorized.

Read-only M5 inspection found the current EdgeMech pane at default tmux
`mechs:16.0`, pane41, linked into `mechs-view-EdgeMech`; it was at an empty Codex
prompt. The old `edgemech` tmux socket is absent. Other M5 jobs are active, so
the historical claim of 32 idle panes is not a capacity measurement. Existing panes
and their histories are preserved. Dedicated new helper sessions are used.

The installed `codex-work` wrapper selects the existing work account and native
Codex executable. Its wrapper is sourced directly; unrelated shell initialization
and credential files are not printed. No model override is requested. Actual
worker identity/settings must come from retained native execution metadata.

The first assigned M5 helper is the bounded **first43** MetaTraits source replay.
Its tracked [task](../../scripts/adhoc/content_review_20261119/metatraits-first43.md)
limits it to one occurrence and prohibits scientific ratings, historical edits,
graph expansion and provider calls. First28 was assigned after the first actual
owner replay and its persisted receipt passed independent inspection.

Typed adjudication inputs for #209 were implemented in parallel. Helper workers
may inspect historical outcomes; they are not eligible as fresh blinded reviewers.

## Results

### First43 completed and independently inspected

The first native helper ran in dedicated tmux session `edgemech-helper-first43`
from runtime `700e5c2` in
`/Users/marcin/agent-work/EdgeMech/content-review-workers-20261119/metatraits`.
Its observed session was `01a1f57d-0a82-7c91-a6c2-cae9cb23a632`, model
`gpt-6-astra`, reasoning `ultra`, using existing work-account defaults. No model
override or provider-credential transfer was supplied by this launcher.

The worker committed `6288103ac63b7185458bc3bdff432dff965e32d6`; the identical
helper/test change was collected into the active branch as `621a613`.
The actual source helper SHA256 is
`a803a16f642b5fd17d7a482e48da75fca769664331d3bdb7836015fbe6d006d8`.
Its actual owner execution used the discovered preserved Python 3.10.11
environment, separately from the helper session's isolated EdgeMech Python 3.14.7
environment. Those distinct roles must not be conflated.

The pinned actual owner loader and complete `_process_single_file` Tier1 method
emitted exactly one original occurrence: positive `biolink:capable_of`, relation
`RO:0002215`, with `has_percentage=0.0`. The exact source nitrogen-fixation summary
is a negative aggregate with ten observations/two databases. No fallback polarity
routine executed. Every original field agrees after the explicitly documented
empty-column normalization; raw TSV byte identity is **not** claimed.

The [source-witness report](metatraits-source-witnesses-20261119.md) records the
interpretation and limits. Separate read-only inspection verified all 31 artifact
hashes, all 17 current owner pins, historical packet copies and producer Git
baselines. Neither taxonomy seeded from the frozen node nor the historical
dirty-build/template consumption was independently reconstructed.

| Retained first43 artifact | SHA256 |
| --- | --- |
| Source replay `first43-canary01/receipt.json` | `5144dfe483f0b56ac7f7710961ee5dd9d6caae721f1dc5570c87844390005f24` |
| Emitted raw edge TSV | `a2b2ffae1aab3535e239c47b81f4e8e493ca63878b62cc02656c9b509911b459` |
| Separate source readback JSON | `3c8cde9072868c0a7211614b401967d35d9076939529363870ab0ca79b4560c7` |
| Native `completion.json` | `66ed794d1bedf3add3b5a85fd9c98e95e2d31b4143ee3eaf270eab65b56571a7` |
| Native `REPORT.md` | `3c389095560f5439bccdc444b8dab96f0c8ad7182c79d10a6d9fad4aa33850ad` |
| Native `events.jsonl` | `f21b34489601d8ae168c1bf2e7d380cf97a7729a7d9c11b16234aac1a8812e44` |

Source artifacts are under that clone's
`.temp/content-review-20261119/first43-canary01`; native outputs are under
`.temp/helper-workers-20261119/first43`. Parent `check` replay passed before any
follow-up native worker started. The completed clone remains at its original
ending commit. Its changed HEAD prevents reuse of the starting-runtime canary
as authorization for later work.

The final worker suite passed **1,386 tests**, 23 focused source tests and Ruff.
This suite covers its `700e5c2` base plus the source helper; it does not cover the
later adjudication integration. Earlier setup attempts are retained: missing
owner dependencies, an incidental cache write, Python 3.10 I/O adaptation and
header discovery. The first broad suite used a disallowed full-text staging
path; the second omitted its new parent directory. Both failed runs remain
recorded. A fresh correctly prepared `.temp/fulltext/.../final03` passed. None
of these failures was reclassified as a successful scientific run.

### Adjudication contract and literature

[#209](https://github.com/CultureBotAI/EdgeMech/issues/209) now has typed original
matrices/seals/comparison and complete retained readiness/runtime lineage, with
independent review repair [#217](https://github.com/CultureBotAI/EdgeMech/issues/217).
All 46 final focused tests passed. Exact-runtime
[CI at `8b4f9ea`](https://github.com/CultureBotAI/EdgeMech/actions/runs/44611302317)
passed 1,415 tests, 16 contracts, Ruff and both builds. This verifies
implementation and synthetic fixtures, not a live M5 scientific adjudication.
Original authoring/scoring remains bound to the initial scientific manifest;
the later phase manifest binds adjudicator launch inputs.

Separate review found and repaired the new prompt's persistence conflict in
[#219](https://github.com/CultureBotAI/EdgeMech/issues/219), commit `972b804`.
Final adjudication validates ten separate drafts/proofs and 60 final axes;
the registered canonical denominator remains the 20 initial pairs. The
adjudicator's actual environment still needs its own production canary. Three
focused policy/finalizer tests and independent read-only re-review passed.

The [fresh05 access report](fresh05-access-20261119.md) records actual coordinator
Valency metadata discovery, failed Tavily/direct-body attempts and a retained
public body-text extraction. No original PDF/publisher full body or figure pixels
were retained/inspected. No licensed full-text or M5 library-service success is
claimed, and no source-row identity or scientific judgment was changed.

### Follow-up dispatch

After the completed first helper and independent inspection, a read-only M5
resource check reported 48 GiB physical memory, 82% system-wide memory free, zero
swap use and 173 GiB disk available. This is a momentary capacity observation,
not a measured peak-RSS guarantee or justification for 32 workers. Concurrency
is limited to two new bounded helper sessions.

Two fresh clones were provisioned successfully at `621a613` (six setup steps,
isolated Python 3.14.7 and 16 contract checks each), then advanced only to committed
task-note revision `8b4f9ea` before launch. Their provisioning receipts remain
unchanged; each new native plan binds its actual new HEAD and environment.

| Helper | M5 clone beneath `content-review-workers-20261119` | Branch / owned tmux session | State |
| --- | --- | --- | --- |
| first28 | `metatraits-followup` | `work/metatraits-first28-20261119` / `edgemech-helper-first28` | Completed at `ad6f9ab`; collected as `9ee7afb`. New first43 replay/readback preceded first28. Conditional GTDB mapping/emission witness; source-field and original identity-selection limits remain. |
| fresh14 | `lpsn-fresh14` | `work/lpsn-fresh14-20261119` / `edgemech-helper-fresh14` | Completed at `40068d2`; collected as `d809284`. Actual type-field emission reproduced; original historical TSV row/build linkage remains unresolved. |

Both use committed tasks and the same reviewed `codex-work` launcher/native
binary. They have separate code/output roots and may inspect historical evidence;
they are not blinded scientific reviewers. Both native parent checks passed,
and both reports and source artifacts received independent read-only inspection.
An early fresh14 check rejected absent completion while the worker was still
finishing; its later completed run passed. The original clones remain at their
recorded ending commits, with all attempts and private evidence preserved.

Both used observed `gpt-6-astra` / `ultra` defaults. First28 native session:
`01a1f58c-1fa9-71e1-a42d-b333bbf9f6cf`; fresh14:
`01a1f58c-3e56-7152-afae-6c10a5c05b62`.

| Retained native artifact | SHA256 |
| --- | --- |
| first28 `REPORT.md` | `7fbec0ff053dfef9deaeed38a88e6ee564906540aad03a01ab354e9bd4a90a48` |
| first28 `completion.json` | `512014ed202d0cc1294ff56c5cb211dfd9ed83fd5dff135baeb82b2ca1e9fb14` |
| fresh14 `REPORT.md` | `cef13f728a315d78d8815120ad99e6f7085aee7bc4b5db9f24dc3f703bfbeb9a` |
| fresh14 `completion.json` | `a6def428c4bb6dee8f9c41df627a78d4826cb223c2ebc2cdbaaa7bb2ac419506` |

Each is beneath its clone's `.temp/helper-workers-20261119/CASE/`. Private exact
copies were saved and hash-checked in the coordinator's
`.temp/m5-source-witnesses-20261119/CASE/`. Native receipts and source-replay
receipts are distinct files with distinct roles.

First28 passed 39 focused tests and **1,431 full-suite tests** in 195.36 seconds.
Fresh14 passed 21 focused tests and **1,436 full-suite tests** in 195.60 seconds.
Both passed Ruff. These are their separate committed runtimes, not a claim that
the later combined branch was tested by either run. Scientific limitations are
in the [MetaTraits](metatraits-source-witnesses-20261119.md) and
[LPSN](lpsn-type-source-witness-20261119.md) coordinator reports.

First28's independent review found
[#221](https://github.com/CultureBotAI/EdgeMech/issues/221): unavailable runtime
or owner inputs could make failure diagnostics fail before persisting the original
error. Re-review found the first repair used an exception-note API unavailable
on the actual Python 3.10 owner runtime (#222). Both repairs passed 54 focused
tests and separate read-only re-review before commit `131669b` was pushed.

A fresh `metatraits-repair-221` clone was provisioned at `131669b` with all six
setup steps and 16 contracts passing. Four synthetic failure-path scenarios then
passed under actual Python 3.10.11, independently inspected without rerunning
the checks. Both free source plans passed; the committed common shell driver
then ran first43, its separate readback and direct emitted-row inspection before
first28. The latter replay/readback also passed. Both emitted edge files match
their earlier successful versions byte-for-byte. The final source helper and
driver hashes, new receipts and precise retained paths are in the
[MetaTraits report](metatraits-source-witnesses-20261119.md#failure-record-repairs-and-fresh-m5-re-canaries).
These are bounded coordinator-run offline source checks, separate from native
worker completion and from scientific reviewer readiness.
Separate read-only inspection verified all 67 new source artifacts, 22 distinct
owner input/code pins, the unchanged before/after runtime inventory, and the
required first43-readback-before-first28 ordering. Private receipt/readback and
smoke-result copies were retained locally and hash-checked.

Combined-code validation is recorded by
[CI at `131669b`](https://github.com/CultureBotAI/EdgeMech/actions/runs/44614234147).
[PR #214](https://github.com/CultureBotAI/EdgeMech/pull/214) carries subsequent
document-only commit checks. The separate native-worker suite counts above
must not be substituted for the combined-candidate checks.

The concrete next-package work is recorded in
[#220](https://github.com/CultureBotAI/EdgeMech/issues/220) and the plan's W5
checklist. Old round03 lacks the new invocation lineage; the November17 package
is engineering-only. Neither may be retroactively accepted as a positive #209
scientific replay. Distinct relative reviewer namespaces, neutral templates,
new evidence dispositions and fresh same-clone canaries are required.

No new scientific round, retained-90 reassessment, 9,900 expansion or graph-release
verification is claimed.
