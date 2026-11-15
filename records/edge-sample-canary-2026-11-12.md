# 50-edge canary report — 2026-11-12

**STOP: only the 50-edge canary was adjudicated. The remaining9,950 edges were not retrieved or reviewed. No graph data were changed and no merge was performed.**

Draft PR: https://github.com/CultureBotAI/EdgeMech/pull/76

## Result and interpretation

Source fidelity: {'NOT_ASSESSABLE': 12, 'SUPPORTED': 33, 'CONTRADICTED': 5}. Scientific support: {'NOT_ASSESSABLE': 22, 'NOT_FOUND': 25, 'SUPPORTED': 3}.

These are descriptive canary results, not per-source population accuracy estimates. NOT_FOUND means no adequate evidence in the recorded bounded search; NOT_ASSESSABLE includes non-biological identity/scaffolding edges and source/provenance gaps. Neither is counted as false. A database record can faithfully contain an association while independent science remains unresolved. Original rule-labelled triples are the review target; curated rewrites are retained separately.

## Sample design

Seed: `20261112-helper3-edge-sample-v1`. Deterministic MD5 ranking of occurrence identity plus seed within 29 strata. A same-hash prefix prefilter bounds remote memory; exact quotas are checked. Occurrence identity and multiplicity are preserved. The 10,000 manifest has8,500 retained edges balanced over 13 transforms then rule verdicts, plus 1,500 omitted edges (300 per omission reason, divided across transforms). Each retained transform has653–654 samples, exceeding385. Stratum weights are N_h/n_h. These allocations do not by themselves guarantee +/-5% weighted confidence intervals after nonresponse and organism clustering.

The canary selects39 retained occurrences (three per transform with verdict diversity) and 11 omitted occurrences covering all five reasons. Its deliberate diversity prevents treating it as a simple random sample. The full manifest and allocation table are committed; only small samples were transferred. Remote sampling used2 threads,4GB memory and a1GB spill cap. Source extraction streamed large raw inputs read-only without remote output files.

Input sizes, modification times and schemas were recorded privately; full multi-gigabyte input hashes were not computed. Manifest and evidence artifacts have SHA256 pins. Public sanitization preserves all 50 claim triples and identities; original manifest bytes remain privately pinned for retrieval replay.

