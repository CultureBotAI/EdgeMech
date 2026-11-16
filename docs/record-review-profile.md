# Bounded occurrence review profile

`edgemech-occurrence-review/v1` is a local acceptance profile over the pinned
CLAW `RecordReview`. CLAW still owns the shared schema, review semantics and
immutable persistence helper. This profile does not change fleet capability
flags: EdgeMech's pinned `record_review` and `evidence_reference_validation`
capabilities remain disabled. It does not create normalized claims, observations,
curation decisions, or KG admissions.

## One occurrence, six separate judgments

Each review targets one exact original occurrence and has exactly six canonical
assessments. Each assessment records `axis`, `category`, and an authored `scope`
as evidence-linked dimensions. The category is a local dimension value, not a
new shared enum or a top-level review verdict.

| Axis | Local categories → canonical outcome |
| --- | --- |
| `claim` | `SUPPORTED_AS_STATED` → supported; `CONTRADICTED_AS_STATED`, `CONFLICTING_EVIDENCE` → concern; `INSUFFICIENT_EVIDENCE`, `NOT_ASSESSABLE`, `UNASSESSED` → unknown |
| `literature` | `SUPPORTS` → supported; `REFUTES`, `CONFLICTING` → concern; `PARTIAL`, `NO_MATCH`, `UNAVAILABLE`, `UNASSESSED` → unknown; `NOT_APPLICABLE` → not_applicable |
| `relation`, `subject_node`, `object_node` | `CORRECT` → supported; `INCORRECT` → concern; `UNRESOLVED`, `UNASSESSED` → unknown |
| `source_fidelity` | `SUPPORTED` → supported; `CONTRADICTED` → concern; `NOT_ASSESSABLE`, `UNASSESSED` → unknown |

`UNASSESSED` is allowed only before review completion. An unresolved result is
an assessed limit, not an unperformed check. Required unavailable checks still
prevent a completed review under the shared contract. Structural assertions may
have inapplicable experimental literature but still require the other five axes.

Claim scope must preserve the original predicate and endpoint definitions. A
reported database value is not automatically a biological claim about every
organism in the taxon. `SUPPORTED_AS_STATED` is evidence-based support within the
declared scope; it is not universal proof. Missing or inaccessible evidence is
never a refutation. Unqualified `pass` requires supported claim and resolved
correct modeling; other review dispositions remain distinct from claim truth.

Additional authored dimensions are mandatory:

- Claim: `assertion_scope`; literature: `search_scope`.
- Relation: `direction`, `domain_range`, `specificity`, `qualifiers`.
- Each node independently: `identity`, `label`, `category_fit`, `rank_or_type`,
  `definition`, `authority_version`.
- Source fidelity: `source_binding`.

These explanations may state explicit unresolved limits. Valid identifiers,
nonempty categories, replayed text and successful validation do not establish
semantic correctness. An incorrect or unassessed model cannot be hidden by a
supported-as-stated claim judgment.

## Complete packet and provenance

`edgemech.occurrence_packet.build_packet` takes the frozen occurrence and its
retained source packet, plus repository-relative file paths and SHA-256 pins.
`validate_packet` rereads those files and recomputes the packet. Both endpoint
records, labels, categories and hashes are preserved alongside the original
assertion. Private source rows remain in ignored `.temp/` staging.

The first measurement adapter joins MicrobeDecoder's exact LPSN endpoint and
BacDive ID to its retained strain, concentration/unit observation, and reference
ID. It preserves the literal value and unit; it does not join by species name,
convert percent to g/L, infer a maximum/optimum, or attach routine cultivation
conditions to an assay. Other source fields explicitly report unresolved context.

For new legacy timed reviews, `review_packet.py begin` requires
`--occurrence-packet`. The displayed context is snapshotted and bound to the
timer; excerpts and finish replay it. Historical snapshots remain unchanged and
explicitly report unavailable context when they lack that companion.
The companion's complete public occurrence/node projection must also match the
selected frozen row; matching only its occurrence ID is insufficient (#123).

## Evidence replay and limits

The private proof sidecar is an adapter input, not another canonical review.
It binds the occurrence, each evidence ID and its applicable axes, support role,
exact/partial/context scope with rationale, inspected extent and raw input pin.
Every sidecar and packet input must also be pinned in canonical review provenance.

Supported representations in this initial implementation:

- JATS with primary article metadata, body and PMCID. DOI/title/PMCID are checked
  against the primary metadata, not references cited by the paper. The existing
  `full_text` extractor and `verify_quote` replay the text and exact short quote,
  offsets, raw/text hashes and extractor. Missing DOI requires an explicit reason
  and bound PMCID URL. Canonical evidence carries DOI URL, quote and locator.
- Versioned authority text, with a literal quote and retained hash. The reviewer
  must establish relevance to the exact relation/node; replay does not infer it.
- The validated packet, for source fidelity and original modeling context. This
  cannot supply independent claim or literature evidence.

Other formats remain explicit unresolved inputs until a replay adapter is added;
this implementation makes no new full-text requests. Positive or refuting claim
judgments require exact-scope independent evidence of the corresponding role;
conflict requires both. Partial or another-strain evidence cannot satisfy these
gates. Resolved modeling requires corresponding versioned authority evidence.
Every axis consumes all proofs declaring its applicability; paper evidence used
for claim or literature binds both axes (#121). Opposing exact modeling
authorities require `UNRESOLVED`, and opposing source proofs require
`NOT_ASSESSABLE` (#122). The 25-word quotation budget groups verified DOI/PMCID
aliases across raw representations of the same publication (#124).
Resolved source fidelity itself requires an exact-scope packet proof of the
corresponding role; partial/context proofs cannot resolve it (#125).

Full paper bodies and raw source packets are private. Public canonical reviews
contain bounded quotations, references, hashes, locators, assessments, findings
and actions. Shared `read_review` alone treats working-tree provenance as an
attestation, so the local `check` operation additionally replays all retained
input hashes, packet content and quote proofs. If private bytes are unavailable,
replay cannot be reported as passed.

## Commands and acceptance

From the repository root with the pinned Python environment:

```sh
PYTHONPATH=src python -m edgemech check-contracts
PYTHONPATH=src python -m edgemech.occurrence_review validate --review .temp/review.json --packet .temp/packet.json --proofs .temp/proofs.json
PYTHONPATH=src python -m edgemech.occurrence_review save --review .temp/review.json --packet .temp/packet.json --proofs .temp/proofs.json
PYTHONPATH=src python -m edgemech.occurrence_review check --review reviews/structured/REVIEW_ID/review.yaml --packet .temp/packet.json --proofs .temp/proofs.json
```

Save uses CLAW's immutable YAML/Markdown publication, reads the saved pair, then
replays the local profile before returning a receipt. Helpers never execute
commands recorded in evidence. Findings identify maintained owner paths and
acceptance checks; corrections belong to those owners, not frozen graph bytes.

The reproducible first-canary launcher is
`scripts/adhoc/run_occurrence_canary_20261115.py`; run `--plan` before its single
live unit. Verify the persisted receipt and review pair before considering a
calibration batch. Focused regression tests are `tests/test_occurrence_packet.py`
and `tests/test_occurrence_review.py`. Run the complete suite on the final PR
candidate. Ten-case calibration, all-100 coverage and demonstrated correction
verification remain separate gates in the [implementation plan](plans/edge-correctness-review-20261115.md).
