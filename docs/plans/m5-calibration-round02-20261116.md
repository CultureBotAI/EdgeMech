# M5 calibration round 02 registration and rubric repair

Round `m5-calibration-20261116-round02` is registered as **preparation only**.
The follow-up is now active on branch `review/m5-calibration-round02-20261116`.
Its [coordinator prompt](../../scripts/adhoc/m5_review_20261116/round02.md)
specifies repairs, evidence preparation, live canaries and fresh scoring; it is
not evidence that a worker or either reviewer has started. Actual process and
phase receipts are maintained in the new private worker output directory.
Round01's frozen inputs, initial matrices, failed gates and adjudication remain
unchanged. This registration does not authorize scoring against an incomplete
package, the retained 90, or the remaining 9,900.

The original [protocol](../../artifacts/edge-calibration-20261115/protocol.json)
and [cohort](../../artifacts/edge-calibration-20261115/cohort.json) still control:
ten original occurrences, six axes, seven applicable literature cases and all
original thresholds. No occurrence replacement, denominator change or relaxed
gate is proposed. Both initial reviewers must be fresh sessions and must not
read round01 judgments; disclose unavoidable exposure. Same-model agreement
remains an operational check.

## Rubric changes to include in the next common instructions

These rules specify evidence requirements without assigning any case a label.

1. **State the exact proposition first.** Distinguish a biological property of
   the identified organism, a reported database value, an assay observation and
   a taxonomic relation. Describe the literal original endpoints and predicate.
   A correction proposal is a separate object, never the reviewed assertion.
2. **Audit each endpoint separately.** Supply evidence for identity, label,
   category, rank/type, definition and authority version. A generic parent
   category cannot establish a generated identifier's definition. Inspect
   inherited constraints as well as the selected term's label and definition;
   unresolved conflicts prevent an unqualified `CORRECT` judgment.
3. **Read predicate meaning as well as its broad domain and range.** A permissive
   schema range does not settle whether the subject denotes the physical bearer
   required by the predicate. Identify any project exception explicitly and
   assess it; current producer use is evidence of convention, not correctness.
4. **Separate historical and current authority.** Bind the sampled producer,
   ontology and source versions where possible. Deprecation in a later release
   does not alone prove that the original use was incorrect. A current-version
   assessment must state its scope and cannot silently supply missing historical
   semantics. Inspect staged Biolink 4.4.0 and maintained 4.4.2 separately.
5. **Require semantic source fidelity.** Exact row replay proves preservation.
   `SUPPORTED` additionally requires the asserted source meaning: a generic
   process is not automatically its specific subtype, and a type-strain
   association is not automatically identity or close equivalence. Mixed source
   identities remain unresolved without making the biological claim false.
6. **Bind paper statements at their actual scope.** Verify publication identity,
   a bounded literal excerpt, organism/strain, methods, units and conditions.
   Abstracts remain abstracts; comparative tables must identify their cited
   original studies. A database paper does not support every record. A reported
   value's meaning and an independently observed biological range are distinct.
7. **Separate evidence absence from refutation and category uncertainty.** State
   the missing fact and the retrieval/authority scope checked. Use unresolved
   categories where appropriate. Agreement on unresolved labels does not count
   toward any resolution floor. Do not infer exact-strain results from another
   strain or infer a complete range from individual positive observations.
8. **Preserve validation failures.** Resolve the documented fresh-05 claim/model
   acceptance boundary in maintained shared semantics before the new freeze.
   Never alter a category merely to make canonical save pass. Keep individual
   axis judgments separate from aggregate review disposition and completion.

## Evidence preparation and launch prerequisites

Obtain the sampled ontology/producer/source hash chain, including selector
semantics for the retained ordinal. Pin exact predicate and node authorities,
generated identifier definitions and relevant inherited constraints. Resolve or
document maintained-owner answers for the nonmotile hierarchy, taxon capability
interpretation and original assay predicate. Retain fresh-04 and fresh-05 source
identity conflicts without substituting accessions.

Seek exact organism/strain literature for the remaining unresolved claims using
retained provenance and anonymous primary sources first. An unavailable source
stays unavailable. Do not use the authenticated general full-text helper until
PR #102 is separately merged. No paid research job is authorized.

Prepare in a new empty private round directory. Canary one fresh-47 preparation
and replay, inspect persisted artifacts, then prepare remaining cases. Remove
historical authored judgment prose from the next evidence view where it can be
separated from the original source bytes; retain the original bytes for mechanical
replay and disclose anything inseparable. Freeze a new manifest containing all
case inputs, authority versions, proof adapters, runtime and common instructions.
Canary the actual launcher and canonical-save path before two new reviewer
sessions. Seal both new matrices before comparison and perform a separate
evidence-grounded audit of every resolved claim/model label.

This is a concrete failed-round follow-up milestone, not a running review job.
The next round's package hash, actual reviewer identities and launch time remain
unset until those prerequisites have been satisfied.
