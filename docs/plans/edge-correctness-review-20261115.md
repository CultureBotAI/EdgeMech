# Edge correctness: claim, evidence, relation and node review

Planning baseline: EdgeMech `2cc688b7527986b68377305acb24fac9697eef04`, 2026-11-15 (America/Los_Angeles). This plan implements the user's priority: find and correct edge problems, categorically assess the statement, retain DOI-linked literature snippets, and check the relation and both endpoint nodes. It describes **proposed implementation**, not new scientific results or an enabled review service.

Start with the existing 100 distinct canary occurrences and their endpoint nodes. Add a new assessment layer; preserve both frozen canaries and all original source/review bytes. The other 9,900 sampled occurrences remain unreviewed. Larger graph coverage requires a separately pinned population and explicit accounting; these 100 do not establish population accuracy.

## 1. Required assessment for every occurrence

Keep these independently authored judgments together in one occurrence-bound review. A single overall score cannot replace them.

| Axis | Required question and result |
| --- | --- |
| Claim correctness | Is the exact original subject–relation–object statement supported or refuted under its organism/strain, polarity, quantifier, units and conditions? Give a categorical verdict and rationale; retain missing context explicitly. |
| Literature support | Which inspected papers directly support, refute, partially address or merely contextualize this claim? Store matched short verbatim snippets with verified DOI identity and precise locators. Record no matching evidence, unavailable access or missing DOI explicitly. |
| Relation modeling | Is the predicate's meaning, direction, domain/range, specificity and qualifier/observation representation appropriate? Assess both formal conformance and semantic fitness. |
| Subject-node modeling | Does the identifier denote the intended entity, with an appropriate label, category, rank/type, definition and versioned authority? Check deprecated/merged IDs and species-versus-strain distinctions. |
| Object-node modeling | Apply the same identity/category checks independently, including chemical form, phenotype definition, habitat specificity, mixture, quantity, unit and measurement-versus-entity distinctions where relevant. |
| Source fidelity | Does the assertion preserve the exact source record and its context? Faithful copying does not make a source crosswalk or biological claim correct. Keep this separate from independent literature support. |

The **22 fresh-canary occurrences excluded from the old biological-literature axis remain in identity, relation and node review**. Taxonomy, mappings, recipe composition and reaction-participant claims need their appropriate versioned source/ontology/authority evidence. An explicit `not_applicable` on the experimental-literature axis must never skip all other axes.

### Proposed categorical rubric

These are proposed profile labels, **not existing shared-schema enum values**. Agree the rubric and validator before producing new review outputs:

| Claim label | Meaning |
| --- | --- |
| `SUPPORTED_AS_STATED` | Evidence supports the exact assertion within its declared scope. This is an evidence-based judgment, not universal proof. |
| `CONTRADICTED_AS_STATED` | Matched evidence refutes the exact assertion; a missing paper or incorrect model alone is not a biological refutation. |
| `CONFLICTING_EVIDENCE` | Relevant evidence supports and refutes a comparably scoped assertion. Retain both sides and their conditions. |
| `INSUFFICIENT_EVIDENCE` | The bounded review completed but evidence does not settle the assertion, including partial scope or another strain. |
| `NOT_ASSESSABLE` | Identity, meaning, required context or access prevents the assessment. Record the specific blocker. |

Report relation, subject-node and object-node modeling separately as correct / incorrect / unresolved, with reasons and versioned evidence. Do not infer correctness from a populated category, a valid CURIE, a matching DOI, a literal quote match or a passing schema check. Preserve `unassessed` before an axis is actually reviewed.

### Evidence and provenance requirements

