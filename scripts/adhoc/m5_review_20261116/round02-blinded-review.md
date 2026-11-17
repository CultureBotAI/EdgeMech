You are one fresh blinded calibration reviewer in round02. This session must
begin without the coordinator conversation, prior ratings, audits or another
reviewer's work. Do not spawn reviewers. Work only in the supplied workdir and
output root. Do not read Git history, GitHub issues, coordinator leads/reports,
the operational save canary, historical review directories or another session.

The common immutable manifest is
`.temp/m5-round02-worker-20261116/round02-final/round-02-manifest.json`.
Verify it with `scripts/adhoc/calibration_round_20261116.py verify --manifest`.
Read its guide `round02-final/evidence-guide.json` beneath that same private run root,
`round02-final/profile-for-reviewers.md`, `docs/record-reviews.md` and the original
protocol `artifacts/edge-calibration-20261115/protocol.json`.
The unabridged profile and cohort remain mechanically pinned; do not open them
because they contain prior canary or selection context. Read every case's
`reviewer_view_path`. Original packet/source/occurrence files are for mechanical
replay only: never print their original_occurrence, review_rationale,
content_accuracy_verdict, curated records or dispositions into your context.
The v3 view discloses redactions and preserves hashes of private originals.
Disclose any unavoidable historical exposure, including producer wording.

Use only listed raw evidence and authorities; do not retrieve new evidence.
Assess all ten original occurrences on all six axes. The seven applicable
literature cases and thresholds in the protocol remain fixed. Record any
applicability challenge as a deviation. Missing evidence is an assessed limit,
not refutation. Never replace an original identity, relation or source row.

First state the exact proposition: distinguish a biological property, a reported
database value, an assay observation and a taxonomic relation. Preserve literal
endpoints and predicate meaning. A proposed correction is a separate object.
Audit each endpoint's identity, label, category_fit, rank_or_type, definition and
authority_version. Generic categories and matching hashes do not independently
define generated identifiers. Inspect relevant inherited constraints.
For relations assess direction, domain_range, specificity and qualifiers;
consider the defined bearer as well as broad domain/range. Producer conventions
are distinct from ontology conformance. Keep historical and current authority
versions separate; later deprecation alone does not settle historical use.

Source fidelity requires the asserted source meaning and exact source binding,
in addition to replayed bytes. Do not infer a specific subtype from a generic
process, or identity from a different relationship. Mixed source identities
remain visible and cannot be repaired by substitution in the original review.
Bind papers to their actual organism/strain, methods, units and conditions.
Abstracts remain abstracts. Distinguish comparative reports from their cited
original experiments. Do not infer full ranges from individual observations.
State missing facts and search/authority limits; agreement on unresolved labels
does not satisfy a resolution floor.

Keep the claim, literature, modeling and source-fidelity judgments separate.
Supported content may coexist with incorrect or unresolved representation when
the exact scoped content proposition can be established. Explain that scope;
do not reinterpret the predicate or endpoints to obtain support. If modeling
uncertainty prevents establishing the proposition, keep the claim unresolved.
Canonical persistence does not establish scientific correctness. Preserve any
save failure; never alter a category merely to satisfy transport validation.

Write an initial matrix:
`{round_id,package_sha256,reviewer:{id,model,session_id,historical_exposure},
cases:[{case_id,occurrence_id,assessments:[{axis,category,scope,rationale,
evidence_ids,dimensions:{...}}]}]}`.
Use the invocation's reviewer ID if supplied; otherwise reviewer-a or reviewer-b
as specified in the workdir name. Determine actual model/session identity from
your own runtime metadata, reading identity fields only. Never use configured
defaults as an asserted actual model. Same-model agreement is operational only.
Use required dimensions from DETAILS in `src/edgemech/occurrence_review.py`.
Evidence IDs must belong to that case in the manifest. Include exact source
paths/locators in rationale. No case may remain UNASSESSED.

Seal both the submitted input and initial matrix using `save-matrix` to
`<output-root>/initial-matrix.json` with repository-relative paths. Do not run
comparison, overwrite a sealed matrix or read another reviewer. Preserve errors.

Then author ten canonical review inputs and proof sidecars from those same
authored ratings using the pinned schema/profile. Start with one fresh-47 actual
save/check and inspect its saved YAML/Markdown before the remaining nine. Use
unique IDs incorporating reviewer and case. Every proof binds original input
hashes, exact literal short quotation, verified DOI/PMID/PMCID or versioned
authority identity, offsets and inspected extent. Do not copy old proofs/prose.
The aggregate 25-word quotation budget is shared across every review from a
publication/authority version; keep excerpts minimal and reuse exact text when
possible. All your originals stay private pending a separate publication gate.
Missing required checks prevent completed review status. No automatic pass.

Author review JSON and proof sidecars directly in your output root. Use existing
reviewed helpers and the production CLI for persistence. Do not create new
execution helpers or alter tracked code, validators or schemas. If a missing
adapter or helper prevents execution, preserve the technical blocker; the
coordinator owns helper changes, focused tests and same-path live canaries.
Persist reviewer-result.json with actual identity, sealed matrix path/hash,
all ten canonical input/proof/pair paths, save/check commands and exit statuses,
exposure, deviations and blockers. Never omit a failed save. No commits, issues,
messages, merges, publication or graph admission. Finish with durable locations;
do not claim work continues after your session exits.
