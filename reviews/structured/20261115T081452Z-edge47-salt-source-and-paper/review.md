# Edge47 salt concentration source units and organism-matched full-text assessment

- Review: 20261115T081452Z-edge47-salt-source-and-paper
- Repository: CultureBotAI/EdgeMech
- Started UTC: 2026-11-15T08:10:29Z
- Finished UTC: 2026-11-15T08:14:52Z
- Reviewer: Codex agent (self_review)
- Completion: completed
- Verdict: needs_curation
- Scientific review: true

## Summary

The frozen source resolves the sampled value as reported NaCl 0-10%, positive growth, for BacDive 6845 (DSM 20190/CIP 103005). The percent basis and linked assay conditions remain unspecified. One complete primary paper was retrieved and inspected: Li et al. (2024) reports a different W. halotolerans isolate, GI38, growing at 3.0% and 6.5% w/v NaCl in MRS broth at 30°C for 2 days. It does not establish the original strain's full 0-10% range. Joined source context should be surfaced before wider review; discordant unused NCBI crosswalk fields need separate reconciliation. Historical decisions and graph status are unchanged.

## Scope And Provenance

One selected historical occurrence; recover its source measurement context and inspect one organism-matched primary paper. No population inference, crosswalk repair, or scientific-status promotion.

Selection: Explicit user-requested follow-up of canary ordinal 47 and its exact occurrence ID.
Coverage: full; 1 reviewed / 1 in the declared population.
Source: working_tree at Git base 4a6db624e0d4b18108b19e2a994261d1c2573635.
Working-tree hashes do not imply those bytes were committed.

| Target | Path / selector | Kind | Label |
| --- | --- | --- | --- |
| edge47-salt-concentration | artifacts/edge-recanary-20261113/canary.jsonl # canary_ordinal=47; occurrence_id=urn:kg-microbe:occurrence:v1:358f925d6342994dbe5598a3d3d2cdfafe3ad30028b7305c3cf21242cf3a9b57 | snapshot_row | Weissella halotolerans reported salt concentration 0-10 |

## Validation

| Check | Status | Required | Targets | Result |
| --- | --- | --- | --- | --- |
| Capture exact target and governing input hashes | passed | True | edge47-salt-concentration | The native inspector bound one occurrence to the frozen 100-row canary and inspected input bytes at 4a6db62. |
| Verify installed shared contract bytes | passed | True | edge47-salt-concentration | All 16 pinned contract files verified against CLAW commit 0ca25b8ee68d1fbccb4d05dcc2002fa8a64c0c34. |
| Replay exact frozen source records and current sibling binding | passed | True | edge47-salt-concentration | The retained trace helper checked two canonical frozen/raw record matches and the exact current concentration/unit source-record key. Current TSV bytes are not asserted identical to the historical release. |
| Retrieve and verify one complete primary article | passed | True | edge47-salt-concentration | Anonymous EuropePMC request saved 149817 XML bytes; primary metadata identifies PMC11117391 and DOI 10.3390/ani14101394, with a readable primary body. Persisted SHA256 matched. |
| Visually inspect the organism row and salt-assay columns | passed | True | edge47-salt-concentration | Two agents visually checked Figure 2. GI38(K) is positive at both salt concentrations; both axis headings explicitly state percent w/v. Methods and organism assignment were checked separately. |
| Determine applicable native review scope | not_applicable | False | edge47-salt-concentration | The pinned fleet manifest does not enable record_review for EdgeMech; an ignored-file-inclusive docs search found no local record-review-profile. The vendored schema is used for this one-off occurrence assessment, with no native fleet admission or status gate asserted. |

## Scientific And Domain Assessments

### Exact source organism and strain binding

identity: supported. Targets: edge47-salt-concentration.

LPSN 783091, BacDive 6845, and CIP 103005 bind the selected measurement to the W. halotolerans type strain. Discordant NCBI fields in the same CSV row were excluded.

### Recover the source-reported unit and measurement meaning

quantity: supported. Targets: edge47-salt-concentration.

