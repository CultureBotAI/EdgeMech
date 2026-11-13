# Fresh 50-edge re-canary report — 2026-11-13

**STOP: this phase reviewed exactly 50 fresh occurrences. Together with the first canary, 100 have been reviewed and 9,900 remain. No expansion or merge was performed.**

Draft PR: https://github.com/CultureBotAI/EdgeMech/pull/76

Do not expand scientific support to the 10,000-edge sample or to an entire transform. Only four of 28 applicable claims resolved; alias contamination and ambiguous strain queries still require manual screening. After fixing issues 88 and 91, a separately authorized small, manually targeted canary could examine evidence-bearing BactoTraits, MicrobeDecoder and PREGO cases. This run does not justify transform-wide expansion. Source fidelity is more tractable with grouped scans, but its four contradictions and five assessment gaps remain explicit follow-up work.

Failures and throttling: the 425 paper-retrieval HTTP attempts comprised 369 HTTP 200 responses, 15 redirects, 29 HTTP 403 responses, five HTTP 401 responses, three HTTP 400 responses, one HTTP 404 response, one HTTP 429 response from Thorax, and two Europe PMC timeouts. Supplemental identifier resolution added four requests. Even serialized retrieval encountered provider limits; concurrent throughput and long-tail coverage remain untested. Missing or inaccessible evidence was not treated as contradiction.

## Separate axes and denominators

Source fidelity: {'SUPPORTED': 41, 'CONTRADICTED': 4, 'NOT_FOUND': 0, 'NOT_ASSESSABLE': 5, 'NOT_APPLICABLE': 0}. Resolution: 45/50 = 90.0%.

Scientific support: {'SUPPORTED': 4, 'CONTRADICTED': 0, 'NOT_FOUND': 8, 'NOT_ASSESSABLE': 16, 'NOT_APPLICABLE': 22}. Resolution: 4/28 = 14.3%. The 22 NOT_APPLICABLE edges are excluded from this denominator; NOT_FOUND and NOT_ASSESSABLE applicable edges remain in it.

Applicability was frozen by transform, predicate and object prefix before searches. Identity, taxonomy, crosswalk, recipe composition and reaction-participant classes were excluded. Unknown classes default conservatively to NOT_APPLICABLE. Class applicability does not establish scientific support. Source fidelity still covers all 50.

The fresh selection preserves 39 retained edges (three per transform) and 11 omitted edges covering all five omission reasons, with no prior-canary occurrence overlap. Original manifest strata and N_h/n_h weights remain attached. Both 50-edge canaries are purposive coverage samples, so rates below are descriptive and do not estimate population accuracy.

The parent 10,000 manifest contains 8,500 retained occurrences balanced over 13 transforms and verdict strata, plus 1,500 omitted occurrences balanced across five reasons. [Original allocation and stratum weights](../edge-sample-review-20261112/allocation.csv) are unchanged. Fresh SHA-256 selection uses seed `20261113-helper3-fresh-recanary-v1`, excluding the first 50; `sampling-metadata.json` pins both fresh representations.

## Counts by transform

S/C/F/A denotes supported/contradicted/not found/not assessable.

| Transform | n | Source S/C/F/A | Source resolved/n | Science applicable | Science S/C/F/A | Science excluded | Science resolved/applicable |
|---|---:|---|---|---:|---|---:|---|
| bacdive/edges.tsv | 3 | 3/0/0/0 | 3/3 | 1 | 0/0/1/0 | 2 | 0/1 |
| bactotraits/edges.tsv | 3 | 1/0/0/2 | 1/3 | 3 | 1/0/0/2 | 0 | 1/3 |
| gold/edges.tsv | 3 | 2/0/0/1 | 2/3 | 1 | 0/0/0/1 | 2 | 0/1 |
| gtdb/edges.tsv | 3 | 3/0/0/0 | 3/3 | 0 | 0/0/0/0 | 3 | not applicable |
| lpsn/edges.tsv | 3 | 2/1/0/0 | 3/3 | 0 | 0/0/0/0 | 3 | not applicable |
| lpsn_api/edges.tsv | 3 | 2/1/0/0 | 3/3 | 0 | 0/0/0/0 | 3 | not applicable |
| madin_etal/edges.tsv | 3 | 3/0/0/0 | 3/3 | 3 | 0/0/0/3 | 0 | 0/3 |
| mediadive/edges.tsv | 3 | 3/0/0/0 | 3/3 | 2 | 0/0/1/1 | 1 | 0/2 |
| metatraits/edges.tsv | 4 | 3/1/0/0 | 4/4 | 4 | 0/0/3/1 | 0 | 0/4 |
| metatraits_gtdb/edges.tsv | 4 | 3/1/0/0 | 4/4 | 4 | 0/0/1/3 | 0 | 0/4 |
| microbedecoder/edges.tsv | 10 | 10/0/0/0 | 10/10 | 5 | 1/0/1/3 | 5 | 1/5 |
| prego_habitat/edges.tsv | 5 | 5/0/0/0 | 5/5 | 5 | 2/0/1/2 | 0 | 2/5 |
| rhea_mappings/edges.tsv | 3 | 1/0/0/2 | 1/3 | 0 | 0/0/0/0 | 3 | not applicable |

