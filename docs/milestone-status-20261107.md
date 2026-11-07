# EdgeMech milestone review — 2026-11-07

This work implements the next #766/#767 stages of the
[2026-11-03 plan](https://github.com/Knowledge-Graph-Hub/kg-microbe/blob/5b785fafba6eeb52adf3ff5dae349ca1e284dbe1/docs/plans/edge-curation-implementation-20261103.md).
The plans remain an architecture baseline, not a claim that later browser,
scientific review-worker, production queue or publication milestones have shipped.
Every PR below remains unmerged; merges require explicit human approval.

| Repository / PR | Deliverable | Dependency or remaining scope |
| --- | --- | --- |
| [CLAW #962](https://github.com/CultureBotAI/culturebotai-claw/pull/962) | Shared artifact/native assertion contracts and reviewed semantics | Contracts-only prerequisite; all five CI checks passed. |
| [EdgeMech #2](https://github.com/CultureBotAI/EdgeMech/pull/2) | Repository scaffold, routing, lossless SQLite migration, external Parquet/DuckDB, native packets and census | Exact reviewed runtime contract pin `1b5391d083ba85ac94e5279c3cba25ac4fde243c`; all 16 imported files checked. |
| [CLAW #953](https://github.com/CultureBotAI/culturebotai-claw/pull/953) | Honest infrastructure capabilities, fleet registration and governance rollout | Blocked by [#960](https://github.com/CultureBotAI/culturebotai-claw/issues/960), the immutable active DUF release policy. |
| [MIM #1147](https://github.com/CultureBotAI/MediaIngredientMech/pull/1147) | Pinned ingredient decision export | Exact substance/predicate/form and payload/evidence scope; packaging extraction remains [#1144](https://github.com/CultureBotAI/MediaIngredientMech/issues/1144). |
| [Trait #2082](https://github.com/CultureBotAI/TraitMech/pull/2082) | Owner-bound canonical example export | Exact organism/strain observations and their reviews remain [#2083](https://github.com/CultureBotAI/TraitMech/issues/2083). |
| [Habitat #2313](https://github.com/CultureBotAI/HabitatMech/pull/2313) | Native decision-table export with original action predicates | Additional scientific surfaces and reviewed projections remain [#2311](https://github.com/CultureBotAI/HabitatMech/issues/2311). |
| [Taxon #229](https://github.com/CultureBotAI/TaxonMech/pull/229) | GTDB-to-NCBI mapping inventory with exact/broad/close/narrow semantics | Mapping-specific review proofs and distinct strain/assembly/nomenclature surfaces remain [#226](https://github.com/CultureBotAI/TaxonMech/issues/226). |
| [Site #541](https://github.com/CultureBotAI/CultureBotAI.github.io/pull/541) | Infrastructure membership without an invented scientific corpus | Depends on CLAW fleet admission; no site deployment is part of this work. |

## Preserved scientific boundaries

The four baseline native export surfaces contain 327,941 assertions. MIM has
2,999 mapping decisions (1,747 supported and 1,252 withheld). Habitat has 1,831
native decisions (424 supported and 1,407 unassessed). Trait contributes 784
unassessed canonical examples from 1,130 owners; Taxon contributes 322,327
unassessed mapping rows. Their exact input manifests and source commits are
recorded in the [validation evidence](validation/20261107.md).

The baseline combined canary completed: all 327,941 native assertions and 1,000
selected KG rows were independently verified and persisted. All selected KG rows
were unmatched; it created zero approvals. This is not the full-population census.
The full 17,637,435-row run is pending the specialist expansions requested later
in this session. The #960 release-policy transition and native follow-up work are
also in progress; the table above records their existing prerequisite state.

Supported native status is inherited within the exported native scope. It does
not approve a KG occurrence, create a claim or count as an independent scientific
review. Transport packets retain the original native payload, locators, evidence,
review status and limitations; canonical decisions remain deferred/withheld.
Unknown distinct observation, claim and experiment counts remain unknown.

The census uses the historical 20260929 KG-Microbe snapshot, with recorded
producer `1408e7099-dirty`; it does not rename that input as a current production
release. Full-population transport accounting and endpoint candidates do not
measure all biological overlap across the Mechs' scientific corpora.

## Review and gate disposition

The local reader contract (`edgemech-reader/v1`) now defines pinned exact detail,
bounded ID search, query-bound pagination and verified artifact streaming. It
does not deploy a browser or authorize publication. Its 12 focused tests and
independent review passed; the complete EdgeMech suite has 167 passing tests.
The wheel/source build succeeds, and the extracted source archive collects all
167 tests. These results precede any later specialist export expansion.

Independent adversarial passes found and filed durability, publication race,
runtime pin closure, reporting provenance, source packaging, native persistence,
catalogue scaling and Arrow transaction-lifetime defects. In-scope repairs are
included in their owning PRs, with negative controls and real persisted canaries.
The [catalogue evidence](validation/native-catalog-20261107.md) retains the
interrupted run and measured defect rather than presenting it as a successful run.

CLAW admission at `abe775da003c9ffb521a0c96baf86e9f0c5b79e7` passes 7,854 tests
with 446 skipped and one failure, solely the unchanged immutable release-policy
gate tracked in #960. Fleet audit likewise has 148 passed and that one failure.
The 16 additional cohort-assumption failures were repaired under
[#963](https://github.com/CultureBotAI/culturebotai-claw/issues/963). The historical
release manifest, active policy and existing consumer pins were not rewritten
to make this gate pass. An approved admission/successor policy is still required.
