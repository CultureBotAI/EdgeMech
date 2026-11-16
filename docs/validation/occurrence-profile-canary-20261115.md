# Occurrence profile: first retained-edge canary

Executed 2026-11-15 America/Los_Angeles (2026-11-16T02:50:24Z), using
`scripts/adhoc/run_occurrence_canary_20261115.py` with the pinned EdgeMech Python
environment. `--plan` verified the two retained input hashes and primary article
identity without writing artifacts. The same launcher then ran exactly one real
unit, saved a canonical review, reread it, replayed all private inputs and verified
the persisted receipt. No batch was started.

[Canonical review](../../reviews/structured/20261116T025024Z-edge47-occurrence-profile/review.md)
records the exact occurrence, both endpoint records, original source-value scope,
DOI-bound short quotation, findings and maintained-owner actions.

| Axis | Result |
| --- | --- |
| Claim | NOT_ASSESSABLE: original reported-value meaning must not silently become a species-wide growth assertion |
| Literature | PARTIAL: retained primary paper concerns another isolate and two salt concentrations |
| Relation | UNRESOLVED pending versioned modeling authorities |
| Subject node | UNRESOLVED pending full identity/category model assessment |
| Object node | UNRESOLVED pending full attribute model/category assessment |
| Source fidelity | SUPPORTED: exact retained source binds NaCl, 0-10, %, growth, positive, strain and reference |

The receipt records two replayed evidence items, one verified quotation, zero
provider calls, zero KG admissions and disabled native capability. The raw paper
and source packet remain private in `.temp/occurrence-canary-edge47-20261115/`.
The public review contains hashes and locators. The source percentage basis and
assay conditions remain unspecified; the paper's conditions are not copied into
the source observation.

The canary proves the single-unit persistence/replay path and explicit unresolved
states. It does not establish reviewer agreement, complete ontology validation,
a corrected graph, behavior under concurrent workers, or coverage beyond this
already retained occurrence. The ten-case calibration selection/thresholds and
the real correction-verification demonstration remain pending.

The first PR review filed #121–#124 before fixing missing evidence accounting,
one-sided modeling judgments under opposing evidence, frozen-assertion binding,
and per-publication quotation budgeting. The original bundle remains unchanged.
A **fresh canary at 2026-11-16T02:55:53Z** passed the corrected implementation
through the same launcher, with `--staging
.temp/occurrence-canary-edge47-120-fixed-20261115` for both plan and live modes.
Its [immutable review](../../reviews/structured/20261116T025553Z-edge47-occurrence-profile/review.md)
retains the same six judgments, two evidence items, one quotation, and zero
provider calls/admissions. This is a repeated review of the same occurrence,
not an increase in population coverage.

To replay the corrected canary while its retained private inputs are present:

```sh
PYTHONPATH=src python -m edgemech.occurrence_review check --review reviews/structured/20261116T025553Z-edge47-occurrence-profile/review.yaml --packet .temp/occurrence-canary-edge47-120-fixed-20261115/packet.json --proofs .temp/occurrence-canary-edge47-120-fixed-20261115/proofs.json
```

The review pins its implementation inputs as observed at execution. If those
bytes change during review, retain this historical bundle and run a new canary
in a fresh staging directory; do not overwrite or silently repin it.