## Measured work per edge

Adjudication clocks start before packet reading and stop after persisting the authored decision. Scientific time sums primary-sufficiency and final-review intervals, excluding intervening network time. Source extraction is one grouped scan per input, so its per-edge allocation is explicitly amortized, not individually measured. Excluded science rows have no scientific adjudication.

The query/reference plan was manually curated within these 50 claims after grouped source-name enrichment. Plan construction and manual reference selection were not separately metered. Software engineering and issue handling are also excluded from measured retrieval and judgment intervals.

| # | Transform | Source verdict | Source adjudication s | Source extraction s (amortized) | Science verdict | Science retrieval s | Science adjudication s | HTTP calls |
|---:|---|---|---:|---:|---|---:|---:|---:|
| 1 | bacdive/edges.tsv | SUPPORTED | 12.34 | 1.15 | NOT_FOUND | 28.16 | 47.16 | 8 |
| 2 | bacdive/edges.tsv | SUPPORTED | 11.31 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 3 | bacdive/edges.tsv | SUPPORTED | 11.53 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 4 | bactotraits/edges.tsv | NOT_ASSESSABLE | 17.64 | 1.15 | NOT_ASSESSABLE | 38.68 | 38.54 | 25 |
| 5 | bactotraits/edges.tsv | SUPPORTED | 17.76 | 1.15 | SUPPORTED | 14.78 | 26.19 | 4 |
| 6 | bactotraits/edges.tsv | NOT_ASSESSABLE | 10.09 | 1.15 | NOT_ASSESSABLE | 4.03 | 23.55 | 4 |
| 7 | gold/edges.tsv | NOT_ASSESSABLE | 8.92 | 1.15 | NOT_ASSESSABLE | 18.18 | 19.66 | 11 |
| 8 | gold/edges.tsv | SUPPORTED | 10.67 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 9 | gold/edges.tsv | SUPPORTED | 10.10 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 10 | gtdb/edges.tsv | SUPPORTED | 10.19 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 11 | gtdb/edges.tsv | SUPPORTED | 10.80 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 12 | gtdb/edges.tsv | SUPPORTED | 10.29 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 13 | lpsn/edges.tsv | SUPPORTED | 13.10 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 14 | lpsn/edges.tsv | CONTRADICTED | 10.85 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 15 | lpsn/edges.tsv | SUPPORTED | 11.36 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 16 | lpsn_api/edges.tsv | SUPPORTED | 10.49 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 17 | lpsn_api/edges.tsv | CONTRADICTED | 11.43 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 18 | lpsn_api/edges.tsv | SUPPORTED | 10.10 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 19 | madin_etal/edges.tsv | SUPPORTED | 34.42 | 1.15 | NOT_ASSESSABLE | 41.10 | 28.75 | 17 |
| 20 | madin_etal/edges.tsv | SUPPORTED | 10.48 | 1.15 | NOT_ASSESSABLE | 38.77 | 36.84 | 24 |
| 21 | madin_etal/edges.tsv | SUPPORTED | 9.02 | 1.15 | NOT_ASSESSABLE | 63.71 | 34.85 | 21 |
| 22 | mediadive/edges.tsv | SUPPORTED | 9.10 | 1.15 | NOT_ASSESSABLE | 37.15 | 30.84 | 30 |
| 23 | mediadive/edges.tsv | SUPPORTED | 12.87 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 24 | mediadive/edges.tsv | SUPPORTED | 11.04 | 1.15 | NOT_FOUND | 33.24 | 28.44 | 14 |
| 25 | metatraits/edges.tsv | SUPPORTED | 10.86 | 1.15 | NOT_ASSESSABLE | 52.35 | 25.15 | 31 |
| 26 | metatraits/edges.tsv | SUPPORTED | 10.05 | 1.15 | NOT_FOUND | 25.80 | 19.84 | 4 |
| 27 | metatraits/edges.tsv | SUPPORTED | 8.92 | 1.15 | NOT_FOUND | 87.21 | 29.79 | 11 |
| 28 | metatraits_gtdb/edges.tsv | SUPPORTED | 8.79 | 1.15 | NOT_ASSESSABLE | 40.53 | 21.39 | 9 |
| 29 | metatraits_gtdb/edges.tsv | SUPPORTED | 17.01 | 1.15 | NOT_FOUND | 17.19 | 29.63 | 6 |
| 30 | metatraits_gtdb/edges.tsv | SUPPORTED | 11.37 | 1.15 | NOT_ASSESSABLE | 42.84 | 24.40 | 8 |
| 31 | microbedecoder/edges.tsv | SUPPORTED | 9.40 | 1.15 | NOT_ASSESSABLE | 43.06 | 35.23 | 23 |
| 32 | microbedecoder/edges.tsv | SUPPORTED | 9.40 | 1.15 | SUPPORTED | 43.31 | 47.25 | 21 |
| 33 | microbedecoder/edges.tsv | SUPPORTED | 10.62 | 1.15 | NOT_FOUND | 2.41 | 29.51 | 2 |
| 34 | prego_habitat/edges.tsv | SUPPORTED | 13.77 | 1.15 | SUPPORTED | 41.23 | 41.09 | 8 |
| 35 | prego_habitat/edges.tsv | SUPPORTED | 11.77 | 1.15 | NOT_FOUND | 16.64 | 20.36 | 8 |
| 36 | prego_habitat/edges.tsv | SUPPORTED | 10.04 | 1.15 | SUPPORTED | 64.36 | 30.45 | 28 |
| 37 | rhea_mappings/edges.tsv | NOT_ASSESSABLE | 11.11 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 38 | rhea_mappings/edges.tsv | NOT_ASSESSABLE | 16.52 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 39 | rhea_mappings/edges.tsv | SUPPORTED | 11.05 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 40 | microbedecoder/edges.tsv | SUPPORTED | 11.76 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 41 | microbedecoder/edges.tsv | SUPPORTED | 11.05 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 42 | microbedecoder/edges.tsv | SUPPORTED | 11.30 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 43 | metatraits/edges.tsv | CONTRADICTED | 10.66 | 1.15 | NOT_FOUND | 1.68 | 40.89 | 2 |
| 44 | metatraits_gtdb/edges.tsv | CONTRADICTED | 10.41 | 1.15 | NOT_ASSESSABLE | 27.12 | 41.06 | 12 |
| 45 | microbedecoder/edges.tsv | SUPPORTED | 11.39 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 46 | microbedecoder/edges.tsv | SUPPORTED | 11.46 | 1.15 | NOT_APPLICABLE | 0.00 | not applicable | 0 |
| 47 | microbedecoder/edges.tsv | SUPPORTED | 10.97 | 1.15 | NOT_ASSESSABLE | 52.52 | 38.40 | 24 |
| 48 | microbedecoder/edges.tsv | SUPPORTED | 10.24 | 1.15 | NOT_ASSESSABLE | 78.66 | 31.96 | 33 |
| 49 | prego_habitat/edges.tsv | SUPPORTED | 10.73 | 1.15 | NOT_ASSESSABLE | 80.87 | 28.83 | 18 |
| 50 | prego_habitat/edges.tsv | SUPPORTED | 11.83 | 1.15 | NOT_ASSESSABLE | 35.27 | 120.77 | 19 |

