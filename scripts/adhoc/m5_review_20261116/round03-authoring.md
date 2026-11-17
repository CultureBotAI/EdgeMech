# Data authoring contract

All helper paths below are under `scripts/adhoc/`. Run with the pinned Python
and `-B`. Paths in authored JSON are repository-relative; write only new private
directories. No helper generates scientific judgments.

`author_m5_review_data_20261116.py --manifest MANIFEST --spec SPEC --output NEW_DIR`
reads one JSON object with these fields:

- `case_id`, `accessed_at` (ISO UTC timestamp), `ownership_note`.
- `reviewer_identity`: `id`, actual `model`, actual `session_id`, and
  `historical_exposure`. Canonical reviewer identity equals `id`.
- `review`: canonical schema metadata including schema_version, review_id,
  title, started_at, finished_at, reviewer, completion, verdict,
  scientific_review, summary, scope, checks, findings, actions, limitations.
  Review IDs use `YYYYMMDDTHHMMSSZ-slug`; provide your own unique ID.
  `reviewer` has identity, kind=agent, model, independence and independence_basis.
  `scope` has description, selection, coverage, population_size=1 and
  reviewed_target_ids containing the exact occurrence ID. Checks/limitations
  must honestly report unavailable and unresolved work. Consult the shared
  schema for valid enum values. Do not include mechanically generated source,
  targets, assessments, evidence, kind, repository or skill fields here.
- `assessments`: six objects with `axis`, `category`, `scope`, `rationale`,
  `evidence_ids` (local proof IDs) and `dimensions` (object of required axis
  dimensions and authored explanations). The helper derives only canonical
  outcome and the list representation. An optional claim `assertion_basis`
  and explicit `report_witnesses` use local proof IDs and preserve scope.
- `proofs`: explicit specifications described below. Evidence IDs may distinguish
  multiple quotations from one manifest input; the seal maps each back to the
  explicit manifest_evidence_id while pinning every complete proof.

Each proof requires evidence_id, manifest_evidence_id, kind (`packet`,
`authority`, `europepmc_abstract`, `jats`), scope (`exact`, `partial`, `context`),
scope_rationale, inspected_extent, support (`supports`, `refutes`, `partial`,
`context_only`), axes, reference, summary and locator. Raw input path/hash comes
from the frozen manifest. A packet proof binds the exact case packet and has
no quotation. Other kinds require a short `quote`; offsets, text hash and
extractor come from existing literal replay logic. Authority version must
exactly equal the manifest version. Report identity/definition authority proofs
declare original_entities for the exact original subject/predicate/object.
Do not infer applicability from the successful literal quote check.

Paper proofs require primary title and DOI/PMID/PMCID as appropriate to their
retained representation. Abstract inspected_extent must be `abstract` and its
locator begin `abstract;`. A missing DOI requires the documented reason and
verified alternate reference. The helper checks primary metadata before spans.
Paper proofs used on claim or literature must declare both axes. All proofs
declaring an axis must appear in that assessment's evidence_ids. Authorities
cannot be literature evidence. Every distinct scientific witness must be bound
explicitly even when the rationale also mentions it.

Outputs are review.json, proofs.json and draft-receipt.json. Read back all three
after the first unit. A validation failure may leave the attempted review/proofs
without a success receipt; preserve them and use a separately identified attempt.
Successful draft validation is not persistence or semantic adjudication.

Use `seal_m5_round03_initial_20261116.py --help` for the final config and CLI.
Its seal binds the complete authored sets and derives the initial matrix.
The production CLI saves/checks canonical pairs only after that seal.

Record your actual identity with
`identify_m5_worker_20261116.py --events .temp/YOUR-OUTPUT/events.jsonl`.
It locates only your matching native session log and emits model/session fields
without conversation text. Record these fields in every authored spec and seal
config. It does not override model or effort.