| Transform | Rule verdict | Disposition | Population | Sample | Weight N/n |
|---|---|---|---:|---:|---:|
| bacdive/edges.tsv | accurate_direct_evidence | retained | 4149060 | 218 | 19032.385 |
| bacdive/edges.tsv | imprecise_or_text_mining_prediction | retained | 151987 | 218 | 697.188 |
| bacdive/edges.tsv | plausible_aggregated_trait_or_habitat | retained | 153845 | 218 | 705.711 |
| bactotraits/edges.tsv | plausible_aggregated_trait_or_habitat | retained | 87809 | 654 | 134.265 |
| gold/edges.tsv | plausible_aggregated_trait_or_habitat | retained | 765987 | 654 | 1171.234 |
| gtdb/edges.tsv | accurate_taxonomy_or_reaction_reference | retained | 1148707 | 327 | 3512.865 |
| gtdb/edges.tsv | imprecise_or_text_mining_prediction | retained | 322327 | 327 | 985.709 |
| lpsn/edges.tsv | accurate_taxonomy_or_reaction_reference | retained | 36918 | 327 | 112.899 |
| lpsn/edges.tsv | imprecise_or_text_mining_prediction | retained | 119239 | 327 | 364.645 |
| lpsn_api/edges.tsv | accurate_taxonomy_or_reaction_reference | retained | 41428 | 327 | 126.691 |
| lpsn_api/edges.tsv | imprecise_or_text_mining_prediction | retained | 124064 | 327 | 379.401 |
| madin_etal/edges.tsv | plausible_aggregated_trait_or_habitat | retained | 191947 | 654 | 293.497 |
| mediadive/edges.tsv | accurate_direct_evidence | retained | 55187 | 327 | 168.768 |
| mediadive/edges.tsv | plausible_aggregated_trait_or_habitat | retained | 57286 | 327 | 175.187 |
| metatraits/edges.tsv | plausible_aggregated_trait_or_habitat | omit_metatraits_zero_percentage_positive_predicate | 701161 | 150 | 4674.407 |
| metatraits/edges.tsv | plausible_aggregated_trait_or_habitat | retained | 3664739 | 654 | 5603.576 |
| metatraits_gtdb/edges.tsv | plausible_aggregated_trait_or_habitat | omit_metatraits_zero_percentage_positive_predicate | 523022 | 150 | 3486.813 |
| metatraits_gtdb/edges.tsv | plausible_aggregated_trait_or_habitat | retained | 2884897 | 654 | 4411.157 |
| microbedecoder/edges.tsv | accurate_direct_evidence | retained | 11101 | 164 | 67.689 |
| microbedecoder/edges.tsv | imprecise_or_text_mining_prediction | retained | 21239 | 164 | 129.506 |
| microbedecoder/edges.tsv | inaccurate_or_uninformative | omit_bergey_other_or_unmapped_hash_attribute | 5651 | 300 | 18.837 |
| microbedecoder/edges.tsv | inaccurate_or_uninformative | omit_microbedecoder_missing_img_subject_node | 18374 | 300 | 61.247 |
| microbedecoder/edges.tsv | inaccurate_or_uninformative | omit_microbedecoder_redundant_bacdive_hash_attribute | 367050 | 300 | 1223.500 |
| microbedecoder/edges.tsv | inaccurate_or_uninformative | retained | 42483 | 163 | 260.632 |
| microbedecoder/edges.tsv | plausible_aggregated_trait_or_habitat | retained | 45247 | 163 | 277.589 |
| prego_habitat/edges.tsv | imprecise_or_text_mining_prediction | omit_prego_low_confidence_score_lt_3 | 154930 | 300 | 516.433 |
| prego_habitat/edges.tsv | imprecise_or_text_mining_prediction | retained | 82815 | 653 | 126.822 |
| rhea_mappings/edges.tsv | accurate_taxonomy_or_reaction_reference | retained | 421455 | 327 | 1288.853 |
| rhea_mappings/edges.tsv | imprecise_or_text_mining_prediction | retained | 15686 | 326 | 48.117 |

## Counts by transform and verdict

S=SUPPORTED; C=CONTRADICTED; F=NOT_FOUND; A=NOT_ASSESSABLE.

| Transform | n | Source S/C/F/A | Scientific S/C/F/A |
|---|---:|---|---|
| bacdive/edges.tsv | 3 | 2/0/0/1 | 0/0/0/3 |
| bactotraits/edges.tsv | 3 | 0/0/0/3 | 0/0/3/0 |
| gold/edges.tsv | 3 | 3/0/0/0 | 0/0/0/3 |
| gtdb/edges.tsv | 3 | 2/0/0/1 | 0/0/0/3 |
| lpsn/edges.tsv | 3 | 2/0/0/1 | 0/0/0/3 |
| lpsn_api/edges.tsv | 3 | 2/1/0/0 | 0/0/0/3 |
| madin_etal/edges.tsv | 3 | 3/0/0/0 | 0/0/3/0 |
| mediadive/edges.tsv | 3 | 1/0/0/2 | 0/0/2/1 |
| metatraits/edges.tsv | 4 | 1/1/0/2 | 0/0/4/0 |
| metatraits_gtdb/edges.tsv | 4 | 1/2/0/1 | 0/0/4/0 |
| microbedecoder/edges.tsv | 10 | 9/1/0/0 | 2/0/2/6 |
| prego_habitat/edges.tsv | 5 | 5/0/0/0 | 1/0/4/0 |
| rhea_mappings/edges.tsv | 3 | 2/0/0/1 | 0/0/3/0 |

## All 50 canary judgments and measured retrieval time

Seconds and calls below measure literature retrieval only. Edge4 includes its initial live canary run (the second invocation hit the cache). Per-edge agent reasoning and source-parser wall times were not instrumented; presenting these numbers as end-to-end review time would be misleading. Complete per-edge rationales and proof hashes are in the committed ledgers.