Grouped source extraction: 57.26 seconds across 74 source files, each scanned once in the 50-edge invocation. The first single-record transport canary took another 6.16 seconds, reported separately as setup verification overhead. Source adjudication: 588.36 summed seconds. Scientific retrieval: 1070.85 summed seconds; scientific adjudication: 970.83 summed active-review seconds.

Paper-retrieval API attempts count actual HTTP hops, including redirects and failures; cache hits add no attempt. Supplemental identifier resolution made 4 separately recorded taxonomy/ontology requests in 2.19 seconds. These metadata lookups are not paper retrieval or scientific evidence. Requests were anonymous and serialized. Source extraction used no literature API.

| Service | Paper-retrieval HTTP attempts | Supplemental identifier requests |
|---|---:|---:|
| crossref | 59 | 0 |
| download:aacrjournals.org | 1 | 0 |
| download:academic.oup.com | 3 | 0 |
| download:assets-eu.researchsquare.com | 2 | 0 |
| download:ijs.microbiologyresearch.org | 1 | 0 |
| download:jamanetwork.com | 1 | 0 |
| download:journals.asm.org | 2 | 0 |
| download:link.springer.com | 3 | 0 |
| download:onlinelibrary.wiley.com | 1 | 0 |
| download:pubs.acs.org | 1 | 0 |
| download:syndication.highwire.org | 1 | 0 |
| download:thorax.bmj.com | 1 | 0 |
| download:www.jstage.jst.go.jp | 2 | 0 |
| download:www.microbiologyresearch.org | 17 | 0 |
| download:www.researchsquare.com | 4 | 0 |
| europe_pmc | 257 | 0 |
| ncbi | 8 | 1 |
| ols | 0 | 3 |
| openalex | 49 | 0 |
| springer | 5 | 0 |
| wiley | 7 | 0 |