The interpretable source report is NaCl 0-10%, positive growth. It is neither an optimum nor a demonstrated maximum tolerance, nor a statement that every strain grows throughout a continuous interval.

### Organism-matched full-paper assay

evidence: supported. Targets: edge47-salt-concentration.

For author-identified W. halotolerans GI38, Figure 2 shows positive growth at 3.0% and 6.5% w/v NaCl; Methods 2.3 supplies MRS broth, 30°C and 2 days. This is a distinct strain-specific observation.

### Independent verification of the original strain's complete range

grounding: unknown. Targets: edge47-salt-concentration.

The primary paper did not test the original source strain or 10% NaCl. BacDive's percentage basis and linked assay conditions remain unspecified. Numeric compatibility at two points for another strain is not replication of the reported range.

### Conditions for safely expanding review

representation: concern. Targets: edge47-salt-concentration.

The standalone label omits recoverable joint measurement context; the source row also contains an unrelated NCBI identity. Wider review should expose the complete context and maintain explicit identity exclusions before reuse.

## Findings

### quantity-context: Standalone review presentation omits recoverable measurement context

minor / open / confirmed; issue key: edge47-joint-measurement-context.

The source sidecar contains unit, salt, relation and growth result, but the displayed concentration label/literature packet does not assemble them. This is a presentation limitation, not evidence that the upstream transform lost the unit.

### discordant-crosswalk: Frozen source row contains an unrelated NCBI identity

major / deferred / confirmed; issue key: microbedecoder-record20904-ncbi-crosswalk.

The row's NCBI fields identify Brachybacterium muris/219301 while its LPSN/BacDive and independent strain authorities identify W. halotolerans. These NCBI fields were not used in this review. Current upstream remediation status has not been audited.

Disposition: Upstream crosswalk remediation is outside this one-record units/full-paper task. A separate issue records the defect and preserves the explicit exclusion from current evidence binding.

## Recommended Actions And Acceptance Checks

### assemble-measurement-context

Surface the joined quantity context in future review presentation using the exact frozen source-record binding.

- Edge47 displays NaCl, 0-10, percent, growth, positive and exact source/strain/reference together.
- Joins by species name alone or mismatched source records are refused.
- Unspecified percent basis and assay conditions stay unknown; no maximum or optimum is inferred.

### reconcile-crosswalk

Locate existing upstream quarantine/remediation for exact record 20904 and independently reconcile any proposed NCBI mapping before reuse.

- Evidence explicitly resolves the discordant organism identity or proves an existing quarantine for this source binding.
- No NCBI field from this row is silently propagated into the W. halotolerans measurement.

## Category Boundaries


## Evidence