| # | Transform | Claim | Source | Science | Retrieval s | EPMC calls |
|---:|---|---|---|---|---:|---:|
| 1 | bacdive/edges.tsv | bacdive_171442 as AH 405 of NCBITaxon:1396 — METPO:2000511 — API 20E - Citrate | NOT_ASSESSABLE | NOT_ASSESSABLE | 0.00 | 0 |
| 2 | bacdive/edges.tsv | bacdive_139636 strain of NCBITaxon:1747 — biolink:close_match — CIP 53.119 | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 3 | bacdive/edges.tsv | DSM 51066 — biolink:subclass_of — Corallococcus coralloides | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 4 | bactotraits/edges.tsv | Sphingomonas molluscorum — biolink:has_phenotype — temperature optimum mid1 | NOT_ASSESSABLE | NOT_FOUND | 8.06 | 4 |
| 5 | bactotraits/edges.tsv | Lewinella cohaerens DSM 23179 — biolink:has_phenotype — NaCl range mid1 | NOT_ASSESSABLE | NOT_FOUND | 22.07 | 4 |
| 6 | bactotraits/edges.tsv | Pseudaeromonas sharmana — biolink:has_phenotype — pH delta low | NOT_ASSESSABLE | NOT_FOUND | 25.41 | 4 |
| 7 | gold/edges.tsv | Streptococcus salivarius AMBR158 — biolink:related_to — Streptococcus salivarius | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 8 | gold/edges.tsv | Lachnospiraceae bacterium RUG12445 — biolink:related_to — uncultured Lachnospiraceae bacterium | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 9 | gold/edges.tsv | Neisseria sp. N177_16 — biolink:related_to — Neisseria sp. N177_16 | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 10 | gtdb/edges.tsv | GCA_016931655.1 — biolink:in_taxon — s__JAFGEJ01_sp016931655 | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 11 | gtdb/edges.tsv | s__Kaistella_salipaludis — biolink:close_match — Chryseobacterium salipaludis | NOT_ASSESSABLE | NOT_ASSESSABLE | 0.00 | 0 |
| 12 | gtdb/edges.tsv | GCF_030540985.1 — biolink:in_taxon — s__Pseudomonas_aeruginosa | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 13 | lpsn/edges.tsv | Paracoccus tegillarcae — biolink:subclass_of — Paracoccus | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 14 | lpsn/edges.tsv | Aliivibrio sifiae — biolink:close_match — Aliivibrio sifiae | NOT_ASSESSABLE | NOT_ASSESSABLE | 0.00 | 0 |
| 15 | lpsn/edges.tsv | Zhihengliuella halotolerans — biolink:subclass_of — Zhihengliuella | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 16 | lpsn_api/edges.tsv | Methanogenium tationis — biolink:subclass_of — Methanogenium | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 17 | lpsn_api/edges.tsv | Hoeflea halophila — biolink:close_match — doi:10.1007/s10482-013-9876-6 | CONTRADICTED | NOT_ASSESSABLE | 0.00 | 0 |
| 18 | lpsn_api/edges.tsv | Rhizobium herbae — biolink:subclass_of — Rhizobium | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 19 | madin_etal/edges.tsv | Staphylococcus aureus W48906 — biolink:has_phenotype — gram positive | SUPPORTED | NOT_FOUND | 2.50 | 2 |
| 20 | madin_etal/edges.tsv | Escherichia coli O157:H7 str. SS52 — biolink:has_phenotype — gram negative | SUPPORTED | NOT_FOUND | 4.90 | 4 |
| 21 | madin_etal/edges.tsv | Sinorhizobium meliloti CIAM1775 — biolink:has_phenotype — non-spore forming | SUPPORTED | NOT_FOUND | 18.46 | 6 |
| 22 | mediadive/edges.tsv | Streptomyces sp001746295 — METPO:2000517 — ROLLED OATS MINERAL MEDIUM DSMZ Medium 84 | NOT_ASSESSABLE | NOT_FOUND | 12.40 | 4 |
| 23 | mediadive/edges.tsv | Main sol. 234 — biolink:has_part — vitamin B12 | NOT_ASSESSABLE | NOT_ASSESSABLE | 0.00 | 0 |
| 24 | mediadive/edges.tsv | bacdive_165511 strain of NCBITaxon:1504 — METPO:2000517 — EG MEDIUM | SUPPORTED | NOT_FOUND | 1.77 | 2 |
| 25 | metatraits/edges.tsv | Lactobacillus algidus — METPO:2000034 — fumarate(2-) | NOT_ASSESSABLE | NOT_FOUND | 3.20 | 2 |
| 26 | metatraits/edges.tsv | Alcanivorax borkumensis — METPO:2000034 — nitrate | NOT_ASSESSABLE | NOT_FOUND | 21.65 | 6 |
| 27 | metatraits/edges.tsv | Vibrio furnissii — METPO:2000042 — Manganese | SUPPORTED | NOT_FOUND | 21.37 | 6 |
| 28 | metatraits_gtdb/edges.tsv | Actinoplanes campanulatus — biolink:has_phenotype — sporulation | NOT_ASSESSABLE | NOT_FOUND | 4.30 | 4 |
| 29 | metatraits_gtdb/edges.tsv | Actinophytocola xinjiangensis — METPO:2000102 — chemoheterotrophic | SUPPORTED | NOT_FOUND | 3.83 | 3 |
| 30 | metatraits_gtdb/edges.tsv | SYIM01 sp009921765 — biolink:has_phenotype — slightly halophilic | CONTRADICTED | NOT_FOUND | 1.84 | 2 |
| 31 | microbedecoder/edges.tsv | Treponema stenostreptum — biolink:produces — acetate | SUPPORTED | SUPPORTED | 3.86 | 3 |
| 32 | microbedecoder/edges.tsv | Methanomethylophilus alvi — biolink:close_match — Escherichia coli HVH 169 (4-1075578) | CONTRADICTED | NOT_ASSESSABLE | 0.00 | 0 |
| 33 | microbedecoder/edges.tsv | Eucapsis microscopica — biolink:has_attribute — reported FAPROTAX Type of metabolism: photosynthetic_cyanobacteria (source value) | SUPPORTED | NOT_FOUND | 1.82 | 2 |
| 34 | prego_habitat/edges.tsv | loam — biolink:location_of — Candidatus Amesbacteria bacterium RIFOXYD1_FULL_47_9 | SUPPORTED | NOT_FOUND | 18.33 | 3 |
| 35 | prego_habitat/edges.tsv | soil — biolink:location_of — Candidatus Magasanikbacteria bacterium RIFCSPHIGHO2_02_FULL_41_13 | SUPPORTED | NOT_FOUND | 5.63 | 4 |
| 36 | prego_habitat/edges.tsv | organic material — biolink:location_of — Ixodes scapularis | SUPPORTED | SUPPORTED | 15.64 | 6 |
| 37 | rhea_mappings/edges.tsv | (4Z,15Z)-bilirubin IXalpha + UDP-alpha-D-glucuronate = (4Z,15Z)-bilirubin IXalpha C12-beta-D-glucuronoside + UDP — biolink:has_participant — (4Z,15Z)-bilirubin IXalpha C12-beta-D-glucuronoside(2-) | NOT_ASSESSABLE | NOT_FOUND | 1.63 | 2 |
| 38 | rhea_mappings/edges.tsv | deamido-NAD(+) + NH4(+) + ATP = AMP + diphosphate + NAD(+) + H(+) — biolink:close_match — NAD(+) synthase | SUPPORTED | NOT_FOUND | 3.55 | 2 |
| 39 | rhea_mappings/edges.tsv | 3,4-dinitrotoluene + NADH + O2 = 4-methyl-6-nitrocatechol + nitrite + NAD(+) — rheav:directionalReaction — 3,4-dinitrotoluene + NADH + O2 => 4-methyl-6-nitrocatechol + nitrite + NAD(+) | SUPPORTED | NOT_FOUND | 0.71 | 1 |
| 40 | microbedecoder/edges.tsv | Alloyangia pacifica — biolink:has_attribute — reported Bergey Type of metabolism: Other (source value) | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 41 | microbedecoder/edges.tsv | Trinickia caryophylli — biolink:has_attribute — reported Bergey Type of metabolism: Other (source value) | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 42 | microbedecoder/edges.tsv | Rickettsiella chironomi — biolink:has_attribute — reported Bergey Type of metabolism: Other (source value) | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 43 | metatraits/edges.tsv | Candidatus Gracilibacteria bacterium HOT-871 — biolink:capable_of — nitrogen fixation | CONTRADICTED | NOT_FOUND | 22.20 | 4 |
| 44 | metatraits_gtdb/edges.tsv | Streptomyces fagopyri — biolink:capable_of — nitrification | CONTRADICTED | NOT_FOUND | 18.90 | 4 |
| 45 | microbedecoder/edges.tsv | IMG:2772190913 — biolink:in_taxon — Leeuwenhoekiella aestuarii | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 46 | microbedecoder/edges.tsv | IMG:2770939627 — biolink:in_taxon — Marinomonas pollencensis | SUPPORTED | NOT_ASSESSABLE | 0.00 | 0 |
| 47 | microbedecoder/edges.tsv | Aromatoleum toluvorans — biolink:has_attribute — reported Oxygen tolerance: anaerobe (source value) | SUPPORTED | SUPPORTED | 20.66 | 6 |
| 48 | microbedecoder/edges.tsv | Longimycelium tulufanense — biolink:has_attribute — reported Enzyme activity: alkaline phosphatase (source value) | SUPPORTED | NOT_FOUND | 23.45 | 4 |
| 49 | prego_habitat/edges.tsv | agricultural soil — biolink:location_of — Methanohalophilus mahii DSM 5219 | SUPPORTED | NOT_FOUND | 8.31 | 5 |
| 50 | prego_habitat/edges.tsv | anthropogenic environmental material — biolink:location_of — Catonella morbi ATCC 51271 | SUPPORTED | NOT_FOUND | 6.81 | 4 |