## Five worked examples

Each excerpt is literal evidence already verified in its ledger. Source-record quotations establish only the source-fidelity axis; they are not promoted to independent scientific support.

### Edge 5: bactotraits/edges.tsv

Original claim: `NCBITaxon:1123071` (Rubritalea squalenifaciens DSM 18772) — `biolink:has_phenotype` — `METPO:1000703` (non motile).

Source: **SUPPORTED**. Science: **SUPPORTED**.

The original species description explicitly reports non-motility for HOact23(T) and identifies the same strain as DSM18772(T), matching both the phenotype and exact sampled strain. The abstract is adequate despite inaccessible publisher full text.

> The strain, designated HOact23(T), was a non-motile, rod-shaped (0.44-0.53x0.65-0.79 microm) bacterium.

Evidence axis: scientific support. Reference: `10.1099/ijs.0.65010-0`. Text SHA-256: `28ae92fb2c8f9d7319bd5ea1effc5587e84e9fb4ea78d6aa6e7a0499eb896f89`.

> type strain HOact23(T) (=MBIC08254(T)=DSM 18772(T))

Evidence axis: scientific support. Reference: `10.1099/ijs.0.65010-0`. Text SHA-256: `28ae92fb2c8f9d7319bd5ea1effc5587e84e9fb4ea78d6aa6e7a0499eb896f89`.

### Edge 32: microbedecoder/edges.tsv

Original claim: `lpsn:775534` (Desulfobacter halotolerans) — `biolink:capable_of` — `kgmicrobe.pathway:microbedecoder_faprotax_type_of_metabolism_48701f8146aa9f1120798eee257448f7d5f71e73e4216acf3d14c101a9fc0fd8` (sulfite_respiration).

Source: **SUPPORTED**. Science: **SUPPORTED**.

Table 1 of the retrieved comparative study places Desulfobacter halotolerans in the fourth species column and explicitly lists sulfate, sulfite and thiosulfate as its electron acceptors. The retained XML table confirms that the electron-acceptor cell is aligned with that species, rather than the newly described APT3 organism. This supports sulfite-respiratory capability; it is a published comparison citing the original description, not a new assay of the sampled source record.

> Property
>
> APT3
>
>
> Desulfonatronobacter acidivorans
>
>
>
> Desulfosalsimonas propionicica
>
>
>
> Desulfobacter halotolerans

Evidence axis: scientific support. Reference: `10.1007/s00792-015-0765-y`. Text SHA-256: `22ed587fad15b4dcccee5f428f9cefda4e37e0668262105bf58bffaa428f8cf1`.

> Electron acceptors
>
> Sulfate, sulfite, thiosulfate
>
> Sulfate, thiosulfate
>
> Sulfate, sulfite, thiosulfate
>
> Sulfate, sulfite, thiosulfate

Evidence axis: scientific support. Reference: `10.1007/s00792-015-0765-y`. Text SHA-256: `22ed587fad15b4dcccee5f428f9cefda4e37e0668262105bf58bffaa428f8cf1`.

