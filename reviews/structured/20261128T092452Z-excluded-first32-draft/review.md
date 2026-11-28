# Exposed partial first-32 taxon crosswalk assessment draft

- Review: 20261128T092452Z-excluded-first32-draft
- Repository: CultureBotAI/EdgeMech
- Started UTC: 2026-11-28T09:24:52Z
- Finished UTC: 2026-11-28T09:24:52.898300Z
- Reviewer: edgemech-native-reviewer-01 (self_review)
- Completion: partial
- Verdict: needs_curation
- Scientific review: true

## Summary

Retained-version authorities contradict the crosswalk while validating both individual endpoint meanings; original generation fidelity remains not assessable. Exposed first-32 preparation only; no production, Queue A/B, blinded calibration or paper-access credit.

## Scope And Provenance

Exposed first-32 preparation only; no production, Queue A/B, blinded calibration or paper-access credit.

Selection: Exactly one user-designated exposed first-32 occurrence; not Queue A/B or a replacement ten-case round.
Coverage: partial; 1 reviewed / 1 in the declared population.
Source: working_tree at Git base 5d470683823323e2dd8d72e08c49ade138229dc6.
Working-tree hashes do not imply those bytes were committed.

| Target | Path / selector | Kind | Label |
| --- | --- | --- | --- |
| urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b | .temp/first32-worker-20261128/draft-07/packet.json # occurrence_id=urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b | snapshot_row | first-32 original crosswalk |

## Validation

| Check | Status | Required | Targets | Result |
| --- | --- | --- | --- | --- |
| Exact input and native packet replay | passed | True | urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b | Pinned original bytes and rebuilt packet replay passed; only private-copy paths changed. |
| Literal authority offset and budget replay | passed | True | urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b | Exact native character and UTF8 byte spans replayed, with conservative repeated-role budgets &lt;=25 per authority. |
| Original version-specific emission lineage | unavailable | True | urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b | Exact source-row co-occurrence is replayed, but the original producer's version-specific field-to-close_match semantics and full emission lineage are not established. |
| Experimental literature for structural crosswalk | not_applicable | False | urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b | Identifier definitions and relation semantics govern this assertion; no paper-access credit. |

## Scientific And Domain Assessments

### claim

evidence: concern. Targets: urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b.

The retained authorities identify an archaeal species and a bacterial E.coli strain, contradicting the asserted semantic taxon correspondence within these versions.

### literature

evidence: not_applicable. Targets: urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b.

Experimental literature is inapplicable to this structural crosswalk. Taxonomic definitions and mapping semantics govern; no experimental-paper/fulltext credit is claimed.

### relation

evidence: concern. Targets: urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b.

The original close_match relation fails semantic similarity, despite valid broad endpoint categories and symmetry.

### subject_node

evidence: supported. Targets: urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b.

The subject identifier, label, species rank and organism-taxon meaning are correct within the retained authority scope.

### object_node

evidence: supported. Targets: urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b.

The object identifier, label, strain rank and organism-taxon meaning are correct within the retained authority scope.

### source_fidelity

evidence: unknown. Targets: urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b.

Exact source-row co-occurrence is replayed, but the original producer's version-specific field-to-close_match semantics and full emission lineage are not established.

## Findings

### crosswalk-mismatch: Crosswalk links distinct taxon concepts

major / open / confirmed; issue key: first32-crosswalk-mismatch.

Version-scoped archaeal species versus bacterial E.coli strain mismatch; this finding does not invalidate the individual IDs or propose a replacement ID.

## Recommended Actions And Acceptance Checks

### trace-crosswalk

Request owner review of original-version source field and crosswalk emission; preserve exact occurrence and seek evidence before proposing any identifier correction.

- Establish original-generation lineage and field semantics
- Independently review retained endpoint meanings and relation applicability
- Do not invent a corrected ID or edit frozen source bytes

## Category Boundaries


## Evidence