## Five worked examples with verified quotations

Quotes below are short excerpts; whitespace is collapsed only for display. Ledgers preserve the literal quotes, exact source/text hashes, URLs, evidence levels and publication identifiers. Database publication DOIs identify source provenance and are not biological proof.

### Edge31: scientific support — SUPPORTED

Table6 lists acetate among Spirochaeta stenostrepta fermentation products (third species column). The same article reclassifies the species as Treponema stenostrepta. LPSN791062 source record marks spelling corrected to T.stenostreptum and binds DSM2028/ATCC25083 plus this DOI; this is the same taxon, not transfer from S.caldaria.

> acetate, ethanol, CO2, H2, (lactate)

DOI/PMID: 10.4056/sigs.3096473. URL: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3739177/fullTextXML. Text SHA256: `1c97552868b4e26ea7483a832719ecb6d7f08a422f7c3439ec96eeb4b5584e20`.

> Spirochaeta stenostrepta [63]

DOI/PMID: 10.4056/sigs.3096473. URL: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3739177/fullTextXML. Text SHA256: `1c97552868b4e26ea7483a832719ecb6d7f08a422f7c3439ec96eeb4b5584e20`.

### Edge36: scientific support — SUPPORTED

A primary I.scapularis experiment reports survival in leaf litter and mulch. These are organic substrates; this supports the broad organic-material habitat assertion through that explicit mapping, not the original PREGO score or a microbial classification of this tick.

