# Pinned source restoration preparation

The recovered census refers to an original source snapshot whose historical
directory is absent locally. Its source members have been recovered privately.
The maintained census verifier requires the original binding; changing the frozen
manifest to point elsewhere would change the evidence being verified.

The new [restoration helper](../../scripts/adhoc/restore_restart_source_20261120.py)
resolves EdgeMech through RepositorySettings and the non-Mech KG-Microbe source
owner through the maintained corpus resolver and exact-origin validator. Its
read-only plan independently passed all three source members' original hashes,
byte counts, row counts, header and selected-prefix checks. Their combined size
is 3,267,015,185 bytes. The [public digest mapping](../../scripts/adhoc/provenance/restart-source-20261120/plan-summary.json)
binds both retained plan versions without exposing private operational paths.

Live restoration remains separate and unexecuted at this checkpoint. It requires
independent final review, complete validation, a reviewed PR and exact published
head. The apply path refuses any existing destination, checks source-owner state
again under a short lease, and preserves failed reservations. It copies the
verified members through guarded regular-file reads and checks persisted bytes.
The original manifest is written under a pending name, flushed and hash-checked;
directory flushes precede an atomic, non-replacing publication. No source host,
provider, native worker or prompt is invoked by this helper.

Independent review identified two defects before live apply, recorded in
[#231](https://github.com/CultureBotAI/EdgeMech/issues/231): a direct manifest
write could expose a partial completion marker, and a replaced FIFO could block
a plain input read while the metadata lease was held. The repaired version uses
atomic publication and the maintained no-follow/nonblocking regular-file reader
for source and persisted inputs. The original executed read-only plan helper
and receipt remain privately unchanged under the provenance policy in
[#228](https://github.com/CultureBotAI/EdgeMech/issues/228).

Sixteen offline tests cover partial marker writes, fsync and directory-flush
failure, concurrent markers, changed bytes, existing/symlink destinations,
nonregular source and readback, lock refusal, changed source-owner state, and
context release after copy failure. Fresh-process regression runs against the
retained pre-fix bytes are private evidence; they never invoke a live restoration.
Complete-suite and final-review results accompany the exact PR candidate.

Restored transport bytes would still require full maintained census replay,
exact occurrence accounting and exhaustive prior-assessment reconciliation.
Scientific coverage remains zero and A/B counts remain unresolved.