- Bind the original occurrence ID, exact source row, subject/predicate/object and endpoint records to input hashes and source/ontology versions. Store proposed corrected assertions separately, with old/new identity lineage; a corrected assertion cannot silently replace the claim being judged.
- For each literary source retain verified DOI/title identity, DOI URL, PMID/PMCID when available, the short exact quotation, section/page/table/figure or text offsets, raw/text hashes, extraction method, inspected extent and supporting/refuting/partial/context role. Verify quotations against retained bytes and independently assess entailment and strain/condition scope.
- Retain newly discovered or corrected reference bindings in the new review layer with provenance. Preserve the original citation separately; do not silently rewrite a source row or assume an inherited dataset DOI supplies experimental evidence for every edge.
- If a paper has no DOI, retain its verified alternate identifier and explicit reason. If no relevant text is available, keep an explicit unresolved result. Structural assertions may be settled by versioned ontology/database authority without a paper; record that basis and the literature gap/applicability separately. Never fabricate a DOI or snippet to fill a cell.
- Keep private source packets and full article bodies outside Git. Public records contain bounded quotations, identifiers, hashes and locators. Search summaries, metadata and HTTP success alone are not inspected experimental evidence.

## 2. Reuse existing governed components

Continue the [content-review plan](content-review-20261109.md), especially its separate presence, fidelity, retrieval, quote-match and entailment states. Reuse `src/edgemech/literature_adjudication.py`, the retained source/targeting/quote validators, and the [shared structured-review contract](../record-reviews.md). The current adjudicator already binds explicit taxon, predicate, object, context and evidence-scope explanations to canonical reviews, but does not require independent categorical verdicts for both nodes and the relation.

The current shared schema has `AssessmentOutcome` values `supported`, `concern`, `unknown`, `not_applicable`, and evidence roles `supports`, `refutes`, `partial`, `context_only`, `unknown`. Its top-level `Verdict` describes review disposition, not scientific truth. Define the new rubric using validated evidence-linked assessments/dimensions and an explicit mapping to those existing outcomes; do not overload the top-level verdict. For example, scoped refutation requires refuting evidence and a concerning claim assessment, whereas a failed retrieval remains unknown. Shared-schema changes, if needed, belong in CLAW and require a reviewed pin update.

The next implementation must supply an EdgeMech occurrence-review profile and acceptance validator. EdgeMech's pinned fleet manifest currently disables native `record_review`, and no local profile is installed. A bounded adapter/profile must not imply fleet admission, native scientific approval or capability enablement. Resolve current ownership/capabilities before implementation; use [routing.yaml](../../conf/routing.yaml) and maintained upstream/native owners for actual corrections.

## 3. Dependency-ordered implementation

