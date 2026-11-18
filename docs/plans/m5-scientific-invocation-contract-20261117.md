# Future scientific invocation contract

Issue #203 separates engineering readiness from the instructions for a future
scientific session. This contract adds coherence checks; it grants no scientific
approval, evidence-sufficiency finding, threshold change or authority to start a
replacement calibration. Completed rounds and their v3 projections remain intact.

`calibration_round_20261116.py freeze` accepts an optional `package_purpose` in its
config. New engineering packages use `engineering_prerequisites`. A separately
reviewed future scientific package uses `scientific_calibration_candidate`.
Legacy packages remain replayable; neither a legacy purpose nor an engineering
purpose can prepare or launch a new scientific invocation.

## Package-pinned instruction plan

Add one JSON file with role `scientific_instructions` to the package. It contains
exactly these fields:

```json
{
  "schema": "edgemech-scientific-instructions/v1",
  "purpose": "scientific_calibration_candidate",
  "round_id": "THE-NEW-PACKAGE-ID",
  "manifest_path": ".temp/NEW-PACKAGE/manifest.json",
  "phase": "blinded_initial_review",
  "instruction_paths": [".temp/NEW-PACKAGE/instructions.json"],
  "read_paths": ["artifacts/edge-calibration-20261115/protocol.json"],
  "sessions": [{
    "reviewer_id": "reviewer-a",
    "workdir": "/ABSOLUTE/NEW-CLONE-A",
    "session_root": "/ABSOLUTE/NEW-CLONE-A/.temp/NEW-SESSION",
    "output_root": "/ABSOLUTE/NEW-CLONE-A/.temp/NEW-SESSION/worker"
  }]
}
```

This is a shape example, not a runnable package. Complete `read_paths` with every
reviewer-facing instruction, case view and evidence path. It must equal the set
of pins marked `visibility: reviewer`, plus the original protocol. Original
packets remain mechanical replay inputs. Each case's evidence IDs must resolve
uniquely to allowed evidence or its original packet. Every instruction path must
be an allowed pin of role `instructions`. Pin the invocation helper and the full
execution/runtime inventory. Existing package replay validates the original
occurrences, endpoint identities, packet inputs and pinned file bytes.

Sessions have distinct clone roots and nonoverlapping, absent session roots. The
worker output is an immediate child of its session root. A fresh output directory
inside a completed session does not constitute a fresh session. The native worker
uses a new `codex exec`, never a resume. Only `blinded_initial_review` is supported.
Issue #209 records why `evidence_adjudication` is rejected: it needs a separately
reviewed typed binding for initial matrices, seals and comparison results before
any prompt can require those inputs. This helper does not establish readiness for
a complete scientific round. Historical adjudication tooling is unchanged, and
no default old scoring roots exist in this new contract.

## Instruction templates

Scientific instruction assets use this JSON format, not historical launch prose:

```json
{
  "schema": "edgemech-scientific-instruction-template/v1",
  "text": "Use package {{round_id}} at {{manifest_path}}. Work under {{output_root}}."
}
```

Supported placeholders are `manifest_path`, `round_id`, `workdir`, `session_root`,
`output_root`, and `reviewer_id`. The helper renders them from the verified plan
and current invocation. Templates cannot contain literal slash or backslash path
expressions or reserved invocation output filenames. Spell out ambiguous prose
such as “save and check”; use placeholders for paths. This conservative constraint
applies to executable instruction templates, not source evidence or quotations.
It rejects the real old round03 launch instructions even if their new file hashes
are correctly pinned. Shared semantic prose must be carried faithfully into a
reviewed template; this helper does not decide scientific semantics.

## Per-clone preparation and launch

After the future package and runtime are reviewed/frozen, run exactly one real
production save/readback canary in each actual new reviewer clone. Its receipt is
an operational prerequisite only. Preparing the invocation is read-only with
respect to package inputs and writes exclusive JSON/prompt artifacts outside the
fresh session root:

```sh
python -B scripts/adhoc/scientific_invocation_20261117.py \
  --root /ABSOLUTE/NEW-CLONE-A \
  --manifest .temp/NEW-PACKAGE/manifest.json \
  --instruction-plan .temp/NEW-PACKAGE/scientific-plan.json \
  --reviewer-id reviewer-a \
  --production-receipt .temp/NEW-CANARY/canary-receipt.json \
  --output .temp/invocations/reviewer-a.json
```

The envelope binds manifest ID/path/hash, instruction-plan hash, actual runtime,
same-clone canary receipt, planned clone/session/output paths and generated prompt.
Use `--scientific-invocation .temp/invocations/reviewer-a.json` with launcher role
`reviewer`, the exact manifest, receipt and output root, and prompt
`.temp/invocations/reviewer-a.json.prompt.md`. First use the launcher's `--plan`.
It does not create a session or load credentials. Scientific execution still
requires the user's authorization for that new work.

A real launch exclusively reserves the session before starting its child and
records the contract in worker metadata. Failure preserves the reservation.
Package, runtime, receipt, prompt and session marker are checked again at exit;
drift cannot produce completed status. Scientific invocations cannot add extra
writable directories. Frozen historical receipt verification stays unchanged.

The v4 case-view helper is `prepare_m5_future_views_20261117.py`. Historical v3
replay remains unchanged. For the exact inspected mixed process description,
v4 removes only three historical review-status tokens and retains the original
definition, scope limitations and version/provenance caveats. The complete source
field hash, omitted UTF-8 byte spans and retained-span hashes bind that change.
Changed source text requires new content inspection. Preserving the original
meaning is not independent confirmation of that meaning or of the generating
source version. Other source fields remain unchanged. External producer-text
omissions still require their separate content-reviewed bounded receipts; code
status alone does not justify retaining evaluation prose.