> Tick viability assays without acaricide indicated tick survival above 80% at week four in Phenocosms with leaf litter and mulch

DOI/PMID: 10.1016/j.ttbdis.2026.102710. URL: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22Ixodes+scapularis%22+AND+%22leaf+litter%22&resultType=core&format=json&pageSize=5. Text SHA256: `6f43e7a478defe0a218a8422c7555f956ca0a99decb208c8fdaeb96d894884a6`.

### Edge43: source fidelity — CONTRADICTED

For the exact HOT-871 taxon the nitrogen-fixation summary is false100% over10observations. An unqualified positive capable_of assertion reverses this source polarity; this supports the rationale for omitting the positive edge.

> "majority_label": "false: (100%)", "name": "nitrogen fixation"

DOI/PMID: 10.1093/nar/gkaf1241. URL: https://metatraits.embl.de/. Text SHA256: `899d048ab49589171e5a2718d5b308f793544eddf0a88d9463c9f2f8160ba83e`.

### Edge17: source fidelity — CONTRADICTED

The source identifies this DOI as the publication describing Hoeflea halophila, not a taxonomic concept equivalent to the organism. Original taxon close_match publication has the wrong predicate/domain; curated mentions is a separate claim.

> "publication_doi": "10.1007/s10482-013-9876-6"