| Evidence | Reference / locator | Support | Observation |
| --- | --- | --- | --- |
| lpsn-name-rank-supports | https://lpsn.dsmz.de/species/methanomethylophilus-alvi; lpsn retained native document; name-rank; chars 379:412 | supports | Endpoint identity evidence |
| lpsn-identifier-supports | https://lpsn.dsmz.de/species/methanomethylophilus-alvi; lpsn retained native document; identifier; chars 3052:3072 | supports | Endpoint identity evidence |
| lpsn-lineage-supports | https://lpsn.dsmz.de/species/methanomethylophilus-alvi; lpsn retained native document; lineage; chars 460:485 | supports | Endpoint identity evidence |
| lpsn-name-rank-refutes | https://lpsn.dsmz.de/species/methanomethylophilus-alvi; lpsn retained native document; name-rank; chars 379:412 | refutes | Version-scoped crosswalk counterevidence |
| lpsn-identifier-refutes | https://lpsn.dsmz.de/species/methanomethylophilus-alvi; lpsn retained native document; identifier; chars 3052:3072 | refutes | Version-scoped crosswalk counterevidence |
| lpsn-lineage-refutes | https://lpsn.dsmz.de/species/methanomethylophilus-alvi; lpsn retained native document; lineage; chars 460:485 | refutes | Version-scoped crosswalk counterevidence |
| ncbi-identifier-name-supports | https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1281099; ncbi retained native document; identifier-name; chars 171:267 | supports | Endpoint identity evidence |
| ncbi-rank-lineage-supports | https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1281099; ncbi retained native document; rank-lineage; chars 307:360 | supports | Endpoint identity evidence |
| ncbi-identifier-name-refutes | https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1281099; ncbi retained native document; identifier-name; chars 171:267 | refutes | Version-scoped crosswalk counterevidence |
| ncbi-rank-lineage-refutes | https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1281099; ncbi retained native document; rank-lineage; chars 307:360 | refutes | Version-scoped crosswalk counterevidence |
| biolink-relation | https://raw.githubusercontent.com/biolink/biolink-model/v4.4.0/biolink-model.yaml; Biolink4.4.0 close match or organism taxon definition; chars 87655:87703 | refutes | Crosswalk fails semantic-similarity criterion |
| biolink-taxon | https://raw.githubusercontent.com/biolink/biolink-model/v4.4.0/biolink-model.yaml; Biolink4.4.0 close match or organism taxon definition; chars 250839:250876 | supports | OrganismTaxon category applicability |
| biolink-strain | https://raw.githubusercontent.com/biolink/biolink-model/v4.4.0/biolink-model.yaml; Biolink4.4.0 close match or organism taxon definition; chars 250993:251015 | supports | OrganismTaxon category applicability |
| source-packet | .temp/first32-worker-20261128/draft-07/packet.json; original_assertion; source_records[0]; CSV data row10743 | context_only | Exact row co-occurrence and packet replay, not complete generation fidelity |

## Limits And Additional Notes

- Exact source-row co-occurrence is replayed, but the original producer's version-specific field-to-close_match semantics and full emission lineage are not established.
- Exposed first-32 preparation only; no production, Queue A/B, blinded calibration or paper-access credit.
- No current authority refresh or historical snapshot reconstruction. Retrieval and update dates remain distinct.
- Generic packet measurement_context remains unresolved; experimental measurements, units and conditions are inapplicable to this structural claim.
- Draft validation is transport/provenance validation, not scientific approval, canonical persistence or exact-runtime admission.
- Biolink OrganismTaxon semantic applicability does not certify LPSN prefix-policy conformance; no original-generating-model version recovered.
- Production scientific coverage0; A/B and cutoff null; all694 candidates retained; historical census outerFAILED1/childUNKNOWN unchanged.
- Complete private authority contexts retained; only bounded literal excerpts used as proof quotes.

## Complete Structured Record

The sibling review.yaml is authoritative.

