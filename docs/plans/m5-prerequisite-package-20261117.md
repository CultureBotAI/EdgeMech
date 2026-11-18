# M5 prerequisite package and actual-environment checks

This engineering procedure addresses #203, #205 and #206, with independent
review fixes #207 and #208. It does not start another calibration or replace
the failed round03 result. The scientific invocation contract additionally
rejects adjudication until its initial matrices, seals and comparison have a
reviewed typed binding (#209).

## Inputs and boundaries

Use `prepare_m5_prerequisite_package_20261117.py` in a freshly provisioned clone
at the exact committed candidate runtime. The retained source is M5's
`m5-calibration-round03-20261116` worktree. The repaired engineering manifest is
`.temp/m5-round03-worker-20261116/publication-runtime-02/manifest.json`, SHA256
`1e0ad8f7dea88d5138d891341d46ac772f8a7896f0282ee11ddaf2b0686fd168`.
Its conservative operational specification is
`.temp/m5-round03-worker-20261116/engineering-operational-canary-spec-02.json`,
SHA256 `3321872d3bb7685836b46d0d799973ffb17335ea6b78a5783bf63c941a7c1e32`.
Also supply `--bootstrap-receipt-sha256
894a803fc18fdf66e715884f51a899fdb5ba5107cec3ad13b237c9c9e369f7af`.
This binds the original `fresh-47/receipt.json` outside the retained manifest.
Its original timestamp and bytes stay unchanged; it is not a new runtime/save
receipt. Configuration equality and the maintained preparation checker are
required before it can be reused for byte replay.

The helper checks both exact input hashes before staging. Retained evidence,
source packets, original records and bounded-view receipts retain their exact
bytes and case/evidence identities. Current tracked runtime files receive new
pins, with old/new identities recorded in a transition ledger. Historical
scientific instructions are excluded from instruction roles. The only active
instruction is the operational replay canary. New v4 case views have distinct
paths; their inclusion does not itself establish blinding or scientific readiness.

Every maintained execution input, including hidden/ignored executable helpers,
is pinned using the launcher's inventory. The original cohort, protocol,
thresholds, schema and shared contract remain bound. The new neutral procedure,
coordinator witness map and setup audit may be supplied with repeated
`--prerequisite-document`; they receive coordinator-only visibility here.

All destinations must be new and private under Git-ignored `.temp`. Metadata,
documents, canonical review destination and source pins are checked before
copying. The helper replays planned evidence hashes, document pins, execution
inventory, HEAD and clean tracked state around freezing and authoring. It
preserves failed attempts rather than overwriting them or emitting success.
The bootstrap quartet is copied at mode 0600 inside a 0700 case directory, as
required by the real checker; other sealed package inputs retain their existing
mode policy. The actual free `prepare_calibration_20261115.py --check fresh-47`
must pass before freezing succeeds. It also reads the retained private source
archive on M5, verifies its expected upstream hashes, and leaves it unchanged.
The public fresh-canary projection is explicitly pinned. This addition fixes
the first actual native-worker failure (#212), which remains preserved.

## Execution sequence

1. Provision exactly one fresh M5 reviewer clone with the maintained setup
   helper. Inspect its on-disk receipt, origin, revision and isolated environment.
2. Run package preparation with `--plan`, then the identical arguments and
   `--run`. Supply the source root/manifest/hash and operational spec/hash above;
   the bootstrap receipt hash, a new `--output`, `--package-id`, UTC `--timestamp` and matching timestamped
   `--review-id` are required. Inspect the persisted preparation receipt.
3. Use the maintained worker launcher with role `canary`, the new manifest,
   `operational/review.json`, `operational/proofs.json`, the original fresh-47
   packet, and `scripts/adhoc/m5_review_20261116/replay-canary.md`. First plan,
   then run through the actual native Codex launcher with a new output root.
4. Inspect the actual canonical YAML/Markdown pair, its exact hashes and the
   parent production save/check validators. Confirm the receipt identifies this
   clone, runtime and manifest. A child success message alone is insufficient.
5. Only after that whole unit passes, provision and check a second fresh clone
   through the same path. A changed runtime or failed canary requires a new
   verified canary before any further fanout.

The operational fixture stays `scientific_review: false`, `not_assessed`, with
all six axes unresolved. It is outside scientific matrices, canonical scientific
pair denominators and graph admission. A new engineering manifest explicitly
uses `package_purpose: engineering_prerequisites`; the scientific invocation
contract rejects it even when all production checks pass.

## What remains scientific work

This freezes complete **available byte bindings**, not missing original
witnesses. The coordinator witness map names the unresolved source selection,
identity, field meaning, units, bin interpretation and version dependencies.
The bounded MetaTraits mapping/polarity replay is a concrete next recovery task.
No new literature service, primary full-paper inspection, scientific rating,
graph release or expansion is part of these operational checks. Retained-90
and 9,900 remain gated on an independently evaluated successful calibration.

Live results belong in a separate validation record naming the actual runtime
and receipts. A later documentation commit does not retroactively change a
frozen clone's runtime or make its receipt valid for another commit.