DOI/PMID: 10.83108/rn.791057. URL: https://lpsn.dsmz.de/taxon/791057. Text SHA256: `9b7880429885370c163dbb37f2287a7585da6500c029e82270cc0a657ab270d4`.

### Edge32: source fidelity — CONTRADICTED

The transform copies NCBI1281099 from its source, but the same source row identifies the LPSN organism as archaeal Methanomethylophilus alvi and the NCBI organism as Escherichia coli. This is an internally inconsistent crosswalk, so close_match fails identifier correctness despite faithful copying.

> "NCBI_Species": "Escherichia coli", "NCBI_Taxonomy_ID": "1281099"

DOI/PMID: 10.1093/nar/gkag515. URL: https://github.com/thackmann/MicrobeDecoder/raw/main/Shiny/MicrobeDecoder/data/database/database.zip. Text SHA256: `c38a95d8c3d7c80365f0af82e7d6d5ee4eeee234254764ca18220d2b8f1ad2de`.

## Protocol, persisted side effects, and telemetry

Every judgment is authored by GPT-6 in Codex (runtime variant not exposed). Source fidelity checks the upstream record, identifier, predicate, direction and qualifier. Scientific support uses an explicit query plan, up to five core records per query and up to two OA full texts per query. Exact strains and chemical forms are not replaced by generic species or chemical-class evidence. Taxonomy links, recipe composition, observation-without-outcome and unspecified Other metadata are explicitly outside the biological-trait axis.

Europe PMC requests were anonymous, serialized through the existing LiteratureCache, with one-second provider spacing, bounded retries and durable content-addressed responses. One real edge completed first: four200 responses, a nonempty packet and matching SHA256 files were checked before completing the 50. All 50 packets and 50 scientific ledger rows persisted; all five scientific quote proofs replayed against raw bytes and matched exact text. Source quotes are independently rechecked against retained raw-source snapshots. No quote-free directional verdicts are allowed.

Literature retrieval: 303.32s across 50 edges (6.07s/edge); 103 API requests (2.06/edge). All 103 returned200; no API throttling, retry exhaustion or parse failure was observed. The 50-edge invocation took295.27s, plus8.05s for the first edge.

Source extraction: 214.72s for 50 selected edges and71 candidate source records (4.29s/edge amortized, not an individual-edge measurement). Initial dry/live source-parser fixes handled identifier-prefix matching, argument-size limits, legacy text encoding and misleading compressed-file extensions. No large remote output files were written.

Supplemental identity checks:8 web-tool calls containing10 search queries and 7 page opens, shared across the canary; two publisher opens failed and primary database/PubMed records provided the needed identities. Europe PMC 103; NCBI E-utilities0; OpenAlex API0; CrossRef API0; Valency0; publisher TDM API0. Browser-backend transport counts are not exposed. One auxiliary14-edge adjudicator recorded a178-second partial interval including waits; complete agent time and per-edge reasoning time are unavailable.

## Remaining9,950: projection and fan-out proposal (not launched)

Linear extrapolation of observed retrieval alone: 16.8 hours and approximately20,497 Europe PMC requests. A naive repeated source-scan extrapolation is11.9 hours; grouping all sample selectors into one scan per source should reduce it substantially. Neither estimate includes deeper retrieval needed to resolve the many NOT_FOUND cases.

Model time/cost was not metered, so a dollar total cannot honestly be inferred. Direct public API fees incurred were$0 and remain$0 at the same services; Codex/subagent usage depends on the account/model rates and actual tokens. A planning allowance of 0.5–2 minutes of adjudication per edge is 83–332 serial agent-hours, or28–111 hours across three adjudicators, excluding retrieval and reconciliation. This is an explicit budgeting assumption, not a measured rate.