```yaml
schema_version: 1.0.0
review_id: 20261128T092452Z-excluded-first32-draft
kind: record
repository: CultureBotAI/EdgeMech
skill: edgemech-occurrence-review/v1
title: Exposed partial first-32 taxon crosswalk assessment draft
started_at: '2026-11-28T09:24:52Z'
finished_at: '2026-11-28T09:24:52.898300Z'
reviewer:
  identity: edgemech-native-reviewer-01
  kind: agent
  model: gpt-6-astra
  independence: self_review
  independence_basis: Explicitly exposed retained fixed case; read coordinator narrative
    and historical annotations in source. New judgments from inspected source/authorities;
    not blinded agreement.
completion: partial
verdict: needs_curation
scientific_review: true
summary: Retained-version authorities contradict the crosswalk while validating both
  individual endpoint meanings; original generation fidelity remains not assessable.
  Exposed first-32 preparation only; no production, Queue A/B, blinded calibration
  or paper-access credit.
source:
  git_revision: 5d470683823323e2dd8d72e08c49ade138229dc6
  state: working_tree
  inputs:
  - path: .temp/first32-worker-20261128/draft-07/authored-spec.json
    sha256: f6f7b7b67d73cc620f0396c71bdcf7824b3349dea650e264fa2edb6fc2b94e41
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/authority/instruction-00.md
    sha256: bb07a3992f66f066d11e83860c8b11a9e48f2c20c6fd28fa4c1dd9466fdb9c28
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/authority/instruction-01.md
    sha256: 172f87b8f2a1e2860944d56144701a2825d1153d5eb094f29a4c6b3faaf0437e
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/authority/instruction-02.md
    sha256: 6c8fe7a82840ca3bb8e1b9a23bc253a6b4b0d8ba9cf55106ba792a5f9cc1fb79
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/authority/instruction-03.md
    sha256: b91e34600ef30bf0ec54c82cf497d40453d8a84188a8fea61f60ee6d53ef23a2
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/authority/instruction-04.md
    sha256: 33f7ec41e27cfaa2e075d53fb23d3601e6575514db41943f82a0c158968ffcd6
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/authority/instruction-05.md
    sha256: 27dfca51a1cc0804e5721e140df95b8440313a9815e6918d944aa9099044f703
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/coordinator-changes.json
    sha256: 7ca9db01c7572f077ab8146343f2181faa24bfa7e0700afb35b777c41960dbe4
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/current-native-metadata.json
    sha256: bd0c5210d93f8ea62be43021d5a7e6449767578026c9848e37478bfbb45fd6f0
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/expected-native.json
    sha256: 80b280d9b1112c739d82a17f05d01c7333b870ac0699dc2b16fb25d01173ca49
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/identity-binding.json
    sha256: bb6c0cd9de134c6553dc888d586abb3e42cb3225a48463ad60318e9945360b8e
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/input-bundle.json
    sha256: bfc95bcd7e8d58968e70c8b0947a0c4e75e5260ac582517ada9374354ea146a6
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/input-manifest.json
    sha256: daff3d0be9fc49f26e1cdcfa7d2c6778f0b1ade7e7da6fdd67526f799a5f7179
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/inputs/biolink.txt
    sha256: 4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/inputs/lpsn-view-receipt.json
    sha256: e5d2609642ebf70e9f49aa4534d59fb155a77aaa7ef8fe03405f0f82e4b3c6d3
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/inputs/lpsn.txt
    sha256: b0d4c227cf90f01256edd978d913821d8ad38dc1d15b6850b0ca9d2abb445875
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/inputs/ncbi.txt
    sha256: 37433381f5915338ee3e342a85ea15e8417fcf7b9bb7f08871cac084f958490d
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/inputs/occurrence.json
    sha256: d80216b91e94eec7e6fe6f8feaf070539286ab7f4601f056562b99b9a2e81c3a
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/inputs/retained-manifest.json
    sha256: 3928396bf4c089620ec0209fdcb986c14f36969259ed01ab563c6807037ee298
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/inputs/retained-packet.json
    sha256: 32cb804b4f6e0f678f01faf3ecf351146101d1beb0abe6e77ecbffedd470ded2
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/inputs/source.json
    sha256: 5c1d2f4d001642bc136718e7ddd67d231d9ca0589b6c406a5d110dd6a6dcdc1e
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/literal-replay.json
    sha256: 9979bec0af1a20ddf8849752a7c8642e087568bcad4d31366a15d243522dee15
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/packet.json
    sha256: c4f8393cd4e0c1dbc0d8b6ea9cd80815cdc7da11641e237af2da8150c6e0df28
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/producer.py.original
    sha256: 70697b6711209db53004250e6c0bfd912d93c808bdd150493e5c7fa3de62a6e4
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/proofs.json
    sha256: 73e2d9073e64592c215a02efc61c3b04c1b6378d01b7274622cc80532fc01431
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_curation/__init__.py
    sha256: fd05790537bfaa2eb7d05fc1595d75b30e4f4b785e18805006b6ef444c5c51c7
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_curation/artifact.py
    sha256: dbbf5b31256258ec75325a7bb5222d4adc43773731f7780100afbe0dd3f27ee5
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_curation/contract.py
    sha256: d9eb93add3fbb438cbd6008767b28a0c4eadfbc03688462d490c965ff034268e
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_curation/identity.py
    sha256: 9c760f3e82051d24b3c1cc79d787e96b35e24529b4ead9254ff55adc1266b948
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_curation/ledger.py
    sha256: 626f473e4e32ce70518c2413cd4980700726d0d8d5c22be48a62400742b8f9d1
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_curation/native.py
    sha256: 51b28b232eb9db0fee9eaf35326a0eb1a3aa4924a7341aa4db9f9bca9da5b84f
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_curation/schema/artifact.json
    sha256: 36f1542e2b570e58ba4a59846a1916a79e1fd51c4c56f4450131993912bf4d08
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_curation/schema/bundle.json
    sha256: 04db51cdeebf19b36d68ea8dae88ebabb9910e8f4eb03e31aff8d46f2902fb5e
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_curation/schema/native_assertion.json
    sha256: 0bb7ebf25e0e1bea9fea17d47981b2773b16f3fa8cdbed31686bccdaeaaa5124
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_governance/__init__.py
    sha256: 69be964b3a65cc7e61d309f3c7e7a2c2f17a0e0fe4de75b5cf5659b053f5bbce
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_governance/artifacts/__init__.py
    sha256: 4e47389554e9e8d6e05a90ecf7dc6ad5708f08e56d012d9129970d58b9c6d069
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_governance/artifacts/schema/record_review.yaml
    sha256: 6fd8191b6c039b822b23245a0ab312697df9c2ff1c6c27989ce7b1f62d00e6d3
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_governance/artifacts/scripts/__init__.py
    sha256: f04a7a4160750e47ff2bee761c610ed7f4d12f6f50b914dd3527ec672ebc1af2
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_governance/artifacts/scripts/check_vendored_sync.py
    sha256: fa527882d9a50ec3f49148afe0032ecc65a2a3c3eb31d62bdfc14fa7104e7bfb
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_governance/artifacts/scripts/record_review.py
    sha256: 292ab82fecd0b01ef2760d0b251f30ae27263aa0e65a789dfd25e4530bed0da0
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime/contracts/kg_microbe_reviews/__init__.py
    sha256: 00d7e11fa36a0424fb28fbbe3ca4fb381bc77bc3bd588ab1b46c65a58de141aa
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/draft-07/runtime-manifest.json
    sha256: ef4c7c734ee513c12e08e350b2a1f696368643afa6b380ea154be7e9c9efd0e4
    role: Exact private draft/source/runtime input
  - path: docs/record-review-profile.md
    sha256: c472d9a4910f40028eff2e0912e9b4ea8dadcc0b1173cefdb6f933db40345c34
    role: Exact private draft/source/runtime input
  - path: pyproject.toml
    sha256: 54b8a153dca2b941ad1add1abf7cb7408324eba3457e519aa8e1bd87c70c63cb
    role: Exact private draft/source/runtime input
  - path: schema/record_review.yaml
    sha256: 6fd8191b6c039b822b23245a0ab312697df9c2ff1c6c27989ce7b1f62d00e6d3
    role: Exact private draft/source/runtime input
  - path: scripts/adhoc/author_m5_review_data_20261116.py
    sha256: c1d847f7d8b677e3ddca8c8615986267d295fdb1eaa57ed627d5c0bae830ada3
    role: Exact private draft/source/runtime input
  - path: scripts/adhoc/calibration_round_20261116.py
    sha256: f9971d269f9b78b0e751fd14fd78f456a90c7b61cbfa436eaac82fc3407ffa26
    role: Exact private draft/source/runtime input
  - path: scripts/adhoc/prepare_first32_native_20261128.py
    sha256: 70697b6711209db53004250e6c0bfd912d93c808bdd150493e5c7fa3de62a6e4
    role: Exact private draft/source/runtime input
  - path: src/edgemech/contract-pins.json
    sha256: e15d37c98777e6eeac5c2d24389d22f26fc3b601ba1b1873855f19d93e77bcbd
    role: Exact private draft/source/runtime input
  - path: src/edgemech/literature_cache.py
    sha256: 12e3d920e2a9978c25b5d7626aae087ccd089609c367339a240eb8f37b7a3fef
    role: Exact private draft/source/runtime input
  - path: src/edgemech/occurrence_packet.py
    sha256: 7526fcb6f4467a342abc644c8f607b9b8c6fb395eac159c61f4654594cc490d7
    role: Exact private draft/source/runtime input
  - path: src/edgemech/occurrence_review.py
    sha256: c977e3170b470292a1715efba3e737d704929af7b4319635bdb262f44fe029d4
    role: Exact private draft/source/runtime input
  - path: src/edgemech/pins.py
    sha256: 1287b62bc74e6b50e1335d14160db575fc095e90aadd76c50713cf7a5329f137
    role: Exact private draft/source/runtime input
  - path: src/edgemech/storage/parquet.py
    sha256: 6f821fb6ce4dde27041fd85bbd6118106642566edad049fe6d4efa7688578dc9
    role: Exact private draft/source/runtime input
  - path: tests/test_prepare_first32_native_20261128.py
    sha256: f74763410690b49f5c14f029391a8f920f63c79cc9a84e2ca4a39e94654b5aae
    role: Exact private draft/source/runtime input
  - path: uv.lock
    sha256: ffdec65db5f8ff7e6b32fd751f655eea1881d0305553c5bb154e3195a70f1033
    role: Exact private draft/source/runtime input
  - path: .temp/first32-worker-20261128/acceptance-01/ACCEPTANCE.json
    sha256: 28433c95baccd7e676ce7f13a20dd9ec458a006d27b5437282a772a87eec4b3d
    role: Exact private draft/source/runtime input
scope:
  description: Exposed first-32 preparation only; no production, Queue A/B, blinded
    calibration or paper-access credit.
  selection: Exactly one user-designated exposed first-32 occurrence; not Queue A/B
    or a replacement ten-case round.
  coverage: partial
  population_size: 1
  reviewed_target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
targets:
- target_id: urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  path: .temp/first32-worker-20261128/draft-07/packet.json
  selector: occurrence_id=urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  label: first-32 original crosswalk
  kind: snapshot_row
  ownership_note: The upstream MicrobeDecoder crosswalk producer/source-field owner
    must establish original-version lineage before any correction; frozen occurrence
    bytes are not edited.
checks:
- check_id: retained-replay
  name: Exact input and native packet replay
  status: passed
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  summary: Pinned original bytes and rebuilt packet replay passed; only private-copy
    paths changed.
- check_id: quote-replay
  name: Literal authority offset and budget replay
  status: passed
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  summary: Exact native character and UTF8 byte spans replayed, with conservative
    repeated-role budgets <=25 per authority.
- check_id: original-generation
  name: Original version-specific emission lineage
  status: unavailable
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  summary: Exact source-row co-occurrence is replayed, but the original producer's
    version-specific field-to-close_match semantics and full emission lineage are
    not established.
- check_id: experimental-paper
  name: Experimental literature for structural crosswalk
  status: not_applicable
  required: false
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  summary: Identifier definitions and relation semantics govern this assertion; no
    paper-access credit.
evidence:
- evidence_id: lpsn-name-rank-supports
  kind: authority
  reference: https://lpsn.dsmz.de/species/methanomethylophilus-alvi
  locator: lpsn retained native document; name-rank; chars 379:412
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: supports
  summary: Endpoint identity evidence
  snapshot_sha256: b0d4c227cf90f01256edd978d913821d8ad38dc1d15b6850b0ca9d2abb445875
  quote: Species Methanomethylophilus alvi
- evidence_id: lpsn-identifier-supports
  kind: authority
  reference: https://lpsn.dsmz.de/species/methanomethylophilus-alvi
  locator: lpsn retained native document; identifier; chars 3052:3072
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: supports
  summary: Endpoint identity evidence
  snapshot_sha256: b0d4c227cf90f01256edd978d913821d8ad38dc1d15b6850b0ca9d2abb445875
  quote: 'Record number: 46511'
- evidence_id: lpsn-lineage-supports
  kind: authority
  reference: https://lpsn.dsmz.de/species/methanomethylophilus-alvi
  locator: lpsn retained native document; lineage; chars 460:485
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: supports
  summary: Endpoint identity evidence
  snapshot_sha256: b0d4c227cf90f01256edd978d913821d8ad38dc1d15b6850b0ca9d2abb445875
  quote: Archaea Methanobacteriati
- evidence_id: lpsn-name-rank-refutes
  kind: authority
  reference: https://lpsn.dsmz.de/species/methanomethylophilus-alvi
  locator: lpsn retained native document; name-rank; chars 379:412
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: refutes
  summary: Version-scoped crosswalk counterevidence
  snapshot_sha256: b0d4c227cf90f01256edd978d913821d8ad38dc1d15b6850b0ca9d2abb445875
  quote: Species Methanomethylophilus alvi
- evidence_id: lpsn-identifier-refutes
  kind: authority
  reference: https://lpsn.dsmz.de/species/methanomethylophilus-alvi
  locator: lpsn retained native document; identifier; chars 3052:3072
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: refutes
  summary: Version-scoped crosswalk counterevidence
  snapshot_sha256: b0d4c227cf90f01256edd978d913821d8ad38dc1d15b6850b0ca9d2abb445875
  quote: 'Record number: 46511'
- evidence_id: lpsn-lineage-refutes
  kind: authority
  reference: https://lpsn.dsmz.de/species/methanomethylophilus-alvi
  locator: lpsn retained native document; lineage; chars 460:485
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: refutes
  summary: Version-scoped crosswalk counterevidence
  snapshot_sha256: b0d4c227cf90f01256edd978d913821d8ad38dc1d15b6850b0ca9d2abb445875
  quote: Archaea Methanobacteriati
- evidence_id: ncbi-identifier-name-supports
  kind: authority
  reference: https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1281099
  locator: ncbi retained native document; identifier-name; chars 171:267
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: supports
  summary: Endpoint identity evidence
  snapshot_sha256: 37433381f5915338ee3e342a85ea15e8417fcf7b9bb7f08871cac084f958490d
  quote: "<TaxId>1281099</TaxId>\n    <ScientificName>Escherichia coli HVH 169 (4-1075578)</ScientificName>"
- evidence_id: ncbi-rank-lineage-supports
  kind: authority
  reference: https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1281099
  locator: ncbi retained native document; rank-lineage; chars 307:360
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: supports
  summary: Endpoint identity evidence
  snapshot_sha256: 37433381f5915338ee3e342a85ea15e8417fcf7b9bb7f08871cac084f958490d
  quote: "<Rank>strain</Rank>\n    <Division>Bacteria</Division>"
- evidence_id: ncbi-identifier-name-refutes
  kind: authority
  reference: https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1281099
  locator: ncbi retained native document; identifier-name; chars 171:267
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: refutes
  summary: Version-scoped crosswalk counterevidence
  snapshot_sha256: 37433381f5915338ee3e342a85ea15e8417fcf7b9bb7f08871cac084f958490d
  quote: "<TaxId>1281099</TaxId>\n    <ScientificName>Escherichia coli HVH 169 (4-1075578)</ScientificName>"
- evidence_id: ncbi-rank-lineage-refutes
  kind: authority
  reference: https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=1281099
  locator: ncbi retained native document; rank-lineage; chars 307:360
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: refutes
  summary: Version-scoped crosswalk counterevidence
  snapshot_sha256: 37433381f5915338ee3e342a85ea15e8417fcf7b9bb7f08871cac084f958490d
  quote: "<Rank>strain</Rank>\n    <Division>Bacteria</Division>"
- evidence_id: biolink-relation
  kind: authority
  reference: https://raw.githubusercontent.com/biolink/biolink-model/v4.4.0/biolink-model.yaml
  locator: Biolink4.4.0 close match or organism taxon definition; chars 87655:87703
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: refutes
  summary: Crosswalk fails semantic-similarity criterion
  snapshot_sha256: 4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb
  quote: semantically similar but not strictly equivalent
- evidence_id: biolink-taxon
  kind: authority
  reference: https://raw.githubusercontent.com/biolink/biolink-model/v4.4.0/biolink-model.yaml
  locator: Biolink4.4.0 close match or organism taxon definition; chars 250839:250876
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: supports
  summary: OrganismTaxon category applicability
  snapshot_sha256: 4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb
  quote: classification of a set of organisms.
- evidence_id: biolink-strain
  kind: authority
  reference: https://raw.githubusercontent.com/biolink/biolink-model/v4.4.0/biolink-model.yaml
  locator: Biolink4.4.0 close match or organism taxon definition; chars 250993:251015
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: supports
  summary: OrganismTaxon category applicability
  snapshot_sha256: 4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb
  quote: strains or subspecies.
- evidence_id: source-packet
  kind: record_content
  reference: .temp/first32-worker-20261128/draft-07/packet.json
  locator: original_assertion; source_records[0]; CSV data row10743
  accessed_at: '2026-11-28T09:24:52.890906Z'
  support: context_only
  summary: Exact row co-occurrence and packet replay, not complete generation fidelity
  snapshot_sha256: c4f8393cd4e0c1dbc0d8b6ea9cd80815cdc7da11641e237af2da8150c6e0df28
assessments:
- assessment_id: claim
  area: evidence
  topic: claim
  outcome: concern
  summary: The retained authorities identify an archaeal species and a bacterial E.coli
    strain, contradicting the asserted semantic taxon correspondence within these
    versions.
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  evidence_ids:
  - lpsn-name-rank-refutes
  - lpsn-identifier-refutes
  - lpsn-lineage-refutes
  - ncbi-identifier-name-refutes
  - ncbi-rank-lineage-refutes
  dimensions:
  - name: axis
    value: claim
    definition: axis
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
  - name: category
    value: CONTRADICTED_AS_STATED
    definition: category
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
  - name: scope
    value: Original lpsn:46511 biolink:close_match / skos:closeMatch NCBITaxon:1281099
      assertion; authority versions retained November16, evaluated in exposed preparation.
    definition: scope
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
  - name: assertion_scope
    value: Original lpsn:46511 biolink:close_match / skos:closeMatch NCBITaxon:1281099
      assertion; authority versions retained November16, evaluated in exposed preparation.
      This is semantic correspondence between taxon concepts, not a source-report
      reinterpretation or an experimental phenotype claim.
    definition: assertion_scope
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
- assessment_id: literature
  area: evidence
  topic: literature
  outcome: not_applicable
  summary: Experimental literature is inapplicable to this structural crosswalk. Taxonomic
    definitions and mapping semantics govern; no experimental-paper/fulltext credit
    is claimed.
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  evidence_ids: []
  dimensions:
  - name: axis
    value: literature
    definition: axis
    evidence_ids: []
  - name: category
    value: NOT_APPLICABLE
    definition: category
    evidence_ids: []
  - name: scope
    value: Original lpsn:46511 biolink:close_match / skos:closeMatch NCBITaxon:1281099
      assertion; authority versions retained November16, evaluated in exposed preparation.
    definition: scope
    evidence_ids: []
  - name: search_scope
    value: Classified the exact retained assertion and source row as an identifier
      crosswalk. Used retained taxonomic definitions and Biolink semantics; no paper
      search/retrieval or paper proof. Embedded DOI/PMID enrichments are source context,
      not experimental crosswalk support or paper-access credit.
    definition: search_scope
    evidence_ids: []
- assessment_id: relation
  area: evidence
  topic: relation
  outcome: concern
  summary: The original close_match relation fails semantic similarity, despite valid
    broad endpoint categories and symmetry.
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  evidence_ids:
  - lpsn-name-rank-refutes
  - lpsn-identifier-refutes
  - lpsn-lineage-refutes
  - ncbi-identifier-name-refutes
  - ncbi-rank-lineage-refutes
  - biolink-relation
  dimensions:
  - name: axis
    value: relation
    definition: axis
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
    - biolink-relation
  - name: category
    value: INCORRECT
    definition: category
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
    - biolink-relation
  - name: scope
    value: Original lpsn:46511 biolink:close_match / skos:closeMatch NCBITaxon:1281099
      assertion; authority versions retained November16, evaluated in exposed preparation.
    definition: scope
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
    - biolink-relation
  - name: direction
    value: Biolink4.4.0 close match is symmetric and exactly maps to skos:closeMatch;
      reversing endpoints cannot repair the taxon mismatch.
    definition: direction
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
    - biolink-relation
  - name: domain_range
    value: The inspected close match -> related to at concept level -> related to
      hierarchy permits named things; two OrganismTaxon instances satisfy broad category
      compatibility but this does not establish conceptual similarity.
    definition: domain_range
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
    - biolink-relation
  - name: specificity
    value: An archaeal species and an Escherichia coli bacterial strain do not express
      the same general taxon concept under the inspected model semantics.
    definition: specificity
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
    - biolink-relation
  - name: qualifiers
    value: No qualifier repairs the crosswalk. Exact generating-graph model version
      is unavailable; judgment is explicitly version-scoped.
    definition: qualifiers
    evidence_ids:
    - lpsn-name-rank-refutes
    - lpsn-identifier-refutes
    - lpsn-lineage-refutes
    - ncbi-identifier-name-refutes
    - ncbi-rank-lineage-refutes
    - biolink-relation
- assessment_id: subject_node
  area: evidence
  topic: subject_node
  outcome: supported
  summary: The subject identifier, label, species rank and organism-taxon meaning
    are correct within the retained authority scope.
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  evidence_ids:
  - lpsn-name-rank-supports
  - lpsn-identifier-supports
  - lpsn-lineage-supports
  - biolink-taxon
  dimensions:
  - name: axis
    value: subject_node
    definition: axis
    evidence_ids:
    - lpsn-name-rank-supports
    - lpsn-identifier-supports
    - lpsn-lineage-supports
    - biolink-taxon
  - name: category
    value: CORRECT
    definition: category
    evidence_ids:
    - lpsn-name-rank-supports
    - lpsn-identifier-supports
    - lpsn-lineage-supports
    - biolink-taxon
  - name: scope
    value: Original lpsn:46511 biolink:close_match / skos:closeMatch NCBITaxon:1281099
      assertion; authority versions retained November16, evaluated in exposed preparation.
    definition: scope
    evidence_ids:
    - lpsn-name-rank-supports
    - lpsn-identifier-supports
    - lpsn-lineage-supports
    - biolink-taxon
  - name: identity
    value: Retained LPSN view explicitly identifies record46511 as Methanomethylophilus
      alvi.
    definition: identity
    evidence_ids:
    - lpsn-name-rank-supports
    - lpsn-identifier-supports
    - lpsn-lineage-supports
    - biolink-taxon
  - name: label
    value: The encoded subject label matches the retained LPSN species name.
    definition: label
    evidence_ids:
    - lpsn-name-rank-supports
    - lpsn-identifier-supports
    - lpsn-lineage-supports
    - biolink-taxon
  - name: category_fit
    value: Biolink4.4.0 OrganismTaxon describes a classification of organisms, fitting
      this species; this does not certify strict prefix-policy conformance or generating-version
      admissibility.
    definition: category_fit
    evidence_ids:
    - lpsn-name-rank-supports
    - lpsn-identifier-supports
    - lpsn-lineage-supports
    - biolink-taxon
  - name: rank_or_type
    value: Species in retained LPSN snapshot; archaeal lineage.
    definition: rank_or_type
    evidence_ids:
    - lpsn-name-rank-supports
    - lpsn-identifier-supports
    - lpsn-lineage-supports
    - biolink-taxon
  - name: definition
    value: Taxon concept defined by the full retained name/rank/lineage record; distinct
      from the bacterial object strain.
    definition: definition
    evidence_ids:
    - lpsn-name-rank-supports
    - lpsn-identifier-supports
    - lpsn-lineage-supports
    - biolink-taxon
  - name: authority_version
    value: LPSN provider snapshot2026-11-16; Biolink4.4.0. Exact LPSN retrieval time
      and update time are not supplied; neither is fabricated or equated to current
      nomenclature.
    definition: authority_version
    evidence_ids:
    - lpsn-name-rank-supports
    - lpsn-identifier-supports
    - lpsn-lineage-supports
    - biolink-taxon
- assessment_id: object_node
  area: evidence
  topic: object_node
  outcome: supported
  summary: The object identifier, label, strain rank and organism-taxon meaning are
    correct within the retained authority scope.
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  evidence_ids:
  - ncbi-identifier-name-supports
  - ncbi-rank-lineage-supports
  - biolink-taxon
  - biolink-strain
  dimensions:
  - name: axis
    value: object_node
    definition: axis
    evidence_ids:
    - ncbi-identifier-name-supports
    - ncbi-rank-lineage-supports
    - biolink-taxon
    - biolink-strain
  - name: category
    value: CORRECT
    definition: category
    evidence_ids:
    - ncbi-identifier-name-supports
    - ncbi-rank-lineage-supports
    - biolink-taxon
    - biolink-strain
  - name: scope
    value: Original lpsn:46511 biolink:close_match / skos:closeMatch NCBITaxon:1281099
      assertion; authority versions retained November16, evaluated in exposed preparation.
    definition: scope
    evidence_ids:
    - ncbi-identifier-name-supports
    - ncbi-rank-lineage-supports
    - biolink-taxon
    - biolink-strain
  - name: identity
    value: NCBI TaxId1281099 identifies Escherichia coli HVH169(4-1075578); full XML
      parent is562.
    definition: identity
    evidence_ids:
    - ncbi-identifier-name-supports
    - ncbi-rank-lineage-supports
    - biolink-taxon
    - biolink-strain
  - name: label
    value: The encoded Escherichia coli HVH 169 (4-1075578) label matches the retained
      ScientificName.
    definition: label
    evidence_ids:
    - ncbi-identifier-name-supports
    - ncbi-rank-lineage-supports
    - biolink-taxon
    - biolink-strain
  - name: category_fit
    value: Biolink4.4.0 OrganismTaxon explicitly includes strains; category fit does
      not validate the mapping.
    definition: category_fit
    evidence_ids:
    - ncbi-identifier-name-supports
    - ncbi-rank-lineage-supports
    - biolink-taxon
    - biolink-strain
  - name: rank_or_type
    value: Strain, parent562, bacterial lineage in the retained full XML.
    definition: rank_or_type
    evidence_ids:
    - ncbi-identifier-name-supports
    - ncbi-rank-lineage-supports
    - biolink-taxon
    - biolink-strain
  - name: definition
    value: The specific E.coli strain concept, not Methanomethylophilus alvi; no corrected
      replacement identifier is proposed.
    definition: definition
    evidence_ids:
    - ncbi-identifier-name-supports
    - ncbi-rank-lineage-supports
    - biolink-taxon
    - biolink-strain
  - name: authority_version
    value: NCBI retrieved2026-11-16T20:38:28.005741+00:00; UpdateDate2013/01/11 12:14:10
      is record metadata, not a 2013 snapshot. Biolink4.4.0.
    definition: authority_version
    evidence_ids:
    - ncbi-identifier-name-supports
    - ncbi-rank-lineage-supports
    - biolink-taxon
    - biolink-strain
- assessment_id: source_fidelity
  area: evidence
  topic: source_fidelity
  outcome: unknown
  summary: Exact source-row co-occurrence is replayed, but the original producer's
    version-specific field-to-close_match semantics and full emission lineage are
    not established.
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  evidence_ids:
  - source-packet
  dimensions:
  - name: axis
    value: source_fidelity
    definition: axis
    evidence_ids:
    - source-packet
  - name: category
    value: NOT_ASSESSABLE
    definition: category
    evidence_ids:
    - source-packet
  - name: scope
    value: Original lpsn:46511 biolink:close_match / skos:closeMatch NCBITaxon:1281099
      assertion; authority versions retained November16, evaluated in exposed preparation.
    definition: scope
    evidence_ids:
    - source-packet
  - name: source_binding
    value: microbedecoder/edges.tsv row85111; database.csv CSV data row10743 contains
      LPSN_ID46511 and NCBI_Taxonomy_ID1281099 with divergent lineages. Exact source-row
      co-occurrence is replayed, but the original producer's version-specific field-to-close_match
      semantics and full emission lineage are not established.
    definition: source_binding
    evidence_ids:
    - source-packet
findings:
- finding_id: crosswalk-mismatch
  issue_key: first32-crosswalk-mismatch
  category: identity
  severity: major
  status: open
  certainty: confirmed
  title: Crosswalk links distinct taxon concepts
  description: Version-scoped archaeal species versus bacterial E.coli strain mismatch;
    this finding does not invalidate the individual IDs or propose a replacement ID.
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  evidence_ids:
  - lpsn-name-rank-refutes
  - lpsn-identifier-refutes
  - lpsn-lineage-refutes
  - ncbi-identifier-name-refutes
  - ncbi-rank-lineage-refutes
  ownership_note: The upstream MicrobeDecoder crosswalk producer/source-field owner
    must establish original-version lineage before any correction; frozen occurrence
    bytes are not edited.
actions:
- action_id: trace-crosswalk
  description: Request owner review of original-version source field and crosswalk
    emission; preserve exact occurrence and seek evidence before proposing any identifier
    correction.
  finding_ids:
  - crosswalk-mismatch
  target_ids:
  - urn:kg-microbe:occurrence:v1:192571d351f25940fa1d092f9943862376a9603e28391d518c131e3d0341669b
  ownership_note: The upstream MicrobeDecoder crosswalk producer/source-field owner
    must establish original-version lineage before any correction; frozen occurrence
    bytes are not edited.
  acceptance_checks:
  - Establish original-generation lineage and field semantics
  - Independently review retained endpoint meanings and relation applicability
  - Do not invent a corrected ID or edit frozen source bytes
limitations:
- Exact source-row co-occurrence is replayed, but the original producer's version-specific
  field-to-close_match semantics and full emission lineage are not established.
- Exposed first-32 preparation only; no production, Queue A/B, blinded calibration
  or paper-access credit.
- No current authority refresh or historical snapshot reconstruction. Retrieval and
  update dates remain distinct.
- Generic packet measurement_context remains unresolved; experimental measurements,
  units and conditions are inapplicable to this structural claim.
- Draft validation is transport/provenance validation, not scientific approval, canonical
  persistence or exact-runtime admission.
- Biolink OrganismTaxon semantic applicability does not certify LPSN prefix-policy
  conformance; no original-generating-model version recovered.
notes:
- Production scientific coverage0; A/B and cutoff null; all694 candidates retained;
  historical census outerFAILED1/childUNKNOWN unchanged.
- Complete private authority contexts retained; only bounded literal excerpts used
  as proof quotes.
```
