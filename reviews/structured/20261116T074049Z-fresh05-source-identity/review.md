# Fresh-05 source identity investigation confirms incompatible culture accessions

- Review: 20261116T074049Z-fresh05-source-identity
- Repository: CultureBotAI/EdgeMech
- Started UTC: 2026-11-16T07:40:49Z
- Finished UTC: 2026-11-16T07:40:49Z
- Reviewer: Codex agent (self_review)
- Completion: partial
- Verdict: needs_curation
- Scientific review: true

## Summary

Primary catalog snapshots confirm that DSM 19353/JCM 14586 and DSM 18772 belong to distinct taxa. No safe source-field replacement, independently verified correction or resolved graph claim follows. Six newly authored categorical assessments remain conservative; the review is partial and excluded from independent calibration.

## Scope And Provenance

One occurrence's source identity investigation after abstract replay.

Selection: Fresh-05 retained original occurrence and source conflict #130.
Coverage: partial; 1 reviewed / 1 in the declared population.
Source: working_tree at Git base a4c8ce937ffd791b7c7b4d05b85121dea1aa09d6.
Working-tree hashes do not imply those bytes were committed.

| Target | Path / selector | Kind | Label |
| --- | --- | --- | --- |
| urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | .temp/identity130-review-v2-20261115/packet.json # occurrence_id=urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | snapshot_row | Fresh-05 source strain identity investigation |

## Validation

| Check | Status | Required | Targets | Result |
| --- | --- | --- | --- | --- |
| Ignored private staging preflight | passed | True | urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | Git ignore check passed; no tracked destination files; fresh private directory and exclusive 0600 files enforce no overwrite. |
| Exact retained source and endpoint replay | passed | True | urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | Fixed input hashes and cohort identity checked; build_packet and validate_packet replayed the newly persisted occurrence/source bytes. |
| Primary abstract identity and quotes | passed | True | urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | The abstract adapter selected the exact MED/PMID primary result, verified DOI/title identity, extracted the complete abstract, and verify_quote matched both literal excerpts with hashes/offsets within one 25-word budget. No full text was inspected or claimed. |
| Pinned CLAW contract byte verification | passed | True | urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | check_contracts returned successfully before review construction. |
| Verified source-row correction | unavailable | True | urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | Catalog identities are disambiguated, but no safe field replacement or implemented source-row quarantine has been independently verified on regenerated candidate bytes. The original graph claim remains unresolved. |
| Predicate and both endpoint authorities | unavailable | True | urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | Scoped versioned NCBI/METPO/Biolink/RO proofs were not authored in this canary; all modeling axes remain unresolved and review completion partial. |
| Captured catalog identity provenance | passed | True | urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | All four raw HTML/text/receipt hashes and the capture helper hash matched; the deterministic text derivative and bounded quotes replayed. Culture identities were independently disambiguated before authoring this review. |
| Maintained download and transform snapshots | passed | True | urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136 | Nonempty download.yaml and BactoTraits transform bytes were read from the Git object at ef27b97a0b450767da54235c6105b5250c178adc and retained as pinned inputs. This is owner tracing, not a source patch or regeneration check. |

## Scientific And Domain Assessments

### Source-identity investigation: claim

grounding: unknown. Targets: urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136.

The retained abstract reports nonmotility for the nominal DSM 18772 strain. The original identifier-bound graph assertion remains not assessable: the source row mixes identities and formal predicate/node checks remain incomplete.

### Source-identity investigation: literature

evidence: unknown. Targets: urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136.

The same two DOI/PMID-bound abstract quotations partly address nonmotility for HOact23/DSM 18772. Catalog identity checks add no full-paper assay evidence and do not establish ownership of every trait in the mixed source row.

### Source-identity investigation: relation

representation: unknown. Targets: urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136.

Culture accession disambiguation does not validate has_phenotype/RO:0002200. A scoped versioned predicate authority assessment remains outstanding.

### Source-identity investigation: subject node

identity: unknown. Targets: urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136.

Current DSMZ/BacDive catalogs verify the nominal DSM 18772/HOact23 culture link. DSM 19353/JCM 14586 instead identify Thioprofundum strain 106. Formal NCBI/Biolink identity, rank and category assessment remains unresolved.

### Source-identity investigation: object node

representation: unknown. Targets: urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136.

Nonmotility is reported for the nominal isolate, but this identity review does not adjudicate METPO:1000703 definition or graph category fitness.

### Source-identity investigation: source fidelity

provenance: unknown. Targets: urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136.

The incompatible culture links are now independently confirmed. The row's BacDive ID/name and collection codes refer to different taxa; the maintained transform selects NCBI by BacDive ID. A safe field replacement and verified row correction have not been established.

## Findings

### source-accession-conflict: Source row carries conflicting strain accessions

major / open / confirmed; issue key: bactotraits-row8521-conflicting-strain-accessions.

BactoTraits row 8521 names Rubritalea squalenifaciens/BacDive 17851 but lists DSM 19353/JCM 14586. Captured DSMZ/JCM authorities place that collection pair in Thioprofundum lithotrophicum strain 106/BacDive 17847/NCBI 571898. DSMZ and current BacDive 17851 instead bind the nominal Rubritalea to DSM 18772/HOact23/MBIC08254/NBRC103619. The incompatible identity fields are confirmed; the intended ownership of all source traits and a safe replacement remain unresolved.

