# Prerequisite adversarial review — 2026-11-17

The implementation was reviewed in separate read-only passes. Reviewers did not
edit files or overwrite outputs while reviewing. Each material finding was
filed before remediation. All old scientific artifacts and historical v3
projections remain unchanged.

| Finding | Resolution in this candidate |
| --- | --- |
| #203: a manifest/receipt can be valid while scientific instructions refer to a different package or completed session | Generate instructions from a package-pinned structured plan and constrained templates; bind the actual runtime, receipt, clone and fresh session; reject legacy/engineering packages, stale prompts and reused sessions. |
| #205: direct semantic comparison versus trace-dependent fidelity was underspecified | Add a neutral dependency-based decision procedure and a coordinator-only ten-case witness map. Preserve all historical ratings and distinguish missing evidence from contradiction. |
| #206: corrected clone setup was manual | Add canonical-origin, exact-commit, isolated-environment provisioning with persisted non-authorizing receipts and preserved failures. |
| #207: invalid output/metadata could fail after evidence copying | Require new private ignored output, valid metadata, prerequisite documents and unused canonical target before staging. Negative tests cover no-write rejection. |
| #208: planned tracked evidence/runtime could drift before freeze recomputed hashes | Replay planned input/document hashes, complete execution inventory, HEAD and clean tracked state before and after freeze and after authoring. Drift prevents a success receipt. |
| #209: adjudication accepted a plan without bound initial results | Reject that phase at validation and prompt generation. A typed initial-matrix/seal/comparison contract remains necessary before a complete future round. |
| #210: whole-field blinding omitted substantive process meaning while claiming definitions were retained | Restore the exact mixed definition except three separable review-status tokens; retain scope/version limitations and provenance with original hashes and bounded byte-span records. |
| #212: first native canary lacked its bootstrap receipt and required seed modes | Bind the unchanged historical receipt and full bootstrap inputs, preserve 0600 files/0700 case directory, and run the actual maintained bootstrap checker before any native worker. Preserve the failed clone and re-canary a new runtime before fanout. |

Independent re-review found #207/#208 corrected and no additional material
defect in the provisioning path or #203/#209 invocation/launcher integration.
The #210 re-review directly compared the actual private original and persisted
view: all 778 substantive bytes remain, 27 review-status bytes are omitted, and
the original/view/helper hashes match the receipt. Final tests are recorded
separately with the actual runtime before live results are claimed. Focused tests
include actual production save/check, rejection of stale instruction assets,
fresh-session enforcement, drift, private output and mixed-field retention.

These checks establish engineering behavior and honest limits. No reviewer
agreement, scientific resolution, independent full-paper inspection or graph
admission follows from them. Live setup and production canaries require actual
same-clone execution; test stubs and coordinator receipts are insufficient.
