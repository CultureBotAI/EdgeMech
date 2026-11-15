# Helper 3 edge sample canary protocol — 2026-11-12

This workflow reviews **original rule-labelled occurrences**, keeping curated and omitted
representations alongside them. An assessment of an original edge is not automatically
an assessment of its rewritten retained version. No graph data are edited.

Sampling: deterministic seed, 8,500 retained occurrences balanced across transforms
and rule verdicts, 1,500 omitted occurrences balanced across omission reasons. All
population counts and allocations are retained for N_h/n_h weighting. The canary is
an intentionally diverse subset, not a precision estimate. At least 385 observations
per transform in the full manifest does not guarantee +/-5% intervals after weighting,
nonresponse or clustering by organism. Separate uncertainty calculations are needed.

Source fidelity: inspect the upstream record, predicate meaning/direction, identifiers,
and qualifiers. Matching a transformed row alone cannot verify fidelity. Current live
records may differ from the historical snapshot. Prefer pinned raw inputs. An absent
node is a graph integrity issue, not evidence that a taxonomic identity is false.

Scientific support: use a per-edge explicit, bounded search plan. Retrieve up to five
Europe PMC core records per query and up to two OA full texts per query; group/cache
identical queries and publication IDs across edges. The recorded queries distinguish
trait searches, taxon descriptions and exact citations. Read retrieved evidence in
context and check the organism/strain, polarity, substrate and experimental setting.
A word match, paper title, database-method paper or generic ontology definition does
not establish the biological assertion. Taxonomy/identifier/attribute scaffolding
without a biological claim can be NOT_ASSESSABLE on this axis, with an edge-specific
reason. Failed requests are NOT_ASSESSABLE rather than NOT_FOUND. NOT_FOUND means
no adequate evidence under this bounded protocol, never a claim of universal absence.

Each axis uses SUPPORTED, CONTRADICTED, NOT_FOUND or NOT_ASSESSABLE. A directional
verdict requires an authored rationale and short exact quote tied to a retrieved text,
response SHA-256, retrieval URL and DOI/PMID (or explicitly identified database
accession for a source record that has no publication identifier). Scientific support
requires a publication identifier. Literal verification is stricter than normalized
whitespace matching and preserves the existing EdgeMech extractor semantics.

Model: GPT-6, as identified in the running Codex system context; more specific model
variant and billable token usage are not exposed. Record this on each authored verdict.
No automated rule assigns scientific approval. No source record is promoted or merged.

The same retrieval runner and cache are used for every batch, with a maximum of 50
unique occurrences per invocation. A dry run validates the cohort and plan without
requests. Exactly one real edge is checked for persistent cache/packet side effects
before completing the rest of this authorized 50-edge canary. No remaining manifest
edge may be retrieved or adjudicated in this task. API requests are anonymous;
full retrieved responses are kept outside Git. Commit only short quotes/hashes.
