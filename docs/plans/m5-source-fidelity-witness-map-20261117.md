# M5 source-fidelity prerequisites after round03

**Coordinator-only. Do not place this file, its historical inventory or any
linked outcome report in blinded reviewer navigation.** The separate
[case-neutral procedure](source-fidelity-decision-procedure-20261117.md) contains
no case results. This map addresses [#205](https://github.com/CultureBotAI/EdgeMech/issues/205)
and refines #156 without re-rating any occurrence.

Round03 remains failed: source agreement was 7/10 and final resolution was 3/10,
both below the unchanged 8/10 floors. Engineering save/readback succeeded, but
missing semantic witnesses, unsupported initial judgments and blinding failure
remain scientific limitations. No new round or expansion is established by this
map. Original assertions, source rows, multiplicity and completed reviews stay
unchanged.

## What the disagreement reveals

The existing neutral rubric already distinguishes faithful preservation,
demonstrated semantic error and unknown derivation. The missing operational
detail is **when a producer trace is necessary**. The final audit accepts narrow
source-crosswalk preservation for first-32 from its explicit source coassignment,
but requires an original branch for first-43 and fresh-14. This may reflect
different dependencies, not incorrect historical labels. A future reviewer must
state the dependency that makes the branch necessary, or explain why directly
bound source and target meanings suffice. The new procedure makes both proof
routes explicit while retaining the original label definitions.

There is also a distinct source-identity dependency in mixed BactoTraits rows:
replaying which identifier the producer selected does not establish which culture
supplied a phenotype cell. A primary organism paper can support biology but
cannot repair that missing data lineage. A successful selection replay and a
recovered source-cell provenance record would establish different facts.

## Exact source → transformation → ontology witness map

`P(case)` denotes the original `packet-<case>` binding. `E(n)` denotes the
original `r03-evidence-<n>` binding. These names refer to the immutable round03
manifest, not to newly retrieved or silently substituted sources. The private
inventory described below carries every full occurrence ID, assertion and pin.
The table records dependencies and recovery candidates, not new verdicts.

| Case and original assertion | Bound source and transformation context | Ontology/identity context | Necessary recovery or next check |
| --- | --- | --- | --- |
| first-01: BacDive171442 strain → METPO2000511 → API20E CIT procedure | P(first-01): original positive CIT observation ref117337, distinct derived record ref68368, transformed row3378887. E039 binds the assay builder. | E040 manufacturer procedure meaning; E045 original relation meaning; E046 material-entity definition; E024 strain identity. | Determine the original emitted relation's result/observation convention and the intended meaning of the generic assay description. A positive assay record is not itself a result-bearing procedure edge. Inspect the exact original builder and emission branch; do not infer assimilation or fermentation from the neighboring derived entry. |
| first-28: NCBI113559 → has_phenotype → METPO1000870 | P(first-28): summary1498, generic sporulation, three observations/two databases; transformed row96074. | E014 exact species authority; E047 original endpoint template. A related synonym is not the source-field definition or proof of execution. | Bind the original MetaTraits field definition and the lookup entry/branch actually selecting this target. Determine whether source generic wording and target specificity can be compared directly or whether field meaning remains unknown. Bounded owner-code recovery lead below. |
| first-30: GTDB SYIM01_sp009921765 → has_phenotype → METPO1000625 | P(first-30): source line54895 separately reports salinity minimum, growth and maximum; transformed row2984816 carries maximum1.8 percent w/v. Original owner-method result and owner003 bind selected-statistic replay. | E047 fixes original optimum-based target meaning. Independent original GTDB release identity remains unresolved. | Preserve the existing bounded maximum/optimum witness. Do not rerun it as a biological experiment. Recover the relevant GTDB release/taxonomy entry for the subject-node/claim dependency; it is separate from the already scoped transformation comparison. Unknown historical dirty state remains an execution limit. |
| first-32: LPSN46511 → close_match → NCBI1281099 | P(first-32): MicrobeDecoder row10743 explicitly coassigns the same IDs; transformed row85111. | E015 and E023 independently establish the different taxonomic concepts; E001 defines the original mapping relation. | Retain explicit source coassignment separately from independent mapping validity. State why the source-to-occurrence linkage permits direct comparison; do not turn source fidelity into approval of the crosswalk. No additional source-fidelity witness was identified as necessary in the completed audit. |
| first-43: NCBI1540872 → capable_of → METPO1005039 | P(first-43): summary10486 has negative aggregate polarity over ten observations/two databases; transformed row820840 is positive. | E047 binds the original process definition; E018 subject identity; E049 a different producer's participation convention, not this producer's polarity rule. | Bind exact MetaTraits lookup, original mapping inputs, polarity handling and emission convention. Determine whether qualifiers preserve the negative source meaning or whether an established branch loses it. Do not treat the negative aggregate as an independent biological refutation. Bounded owner-code recovery lead below. |
| fresh-04: NCBI1642702 → has_phenotype → METPO1000471 | P(fresh-04): BactoTraits row10677, transformed row85027; three salt-bin weights0.25/0.25/0.5 and separate optimum datum. Name/BacDive and culture-accession chains conflict. | E017 exact endpoint identity; E025 conflicting culture authority; E047 original range-class template. Numeric bounds alone do not define the source weights. | Recover the original bin/weight data dictionary, selected-cell lineage and culture-selection rule. Identify what0.25 measures and which culture supplied it. Original BactoTraits publication/supplement/versioned input are recovery candidates, not already-inspected proof. This also blocks the object-node disagreement. |
| fresh-05: NCBI1123071 → has_phenotype → METPO1000703 | P(fresh-05): BactoTraits row8521, transformed row78420; nonmotile indicator. Name/BacDive identity conflicts with DSM19353/JCM14586. | E020/E021 bind opposing culture identities; E016 original subject; E047 original trait meaning. E011 is a matching primary abstract, not cell-lineage evidence. | Recover original cell provenance and producer identity-selection rule. Later quarantine cannot assign the original cell to a culture. Independent published biology does not resolve the mixed-row association. The full primary paper remains a separate literature task; only its abstract was inspected in round03. |
| fresh-14: LPSN781160 → close_match → JCM14905 strain | P(fresh-14): LPSN row29573 nomenclatural-type field; transformed row116674. E007 can emit type-strain and close-match relations. | E005 type meaning, E006 exact species/type listing, E001 relation meaning. | Establish why this original occurrence is linked to the type field, then determine whether directly bound meanings suffice or the historical emitting branch/lookup must be recovered. A later producer capable of two paths does not identify the original path. Preserve species/strain scope independently of source fidelity. |
| fresh-32: LPSN775534 → capable_of → original hashed process | P(fresh-32): MicrobeDecoder row5072, transformed row153238. E032/E033/E041 preserve source token, process-generation context and FAPROTAX context. | E051 exact species identity. The sampled process description was unavailable to the blinded adjudicator; the process hash does not supply its meaning. | Recover the full original producer definition inputs and create a content-reviewed bounded authority view that preserves every substantive process definition/counterwitness while excluding historical verdicts. Verify the exact original process ID/version. Current FAPROTAX membership or a later label is insufficient. |
| fresh-47: LPSN783091 → has_attribute → original hashed source attribute | P(fresh-47): MicrobeDecoder row20904, transformed row241764, selected salt token and BacDive6845 observation ref119830; E028 source-field/literal minting. | E001 relation/Attribute context; original proposition is a source report. Independent subject authority remains missing in the final assessment. | Preserve the report-only scope and participating LPSN/BacDive chain. Independently recover original LPSN subject authority for the claim/node requirement. The unrelated NCBI crosswalk cannot automatically invalidate the selected literal report. The old E028 producer view had exposure; only a separately reviewed future view may repair that preparation defect. |

## A concrete local recovery lead

Read-only M5 inspection on 2026-11-17 located the actual owner file
`kg_microbe/transform_utils/metatraits/metatraits.py` in the canonical KG-Microbe
checkout. Comparing sampled clean base `bcfa6bf5bfaa5fca23063fd1483d9fcbcb58a977`
with `d6baf5b90003a2032747559d94c00f86a7a4c615` showed no diff for that file.
This does not recover the sampled build's unknown dirty state.

The serial branch around lines2834–2854 and worker branch around3503–3520 read
the source majority and true-percentage fields, then select the Tier1 ontology
mapping's stored predicate. The later fallback branches invoke a separate
polarity routine. This identifies a concrete **candidate** first-28/first-43
mapping witness. It has not yet established which exact lookup entry was loaded
for those occurrences, replayed their emitted output, or resolved the source
field's original meaning.

The next bounded owner replay must bind the source row, ontology/mapping input,
loader and selected branch, preserve all output qualifiers, and compare against
the original occurrence. Start with exactly one occurrence through the intended
replay helper and inspect its persisted receipt before a second. Preserve input
hashes and failed attempts. Do not substitute a handwritten classification rule
or infer biological truth from the result. A full graph transform is unnecessary
for testing this bounded dependency and would not itself recover dirty history.

## Bounded recovery of the mixed fresh-32 description

Independent review found that the future v4 projection inherited v3's omission
of the entire mixed fresh-32 description while claiming substantive definitions
were preserved. [Issue #210](https://github.com/CultureBotAI/EdgeMech/issues/210)
records that finding. The original description contains both historical review
status and substantive process meaning, scope limits, FAPROTAX source/version
provenance and a warning that the vocabulary version does not establish the
generating CSV version. Those substantive spans can be retained independently
of the status tokens.

The corrected future v4 projection requires the complete original description
SHA256 `5d1f1915951a1ebfed7d6cbe745bb5fa316f89054dea753b0c73871db2b3c5e8`.
It omits only three nine-byte status tokens at UTF-8 half-open offsets `[0,9)`,
`[310,319)` and `[709,718)`. Its retained spans preserve the other 778 of 805 bytes,
with per-span hashes, the full source-field hash and the unchanged original
endpoint record identity. Source rows, assertion, measurement context and other
endpoint fields are unchanged. The old v3 projection and old packet remain intact.

The private actual-packet check is
`.temp/source-fidelity-prerequisites-20261117/fresh32-bounded-verification.json`,
SHA256 `7d3df1dfa8a26dca8c9785d0b49d5d9f60e9d378f3541bac7c634ef35f92122a`.
Its sibling `.view.json` has SHA256
`e5b1cb5e4fc2e627875b976ca877349c97c15cf530579757270d42b31ab560f2`.
Both were persisted and read back. The maintained
[`inspect_fresh32_definition_20261117.py`](../../scripts/adhoc/inspect_fresh32_definition_20261117.py)
pins the exact original packet and verifies that the actual projection changes
no bytes beyond the independently enumerated status spans. The first projection
invocation used an interpreter without the project dependency; the next exposed
a tuple/set mismatch in the inspection helper. Both stopped before producing
projection artifacts. The corrected invocation under the project environment
passed, as did six focused v3/v4 tests and Ruff.

The historical blinded adjudicator still lacked this description. Restoring it
in a separately identified future view does not repair that completed assessment
or promote the original producer description into independent authority. The
generating-version caveat and need for exact source-to-process evidence remain.

## Search scope, services and verification

The inspection used the retained round03 manifest, final audit and case fragments;
the retained preparation/rubric/results; selected original evidence views; and
the canonical M5 owner source. Ignored and hidden paths were included with
`rg --files -uu` over the old round03 `.temp` tree and the canonical KG-Microbe
`data` and `docs` trees, plus `rg -uu` over the actual MetaTraits producer.
The search identified retained replay files, raw BactoTraits/LPSN/MicrobeDecoder
inputs and transformation metadata. It was not a complete search of every M5
checkout, compressed source body, remote archive or historical Git object.
“Missing” above means unresolved in the audited frozen evidence, not nonexistent
everywhere. No remote literature query was needed for this dependency inventory.

No new LBNL/CBORG literature service, paid research or authenticated full-text
helper was used. The retained E040 manifest identifies an earlier Tavily capture
of the manufacturer manual; that is provenance of reused evidence, not a new
retrieval by this task. No new paper DOI, snippet or full-text inspection is
claimed. Private evidence stays private; this document quotes no source passages.

The new helper
[`inventory_m5_source_fidelity_witnesses_20261117.py`](../../scripts/adhoc/inventory_m5_source_fidelity_witnesses_20261117.py)
checks the exact original manifest SHA256
`3928396bf4c089620ec0209fdcb986c14f36969259ed01ab563c6807037ee298`
and audit SHA256
`ff949f12e4e88c332736085798fa2b4454b107a5ed32203cc6ed4ecf7024cefe`.
It requires the same ten case and occurrence identities and every historical
source-fidelity evidence ID in the correct case and manifest. Its private output
is `.temp/source-fidelity-prerequisites-20261117/historical-witness-inventory.json`,
SHA256 `d0382822b3dbcef69085413920e30f74f76b0b1cf0142671019eefa6d04eacce`.
The output was read back after creation; it preserves all ten original
assertions and outcomes. The initial invocation failed before output on a
manifest key typo, corrected before the successful invocation. This inventory
does **not** replay the underlying source bytes or prove scientific sufficiency.

Freeze a future package only after these distinctions and the invocation
contract receive independent review. Complete evidence bindings mean every
required file/role can be checked; complete semantic support means the necessary
dependencies actually resolve. Record unresolved dependencies explicitly even
when the engineering freeze succeeds. Neither state warrants inventing labels
to reach eight resolved source-fidelity cases.