| Evidence | Reference / locator | Support | Observation |
| --- | --- | --- | --- |
| frozen-target | artifacts/edge-recanary-20261113/canary.jsonl; canary_ordinal 47; exact occurrence selector in targets | context_only | The species-labelled occurrence asserts a reported source field value 0-10 and remains historically omitted as a redundant source attribute. The dataset citation is not a primary salt experiment. |
| frozen-csv | MicrobeDecoder database.csv; source-file SHA256 0c6ff730a108720a5d6972400f2bccf2eca8621713b62736abdf5df0fb188c95; CSV data record 20904; BacDive_Salt_concentration and BacDive_Salt_concentration_unit; frozen sidecar records[0].text | supports | Exact frozen row supplies 0-10 and percent together with LPSN 783091/BacDive 6845. Its unused NCBI fields instead name Brachybacterium muris/219301; those fields are excluded from organism binding. |
| frozen-bacdive | https://doi.org/10.13145/bacdive6845.20241212.9.2; BacDive 6845; Physiology and metabolism/halophily; frozen sidecar records[1].text | supports | The joint observation is NaCl, positive growth, 0-10%, reference 119830. Exact strain identity includes DSM 20190/ATCC 35410/CIP 103005. The observation has no specified percent basis or linked assay medium, temperature, duration, or negative upper endpoint. |
| current-bacdive | https://bacdive.dsmz.de/strain/6845; Halophily table and reference 119830; current public record | supports | The current public record corroborates the same joint observation and identifies its source as CIP curators. It is a current corroboration, not a replacement for the frozen source. |
| field-dictionary | https://api.bacdive.dsmz.de/strain_fields_information; physiology_metabolism/halophily fields salt, ability, test_type, salt_concentration, salt_concentration_unit | supports | Official definitions require interpreting salt, concentration, unit, relation and growth result together. They do not define all percentage values as w/v. |
| cip-identity | https://catalogue-crbip.pasteur.fr/fiche_catalogue.xhtml?crbip=CIP+103005; CIP 103005 culture identity and routine cultivation fields | context_only | CIP corroborates the type-strain identity. Its routine cultivation conditions are not a linked salt-assay protocol and were not attached to the halophily observation. |
| current-siblings | Current KG-Microbe transformed/microbedecoder/edges.tsv; lines 241350-241351; source_record sha256:0c6ff730a108720a5d6972400f2bccf2eca8621713b62736abdf5df0fb188c95#record=20904 | context_only | Current concentration and unit attributes share the exact source-record key. The current TSV is not claimed identical to the historical release whose sampled row number differs. |
| primary-paper | https://doi.org/10.3390/ani14101394; PMC11117391; Methods 2.3, Results 3.2-3.3, Table 1 and Figure 2; Discussion's reference 41 separately distinguished | partial | Li et al. (2024) tests 3.0% and 6.5% NaCl in MRS broth at 30°C for 2 days. Table 1 identifies GI38 as group K; Results 3.3 assigns it to W. halotolerans by 16S analysis. This different isolate supplies organism-matched evidence, not independent verification of DSM 20190/CIP 103005's entire 0-10% range. The discussion's 12% statement is a citation to Kandler (1983), not a new measurement. |
| primary-figure | https://pmc.ncbi.nlm.nih.gov/articles/PMC11117391/figure/animals-14-01394-f002/; Figure 2; third row GI38(K); NaCl 3 and NaCl 6.5 columns and positive legend | partial | Both NaCl axis headings explicitly state percent w/v; GI38(K) has positive-color cells at 3.0 and 6.5. This establishes the study assay basis directly from the figure, not from its unrelated 0.85% w/v dilution buffer. The basis is not transferred to BacDive's original observation. |

## Limits And Additional Notes

- Source-report support is not independent replication of the original strain's complete range or authorization for graph promotion.
- The original 0-10% observation does not state percentage basis, linked assay medium, temperature, duration, endpoint, test grid or negative upper bound; the absence claim is scoped to the inspected frozen/public records.
- GI38 is a different strain. Its percent w/v basis and experimental conditions cannot fill missing details in the BacDive 6845 observation.
- The paper's 12% statement cites 1983 work; it was not newly tested in the inspected 2024 experiment. Routine CIP culture conditions and the paper's 0.85% w/v dilution buffer were not borrowed as salt-assay evidence.
- Priority 1983 and 1993 papers were not obtained as full text through the bounded legal checks; 1993 Wiley retrieval returned 403. The complete 2024 primary paper was the inspected organism-matched alternative.
- Taxonomic assignment of GI38 is the authors' reported identification, not an independent sequence reanalysis.
- The current transformed sibling edges are not asserted byte-identical to the frozen release. Frozen raw evidence supplies the unit independently of this current corroboration.
- Raw source snapshots, copyrighted article bodies and images remain in ignored private staging. Public review evidence retains identifiers, hashes, precise locators and one short quotation.

## Complete Structured Record

The sibling review.yaml is authoritative.