## Recommended Actions And Acceptance Checks

### quarantine-and-verify-source-identity

Propose a complete-reviewed-row-hash-bound quarantine at the maintained BactoTraits transform; do not silently substitute accession or taxon fields. Establish the intended source identity with the table owner, preserve the before/after proposal and independently verify regenerated candidate occurrences before claiming correction.

- Retain original row hash, occurrence and all conflicting fields.
- Quarantine acceptance is keyed by the complete reviewed row hash and exact row identity; retain whole-source-file hash as receipt provenance, not as a requirement to reject an otherwise unchanged reviewed row.
- Do not replace graph subject 1123071 with 571898 from accessions alone.
- Add a regression against mixed-strain joins without altering unrelated rows.
- Independently verify candidate regeneration and affected occurrences.

## Category Boundaries


## Evidence

| Evidence | Reference / locator | Support | Observation |
| --- | --- | --- | --- |
| packet-source | .temp/identity130-review-v2-20261115/packet.json; original_assertion; endpoints; source_records: BactoTraits CSV row 8521, BacDive 17851, LPSN 785725 | context_only | Exact retained source/endpoint context includes incompatible collection-code fields; this is not independent biological proof. |
| abstract-nonmotility | https://doi.org/10.1099/ijs.0.65010-0; abstract; PMID 17625207; chars 162:265; text_sha256=28ae92fb2c8f9d7319bd5ea1effc5587e84e9fb4ea78d6aa6e7a0499eb896f89 | partial | Literal primary abstract excerpt inspected in full abstract context; nominal DSM 18772 strain match does not settle disputed source accessions or the entire identifier-bound graph assertion. |
| abstract-strain | https://doi.org/10.1099/ijs.0.65010-0; abstract; PMID 17625207; chars 1157:1208; text_sha256=28ae92fb2c8f9d7319bd5ea1effc5587e84e9fb4ea78d6aa6e7a0499eb896f89 | partial | Literal primary abstract excerpt inspected in full abstract context; nominal DSM 18772 strain match does not settle disputed source accessions or the entire identifier-bound graph assertion. |
| catalog-dsm19353 | https://www.dsmz.de/collection/catalogue/details/culture/DSM-19353; catalog identity; chars 3153:3297; text_sha256=8fa3d180a19442d947a7bbdd86cf1efd78f6ca891fe2acbc42f2c6a9d15c6d82 | context_only | DSM 19353 and JCM 14586 identify Thioprofundum lithotrophicum strain 106, not the nominal Rubritalea strain. |
| catalog-jcm14586 | https://www.jcm.riken.jp/cgi-bin/jcm/jcm_number?JCM=14586; catalog identity; chars 776:820; text_sha256=93d5aec6c739d6bd48c4c4aa66416c7dfe4220ff9ca5c572a1010ad02be0440f | context_only | JCM 14586's complete catalog page corroborates strain 106/DSM 19353 and binds it to BacDive 17847 and NCBI 571898. It documents the original-paper JCM 14596 typographical error; that typo is not a new equivalent accession. |
| catalog-dsm18772 | https://www.dsmz.de/collection/catalogue/details/culture/DSM-18772; catalog identity; chars 3083:3242; text_sha256=99c07d7d2dfeb73ed1fbb69e8213c8034146e51140b2a80f160bd59faead79c8 | context_only | The nominal Rubritalea squalenifaciens type strain has DSM 18772, HOact 23, MBIC08254 and NBRC 103619 aliases. |
| catalog-bacdive17851 | https://bacdive.dsmz.de/strain/17851; catalog identity; chars 674:819; text_sha256=29f41098eb41eb4a6ca0d46abe5ecd746e8cc5dbb4edac5cb6b8233bd6cdd7bc | context_only | Current BacDive 17851 retains the Rubritalea culture aliases. Its inspected sequence sections distinguish strain/genome 1123071 from species/16S 407226; this catalog is not independent NCBI ontology adjudication. |

## Limits And Additional Notes

- Partial self-review; not an independent calibration rating, agreement result or gold label.
- Complete catalog pages and the retained abstract were inspected; no full scientific paper.
- Four catalog snapshots resolve competing aliases, not all original statement/model semantics.
- The confirmed source conflict does not establish biological refutation or a safe field repair.
- Neighbor investigation #132 is context only and contributes no new reviewed occurrence here.
- Investigation used 3 successful CBORG Tavily calls and 4 anonymous catalog GETs; no Valency, publisher TDM or licensed-library full text. This replay launcher makes zero requests.
- Original source bytes/reviews remain intact; no source patch, native capability or graph admission.
- Private catalog/source bodies remain ignored; canonical review contains bounded snippets and hashes.

## Complete Structured Record

The sibling review.yaml is authoritative.

