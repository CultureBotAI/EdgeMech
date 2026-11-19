# Bind original results before evidence adjudication

Implementation for [#209](https://github.com/CultureBotAI/EdgeMech/issues/209),
2026-11-19. `scientific_invocation_20261117.py` checks phase-specific launch
inputs; shared review semantics and schemas remain in pinned CLAW. These checks
do not establish semantic correctness, scientific independence, canonical
persistence or a calibration pass.

## Two immutable phase manifests

The initial manifest cannot include matrices that themselves contain its hash.
Keep the original manifest and its files unchanged. After both initial workers
finish, freeze a second manifest for adjudication, retaining the same `round_id`,
cohort, ten case bindings, evidence IDs, source bytes, runtime bytes, roles and
authority versions. The only permitted change to an original file entry is
visibility: original initial instructions become hidden mechanical inputs and
phase-specific instructions become visible. Initial matrices continue to name
the original manifest hash. The new phase manifest pins those original bytes
and every original authored-seal dependency.

The adjudication plan uses `edgemech-scientific-instructions/v2` and
`phase: evidence_adjudication`, with the existing eight plan fields plus
`adjudication`. Blinded initial plans continue to use version 1, with no
`adjudication` field. Initial packages reject phase-result roles, even if their
files are marked hidden. No adjudication input defaults to a historical path.

`adjudication` has exactly these fields:

| Field | Required binding |
| --- | --- |
| `schema` | `edgemech-initial-results-binding/v1` |
| `initial_manifest` | Exact original repository-relative `path` and `sha256`; role `initial_manifest`, hidden |
| `runtime_git_head` | Original full 40-character Git commit, also present in both original launch envelopes, completed worker metadata and every authored review |
| `reviewers` | Exactly two ordered entries with positions `reviewer_a`, `reviewer_b` |
| `comparison` | Exact `path` and `sha256`; role `initial_comparison`, visible; must equal a fresh deterministic `calibration_round_20261116.compare` over the two original matrices in that order |

Each reviewer entry has exactly `position`, `reviewer`, `saved_at`, `matrix`,
`receipt`, `seal`, `invocation`, `metadata`, `identity`, `events` and
`native_session`. Every artifact binding contains exactly `path` and `sha256`.
Paths are relative to the adjudicator clone, preserve the originals' relative
layout, and are explicitly included in the new package manifest.

The complete original reviewer object is preserved, including actual model,
native session ID and historical exposure. It must equal both matrix and receipt
identity; the two IDs, native sessions and original clone roots must be distinct.
`saved_at` must be byte-for-byte identical to the seal and matrix receipt, carry
a timezone, fall within the original worker's start/completion interval, and
precede the new phase freeze. The separate adjudicator uses a new identity and
clone. Same-model agreement still establishes only operational agreement.

## Required retained artifacts

| Binding or dependency | Manifest role | Adjudicator visibility |
| --- | --- | --- |
| Original matrix | `initial_matrix` | Visible |
| Matrix's adjacent `.receipt.json` | `initial_receipt` | Visible |
| Authored initial seal | `initial_seal` | Visible |
| Every seal validation's canonical draft | `initial_authored_review` | Visible |
| Every seal validation's proof sidecar | `initial_proof_sidecar` | Visible |
| Sealing config | `initial_config` | Hidden |
| Original scientific invocation envelope | `initial_invocation` | Hidden |
| Original generated prompt | `initial_prompt` | Hidden |
| Completed launch metadata | `initial_worker_metadata` | Hidden |
| Final observed identity receipt | `initial_worker_identity` | Hidden |
| Final worker events | `initial_worker_events` | Hidden |
| Private snapshot of that native session log | `initial_native_session` | Hidden |
| Original production-readiness receipt and its additional lineage | `initial_readiness` | Hidden |

The original seal is replayed with the existing authored-review/proof validator,
not accepted merely because a matrix and receipt share a hash. All transitive
seal inputs must be pinned. Its canonical drafts must name the original runtime
commit. The original invocation must be a valid blinded plan over the unchanged
original manifest and generated prompt. Launch metadata must show completion,
exit zero, the exact envelope and original clone/output, matching runtime
bindings and unchanged ending Git head.

[Adversarial finding #217](https://github.com/CultureBotAI/EdgeMech/issues/217)
added a separate historical readiness replay. Each original launch envelope must
carry every maintained `run_m5_review_worker_20261116.RUNTIME_KEYS` field, including
the original host, Python executable/prefix/version/hash, installed-distribution
and environment fingerprints, native executable identity and repository origin.
Its launcher and lock hashes must match the original frozen files. Python paths
must belong to the recorded original isolated clone. An arbitrary two-field
runtime object cannot substitute for these bindings.
The actual adjudicator invocation must use that same Git commit, including for
doc-only changes; a matching set of old source hashes cannot waive the commit
binding. Its separate clone/environment still requires its own production
readiness receipt.

The original `production_receipt` must exist and be pinned. Retain its adjacent
metadata and result, named bootstrap artifacts, prompt, all five independent
validator records and stdout/stderr, production spec and execution inventory,
authored production inputs and source dependencies, and saved canonical
YAML/Markdown pair. The receipt, metadata and result must agree on successful
same-clone production scope and runtime; canary completion must precede that
initial worker. Both the initial worker's entry and exit replay must bind this
same receipt and production spec/output. Validator commands must equal the
maintained commands under the original clone/interpreter, and production
validator JSON must equal current read-only replay of those retained bytes.

This check preserves original absolute clone paths in the receipts and interprets
them only to locate their byte-identical retained copies. It never executes an
old command, interpreter, credential or binary, and never claims the adjudicator
clone has the old runtime environment. Runtime/environment fingerprints are
recorded observations whose consistency is checked; they are not independent
hardware attestation. Missing original lineage blocks adjudication and is not
replaced by the adjudicator's own fresh canary. Additional copies stay private;
existing pinned source files retain their original evidence roles/visibility.

After each initial worker exits, run the maintained own-session identity helper
against its final `events.jsonl`, retaining the resulting JSON and a private
snapshot of the exact native-session log it identified. The phase checker reads
only event identity fields: the worker thread UUID, native session metadata ID
and observed model must agree with the original reviewer identity. Both final
log hashes must match the identity receipt. A receipt captured while the worker
was still writing its logs must be finalized before freezing; do not silently
rewrite a previously frozen receipt. Native logs and article/source bodies
remain private and are never committed or exposed as scientific navigation.

The adjudicator's `read_paths` equals the initial evidence navigation with its
initial instruction templates removed, plus the visible original results,
authored drafts and proofs, and the new phase instruction templates. Extra
coordinator history, prior-round ratings, original prompts and native logs are
rejected. The generated prompt exposes the two original identities, timestamps,
matrix/receipt/seal pins and comparison, and explicitly requires auditing
agreements as well as disagreements without changing either original seal.

## Execution and limits

1. Finish and preserve both initial sessions. A failed or incomplete initial
   launch is an explicit blocker; it is not relabeled completed to permit this
   phase. Preserve scientific failures even when transport succeeded.
2. Collect unchanged originals into a fresh adjudicator clone at the frozen
   runtime. Freeze the separate phase package with the bindings above. Replay
   the original seals and comparison before invoking an agent.
3. Run the production save/readback canary in this actual clone against this
   phase package. Earlier clone/package receipts do not transfer automatically.
4. Prepare the normal per-clone invocation envelope with the version 2 plan.
   Use the launcher's `--plan`, then the authorized fresh worker launch. Entry
   and exit checks replay all phase bindings. Test one final canonical draft
   and readback through the real path before the remaining final cases.
5. Preserve final assessments and all original unsupported labels, missing
   slots, failed gates and unresolved disagreements. Existing numerical
   thresholds and expansion decisions remain separate mandatory checks.

Final scientific authoring, evidence replay and scoring use the unchanged
`initial_manifest` named in the typed binding. The later adjudication manifest
is the launch/input envelope: it binds the original results without replacing
the original scientific package hash inside matrices or proofs. Phase templates
must make this distinction explicit. Any helper that only accepts the phase
manifest as a replacement scientific package is a tooling blocker.

The helper does not define a new final adjudication output schema, implement an
adjudication algorithm, certify useful evidence or launch another round by
itself. Phase-specific final authoring/scoring helpers must be independently
reviewed, pinned and referenced by the phase templates; missing tooling blocks
execution. Historical round03 lacks this new invocation provenance and remains
historical. Rejection of that old package is a negative engineering canary, not
a successful live adjudication or a repair of round03.

Focused tests exercise two genuine synthetic ten-case authored seals and reject
missing reviewers, swapped identities/order, changed timestamps/commit,
unbound seal dependencies, modified comparisons, incomplete worker metadata,
wrong observed identity, missing native logs and reused initial clones. These
also reject missing/substituted readiness receipts, incomplete runtimes, wrong
frozen launcher/lock identities, another clone's Python paths, unbound canonical
output, forged validator commands and rehashed false validator output. The
positive fixture actually saves and replays canonical YAML/Markdown with the
shared implementation; its recorded native execution/environment observations
are explicitly synthetic. These are deterministic contract tests, not scientific
ratings or live M5 acceptance.
