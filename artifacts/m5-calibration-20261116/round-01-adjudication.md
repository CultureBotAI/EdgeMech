# Independent adjudication of frozen M5 round 01

Round `m5-calibration-20261116-round01` failed. The initial object-node agreement remains 7/10 against the preregistered minimum 8/10. Neither matrix was rewritten. No remaining-90 work or expansion is authorized.

The audit independently assessed all 60 final axes and all 53 initial resolved claim/model labels, including agreement. Eight initial labels are unsupported: 6/33 emitted CORRECT model judgments and 2/14 emitted INCORRECT model judgments. The 2 SUPPORTED_AS_STATED and 4 CONTRADICTED_AS_STATED initial labels were supported within their stated scopes. No CONFLICTING_EVIDENCE label was emitted, so that critical class is untested. All 23 final resolved claim/model labels were separately audited; none is unsupported.

| Final accounting | Result | Fixed minimum |
| --- | ---: | ---: |
| Authored axes | 60/60, no UNASSESSED | 60/60 |
| Resolved claims | 3/10 | 2/10 |
| Resolved source fidelity | 7/10 — failed | 8/10 |
| Resolved relation / subject / object | 7/10 / 7/10 / 6/10 | 5/10 each |
| Critical overclaims | 8 initial + 0 final — failed | maximum 0 |
| Blocking unresolved disagreements | 2 — failed | 0 |
| Exact paper-backed directional claim | fresh-05 | at least 1 |
| Exact authority-backed incorrect modeling | 6 cases | at least 1 |

The four initial disagreements remain distinct. first-01 claim is disposed to NOT_ASSESSABLE because the exact obsolete predicate semantics cannot be recovered. fresh-04 object is CORRECT within the frozen METPO definition: the 3–8 percent equivalent-class expression and phenotype ancestry resolve the node itself; source fraction 0.25 and strain attribution remain unresolved on their own axes. fresh-05 and fresh-47 objects remain UNRESOLVED; their original resolved CORRECT judgments remain blocking disagreements.

The eight critical labels arise from three findings:

- Both reviewers marked first-01 relation INCORRECT from current deprecation. The retained METPO term proves obsolete status, but has no operative definition/domain/range and does not reconstruct the sampled generating version. That is insufficient to establish semantic incorrectness of the exact original assay link. Final relation: UNRESOLVED.
- Both reviewers marked first-43 and fresh-32 capable_of relations CORRECT. Their broad NamedThing→Occurrent categories fit, but both Biolink versions describe a physical entity/continuant's ability, while OrganismTaxon denotes a classification. The frozen evidence does not establish the required taxon-to-physical-bearer interpretation or member quantification. Final relations: UNRESOLVED, without inferring the opposite biological truth.
- Reviewer A marked fresh-05 and fresh-47 objects CORRECT. METPO nonmotile 1000703 inherits from motility 1000701 whose definition asserts positive autonomous movement; that hierarchy/definition conflict is unresolved. For fresh-47, generic Biolink Attribute meaning does not independently validate the exact hash-minted local identifier's definition/generation version. Final objects: UNRESOLVED.

Two additional source-semantics findings do not enter critical claim/model counts. first-28 source fidelity is NOT_ASSESSABLE: generic sporulation summaries do not establish endospore-specific fidelity merely because the positive token survives. fresh-14 source fidelity is CONTRADICTED: a documented type-strain designation was replaced by close_match; retaining the endpoint pair does not preserve the relationship meaning. Its actual species/type-strain association remains supported.

The exact paper-backed exercise is fresh-05: verified MED/PMID 17625207, DOI 10.1099/ijs.0.65010-0, directly binds nonmotility to HOact23=DSM 18772. This is abstract-limited support of the original named-strain characterization, independent of the mixed BactoTraits source row and modeling defects. fresh-32 remains PARTIAL: PMC4546703 Table 1's target-species column reports sulfite use but attributes prior characterization to Brandt and Ingvorsen 1997; its new experiments are APT3. fresh-47's GI38 assays are another isolate and do not establish G1's complete 0–10 report. fresh-04 optimum/range passages do not explain fractional bins or fix mixed accessions.

For fresh-05, the original subject remains NCBITaxon:1123071, independently bound to DSM 18772; the mixed source-row accessions are not used to replace it. The original direct has-phenotype reading and the object's own nonmotility definition are retained. Support does not certify full OWL entailment closure, strict typed-edge validity or every-environment inability. The parent-term conflict therefore remains a separate unresolved model dimension. Requiring claim truth to certify formal closure as well would expose an underspecified claim/model boundary that must be settled prospectively; the current canonical save prohibition is explicitly preserved, not evaded.