Do not fan out the current evidence-search protocol unchanged: recent generic hits and inaccessible original-description full texts leave low resolution. First repair citation identity tables and improve synonym/type-strain and cited-primary-paper targeting, then canary the changed path. If authorized later, use one local retrieval coordinator and one durable cache, then three Codex adjudicators reading disjoint cached50-edge batches grouped by taxon. Preserve all original sample weights and validate ledger coverage centrally. Keep source scans read-only on the storage host and all review/cache output local; a remote32-worker pool would add provider contention without solving evidence gaps. No remote worker sessions were started.

## Review findings, checks, and public-repository handling

Code integrity findings64–67 were filed and fixed before finalization: unconditional50-edge bound, full-ID packet filenames, raw-metadata citation identity checks and manifest-byte binding. Follow-up 68 records an internally inconsistent MicrobeDecoder taxon crosswalk; 69 records unrelated inherited dataset DOIs. Follow-ups 70–73 cover salinity-tolerance overreach, zero-percent positive edges, generic sporulation versus endospores, and original taxon-to-publication predicates. Issue 74 records the fixed CSV line-ending check; 75 retains the obsolete observation-predicate finding. Independent PR review findings 77–79 added guards for alternate raw-root privacy, metadata-driven report paths and source-claim hash binding; all were fixed and regression-tested. The public source transport was parameterized after the live run; that exact revised transport was not live re-canaried and requires a fresh single-record transport canary before any future expansion. No underlying graph fix is included.

Validation receipt: `{"canary_regressions": {"command": "PYTHONPATH=src python -m pytest -q tests/test_edge_sample_canary.py", "coverage": ["Hard 50-edge batch bound remains active under optimized Python", "Unique manifest and plan identities; collision-resistant packet paths", "Dry run performs no retrieval or output writes", "Synthetic successful and failed provider calls persist cache and telemetry", "Quote replay rejects forged text and unbound publication identifiers", "Finalization rejects a manifest changed after retrieval", "NOT_FOUND rejects incomplete searches and failed attempted full-text retrieval", "Deterministic 10000-edge allocation: 8500 retained and 1500 omitted", "Saved manifest quotas, weights, seeded hashes, and artifact hashes", "50-edge canary replay covers 13 transforms and all five omission reasons", "Report resolves both fresh and migrated private-canary layouts and verifies SHA", "Report rejects absolute paths, parent traversal, and escaping symlinks", "Alternate raw-source roots produce relative public paths or fail closed", "Source verification rejects changed claim bytes against the frozen metadata hash"], "passed": 37, "status": "passed"}, "completed_at_utc": "2026-11-13T07:54:27Z", "contracts": {"claw_commit": "0ca25b8ee68d1fbccb4d05dcc2002fa8a64c0c34", "command": "PYTHONPATH=src python -m edgemech check-contracts", "exit_code": 0, "files": 16, "reused_after_changes_outside_contracts": true, "status": "passed", "verified": true}, "logs_are_private": true, "prior_full_suite": {"log": "validation/full-pytest-before-review-fixes.log", "passed": 370, "wall_seconds": 101.1}, "pytest": {"command": "PYTHONPATH=src python -m pytest -q", "exit_code": 0, "failed": 0, "log": "validation/full-pytest.log", "passed": 381, "status": "passed", "wall_seconds": 72.15}, "ruff": {"command": "ruff check --no-cache src/edgemech tests scripts/adhoc", "exit_code": 0, "log": "validation/full-ruff.log", "status": "passed"}, "status": "passed"}`.

Before commit, the staged diff was scanned for personal home paths, machine hostnames, email addresses and key-like strings. Public helpers take data locations/hosts as arguments or environment variables. Private command lines, receipts, raw source records and full retrieved text remain outside Git. Public artifacts contain graph identifiers, short quotes, provenance URLs and hashes. Original/private and sanitized/public canary hashes are both recorded; replay uses the original, and identity/triple equivalence is checked. No merge is authorized.
