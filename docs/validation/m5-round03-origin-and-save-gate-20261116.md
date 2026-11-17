# Canonical origin and same-clone save readiness — 2026-11-16

Issue #176 exposed a gap between a successful preparation replay and a working
canonical save. Both round02 reviewer clones had filesystem origins; pinned
CLAW requires an explicit GitHub repository identity. The original clones,
failed attempts, zero-pair accounting and scientific ratings remain unchanged.

The launcher now uses pinned CLAW's `repository_identity` before a child starts
and requires `CultureBotAI/EdgeMech`. Its v3 provenance binds both that parsed
identity and the exact origin URL. Local origins, another GitHub repository,
and an origin change after a canary all fail before follow-on execution.
Old v2 receipts remain historical and cannot authorize the new runtime.

## Two distinct capabilities

An ordinary `--role canary` still proves only operational bootstrap: current
runtime contracts and exact fresh47 preparation replay. A `calibration`
coordinator or `release` worker can use that receipt; it never certifies a
scientific reviewer or a successful canonical save.

A production canary additionally specifies `--production-review`,
`--production-packet`, `--production-proofs` and `--package-manifest`, all relative
to the intended reviewer clone. Before starting its child, the parent pins the
authored inputs, invokes the existing complete round verifier, validates the
actual occurrence-review input, and requires the intended canonical target to
be absent. The selected packet must belong to the frozen cohort.

After the operational replay child completes, the parent executes the actual
`edgemech.occurrence_review save` and `check` commands using the same interpreter,
environment and clone. It inspects both canonical files through the shared
bundle reader, compares the complete persisted document with the authored
input, and binds input/output hashes plus the package and absolute clone root.
An agent's success statement or a pre-existing pair cannot substitute for this.

`--role reviewer` requires that distinct production receipt and the current
`--package-manifest`. It replays the entire package's referenced input pins,
current production inputs, both saved files and the occurrence-profile check.
Receipts cannot move between clones, even when their heads and origins match.
Reviewer completion repeats the runtime/origin checks and the complete
same-clone production receipt/package replay (#187). A zero child exit code
cannot mark a reviewer completed after its head, tracked runtime, native/helper
binary, Python environment, origin, evidence package, input or saved pair drifted.
The failure retains the child's logs and outputs for inspection.

The production receipt also inventories execution files below `scripts/` and
`src/`, including hidden and Git-ignored files. Added or changed helpers in that
bounded scope fail the reviewer gate; new review/proof data remains allowed.
Reviewer helpers must be reviewed and frozen before the canary. This is not an
audit of arbitrary inline execution or helpers outside those directories; the
reviewer instructions separately prohibit creating or executing such new code.
The receipt's capability remains execution readiness, never calibration passage,
independent assessment or graph admission. Operational fixtures are excluded
from the scientific matrices and expected canonical-pair denominator.

## Required order for a new round

1. Create fresh reviewer clones. Set and verify each canonical origin before
   freezing anything. Do not edit origins or outputs in retained old rounds.
2. Copy the prepared inputs and freeze the immutable scientific package under
   the reviewed runtime. Verify all pins in each actual reviewer clone.
3. Prepare a separately identified, conservative operational review using one
   packet from that package. Keep its input, output and execution receipt outside
   the immutable scientific package, avoiding a hash cycle.
4. In **each** intended reviewer clone, run the production canary through the
   same durable launcher/shell/environment used for its later reviewer. Use
   `scripts/adhoc/m5_review_20261116/replay-canary.md` for this seeded path; it
   must not re-prepare inputs or require an empty preparation directory.
5. Inspect the independently verified receipt and saved pair, then start that
   clone's fresh session with `--role reviewer`. Do not use `calibration` as a
   substitute for this gate. Seal all new scientific evidence bindings before
   comparison; readiness does not fix failed agreement or resolution gates.

The production flags supplement the ordinary launcher arguments:

```bash
# First use --plan; then --run through the intended tmux launch path.
--role canary \
--prompt scripts/adhoc/m5_review_20261116/replay-canary.md \
--production-review .temp/round03-save-canary/review.json \
--production-packet .temp/round03/cases/fresh-47/packet.json \
--production-proofs .temp/round03-save-canary/proofs.json \
--package-manifest .temp/round03/manifest.json

# Fresh reviewer in that same clone and runtime, after the canary passes.
--role reviewer \
--canary-receipt /absolute/reviewer/root/.temp/save-canary-run/canary-receipt.json \
--package-manifest .temp/round03/manifest.json
```

`--production-receipt` is an alias for `--canary-receipt`. An operational-only
receipt is rejected for `reviewer`. Changes to origin, runtime, package, authored
input, evidence pins or saved pair require a new canary; preserving a failed
attempt means choosing a new output directory and operational review ID.

## Verification boundary

Focused tests exercise the real shared Git-origin parser, the actual occurrence
save/check CLI and shared bundle readback, plus negative origin, capability,
cross-clone, changed-input, changed-output and package-verifier cases. Reviewer
exit tests mutate origin, head, tracked code, package/source bytes and hidden
ignored helper code; each preserves failed output rather than claiming completion.
An unchanged reviewer records its successful end replay. Existing
round tests own the package verifier's scientific input contract. A real M5
same-clone production canary remains required before reviewer fan-out; synthetic
test fixtures do not replace it.