### Edge 34: prego_habitat/edges.tsv

Original claim: `ENVO:00000447` (marine biome) — `biolink:location_of` — `NCBITaxon:1935118` (unlabelled).

Source: **SUPPORTED**. Science: **SUPPORTED**.

The NCBI taxonomy response binds the original1935118 identifier as an alias of Candidatus Hecatella orcuttiae. The genomic study explicitly identifies that taxon with JdFR-10/11 and places its order's recovered genomes in eastern-Pacific geothermal environments; the original Juan de Fuca sampling paper locates these crustal fluids in ocean crust. Together these support the broad marine-biome location at the level of metagenomic sampling, not cultivation or an obligate habitat.

> Ca. H. orcuttiae*/JdFR-10,11

Evidence axis: scientific support. Reference: `10.1126/sciadv.abm9651`. Text SHA-256: `a30051043278bdde4dbcc9e2bf7ceb35b58090a7259c487ed30e3c3b267634a9`.

> Hecatellales* MAGs have only been recovered from geothermal environments in the eastern Pacific

Evidence axis: scientific support. Reference: `10.1126/sciadv.abm9651`. Text SHA-256: `a30051043278bdde4dbcc9e2bf7ceb35b58090a7259c487ed30e3c3b267634a9`.

> 3.5 million-year-old ocean crust east of the Juan de Fuca spreading center.

Evidence axis: scientific support. Reference: `10.1038/sdata.2017.37`. Text SHA-256: `35ee067b31db52078e106bfced85a5d3db3e719000263a4d8c28cc4a7e4c4351`.

### Edge 36: prego_habitat/edges.tsv

Original claim: `BTO:0000648` (unlabelled) — `biolink:location_of` — `NCBITaxon:265975` (Oribacterium).

Source: **SUPPORTED**. Science: **SUPPORTED**.

The official ontology response identifies BTO0000648 as intestine. An independent chicken study explicitly uses shotgun metagenomics to identify cecal bacteria and identifies Oribacterium asaccharolyticum among its cecal microbial biomarkers. The cecum is an intestinal site, so presence of this member supports the genus-level intestinal-location edge. This is sequencing-based occurrence, not a claim that every Oribacterium species is intestinal or that live cultures were isolated.

> This study used shotgun metagenomic sequencing to delineate the cecal bacterial species

Evidence axis: scientific support. Reference: `10.1016/j.psj.2026.107187`. Text SHA-256: `52112ac08007cd3e8f6265f3f75a90970d3e87cbf8e2585e7c9e9fb9edc1034c`.

> Subdoligranulum variabile and Oribacterium asaccharolyticum served as key biomarkers

Evidence axis: scientific support. Reference: `10.1016/j.psj.2026.107187`. Text SHA-256: `52112ac08007cd3e8f6265f3f75a90970d3e87cbf8e2585e7c9e9fb9edc1034c`.

### Edge 14: lpsn/edges.tsv

Original claim: `lpsn:781160` (Stackebrandtia nassauensis) — `biolink:close_match` — `kgmicrobe.strain:JCM-14905` (JCM 14905).

Source: **CONTRADICTED**. Science: **NOT_APPLICABLE**.

LPSN identifies 781160 as a species and lists JCM 14905 as one accession of its type strain. A taxon and its nomenclatural type strain are different entities. Encoding their typification relationship as close_match collapses the source distinction; a type-strain or strain-in-taxon relation would preserve it.

> "category": "species"

Evidence axis: source fidelity. Reference: `doi:10.1099/ijsem.0.004332`. Text SHA-256: `8ec8bd4938de062fe83070eb4170b8a424f1307fa3c6307413c08b8d8eb3b6a7`.

> "nomenclatural_type": "DSM 44728; JCM 14905; LLR-40K-21; NBRC 102104; NRRL B-16338"

Evidence axis: source fidelity. Reference: `doi:10.1099/ijsem.0.004332`. Text SHA-256: `c7024f0fe3d29afec99cc98973bf2fb6f4314fc343ae741ee2ac33c3dadd432c`.


## Projection for the remaining 9,900

Only the hash-pinned class rules were applied to the remaining manifest for these counts; no additional edge was retrieved or adjudicated. Projections multiply each transform's measured per-edge mean by its remaining count. They are lower-bound measured-work scenarios, not completion-time estimates or confidence intervals: unmetered targeting setup, manual reference selection, engineering and issue handling remain additional work. Unobserved cells are left unestimated. Actual cost depends on cache sharing, paper accessibility and provider limits.

