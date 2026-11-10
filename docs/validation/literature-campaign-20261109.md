# Literature evidence campaign: executed pilot

PR #38, stacked on unmerged PR #33. This report covers the 463-occurrence
MicrobeDecoder literature cohort, not scientific completion of the 17M census.

## Persisted results

| Measure | Result |
|---|---:|
| Exact source occurrences retained | 463 |
| Occurrences with explicit DOI references | 185 |
| Occurrences needing bibliographic identifier resolution | 278 |
| Unique DOIs processed | 33 |
| Papers with retrieved text | 29 |
| Cached provider responses, all HTTP 200 | 35 |
| Retained response bytes | 469,249 |
| Repeat-run metadata cache hits | 33 / 33 |
| Explicit scientific assessments | 10 |
| Supported / unknown / concern | 4 / 6 / 0 |
| Exact quotation proofs | 10 |
| Occurrences deferred | 453 |
| KG admissions | 0 |

One occurrence completed the real preparation/retrieval/quote/review path before
the full cohort ran. The canary verified persisted response bytes and validated
CLAW review artifacts. The subsequent complete retrieval and cache replay verify
durability; they do not establish load behavior for concurrent remote workers.

The scientific pilot checks three primary species descriptions: Succiniclasticum
ruminis, Basfia succiniciproducens and Actinobacillus succinogenes. Four supported
interpretations concern fermentation, succinate consumption and propionate
production in S. ruminis, and glucose substrate use in B. succiniciproducens.
Support is bounded to the retrieved description and stated conditions.

Six unknown outcomes require stronger process evidence, an explicit chemical
normalization policy, evidence for consumption of a mixed medium, or acetate
production evidence. Absence from an abstract is not a contradiction. These
follow-ups are recorded in [issue #41](https://github.com/CultureBotAI/EdgeMech/issues/41).
Every decision is withheld; there are no synthesized assays or admitted claims.
The agent both authored and reviewed these judgments; no independent scientific
agreement or calibrated error rate is claimed.

## Reproducibility

Explicit judgments: `conf/literature_assessments/20261109-pilot-judgments.json`.
The builder and campaign launcher are committed under `scripts/adhoc/`.
Local bulk artifacts are retained in ignored `workspace/`:

| Artifact directory | Manifest or artifact SHA-256 |
|---|---|
| `literature-cohort-full-v2-20261109` manifest | `bd3d9ad56e74a4661830a9253b4fc58006ac6b6a081b57ba42e6497e7a50681d` |
| `literature-retrieval-full-20261109` manifest | `f4082e91c0df43d1cdcf72a00696bd6e02b0f1e24694e12841a435dde9eab5dc` |
| `literature-adjudication-pilot-20261109/bundle.json` | `a8b46c16b3c0afce07fe6aaf48d04eadafa7cb521d02382472faa9701ad0396b` |
| `literature-adjudication-pilot-20261109/quote-proofs.json` | `dbf91bc266850c6f9aa33d3bdcbc075001804f076a371e7ccd138c2e99894e4b` |

`literature-retrieval-cache-replay-20261109` records all 33 identifiers completed,
zero deferred identifiers and 33 metadata cache hits. The original retrieval
manifest predates the added attempted/deferred counters; its 33 completion count
is valid because this actual run had no deferred requests.

Read-only review of ee7c8d0 identified the copied source-manifest verification
gap ([#39](https://github.com/CultureBotAI/EdgeMech/issues/39)) and negative-cache
expiry/progress-accounting gaps ([#40](https://github.com/CultureBotAI/EdgeMech/issues/40)).
Both are corrected with regression coverage. Original source bytes are preserved,
including the producer's documented malformed-UTF-8 citation display policy.

The implementation plan and primary API references are in
`docs/plans/literature-campaign-20261109.md`. Remaining work is bibliographic
resolution for 278 occurrences, explicit assessments for the remaining 453,
resolution of the six uncertainties, independent scientific review, and selection
of subsequent census cohorts. This pilot does not authorize automatic propagation.
