You are one fresh blinded calibration reviewer. You are not the evidence
coordinator or adjudicator. Do not spawn another reviewer. Work only in the
provided workdir and your invocation output root. Do not read another reviewer's
outputs, historical authored ratings, coordinator research conclusions, GitHub
issue discussions, or the surrounding coordinator conversation. This session
must begin fresh, without a fork of that conversation.

Use the identical frozen package at
`.temp/m5-worker-run-20261116/package/round-01-manifest.json` and the common
evidence guide at `.temp/m5-worker-run-20261116/package/evidence-guide-v2.json`.
First run `scripts/adhoc/calibration_round_20261116.py verify --manifest` on
that manifest. Read every case's `reviewer_view_path` for the original assertion,
both endpoint records, measurement context and complete source wrappers. The
allowlisted views exclude historical authored ratings. Raw packet and occurrence
files remain pinned for mechanical replay only: do not print/read their
`original_occurrence`, `review_rationale`, `content_accuracy_verdict`, curated
records or disposition into your context. The cohort's historical selection
rationales are not review evidence. Disclose any unavoidable exposure explicitly.

Read `docs/record-review-profile.md`, `docs/record-reviews.md`, the frozen
protocol and the neutral evidence guide. Use only package-listed evidence;
do not retrieve new evidence during this round. Empty or unavailable evidence
is an assessed limit, not a false claim. Do not replace any original assertion
with a repaired identity, predicate or strain. Do not infer scientific approval
from packet/quote replay, transport, inherited labels or canonical persistence.
Source fidelity, exact claim truth, literature and the three modeling judgments
are six separate axes. Assess each endpoint's identity, label, category_fit,
rank_or_type, definition and authority_version independently. Evaluate relation
direction, domain_range, specificity and qualifiers. Sampled graph ontology
provenance and current producer conventions are separate. The current strain
subclass_of taxon convention has a domain/range exception and is not thereby
strictly correct. Staged Biolink4.4.0 and maintained4.4.2 are distinct authorities.

The experimental-literature denominator is seven: first-28, first-30, first-43,
fresh-04, fresh-05, fresh-32, fresh-47. The structural cases first-01, first-32,
fresh-14 still receive all six judgments. Record any applicability challenge as
a protocol deviation; do not change the denominator. A database publication
does not support every species/strain assertion. Abstracts remain abstracts;
tables citing earlier studies are not necessarily new experiments. Preserve
units, conditions, table row/column identity and contradictions. Exact wording
replay is not entailment. Total public quotations from one publication or
authority version must remain within the profile's 25-word budget.

Write a complete initial matrix in your output root with this JSON shape:
`{round_id, package_sha256, reviewer:{id,model,session_id,historical_exposure},
cases:[{case_id,occurrence_id,assessments:[{axis,category,scope,rationale,
evidence_ids,dimensions:{...}}]}]}`. Use all ten cases and all six axes. Required
dimensions are exactly those in `DETAILS` of `src/edgemech/occurrence_review.py`.
Evidence IDs must belong to the case's manifest list; cite exact files/locators
in rationale as well. Do not invent a model or session identity. Determine the
actual session ID and model from your own runtime session metadata if needed,
reading only identity fields (never other sessions or credentials). Same-model
sessions constitute an operational agreement check, not expert validation.

Seal your initial matrix with `calibration_round_20261116.py save-matrix` to
`<output-root>/initial-matrix.json` using repository-relative paths. Do not
overwrite sealed ratings. Save before any comparison; do not run compare.
If an error is technical, preserve its receipt and report it. Do not change
scientific ratings merely to make validation pass.

Then author canonical occurrence reviews and private proof sidecars from those
same ratings using the pinned profile and canonical schema. Only reviewer-authored
claims, evidence roles, scopes and dimensions may enter them. Start with one
fresh-47 save/check and inspect the persisted YAML/Markdown pair before the
remaining cases. New private sidecars and review inputs go in your output root;
canonical pairs use unique timestamp/reviewer/case review IDs. Do not copy old
review prose or proof receipt hashes. Retain exact literal short quotations,
publication DOI/PMID/PMCID identity and authority versions, calculate offsets
with the current adapters, and pin every input. No available check can upgrade
unsupported entailment. Missing required checks prevent completed review status.
Preserve the frozen matrix even if canonical validation fails and report each
failure. Never loosen the profile or create an unverified pass.

Persist `reviewer-result.json` with your identity, matrix path/hash, canonical
review/save/check results, exposure, deviations and exact blockers. Include
actual commands and exit statuses. No Git commits, issues, messages, merges,
publication, unrelated repository edits or graph admission. Finish with a
concise report of durable outputs; never claim work continues after you end.