| Transform | Source remaining | Science applicable remaining | Source adjudication s | Science retrieval s | Science adjudication s |
|---|---:|---:|---:|---:|---:|
| bacdive/edges.tsv | 648 | 206 | 7600.06 | 5800.14 | 9713.94 |
| bactotraits/edges.tsv | 648 | 648 | 9824.98 | 12415.60 | 19069.28 |
| gold/edges.tsv | 648 | 205 | 6413.58 | 3725.89 | 4030.02 |
| gtdb/edges.tsv | 648 | 0 | 6755.79 | 0.00 | 0.00 |
| lpsn/edges.tsv | 648 | 0 | 7625.76 | 0.00 | 0.00 |
| lpsn_api/edges.tsv | 648 | 0 | 6916.30 | 0.00 | 0.00 |
| madin_etal/edges.tsv | 648 | 648 | 11647.63 | 31013.76 | 21693.93 |
| mediadive/edges.tsv | 648 | 323 | 7128.55 | 11368.22 | 9573.83 |
| metatraits/edges.tsv | 796 | 796 | 8058.50 | 33241.37 | 23018.44 |
| metatraits_gtdb/edges.tsv | 796 | 796 | 9467.04 | 25408.97 | 23179.74 |
| microbedecoder/edges.tsv | 1534 | 694 | 16505.56 | 30531.06 | 25311.36 |
| prego_habitat/edges.tsv | 943 | 943 | 10962.03 | 44957.12 | 45547.78 |
| rhea_mappings/edges.tsv | 647 | 0 | 8341.58 | 0.00 | 0.00 |

The conservative unresolved-class fallback excludes 1 of the remaining 9,900 from scientific retrieval. Those rows require a separately reviewed applicability change before searching; their exclusion must not be interpreted as nonbiological truth. Per-rule counts and projected API calls by service are in `recanary-summary.json`.

A scenario that repeats a comparable 50-edge grouped source scan for each of 198 batches adds approximately 11338.29 source-extraction seconds; this assumes comparable source coverage and scan performance. A single larger grouped scan has different selector costs and has not been benchmarked or authorized.

Model token billing was not exposed, so no dollar estimate is reported. Measured adjudication, retrieval and service-call counts remain separate; source and science resolution rates must not be pooled.

## Reproducibility and limits

Fresh/private and public canary hashes, fixed selection seed, original weights, applicability table and decisions, source snapshots, literal quote hashes, packet/decision-bound timing receipts and HTTP attempt logs are retained. Public artifacts contain identifiers, short quotations and hashes; raw source records, full texts, credentials and machine-specific receipts stay private. Directional science requires a verified quote tied to raw-bound DOI/PMID. A retrieved paper or faithful source record alone is not scientific approval.

Manual screening removed broad wrong-organism names and primary references, but did not eliminate every contaminated strain alias ([issue 88](https://github.com/CultureBotAI/EdgeMech/issues/88)). For edge 47, an ATCC 12706 fallback query still returned Weissella viridescens literature for a Weissella halotolerans claim; those papers were rejected as evidence and the claim remained NOT_ASSESSABLE. Other fallback queries used ambiguous numeric-only strain aliases and returned unrelated papers ([issue 91](https://github.com/CultureBotAI/EdgeMech/issues/91)). Frozen plans, packets and measured decisions preserve these actual targeting errors. Organism/source binding and query specificity still require manual checks. These defects block unattended review of the remaining manifest, regardless of the observed resolution rate.

Scientific expansion is a NO-GO. After fixes for issues 88 and 91, any future work should require separate authorization for a small manually targeted set of cases, potentially in BactoTraits, MicrobeDecoder or PREGO. The few resolved canary claims do not justify transform-wide accuracy or scalability conclusions.

No scientific extrapolation is claimed for NOT_APPLICABLE classes. A failed request or unresolved exact strain/trait binding remains an assessment limitation, not biological contradiction. Final test/privacy receipts and independent review findings are recorded in the PR; no merge is authorized.

Final offline checks passed: packets, pytest, ruff, sampling, staged_whitespace. All recorded staged privacy-match counts were zero. The private receipt retains command-log hashes; the public report omits the staged-diff hash to avoid self-reference.