```yaml
schema_version: 1.0.0
review_id: 20261115T081452Z-edge47-salt-source-and-paper
kind: record
repository: CultureBotAI/EdgeMech
title: Edge47 salt concentration source units and organism-matched full-text assessment
started_at: '2026-11-15T08:10:29Z'
finished_at: '2026-11-15T08:14:52Z'
reviewer:
  identity: Codex agent
  kind: agent
  independence: self_review
  independence_basis: The agent prepared retrieval/provenance helpers and assessed
    this bundle. A separate read-only agent checked the source and scientific scope;
    this is not independent experimental replication.
skill: lbnl-literature-and-db-access; lbnl-mech-record-review
completion: completed
verdict: needs_curation
native_verdict: SOURCE_REPORT_SUPPORTED; EXACT_ASSAY_RANGE_NOT_INDEPENDENTLY_VERIFIED
scientific_review: true
summary: 'The frozen source resolves the sampled value as reported NaCl 0-10%, positive
  growth, for BacDive 6845 (DSM 20190/CIP 103005). The percent basis and linked assay
  conditions remain unspecified. One complete primary paper was retrieved and inspected:
  Li et al. (2024) reports a different W. halotolerans isolate, GI38, growing at 3.0%
  and 6.5% w/v NaCl in MRS broth at 30°C for 2 days. It does not establish the original
  strain''s full 0-10% range. Joined source context should be surfaced before wider
  review; discordant unused NCBI crosswalk fields need separate reconciliation. Historical
  decisions and graph status are unchanged.'
source:
  git_revision: 4a6db624e0d4b18108b19e2a994261d1c2573635
  state: working_tree
  inputs:
  - path: artifacts/edge-recanary-20261113/canary.jsonl
    sha256: 76b4556e9bb62cde92eaed764710f8bbe4a420b016602be1945cb9ed3d53d703
    role: target
  - path: schema/record_review.yaml
    sha256: 229baf9b69118a1fe318e4c31085c0820e4e3d1365e7b04d6ace451b7c35f9bb
    role: context
  - path: scripts/adhoc/edge_recanary_20261113/build_targeting.py
    sha256: 7caacc5e881316fb116ebe72e4d80c01b1d976decf05a7e68539627313a92430
    role: context
scope:
  description: One selected historical occurrence; recover its source measurement
    context and inspect one organism-matched primary paper. No population inference,
    crosswalk repair, or scientific-status promotion.
  selection: Explicit user-requested follow-up of canary ordinal 47 and its exact
    occurrence ID.
  coverage: full
  population_size: 1
  reviewed_target_ids:
  - edge47-salt-concentration
  exclusions:
  - target: Other 99 retained canary records and remaining review population
    reason: No batch expansion is included.
  - target: Original source strain's full salt assay and upstream NCBI crosswalk remediation
    reason: The inspected records do not establish assay conditions or percentage
      basis; current upstream remediation status was not audited.
targets:
- target_id: edge47-salt-concentration
  path: artifacts/edge-recanary-20261113/canary.jsonl
  selector: canary_ordinal=47; occurrence_id=urn:kg-microbe:occurrence:v1:358f925d6342994dbe5598a3d3d2cdfafe3ad30028b7305c3cf21242cf3a9b57
  label: Weissella halotolerans reported salt concentration 0-10
  record_class: ReleaseOccurrence
  kind: snapshot_row
  ownership_note: Historical sample bytes are immutable. New interpretation belongs
    to EdgeMech review context; upstream scientific source and crosswalk ownership
    must be resolved before any correction outside this repository.
checks:
- check_id: input-inspection
  name: Capture exact target and governing input hashes
  status: passed
  required: true
  summary: The native inspector bound one occurrence to the frozen 100-row canary
    and inspected input bytes at 4a6db62.
  target_ids:
  - edge47-salt-concentration
  command: .venv/bin/python scripts/record_review.py inspect --targets .temp/salt-evidence-47-20261115/targets.yaml
    --input schema/record_review.yaml --input scripts/adhoc/edge_recanary_20261113/build_targeting.py
  exit_code: 0
  evidence_ids:
  - frozen-target
- check_id: pinned-contracts
  name: Verify installed shared contract bytes
  status: passed
  required: true
  summary: All 16 pinned contract files verified against CLAW commit 0ca25b8ee68d1fbccb4d05dcc2002fa8a64c0c34.
  target_ids:
  - edge47-salt-concentration
  command: .venv/bin/python -m edgemech check-contracts
  exit_code: 0
- check_id: source-replay
  name: Replay exact frozen source records and current sibling binding
  status: passed
  required: true
  summary: The retained trace helper checked two canonical frozen/raw record matches
    and the exact current concentration/unit source-record key. Current TSV bytes
    are not asserted identical to the historical release.
  target_ids:
  - edge47-salt-concentration
  exit_code: 0
  evidence_ids:
  - frozen-csv
  - frozen-bacdive
  - current-siblings
- check_id: fulltext-identity
  name: Retrieve and verify one complete primary article
  status: passed
  required: true
  summary: Anonymous EuropePMC request saved 149817 XML bytes; primary metadata identifies
    PMC11117391 and DOI 10.3390/ani14101394, with a readable primary body. Persisted
    SHA256 matched.
  target_ids:
  - edge47-salt-concentration
  exit_code: 0
  evidence_ids:
  - primary-paper
- check_id: figure-inspection
  name: Visually inspect the organism row and salt-assay columns
  status: passed
  required: true
  summary: Two agents visually checked Figure 2. GI38(K) is positive at both salt
    concentrations; both axis headings explicitly state percent w/v. Methods and organism
    assignment were checked separately.
  target_ids:
  - edge47-salt-concentration
  evidence_ids:
  - primary-paper
  - primary-figure
- check_id: fleet-native-profile
  name: Determine applicable native review scope
  status: not_applicable
  required: false
  summary: The pinned fleet manifest does not enable record_review for EdgeMech; an
    ignored-file-inclusive docs search found no local record-review-profile. The vendored
    schema is used for this one-off occurrence assessment, with no native fleet admission
    or status gate asserted.
  target_ids:
  - edge47-salt-concentration
evidence:
- evidence_id: frozen-target
  kind: record_content
  reference: artifacts/edge-recanary-20261113/canary.jsonl
  locator: canary_ordinal 47; exact occurrence selector in targets
  accessed_at: '2026-11-15T08:10:29Z'
  support: context_only
  summary: The species-labelled occurrence asserts a reported source field value 0-10
    and remains historically omitted as a redundant source attribute. The dataset
    citation is not a primary salt experiment.
  snapshot_sha256: 76b4556e9bb62cde92eaed764710f8bbe4a420b016602be1945cb9ed3d53d703
- evidence_id: frozen-csv
  kind: database
  reference: MicrobeDecoder database.csv; source-file SHA256 0c6ff730a108720a5d6972400f2bccf2eca8621713b62736abdf5df0fb188c95
  locator: CSV data record 20904; BacDive_Salt_concentration and BacDive_Salt_concentration_unit;
    frozen sidecar records[0].text
  accessed_at: '2026-11-15T08:14:10Z'
  support: supports
  summary: Exact frozen row supplies 0-10 and percent together with LPSN 783091/BacDive
    6845. Its unused NCBI fields instead name Brachybacterium muris/219301; those
    fields are excluded from organism binding.
  snapshot_sha256: 02f3965c70e68a1a2fa1d44f595af1d89165db4d5e7b75e2eed1aea1c92ebf89
- evidence_id: frozen-bacdive
  kind: database
  reference: https://doi.org/10.13145/bacdive6845.20241212.9.2
  locator: BacDive 6845; Physiology and metabolism/halophily; frozen sidecar records[1].text
  accessed_at: '2026-11-15T08:14:10Z'
  support: supports
  summary: The joint observation is NaCl, positive growth, 0-10%, reference 119830.
    Exact strain identity includes DSM 20190/ATCC 35410/CIP 103005. The observation
    has no specified percent basis or linked assay medium, temperature, duration,
    or negative upper endpoint.
  snapshot_sha256: 49506010e66f0b71b66f86485c9231af0ca2c059c4f266d762c15de6d1d402c0
- evidence_id: current-bacdive
  kind: database
  reference: https://bacdive.dsmz.de/strain/6845
  locator: Halophily table and reference 119830; current public record
  accessed_at: '2026-11-15T08:11:26Z'
  support: supports
  summary: The current public record corroborates the same joint observation and identifies
    its source as CIP curators. It is a current corroboration, not a replacement for
    the frozen source.
  snapshot_sha256: ee1b11f75ff8407505b4fb305bd808ec937ae5054e43e554fac9a82f879674b0
- evidence_id: field-dictionary
  kind: authority
  reference: https://api.bacdive.dsmz.de/strain_fields_information
  locator: physiology_metabolism/halophily fields salt, ability, test_type, salt_concentration,
    salt_concentration_unit
  accessed_at: '2026-11-15T08:12:00Z'
  support: supports
  summary: Official definitions require interpreting salt, concentration, unit, relation
    and growth result together. They do not define all percentage values as w/v.
  snapshot_sha256: 86016437a8c2f7d8b1e28bcde382c82e1b98cdfe1adf2fd4672eb8e0fbdfe7da
- evidence_id: cip-identity
  kind: database
  reference: https://catalogue-crbip.pasteur.fr/fiche_catalogue.xhtml?crbip=CIP+103005
  locator: CIP 103005 culture identity and routine cultivation fields
  accessed_at: '2026-11-15T08:11:58Z'
  support: context_only
  summary: CIP corroborates the type-strain identity. Its routine cultivation conditions
    are not a linked salt-assay protocol and were not attached to the halophily observation.
  snapshot_sha256: df18e8a9c8e4481ab6033df2d2a8d6ae15e9d73a8655f946fea1644433a64aa5
- evidence_id: current-siblings
  kind: record_content
  reference: Current KG-Microbe transformed/microbedecoder/edges.tsv
  locator: lines 241350-241351; source_record sha256:0c6ff730a108720a5d6972400f2bccf2eca8621713b62736abdf5df0fb188c95#record=20904
  accessed_at: '2026-11-15T08:14:10Z'
  support: context_only
  summary: Current concentration and unit attributes share the exact source-record
    key. The current TSV is not claimed identical to the historical release whose
    sampled row number differs.
  snapshot_sha256: 5476c0d905ad454e90ff86ec40c175a04d7bbe0c8b1475a23a20cab0b52615f9
- evidence_id: primary-paper
  kind: primary_source
  reference: https://doi.org/10.3390/ani14101394
  locator: PMC11117391; Methods 2.3, Results 3.2-3.3, Table 1 and Figure 2; Discussion's
    reference 41 separately distinguished
  accessed_at: '2026-11-15T08:14:10Z'
  support: partial
  summary: Li et al. (2024) tests 3.0% and 6.5% NaCl in MRS broth at 30°C for 2 days.
    Table 1 identifies GI38 as group K; Results 3.3 assigns it to W. halotolerans
    by 16S analysis. This different isolate supplies organism-matched evidence, not
    independent verification of DSM 20190/CIP 103005's entire 0-10% range. The discussion's
    12% statement is a citation to Kandler (1983), not a new measurement.
  quote: Salt tolerance was observed in the MRS broth containing 3.0% and 6.5% of
    NaCl
  snapshot_sha256: df87ed3eabcefee07f32f61c7b909e616dd072b1cd7ee7dafff42f5872345838
- evidence_id: primary-figure
  kind: primary_source
  reference: https://pmc.ncbi.nlm.nih.gov/articles/PMC11117391/figure/animals-14-01394-f002/
  locator: Figure 2; third row GI38(K); NaCl 3 and NaCl 6.5 columns and positive legend
  accessed_at: '2026-11-15T08:14:10Z'
  support: partial
  summary: Both NaCl axis headings explicitly state percent w/v; GI38(K) has positive-color
    cells at 3.0 and 6.5. This establishes the study assay basis directly from the
    figure, not from its unrelated 0.85% w/v dilution buffer. The basis is not transferred
    to BacDive's original observation.
  snapshot_sha256: 7a78e0701a9178c92ce5fd1cd5ea6f81079b786ca66a2adf3e81dc13e79fcaa5
assessments:
- assessment_id: source-identity
  area: identity
  topic: Exact source organism and strain binding
  outcome: supported
  summary: LPSN 783091, BacDive 6845, and CIP 103005 bind the selected measurement
    to the W. halotolerans type strain. Discordant NCBI fields in the same CSV row
    were excluded.
  target_ids:
  - edge47-salt-concentration
  evidence_ids:
  - frozen-csv
  - frozen-bacdive
  - cip-identity
- assessment_id: reported-measurement
  area: quantity
  topic: Recover the source-reported unit and measurement meaning
  outcome: supported
  summary: The interpretable source report is NaCl 0-10%, positive growth. It is neither
    an optimum nor a demonstrated maximum tolerance, nor a statement that every strain
    grows throughout a continuous interval.
  target_ids:
  - edge47-salt-concentration
  evidence_ids:
  - frozen-csv
  - frozen-bacdive
  - current-bacdive
  - field-dictionary
  dimensions:
  - name: concentration_as_reported
    value: 0-10%
    definition: Literal range and unit in the exact source observation; percentage
      basis unspecified.
    evidence_ids:
    - frozen-csv
    - frozen-bacdive
  - name: tested_relation
    value: positive growth with NaCl
    definition: Joint substance, result and relation from the same BacDive halophily
      observation.
    evidence_ids:
    - frozen-bacdive
- assessment_id: primary-assay
  area: evidence
  topic: Organism-matched full-paper assay
  outcome: supported
  summary: For author-identified W. halotolerans GI38, Figure 2 shows positive growth
    at 3.0% and 6.5% w/v NaCl; Methods 2.3 supplies MRS broth, 30°C and 2 days. This
    is a distinct strain-specific observation.
  target_ids:
  - edge47-salt-concentration
  evidence_ids:
  - primary-paper
  - primary-figure
  dimensions:
  - name: literature_channel
    value: europepmc_oa
    definition: One complete primary JATS article with exact identifiers and persisted
      bytes, plus its actual figure image.
    evidence_ids:
    - primary-paper
    - primary-figure
  - name: strain_scope
    value: GI38, group K; not asserted equivalent to DSM 20190/CIP 103005
    definition: Organism matching follows the paper's reported identification; culture-collection
      strain equivalence is not inferred.
    evidence_ids:
    - primary-paper
- assessment_id: original-assay-range
  area: grounding
  topic: Independent verification of the original strain's complete range
  outcome: unknown
  summary: The primary paper did not test the original source strain or 10% NaCl.
    BacDive's percentage basis and linked assay conditions remain unspecified. Numeric
    compatibility at two points for another strain is not replication of the reported
    range.
  target_ids:
  - edge47-salt-concentration
  evidence_ids:
  - frozen-bacdive
  - primary-paper
  - primary-figure
- assessment_id: context-and-crosswalk
  area: representation
  topic: Conditions for safely expanding review
  outcome: concern
  summary: The standalone label omits recoverable joint measurement context; the source
    row also contains an unrelated NCBI identity. Wider review should expose the complete
    context and maintain explicit identity exclusions before reuse.
  target_ids:
  - edge47-salt-concentration
  evidence_ids:
  - frozen-target
  - frozen-csv
  - frozen-bacdive
  - field-dictionary
findings:
- finding_id: quantity-context
  issue_key: edge47-joint-measurement-context
  category: representation
  severity: minor
  status: open
  certainty: confirmed
  title: Standalone review presentation omits recoverable measurement context
  description: The source sidecar contains unit, salt, relation and growth result,
    but the displayed concentration label/literature packet does not assemble them.
    This is a presentation limitation, not evidence that the upstream transform lost
    the unit.
  target_ids:
  - edge47-salt-concentration
  field_paths:
  - object_label
  - BacDive_Salt_concentration
  - BacDive_Salt_concentration_unit
  evidence_ids:
  - frozen-target
  - frozen-csv
  - frozen-bacdive
  - field-dictionary
  owner_paths:
  - repository: CultureBotAI/EdgeMech
    path: scripts/adhoc/edge_recanary_20261113/review_packet.py
    role: Render source-aware evidence for one frozen occurrence
  external_issues:
  - https://github.com/CultureBotAI/EdgeMech/issues/105
- finding_id: discordant-crosswalk
  issue_key: microbedecoder-record20904-ncbi-crosswalk
  category: identity
  severity: major
  status: deferred
  certainty: confirmed
  title: Frozen source row contains an unrelated NCBI identity
  description: The row's NCBI fields identify Brachybacterium muris/219301 while its
    LPSN/BacDive and independent strain authorities identify W. halotolerans. These
    NCBI fields were not used in this review. Current upstream remediation status
    has not been audited.
  target_ids:
  - edge47-salt-concentration
  field_paths:
  - NCBI_Genus
  - NCBI_Species
  - NCBI_Taxonomy_ID
  evidence_ids:
  - frozen-csv
  - frozen-bacdive
  - cip-identity
  ownership_note: The exact frozen crosswalk needs upstream MicrobeDecoder/KG-Microbe
    join-owner triage; EdgeMech must retain the exclusion until independently reconciled.
    Historical source bytes are not edited.
  disposition_reason: Upstream crosswalk remediation is outside this one-record units/full-paper
    task. A separate issue records the defect and preserves the explicit exclusion
    from current evidence binding.
  external_issues:
  - https://github.com/CultureBotAI/EdgeMech/issues/106
actions:
- action_id: assemble-measurement-context
  description: Surface the joined quantity context in future review presentation using
    the exact frozen source-record binding.
  finding_ids:
  - quantity-context
  target_ids:
  - edge47-salt-concentration
  owner_paths:
  - repository: CultureBotAI/EdgeMech
    path: scripts/adhoc/edge_recanary_20261113/review_packet.py
    role: Display source-derived measurement context without changing historical artifacts
  acceptance_checks:
  - Edge47 displays NaCl, 0-10, percent, growth, positive and exact source/strain/reference
    together.
  - Joins by species name alone or mismatched source records are refused.
  - Unspecified percent basis and assay conditions stay unknown; no maximum or optimum
    is inferred.
- action_id: reconcile-crosswalk
  description: Locate existing upstream quarantine/remediation for exact record 20904
    and independently reconcile any proposed NCBI mapping before reuse.
  finding_ids:
  - discordant-crosswalk
  target_ids:
  - edge47-salt-concentration
  ownership_note: Route through the upstream source/join owner; preserve the EdgeMech
    frozen snapshot and identity exclusion while current remediation status is established.
  acceptance_checks:
  - Evidence explicitly resolves the discordant organism identity or proves an existing
    quarantine for this source binding.
  - No NCBI field from this row is silently propagated into the W. halotolerans measurement.
limitations:
- Source-report support is not independent replication of the original strain's complete
  range or authorization for graph promotion.
- The original 0-10% observation does not state percentage basis, linked assay medium,
  temperature, duration, endpoint, test grid or negative upper bound; the absence
  claim is scoped to the inspected frozen/public records.
- GI38 is a different strain. Its percent w/v basis and experimental conditions cannot
  fill missing details in the BacDive 6845 observation.
- The paper's 12% statement cites 1983 work; it was not newly tested in the inspected
  2024 experiment. Routine CIP culture conditions and the paper's 0.85% w/v dilution
  buffer were not borrowed as salt-assay evidence.
- Priority 1983 and 1993 papers were not obtained as full text through the bounded
  legal checks; 1993 Wiley retrieval returned 403. The complete 2024 primary paper
  was the inspected organism-matched alternative.
- Taxonomic assignment of GI38 is the authors' reported identification, not an independent
  sequence reanalysis.
- The current transformed sibling edges are not asserted byte-identical to the frozen
  release. Frozen raw evidence supplies the unit independently of this current corroboration.
- Raw source snapshots, copyrighted article bodies and images remain in ignored private
  staging. Public review evidence retains identifiers, hashes, precise locators and
  one short quotation.
links:
- https://github.com/CultureBotAI/EdgeMech/issues/105
- https://github.com/CultureBotAI/EdgeMech/issues/106
- https://bacdive.dsmz.de/strain/6845
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11117391/
tags:
- salt
- source-provenance
- strain-scope
- bounded-review
```