All ten literature labels: first-01 NOT_APPLICABLE; first-28 NO_MATCH; first-30 NO_MATCH; first-32 NOT_APPLICABLE; first-43 NO_MATCH; fresh-04 PARTIAL; fresh-05 SUPPORTS; fresh-14 NOT_APPLICABLE; fresh-32 PARTIAL; fresh-47 PARTIAL. Exact directional literature coverage is 1/7. The fixed experimental denominator remains seven.

Independent replay used the existing occurrence_review check command on each persisted YAML/Markdown pair and its own proof sidecar. All 18/18 available pairs passed, retained sealed categories and remained partial with required checks unavailable. Availability is separately only 18/20: both fresh-05 canonical saves failed. A gitignore-independent recursive enumeration found no saved fresh-05 pair for either reviewer. Both reviewers ended and their reviewer-result manifests were inspected. The audit independently reran validate on each failed input and reproduced `Supported-as-stated cannot conceal incorrect/unassessed original modeling`. This is an acceptance-policy conflict with separately stated claim/model judgments; it is not a biological refutation or an excuse to change ratings. The evidence-integrity gate fails: missing canonical pairs, required version/evidence limits and unsupported semantic proof roles remain visible despite valid literal replay.

Maintained owners and concrete changes needed before a separately registered next round:

1. EdgeMech review-profile maintainers and pinned CLAW semantics owners: resolve the fresh-05 claim/model coupling policy in `src/edgemech/occurrence_review.py` and `docs/record-review-profile.md`. Specify how an independently supported bounded biological characterization and an incorrect model coexist without granting an unqualified pass. Preserve the two failed inputs as regression fixtures; do not patch this round's profile or ratings.
2. EdgeMech rubric owners and KG-Microbe ontology/modeling maintainers: specify current-version semantic assessment separately from sampled generation-chain provenance, distinguish deprecation from semantic refutation, and require a justified taxon/instance interpretation for capable_of. A generic domain/range quote alone must not satisfy exact semantic correctness.
3. METPO maintainers: reconcile 1000703 with the positive-capability definition of parent 1000701 and review descendant meaning. Rebuild a versioned ontology artifact; inspect the affected original endpoint against those candidate bytes before a new round.
4. KG-Microbe local vocabulary maintainers: retain versioned identifier-generation rules and exact definitions for the hash-minted source-attribute/process nodes; bind complete generating inputs to their outputs. Include the API 20E kit/procedure definition and former METPO observation semantics where historical interpretation is required.
5. BactoTraits/MetaTraits/MicrobeDecoder and KG-Microbe transform maintainers: retain field-level strain attribution for fresh-04/fresh-05, original observations behind endospore/nitrogen-fixation summaries, and fractional-bin semantics with units. Semantic source fidelity must test quantity, polarity and relationship meaning, not just row/token copying.
6. KG-Microbe LPSN transform maintainers, including `_make_type_strain_edge` in the maintained LPSN transform: independently validate a type-designation representation with the actual ontology category rules. The current subclass_of convention's exception is not proof of strict validity. Verify candidate regeneration without rewriting the retained source row.
7. EdgeMech package/blinding owners: register a new immutable package with exact authorities, publication identities and original-study attribution; remove inherited authored-review prose and prior-review hints from reviewer views and instructions where possible. Keep both round-01 initial matrices, disagreements, failed saves and every fixed threshold unchanged.

Evidence audit artifacts: `audit.json`, machine-computed `gates-final.json`, `canonical-replay.json`, `package-replay.json`, per-pair actual check receipts, both fresh-05 validation failures and `reviewer-result-inspection.json`. The final accounting helper exited 0 and returned `failed_gate`; it did not infer integrity passage from receipt existence.

Adjudicator session is the tool-managed `/root/round01_adjudication`. Model gpt-6-astra is supported by independently verified parent runtime plus the tool's no-override inheritance contract; child-specific model telemetry is unavailable. All three sessions using the same model is an operational calibration constraint, not independent expert validation. No new evidence retrieval, remote calls, source modifications, issues, commits or publication were performed by this adjudicator.

The first `gates.json` is retained as a pre-clarification calculation. Adding the explicit fresh-05 scope note changed the audit hash without changing labels; an attempted overwrite was correctly rejected and retained in `accounting-command-second-attempt.json`. `gates-final.json` is the authoritative computation pinned to the final audit bytes.
