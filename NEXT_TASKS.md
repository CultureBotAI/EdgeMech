# Edge-review next tasks

Last reconciled: **2026-11-15**, against `main` at `a88ebb72223d8e8c321703da57bade6e465f8c36`, open GitHub issues/PRs, and retained review evidence.

Scope: the stratified edge review and related edge-quality follow-ups. Update this file when work starts or ships, checking GitHub and current code before changing status. Record completion dates and PRs. Preserve historical manifests, packets, reports and scientific decisions; a merged engineering PR does not promote an edge's scientific status. Unrelated release/deployment work is outside this backlog.

## Review coverage and completed work

- **DONE — 2026-11-15, [PR #76](https://github.com/CultureBotAI/EdgeMech/pull/76):** a reproducible 10,000-occurrence manifest and two disjoint 50-occurrence canaries, with separate source-fidelity and scientific-support assessments. The 100 reviewed occurrences are purposive coverage samples; **9,900 remain without retrieval or adjudication**. The reviewed 100 are not 100 scientifically validated claims.
- **DONE — 2026-11-15, [PR #94](https://github.com/CultureBotAI/EdgeMech/pull/94):** exact organism/strain/reference binding, source-sidecar replay, anchored fallback queries and private output guards. The retrieval guard fixes from #76 are integrated. Adversarial-review issues #111–#115 are closed; both PRs' post-merge contracts/test/build and merge-integrity workflows passed. Final suites: 462 tests for #76 and 533 for #94.
- **DONE — 2026-11-15, [PR #107](https://github.com/CultureBotAI/EdgeMech/pull/107), included in #94:** edge47's source unit and one complete organism-matched primary paper were inspected. The source reports **NaCl 0–10%, positive growth**, for BacDive 6845 / DSM 20190 / CIP 103005. Percentage basis and linked assay conditions remain unspecified. The paper reports another isolate, GI38, growing at 3.0% and 6.5% w/v; it does not independently verify the original strain's full range. No graph promotion or review expansion occurred.

The fresh 50-occurrence canary resolved source fidelity for 45/50 (41 supported, four contradicted, five not assessable). Scientific support resolved only **4/28 applicable claims**: four supported, eight not found, 16 not assessable; 22 other occurrences were excluded from this axis. Missing evidence is not contradiction. These descriptive rates do not estimate population accuracy.

Evidence: [fresh-canary report](artifacts/edge-recanary-20261113/RECANARY-REPORT.md), [first-canary report](records/edge-sample-canary-2026-11-12.md), [targeting validation](docs/validation/organism-targeting-20261114.md), and [edge47 source/paper assessment](reviews/structured/20261115T081452Z-edge47-salt-source-and-paper/review.md). Historical references to draft PRs or pre-fix blockers in those reports describe their frozen runs; use this backlog for current work status.

## Recommended sequence

| Priority / status | Work | Next action and completion evidence |
| --- | --- | --- |
| 1 — **IN PROGRESS** | General full-text credential protection: [#100](https://github.com/CultureBotAI/EdgeMech/issues/100), [PR #102](https://github.com/CultureBotAI/EdgeMech/pull/102) | The draft has a clean independent review and green CI at `2364161819951b7899ba62cebcd461bf0394c4a7`. Reconcile it with current main and validate the final candidate before seeking explicit merge authorization. The targeted launcher fix in #76 does not close this separate general-helper issue. Complete this before further authenticated general-helper retrieval. |
| 2 — **PENDING, actionable** | Joined measurement context: [#105](https://github.com/CultureBotAI/EdgeMech/issues/105) | Display substance, literal value, recorded unit, relation, growth result, exact organism/strain and reference together, bound to the frozen source record. For edge47 show NaCl / 0–10 / % / growth / positive. Refuse mismatched-record joins. Keep unknown percentage basis and assay conditions explicit; infer neither an optimum nor a maximum. Preserve historical decision bytes. |
| 3 — **PENDING, actionable audit; remediation depends on upstream owners** | Source identity and interpretation findings in the table below | Check maintained transforms and existing quarantine/fixes against each exact frozen example before proposing changes. Preserve provenance and add evidence-backed regressions. A historical defect does not establish that today's upstream release still has it. Publish source/ontology corrections through their owning repositories and normal release procedures. |
| 4 — **PENDING, gated live work** | One new end-to-end retrieval canary, then a bounded scientific review | After the relevant access, context and identity prerequisites are met, rebuild the source-bound plan and dry-run it. Run exactly one real unit through the intended launcher, worker environment and output path. Verify nonempty saved evidence, hashes, organism/strain identity and the actual claim assessment before any expansion. Record provider failures and active review time. Candidate sources are BactoTraits, MicrobeDecoder and PREGO. Larger retrieval/adjudication remains unlaunched. |

**Recommended start:** finish #102's integration/merge decision and implement #105. The #105 presentation work can proceed independently of publisher access. Preparing a canary does not require assuming that all older source issues are resolved; select a claim whose own prerequisites are satisfied and keep unresolved bindings excluded.

## Source, ontology and regression follow-ups

All entries below remain open as of the reconciliation date. Local evidence audits are actionable; upstream repair/publication is a dependency where applicable, not a completed EdgeMech deliverable.

| Issues | What remains | Closure evidence |
| --- | --- | --- |
| [#68](https://github.com/CultureBotAI/EdgeMech/issues/68), [#106](https://github.com/CultureBotAI/EdgeMech/issues/106) | Discordant MicrobeDecoder organism crosswalks, including frozen records 10743 and 20904 | Trace the exact joins, independently resolve identity or prove an existing quarantine, and prevent unrelated NCBI fields from entering the measurement/reference binding. Edge47 currently excludes the discordant fields. |
| [#69](https://github.com/CultureBotAI/EdgeMech/issues/69) | Inherited dataset DOIs identify unrelated publications | Verify exact titles/identifiers in the maintained assignment table; prove corrections with a bounded regression before any bulk repair. Database provenance is not biological claim evidence. |
| [#70](https://github.com/CultureBotAI/EdgeMech/issues/70), [#72](https://github.com/CultureBotAI/EdgeMech/issues/72) | Maximum salinity tolerance mapped to halophily; generic sporulation mapped to endospore formation | Establish the correct trait semantics and a source-grounded mapping or explicit exclusion. Preserve range/optimum/tolerance and spore-type distinctions. |
| [#75](https://github.com/CultureBotAI/EdgeMech/issues/75), [#86](https://github.com/CultureBotAI/EdgeMech/issues/86), [#87](https://github.com/CultureBotAI/EdgeMech/issues/87) | Obsolete observation predicate; taxon/type-strain conflation; opaque BactoTraits quantitative classes | Obtain maintained predicate/type-strain representations and auditable bin definitions with bounds, endpoint conventions, units and range-versus-optimum meaning. Preserve API-kit outcome context. Do not invent local ontology definitions. |
| [#71](https://github.com/CultureBotAI/EdgeMech/issues/71), [#73](https://github.com/CultureBotAI/EdgeMech/issues/73) | Confirm zero-percent capability omission and original-versus-curated publication-predicate corrections | Show the maintained transform preserves the intended correction with the retained examples as regressions. Existing curated/omitted behavior may already be correct; proof can close these without another graph edit. |

Related earlier edge-quality work, **PENDING audit / upstream remediation**:

- [#56](https://github.com/CultureBotAI/EdgeMech/issues/56): preserve the distinct enrichment and screening stages of the Actinobacillus medium evidence; do not split a reported mixture into three consumption claims.
- [#36](https://github.com/CultureBotAI/EdgeMech/issues/36): triage missing labels/categories affecting 238,422 pinned edge occurrences. This is an occurrence count, not a distinct-node count; incomplete metadata alone does not establish scientific invalidity.

## LBNL/library service usage and next access check

Usage below is scoped to the two canaries and the edge47 follow-up. The LBNL literature/review skills were used for the follow-up, but successful licensed-library full-text retrieval was not demonstrated in these runs.

| Run / service | Observed use and result |
| --- | --- |
| First 50 | 103 public Europe PMC requests, all HTTP 200. The report explicitly records Valency 0 and publisher TDM 0. |
| Fresh 50 | 425 total paper-retrieval HTTP attempts. Five credential-backed Springer **open-access JATS** API attempts all returned 401. Seven Wiley TDM attempts returned four 403s and three 400s. These publisher attempts supplied no successful full text. Public discovery/retrieval also used Europe PMC, Crossref, OpenAlex and NCBI. |
| Edge47 follow-up | The authenticated Wiley attempt for the 1993 paper returned 403. Local Zotero search found neither the priority 1983 nor 1993 paper. The 1983 access check skipped the LibKey/proxy route because it was unconfigured at that time. The complete 2024 paper actually inspected was retrieved anonymously through Europe PMC, with 149,817 XML bytes saved and verified. |
| CBORG tools | No Valency, Tavily or Context7 execution is recorded in the examined fresh-canary/edge47 transport, packet and receipt metadata. This is a statement about retained traces, not proof that no conversation-level tool call ever occurred. Skill names alone do not establish service execution. |

Public provenance is in the reports linked above. Detailed private receipts remain outside Git: `edge-sample-review-20261112-data/phase2/literature/http-attempts.jsonl` (Springer entries 17, 44, 165, 223, 397; Wiley entries 93, 95, 103, 105, 124, 126, 345), and `retained-pr107-20261115/.temp/fulltext/salt-evidence-47-20261115/` (`local-search.json`, `kandler1983-access.json`, Wiley and primary2024 receipts). These are relative archive locators under the private EdgeMech agent-work directory, not repository files. Do not commit raw article bodies, private source packets or credentials.

The next access canary should establish actual usable evidence through the intended worker environment. Check configured publisher/Library access and, where useful, Valency/Tavily discovery; record the service and outcome without exposing credentials. Verify paper identity and readable full text separately from HTTP success. Older exact-strain evidence may still be unavailable; leave the original salt-assay basis, conditions and full range unverified unless a matching source supplies them.