```yaml
schema_version: 1.0.0
review_id: 20261116T074049Z-fresh05-source-identity
kind: record
repository: CultureBotAI/EdgeMech
title: Fresh-05 source identity investigation confirms incompatible culture accessions
started_at: '2026-11-16T07:40:49Z'
finished_at: '2026-11-16T07:40:49Z'
reviewer:
  identity: Codex agent
  kind: agent
  independence: self_review
  independence_basis: New authored source-identity judgments using retained source/abstract
    and current catalogs. Historical reviews and labels were visible; excluded from
    independent calibration matrices.
skill: edgemech-occurrence-review/v1
completion: partial
verdict: needs_curation
scientific_review: true
summary: Primary catalog snapshots confirm that DSM 19353/JCM 14586 and DSM 18772
  belong to distinct taxa. No safe source-field replacement, independently verified
  correction or resolved graph claim follows. Six newly authored categorical assessments
  remain conservative; the review is partial and excluded from independent calibration.
source:
  git_revision: a4c8ce937ffd791b7c7b4d05b85121dea1aa09d6
  state: working_tree
  inputs:
  - path: .temp/identity130-review-v2-20261115/abstract.json
    sha256: 82d96c9481a6d11eefc5976e65b2863e10bed3cedf8b02f9b09cdb92802cf807
    role: context
  - path: .temp/identity130-review-v2-20261115/bacdive17851.html
    sha256: 1a6b1f17cea659277484d7461db6ad3f50e6e32a85c6bf5abdc472e8a489b592
    role: context
  - path: .temp/identity130-review-v2-20261115/bacdive17851.json
    sha256: 6a0e0f46648056fa529748d5010db3df04600a40fb86ab1da2edeba85ac26ea9
    role: context
  - path: .temp/identity130-review-v2-20261115/bacdive17851.txt
    sha256: 29f41098eb41eb4a6ca0d46abe5ecd746e8cc5dbb4edac5cb6b8233bd6cdd7bc
    role: context
  - path: .temp/identity130-review-v2-20261115/cborg-service-provenance.json
    sha256: f9e7ce85c9c9a2738d14384f46251797ad5d213f1efb1d7b8a2ce95d76b289d0
    role: context
  - path: .temp/identity130-review-v2-20261115/cborg-tavily-dsm18772.json
    sha256: 49096c6b7b7607d1071415bac9e70ab298326c9628d45f7b2aa36351e1611481
    role: context
  - path: .temp/identity130-review-v2-20261115/dsm18772.html
    sha256: e6ce0ea2affb04b490b537478a4b804371e187e3eb44f29cff2a99e0875b7079
    role: context
  - path: .temp/identity130-review-v2-20261115/dsm18772.json
    sha256: c4dff78887cf1fc393286867e2954d2d39198ff521dec8417984cdecb3359328
    role: context
  - path: .temp/identity130-review-v2-20261115/dsm18772.txt
    sha256: 99c07d7d2dfeb73ed1fbb69e8213c8034146e51140b2a80f160bd59faead79c8
    role: context
  - path: .temp/identity130-review-v2-20261115/dsm19353.html
    sha256: d416237bc389c88a12185f6981a97faf10cfb091c579b6fb10f721a24c9e1921
    role: context
  - path: .temp/identity130-review-v2-20261115/dsm19353.json
    sha256: 99b8f7dde10107d7e6510f2cfb2ded46ca4dfba3e8b6e6230ef7990dc49e8bbf
    role: context
  - path: .temp/identity130-review-v2-20261115/dsm19353.txt
    sha256: 8fa3d180a19442d947a7bbdd86cf1efd78f6ca891fe2acbc42f2c6a9d15c6d82
    role: context
  - path: .temp/identity130-review-v2-20261115/jcm14586.html
    sha256: 6ee861e0a76f89b937aa79249450267985202f26a326ce629d0119d1b36effaf
    role: context
  - path: .temp/identity130-review-v2-20261115/jcm14586.json
    sha256: 8906c5337592813bbcf2767bc45cfe08f5520a45922e00df0545f84e01071b9c
    role: context
  - path: .temp/identity130-review-v2-20261115/jcm14586.txt
    sha256: 93d5aec6c739d6bd48c4c4aa66416c7dfe4220ff9ca5c572a1010ad02be0440f
    role: context
  - path: .temp/identity130-review-v2-20261115/kg-microbe-bactotraits.py
    sha256: 0d75c432f89f70f90ace3135e7142909721140ba416a638b95e52ac8fcfd7523
    role: context
  - path: .temp/identity130-review-v2-20261115/kg-microbe-download.yaml
    sha256: 209669d1de7e2dfea17712a755217fd201241d2e32f763366ff0570270610153
    role: context
  - path: .temp/identity130-review-v2-20261115/occurrence.json
    sha256: 7b537e0809c90529f7663866359bace6b7d9bd5c7547c74cf4faf88268430426
    role: context
  - path: .temp/identity130-review-v2-20261115/packet.json
    sha256: 8198616d22c932487940fe40a55926a9f8c2c35c9e473a3210a223a435c86703
    role: target
  - path: .temp/identity130-review-v2-20261115/prepared-packet.json
    sha256: 9a456958680990e4d6742b2bc012579d6e48d5d2adefdfcd24c6f0b6ab56b34b
    role: context
  - path: .temp/identity130-review-v2-20261115/proofs.json
    sha256: 21cebf11f52cf65a37fccb25f62fc457050467ea0f19a83834ea41b4fb08914e
    role: context
  - path: .temp/identity130-review-v2-20261115/source.json
    sha256: 9ff02c936f66ec58ad26b25f6176cf96d1f2f92bb556b6c4e7c971995a42f8e7
    role: context
  - path: artifacts/edge-calibration-20261115/cohort.json
    sha256: 1dc756b0ba628756baf544cacf36f0a1ab2e4c68eed6724ee281205f22d606ee
    role: context
  - path: artifacts/edge-calibration-20261115/protocol.json
    sha256: d24b9e1e9833d70407bf06a04ae6c0ff92f5564149a3b51e6402e5416e866517
    role: context
  - path: docs/record-review-profile.md
    sha256: 45e4a564d4926ad491e6a8c2ec4426f8249dfc18318d8c7e2e4d4422dd8143f6
    role: context
  - path: reviews/structured/20261116T052355Z-fresh05-abstract-adapter/review.yaml
    sha256: b1ca23d2c1d2854f73c85564d2cad27572736465c06ef47345319266664b3427
    role: context
  - path: schema/record_review.yaml
    sha256: 229baf9b69118a1fe318e4c31085c0820e4e3d1365e7b04d6ace451b7c35f9bb
    role: context
  - path: scripts/adhoc/capture_strain_authorities_130_20261115.py
    sha256: 56b1ef847187e15a80a00e7b197f28435fcb465bdb0c3954cc097ffbe07388f1
    role: context
  - path: scripts/adhoc/review_bactotraits_identity_130_20261115.py
    sha256: 798dd020dea338e37eccb952c6715b3b2d33e23ce5fbf51b6905d5eef99ac5b9
    role: context
  - path: scripts/adhoc/run_abstract_canary_20261115.py
    sha256: 467f3dbdc899bbcc23f3097a87f51cd4b1f712abbafefd13ed02591c28d03e68
    role: context
  - path: src/edgemech/contract-pins.json
    sha256: 788ecc876a432feebeb89627fbe5a40dba1c1001598683c19834e4626667842c
    role: context
  - path: src/edgemech/literature_cache.py
    sha256: 12e3d920e2a9978c25b5d7626aae087ccd089609c367339a240eb8f37b7a3fef
    role: context
  - path: src/edgemech/occurrence_packet.py
    sha256: 7526fcb6f4467a342abc644c8f607b9b8c6fb395eac159c61f4654594cc490d7
    role: context
  - path: src/edgemech/occurrence_review.py
    sha256: 8821065a01a03752f1952accd0ae7fb53c5d31e85a8f5be621c2d8a7f43d43e3
    role: context
targets:
- target_id: urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  path: .temp/identity130-review-v2-20261115/packet.json
  selector: occurrence_id=urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  kind: snapshot_row
  record_class: ReleaseOccurrence
  label: Fresh-05 source strain identity investigation
  ownership_note: Source publisher controls the BactoTraits table; maintained KG-Microbe
    download/join paths are identified at ef27b97a0b450767da54235c6105b5250c178adc.
  owner_paths:
  - repository: Knowledge-Graph-Hub/kg-microbe
    path: download.yaml
    role: Maintained BactoTraits source download and checksum pin
  - repository: Knowledge-Graph-Hub/kg-microbe
    path: kg_microbe/transform_utils/bactotraits/bactotraits.py
    role: Maintained BacDive-ID to NCBI identity join and BactoTraits transform
scope:
  description: One occurrence's source identity investigation after abstract replay.
  selection: 'Fresh-05 retained original occurrence and source conflict #130.'
  coverage: partial
  population_size: 1
  reviewed_target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  exclusions:
  - target: Independent ten-case calibration scoring
    reason: Self-review with historical labels visible; no new rating.
  - target: 'Neighbor-row finding #132'
    reason: Contextual follow-up only; not an additional reviewed target.
  - target: Other retained occurrences and remaining 9900
    reason: No review expansion or population inference.
checks:
- check_id: private-staging
  name: Ignored private staging preflight
  status: passed
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  command: git check-ignore --no-index --quiet .temp/identity130-review-v2-20261115/abstract.json
  exit_code: 0
  expected_exit_code: 0
  summary: Git ignore check passed; no tracked destination files; fresh private directory
    and exclusive 0600 files enforce no overwrite.
- check_id: source-packet
  name: Exact retained source and endpoint replay
  status: passed
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - packet-source
  summary: Fixed input hashes and cohort identity checked; build_packet and validate_packet
    replayed the newly persisted occurrence/source bytes.
- check_id: abstract-identity-quotes
  name: Primary abstract identity and quotes
  status: passed
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - abstract-nonmotility
  - abstract-strain
  summary: The abstract adapter selected the exact MED/PMID primary result, verified
    DOI/title identity, extracted the complete abstract, and verify_quote matched
    both literal excerpts with hashes/offsets within one 25-word budget. No full text
    was inspected or claimed.
- check_id: pinned-contracts
  name: Pinned CLAW contract byte verification
  status: passed
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  summary: check_contracts returned successfully before review construction.
- check_id: source-identity-resolution
  name: Verified source-row correction
  status: unavailable
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - packet-source
  - catalog-dsm19353
  - catalog-jcm14586
  - catalog-dsm18772
  - catalog-bacdive17851
  summary: Catalog identities are disambiguated, but no safe field replacement or
    implemented source-row quarantine has been independently verified on regenerated
    candidate bytes. The original graph claim remains unresolved.
- check_id: versioned-modeling
  name: Predicate and both endpoint authorities
  status: unavailable
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  summary: Scoped versioned NCBI/METPO/Biolink/RO proofs were not authored in this
    canary; all modeling axes remain unresolved and review completion partial.
- check_id: catalog-identity-replay
  name: Captured catalog identity provenance
  status: passed
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - catalog-dsm19353
  - catalog-jcm14586
  - catalog-dsm18772
  - catalog-bacdive17851
  summary: All four raw HTML/text/receipt hashes and the capture helper hash matched;
    the deterministic text derivative and bounded quotes replayed. Culture identities
    were independently disambiguated before authoring this review.
- check_id: maintained-owner-snapshots
  name: Maintained download and transform snapshots
  status: passed
  required: true
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  summary: Nonempty download.yaml and BactoTraits transform bytes were read from the
    Git object at ef27b97a0b450767da54235c6105b5250c178adc and retained as pinned
    inputs. This is owner tracing, not a source patch or regeneration check.
evidence:
- evidence_id: packet-source
  kind: record_content
  reference: .temp/identity130-review-v2-20261115/packet.json
  locator: 'original_assertion; endpoints; source_records: BactoTraits CSV row 8521,
    BacDive 17851, LPSN 785725'
  accessed_at: '2026-11-16T07:40:49Z'
  support: context_only
  snapshot_sha256: 8198616d22c932487940fe40a55926a9f8c2c35c9e473a3210a223a435c86703
  summary: Exact retained source/endpoint context includes incompatible collection-code
    fields; this is not independent biological proof.
- evidence_id: abstract-nonmotility
  kind: primary_source
  reference: https://doi.org/10.1099/ijs.0.65010-0
  locator: abstract; PMID 17625207; chars 162:265; text_sha256=28ae92fb2c8f9d7319bd5ea1effc5587e84e9fb4ea78d6aa6e7a0499eb896f89
  accessed_at: '2026-11-16T07:40:49Z'
  support: partial
  quote: The strain, designated HOact23(T), was a non-motile, rod-shaped (0.44-0.53x0.65-0.79
    microm) bacterium.
  snapshot_sha256: 82d96c9481a6d11eefc5976e65b2863e10bed3cedf8b02f9b09cdb92802cf807
  summary: Literal primary abstract excerpt inspected in full abstract context; nominal
    DSM 18772 strain match does not settle disputed source accessions or the entire
    identifier-bound graph assertion.
- evidence_id: abstract-strain
  kind: primary_source
  reference: https://doi.org/10.1099/ijs.0.65010-0
  locator: abstract; PMID 17625207; chars 1157:1208; text_sha256=28ae92fb2c8f9d7319bd5ea1effc5587e84e9fb4ea78d6aa6e7a0499eb896f89
  accessed_at: '2026-11-16T07:40:49Z'
  support: partial
  quote: type strain HOact23(T) (=MBIC08254(T)=DSM 18772(T))
  snapshot_sha256: 82d96c9481a6d11eefc5976e65b2863e10bed3cedf8b02f9b09cdb92802cf807
  summary: Literal primary abstract excerpt inspected in full abstract context; nominal
    DSM 18772 strain match does not settle disputed source accessions or the entire
    identifier-bound graph assertion.
- evidence_id: catalog-dsm19353
  kind: authority
  support: context_only
  reference: https://www.dsmz.de/collection/catalogue/details/culture/DSM-19353
  accessed_at: '2026-11-16T07:31:54.779207Z'
  quote: '19353, Type strain dsm-19353 dsm19353 dsm 19353 Thioprofundum lithotrophicum

    Strain designation:

    106

    Other collection no.

    or WDCM no.:

    JCM 14586'
  snapshot_sha256: 8fa3d180a19442d947a7bbdd86cf1efd78f6ca891fe2acbc42f2c6a9d15c6d82
  locator: catalog identity; chars 3153:3297; text_sha256=8fa3d180a19442d947a7bbdd86cf1efd78f6ca891fe2acbc42f2c6a9d15c6d82
  summary: DSM 19353 and JCM 14586 identify Thioprofundum lithotrophicum strain 106,
    not the nominal Rubritalea strain.
- evidence_id: catalog-jcm14586
  kind: authority
  support: context_only
  reference: https://www.jcm.riken.jp/cgi-bin/jcm/jcm_number?JCM=14586
  accessed_at: '2026-11-16T07:32:41.164578Z'
  quote: 'BacDive ID: 17847.

    NCBI Taxonomy ID: 571898.'
  snapshot_sha256: 93d5aec6c739d6bd48c4c4aa66416c7dfe4220ff9ca5c572a1010ad02be0440f
  locator: catalog identity; chars 776:820; text_sha256=93d5aec6c739d6bd48c4c4aa66416c7dfe4220ff9ca5c572a1010ad02be0440f
  summary: JCM 14586's complete catalog page corroborates strain 106/DSM 19353 and
    binds it to BacDive 17847 and NCBI 571898. It documents the original-paper JCM
    14596 typographical error; that typo is not a new equivalent accession.
- evidence_id: catalog-dsm18772
  kind: authority
  support: context_only
  reference: https://www.dsmz.de/collection/catalogue/details/culture/DSM-18772
  accessed_at: '2026-11-16T07:32:36.482044Z'
  quote: '18772, Type strain dsm-18772 dsm18772 dsm 18772 Rubritalea squalenifaciens

    Strain designation:

    HOact 23

    Other collection no.

    or WDCM no.:

    MBIC08254,NBRC 103619'
  snapshot_sha256: 99c07d7d2dfeb73ed1fbb69e8213c8034146e51140b2a80f160bd59faead79c8
  locator: catalog identity; chars 3083:3242; text_sha256=99c07d7d2dfeb73ed1fbb69e8213c8034146e51140b2a80f160bd59faead79c8
  summary: The nominal Rubritalea squalenifaciens type strain has DSM 18772, HOact
    23, MBIC08254 and NBRC 103619 aliases.
- evidence_id: catalog-bacdive17851
  kind: authority
  support: context_only
  reference: https://bacdive.dsmz.de/strain/17851
  accessed_at: '2026-11-16T07:33:14.199643Z'
  quote: 'BacDive ID

    17851

    Type strain

    Strain Designation

    HOact 23

    Culture col. no.

    DSM 18772

    MBIC 08254

    NBRC 103619

    HOact 23

    NCBI tax ID(s)

    1123071

    407226'
  snapshot_sha256: 29f41098eb41eb4a6ca0d46abe5ecd746e8cc5dbb4edac5cb6b8233bd6cdd7bc
  locator: catalog identity; chars 674:819; text_sha256=29f41098eb41eb4a6ca0d46abe5ecd746e8cc5dbb4edac5cb6b8233bd6cdd7bc
  summary: Current BacDive 17851 retains the Rubritalea culture aliases. Its inspected
    sequence sections distinguish strain/genome 1123071 from species/16S 407226; this
    catalog is not independent NCBI ontology adjudication.
assessments:
- assessment_id: claim
  area: grounding
  topic: 'Source-identity investigation: claim'
  outcome: unknown
  summary: 'The retained abstract reports nonmotility for the nominal DSM 18772 strain.
    The original identifier-bound graph assertion remains not assessable: the source
    row mixes identities and formal predicate/node checks remain incomplete.'
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - abstract-nonmotility
  - abstract-strain
  dimensions:
  - name: axis
    value: claim
    definition: 'Authored bounded source-identity judgment: axis'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
  - name: category
    value: NOT_ASSESSABLE
    definition: 'Authored bounded source-identity judgment: category'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
  - name: scope
    value: Original fresh-05 occurrence; bounded source-identity investigation
    definition: 'Authored bounded source-identity judgment: scope'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
  - name: assertion_scope
    value: NCBITaxon:1123071 biolink:has_phenotype METPO:1000703, with original DSM
      18772/non motile labels. The accession conflict is not a biological refutation
      and is not repaired by replacing the subject.
    definition: 'Authored bounded source-identity judgment: assertion_scope'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
- assessment_id: literature
  area: evidence
  topic: 'Source-identity investigation: literature'
  outcome: unknown
  summary: The same two DOI/PMID-bound abstract quotations partly address nonmotility
    for HOact23/DSM 18772. Catalog identity checks add no full-paper assay evidence
    and do not establish ownership of every trait in the mixed source row.
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - abstract-nonmotility
  - abstract-strain
  dimensions:
  - name: axis
    value: literature
    definition: 'Authored bounded source-identity judgment: axis'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
  - name: category
    value: PARTIAL
    definition: 'Authored bounded source-identity judgment: category'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
  - name: scope
    value: Original fresh-05 occurrence; bounded source-identity investigation
    definition: 'Authored bounded source-identity judgment: scope'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
  - name: search_scope
    value: Retained complete abstract only, DOI 10.1099/ijs.0.65010-0, PMID 17625207;
      no new paper search or full-paper inspection.
    definition: 'Authored bounded source-identity judgment: search_scope'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
  - name: literature_channel
    value: europepmc_abstract_retained; separate catalog discovery used 3 CBORG Tavily
      calls and 4 anonymous primary-catalog GETs; no TDM.
    definition: 'Authored bounded source-identity judgment: literature_channel'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
  - name: inspected_extent
    value: Complete retained abstract and its two unchanged short snippets.
    definition: 'Authored bounded source-identity judgment: inspected_extent'
    evidence_ids:
    - abstract-nonmotility
    - abstract-strain
- assessment_id: relation
  area: representation
  topic: 'Source-identity investigation: relation'
  outcome: unknown
  summary: Culture accession disambiguation does not validate has_phenotype/RO:0002200.
    A scoped versioned predicate authority assessment remains outstanding.
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - packet-source
  dimensions:
  - name: axis
    value: relation
    definition: 'Authored bounded source-identity judgment: axis'
    evidence_ids:
    - packet-source
  - name: category
    value: UNRESOLVED
    definition: 'Authored bounded source-identity judgment: category'
    evidence_ids:
    - packet-source
  - name: scope
    value: Original fresh-05 occurrence; bounded source-identity investigation
    definition: 'Authored bounded source-identity judgment: scope'
    evidence_ids:
    - packet-source
  - name: direction
    value: Original organism-to-phenotype direction preserved.
    definition: 'Authored bounded source-identity judgment: direction'
    evidence_ids:
    - packet-source
  - name: domain_range
    value: No new versioned domain/range proof authored.
    definition: 'Authored bounded source-identity judgment: domain_range'
    evidence_ids:
    - packet-source
  - name: specificity
    value: Relation fitness for the original nonmotility statement unresolved.
    definition: 'Authored bounded source-identity judgment: specificity'
    evidence_ids:
    - packet-source
  - name: qualifiers
    value: Abstract and catalogs do not supply complete assay conditions or warrant
      a universal-condition reading.
    definition: 'Authored bounded source-identity judgment: qualifiers'
    evidence_ids:
    - packet-source
- assessment_id: subject-node
  area: identity
  topic: 'Source-identity investigation: subject node'
  outcome: unknown
  summary: Current DSMZ/BacDive catalogs verify the nominal DSM 18772/HOact23 culture
    link. DSM 19353/JCM 14586 instead identify Thioprofundum strain 106. Formal NCBI/Biolink
    identity, rank and category assessment remains unresolved.
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - packet-source
  - catalog-dsm19353
  - catalog-jcm14586
  - catalog-dsm18772
  - catalog-bacdive17851
  dimensions:
  - name: axis
    value: subject_node
    definition: 'Authored bounded source-identity judgment: axis'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: category
    value: UNRESOLVED
    definition: 'Authored bounded source-identity judgment: category'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: scope
    value: Original fresh-05 occurrence; bounded source-identity investigation
    definition: 'Authored bounded source-identity judgment: scope'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: identity
    value: NCBITaxon:1123071 retained. BacDive 17851 distinguishes genome 1123071
      from species/16S 407226. The competing culture pair maps through JCM to BacDive
      17847/NCBI 571898, not an equivalent Rubritalea accession.
    definition: 'Authored bounded source-identity judgment: identity'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: label
    value: Original Rubritalea squalenifaciens DSM 18772 label preserved.
    definition: 'Authored bounded source-identity judgment: label'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: category_fit
    value: biolink:OrganismTaxon retained; catalog agreement is not formal Biolink
      category validation.
    definition: 'Authored bounded source-identity judgment: category_fit'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: rank_or_type
    value: Catalogs distinguish type-strain aliases and species/genome identifiers;
      independent NCBI rank/status verification remains incomplete.
    definition: 'Authored bounded source-identity judgment: rank_or_type'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: definition
    value: No complete versioned node-definition proof authored.
    definition: 'Authored bounded source-identity judgment: definition'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: authority_version
    value: Four independently captured catalog snapshots are bound by capture timestamps,
      raw/text hashes and receipts; the unresolved source join prevents treating them
      as complete original-assertion validation.
    definition: 'Authored bounded source-identity judgment: authority_version'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
- assessment_id: object-node
  area: representation
  topic: 'Source-identity investigation: object node'
  outcome: unknown
  summary: Nonmotility is reported for the nominal isolate, but this identity review
    does not adjudicate METPO:1000703 definition or graph category fitness.
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - packet-source
  dimensions:
  - name: axis
    value: object_node
    definition: 'Authored bounded source-identity judgment: axis'
    evidence_ids:
    - packet-source
  - name: category
    value: UNRESOLVED
    definition: 'Authored bounded source-identity judgment: category'
    evidence_ids:
    - packet-source
  - name: scope
    value: Original fresh-05 occurrence; bounded source-identity investigation
    definition: 'Authored bounded source-identity judgment: scope'
    evidence_ids:
    - packet-source
  - name: identity
    value: Original METPO:1000703 retained; no replacement proposed.
    definition: 'Authored bounded source-identity judgment: identity'
    evidence_ids:
    - packet-source
  - name: label
    value: Original non motile label retained.
    definition: 'Authored bounded source-identity judgment: label'
    evidence_ids:
    - packet-source
  - name: category_fit
    value: biolink:PhenotypicQuality requires a scoped authority check.
    definition: 'Authored bounded source-identity judgment: category_fit'
    evidence_ids:
    - packet-source
  - name: rank_or_type
    value: Nominal phenotype class; formal typing remains unresolved.
    definition: 'Authored bounded source-identity judgment: rank_or_type'
    evidence_ids:
    - packet-source
  - name: definition
    value: No new versioned METPO definition proof authored.
    definition: 'Authored bounded source-identity judgment: definition'
    evidence_ids:
    - packet-source
  - name: authority_version
    value: Preparation authorities are not substituted for new inspected and scoped
      modeling evidence.
    definition: 'Authored bounded source-identity judgment: authority_version'
    evidence_ids:
    - packet-source
- assessment_id: source-fidelity
  area: provenance
  topic: 'Source-identity investigation: source fidelity'
  outcome: unknown
  summary: The incompatible culture links are now independently confirmed. The row's
    BacDive ID/name and collection codes refer to different taxa; the maintained transform
    selects NCBI by BacDive ID. A safe field replacement and verified row correction
    have not been established.
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  evidence_ids:
  - packet-source
  - catalog-dsm19353
  - catalog-jcm14586
  - catalog-dsm18772
  - catalog-bacdive17851
  dimensions:
  - name: axis
    value: source_fidelity
    definition: 'Authored bounded source-identity judgment: axis'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: category
    value: NOT_ASSESSABLE
    definition: 'Authored bounded source-identity judgment: category'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: scope
    value: Original fresh-05 occurrence; bounded source-identity investigation
    definition: 'Authored bounded source-identity judgment: scope'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
  - name: source_binding
    value: Original BactoTraits row 8521 and all retained source records remain unchanged.
      Maintained owner snapshots at ef27b97a0b450767da54235c6105b5250c178adc identify
      the download pin and BacDive-to-NCBI join. Quarantine is a proposed action,
      not an implemented or independently verified graph fix.
    definition: 'Authored bounded source-identity judgment: source_binding'
    evidence_ids:
    - packet-source
    - catalog-dsm19353
    - catalog-jcm14586
    - catalog-dsm18772
    - catalog-bacdive17851
findings:
- finding_id: source-accession-conflict
  issue_key: bactotraits-row8521-conflicting-strain-accessions
  category: identity
  severity: major
  status: open
  certainty: confirmed
  title: Source row carries conflicting strain accessions
  description: BactoTraits row 8521 names Rubritalea squalenifaciens/BacDive 17851
    but lists DSM 19353/JCM 14586. Captured DSMZ/JCM authorities place that collection
    pair in Thioprofundum lithotrophicum strain 106/BacDive 17847/NCBI 571898. DSMZ
    and current BacDive 17851 instead bind the nominal Rubritalea to DSM 18772/HOact23/MBIC08254/NBRC103619.
    The incompatible identity fields are confirmed; the intended ownership of all
    source traits and a safe replacement remain unresolved.
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  field_paths:
  - 'source_records[0].text: culture collection codes'
  - 'source_records[0].text: Bacdive_ID'
  evidence_ids:
  - packet-source
  - catalog-dsm19353
  - catalog-jcm14586
  - catalog-dsm18772
  - catalog-bacdive17851
  - abstract-nonmotility
  - abstract-strain
  ownership_note: Source publisher owns table correction; KG-Microbe owns download/join
    and any reviewed row-quarantine policy at the listed maintained paths.
  external_issues:
  - https://github.com/CultureBotAI/EdgeMech/issues/130
  owner_paths:
  - repository: Knowledge-Graph-Hub/kg-microbe
    path: download.yaml
    role: Maintained BactoTraits source download and checksum pin
  - repository: Knowledge-Graph-Hub/kg-microbe
    path: kg_microbe/transform_utils/bactotraits/bactotraits.py
    role: Maintained BacDive-ID to NCBI identity join and BactoTraits transform
  previous_occurrences:
  - repository: CultureBotAI/EdgeMech
    review_id: 20261116T052355Z-fresh05-abstract-adapter
    finding_id: source-accession-conflict
actions:
- action_id: quarantine-and-verify-source-identity
  finding_ids:
  - source-accession-conflict
  target_ids:
  - urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136
  description: Propose a complete-reviewed-row-hash-bound quarantine at the maintained
    BactoTraits transform; do not silently substitute accession or taxon fields. Establish
    the intended source identity with the table owner, preserve the before/after proposal
    and independently verify regenerated candidate occurrences before claiming correction.
  ownership_note: The maintained owner paths are known; no correction or quarantine
    is claimed merged by this investigation.
  acceptance_checks:
  - Retain original row hash, occurrence and all conflicting fields.
  - Quarantine acceptance is keyed by the complete reviewed row hash and exact row
    identity; retain whole-source-file hash as receipt provenance, not as a requirement
    to reject an otherwise unchanged reviewed row.
  - Do not replace graph subject 1123071 with 571898 from accessions alone.
  - Add a regression against mixed-strain joins without altering unrelated rows.
  - Independently verify candidate regeneration and affected occurrences.
  owner_paths:
  - repository: Knowledge-Graph-Hub/kg-microbe
    path: download.yaml
    role: Maintained BactoTraits source download and checksum pin
  - repository: Knowledge-Graph-Hub/kg-microbe
    path: kg_microbe/transform_utils/bactotraits/bactotraits.py
    role: Maintained BacDive-ID to NCBI identity join and BactoTraits transform
limitations:
- Partial self-review; not an independent calibration rating, agreement result or
  gold label.
- Complete catalog pages and the retained abstract were inspected; no full scientific
  paper.
- Four catalog snapshots resolve competing aliases, not all original statement/model
  semantics.
- The confirmed source conflict does not establish biological refutation or a safe
  field repair.
- 'Neighbor investigation #132 is context only and contributes no new reviewed occurrence
  here.'
- Investigation used 3 successful CBORG Tavily calls and 4 anonymous catalog GETs;
  no Valency, publisher TDM or licensed-library full text. This replay launcher makes
  zero requests.
- Original source bytes/reviews remain intact; no source patch, native capability
  or graph admission.
- Private catalog/source bodies remain ignored; canonical review contains bounded
  snippets and hashes.
links:
- https://github.com/CultureBotAI/EdgeMech/issues/130
- https://github.com/CultureBotAI/EdgeMech/issues/132
- https://doi.org/10.1099/ijs.0.65010-0
- https://github.com/Knowledge-Graph-Hub/kg-microbe/blob/ef27b97a0b450767da54235c6105b5250c178adc/download.yaml
- https://github.com/Knowledge-Graph-Hub/kg-microbe/blob/ef27b97a0b450767da54235c6105b5250c178adc/kg_microbe/transform_utils/bactotraits/bactotraits.py
tags:
- source-identity-investigation
- partial-review
- excluded-from-calibration-scoring
```