1. **Profile and complete packet.** Specify mandatory axes, rubric, source/target/reference bindings and validator; implement joined measurement context from [#105](https://github.com/CultureBotAI/EdgeMech/issues/105). Include both endpoint records and governing definitions. Reject missing/duplicate axes, unbound evidence and a positive verdict unsupported within scope. Report required checks that could not run rather than calling them passed.
2. **Identity and modeling checks on the selected nodes/edges.** Resolve relevant crosswalk problems [#68](https://github.com/CultureBotAI/EdgeMech/issues/68)/[#106](https://github.com/CultureBotAI/EdgeMech/issues/106), predicate/type-strain/bin problems [#75](https://github.com/CultureBotAI/EdgeMech/issues/75)/[#86](https://github.com/CultureBotAI/EdgeMech/issues/86)/[#87](https://github.com/CultureBotAI/EdgeMech/issues/87), and inspect semantic categories even when nonempty. Pin ontology/Biolink versions. Deterministic checks identify candidate defects; authored judgments establish whether the specific model is appropriate.
3. **DOI identity and scoped literary evidence.** Check publication identity [#69](https://github.com/CultureBotAI/EdgeMech/issues/69), then replay retained source/paper evidence before new retrieval. Use local provenance/Zotero, public OA and appropriate LBNL publisher access; use Valency/Tavily for discovery where useful. Retrieve Methods, tables or figures when abstracts cannot answer the claim. Record access failures separately from a completed search with no relevant evidence.
4. **One canary, then a finite review of the retained cohort.** Run one occurrence end to end through the intended launcher/worker environment: packet, categorical assessments, quote proofs, findings and corrective-action record, save/read-back validation. Edge47 is a useful initial context/partial-support case; its original strain's full 0–10% range must remain unresolved on the currently inspected evidence. After this passes, use a ten-occurrence calibration set drawn from the existing 100, then cover all 100 with the same path. Include supported controls, unresolved evidence, wrong-relation, type-strain, quantitative-bin, sporulation/tolerance and zero-positive cases. Pin exact selected IDs; do not select ten convenient positive examples or count re-review as new population coverage.
5. **Correct and independently verify.** Fix the maintained source, transform, ontology or native owner identified by a finding; regenerate a new candidate rather than editing a frozen graph. Check the affected edge and node records and independently re-assess the resulting assertions. Preserve justified no-change, quarantine and deferred outcomes when a factual correction is not established.

**Parallel prerequisite:** [PR #102](https://github.com/CultureBotAI/EdgeMech/pull/102)/[#100](https://github.com/CultureBotAI/EdgeMech/issues/100) protects the general authenticated full-text helper. Integrate and validate it against current main before its separately authorized merge and further authenticated general-helper calls. Retained-evidence review and local modeling work can proceed independently; access work is not the primary success metric.

## 4. Correction closure and expansion gates

Each finding needs exact affected IDs/fields, evidence, owner paths, issue/PR, before/after proposal, rationale, regression and implementation status. For a shared node, enumerate affected occurrence bindings and account for collateral model changes; deduplicating node checks must not lose per-edge multiplicity or context.

Distinguish a merged source fix, verified component replay, regenerated graph release and verified corrected occurrence. Close an implementation issue when its own acceptance criteria are met, but keep graph-level correction pending until the relevant regenerated bytes are checked. Link the new immutable review to the earlier finding. A justified no-change decision requires evidence and an independent disposition, not silent removal of the finding.

Before expanding beyond the retained 100:

- Account for every selected occurrence and both endpoint nodes, with each required axis assessed or explicitly unresolved; no success-only denominator and no blanket structural exclusion.
- Replay every published quotation against its retained source and verify every claimed DOI binding. Independently review positive/refuting judgments and correction candidates; retain disagreements rather than collapsing them to support.
- Report resolved/unresolved truth states, literature coverage, relation/node defects, corrected-versus-quarantined cases, observed reviewer disagreements and false-support cases separately. Agree acceptable error/coverage thresholds before the calibration results are scored; do not invent a green gate after seeing the data or treat this purposive sample as a population error estimate.
- Demonstrate at least one real retained finding's complete correction-verification path: regenerate candidate bytes from the maintained source/transform/ontology, retain the input/output identities and regression result, and independently verify the corrected assertion or node against those bytes. A successful retrieval-only run or a proposed correction is insufficient.
- Record owner/release blockers separately. If a blocker prevents that demonstration, the expansion gate remains unmet; explaining the blocker is not a passing substitute. Investigation and preparation within the retained 100 can continue. Publication of a graph release may remain pending after candidate verification, and must remain explicitly pending until the released bytes are checked.
- Verify persisted artifacts, bounded provider cost/time/failures and worker behavior with the same launcher. The remaining 9,900 stay deferred until these results justify the next bounded selection; there is no automatic full-graph expansion.

## 5. Node metadata work already completed

The [distinct-node triage](../validation/scientific-followups-20261110.md) already reconciled 238,422 affected occurrences to 79,573 incomplete nodes and 239,797 endpoint roles. All observed gaps were missing labels; zero missing categories does **not** mean categories were semantically verified.

The [component repair report](../validation/chemical-scope-metadata-20261110.md) and [latest #36 status](https://github.com/CultureBotAI/EdgeMech/issues/36#issuecomment-6788046529) record merged upstream [PR #1836](https://github.com/Knowledge-Graph-Hub/kg-microbe/pull/1836), including citation and BTO label repairs. Remaining #36 work is release regeneration/verification, 21 conflicting DOI citation labels, owner-supplied IMG/INSDC metadata and partial/obsolete EC semantics. Reuse the retained node inventory; do not rerun the entire 238,422-occurrence completeness audit as a prerequisite for the bounded semantic pilot.
