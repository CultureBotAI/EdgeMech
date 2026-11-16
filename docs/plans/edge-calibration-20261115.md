# Ten-case edge-review calibration preparation

Baseline: EdgeMech `c446cf5440c7c4d764459f3ed82aae3901e09d1d`, 2026-11-15
(America/Los_Angeles). This preparation fixes the cohort and operational thresholds
before new ratings. It does not report a calibration pass, ten scientific reviews,
or a corrected graph. The [machine-readable protocol](../../artifacts/edge-calibration-20261115/protocol.json)
and [cohort manifest](../../artifacts/edge-calibration-20261115/cohort.json) are the
inputs for the next review round.

## Selection and exact scope

The ten occurrences come from the existing two disjoint 50-case canaries. They
are deliberately selected challenges, not a random sample. Historical support
labels and issue descriptions informed selection; neither supplies a new answer
or a gold standard. Every assessment targets the original assertion, including
an original assertion whose curated counterpart was omitted or repaired.

| Case | Historical selection reason | Existing finding |
| --- | --- | --- |
| first-01 | Observation predicate and API-kit result context | #75 |
| first-28 | Generic sporulation versus endospore formation | #72 |
| first-30 | Maximum tolerance versus salt preference | #70 |
| first-32 | Discordant organism crosswalk | #68 |
| first-43 | Zero-positive capability and omission policy | #71 |
| fresh-04 | Quantitative bin and unit definition | #87 |
| fresh-05 | Previously supported exact-strain abstract | No assumed new verdict |
| fresh-14 | Species versus nomenclatural type strain | #86 |
| fresh-32 | Previously supported full-paper table | No assumed new verdict |
| fresh-47 | Original salt value, strain scope and partial paper evidence | #106 |

`first` refers to `artifacts/edge-sample-review-20261112/canary.jsonl`; `fresh`
refers to `artifacts/edge-recanary-20261113/canary.jsonl`. Ordinals are cohort-local:
first-47 is not the salt case. The manifest pins full occurrence IDs, original
triples, both endpoint records, public input files, private source inputs and
source-record selectors/hashes. No occurrence is replaced after scoring starts.

## Thresholds fixed before scoring

Two reviewers must independently freeze all six categorical judgments for all
ten cases before seeing each other's new ratings. They receive the same pinned
evidence package. Record actual reviewer/model identities and exposure to old
labels. Separate sessions of the same model do not establish independent expert
validation or independent error distributions.

The following are operational design choices, not validated scientific accuracy
standards or population error estimates:

| Gate | Requirement |
| --- | --- |
| Input coverage | 10/10 replayed packets; 20/20 endpoint roles retained |
| Final assessment coverage | 60/60 authored axes; no `UNASSESSED`; explicit reasons for unresolved outcomes |
| Initial exact-category agreement | At least 54/60 overall, 8/10 on each axis, and 9/10 on claim |
| Unsupported resolved judgments | Zero independently adjudicated unsupported claim support, refutation or conflict; zero unsupported model `CORRECT` or `INCORRECT` judgments |
| Evidence integrity | Every input, quote, publication identity, authority version and immutable saved review pair passes replay |
| Resolution floor | Source fidelity at least 8/10; claim at least 2/10; each of relation, subject and object modeling at least 5/10 |
| Nontrivial evidence exercise | At least one exact-scope paper-backed directional claim and one exact-authority-backed `INCORRECT` modeling judgment |
| Disagreement disposition | Preserve both initial ratings and an evidence-based disposition; an unresolved disagreement over a resolved claim/model judgment blocks passage |

Publish the initial six per-axis confusion tables before reconciliation. Count
critical errors separately over all corresponding labels emitted by both
reviewers, then audit the final judgments too. An empty label class is untested,
not proof of zero error. Agreement on unresolved labels can count as agreement,
but cannot satisfy the resolution floors.

The experimental-literature denominator is prospectively seven: first-28,
first-30, first-43, fresh-04, fresh-05, fresh-32 and fresh-47. The observation-only
link first-01, identity link first-32 and type-strain link fresh-14 use structural
authorities; they still receive all six assessments and an explicit literature
applicability judgment. A reviewer contesting this applicability records a
protocol deviation, not a silent denominator change. Report all ten literature
categories as well as exact support/refutation/conflict over the seven applicable
cases. Partial evidence does not count as resolved exact literature support.

If a gate fails, preserve the result, improve evidence or the rubric and register
a new round. Do not lower thresholds after seeing ratings. Passing permits depth
review of the remaining retained 90. Expansion to the other 9,900 still requires
all-100 accounting and independent verification of at least one real correction
against regenerated candidate bytes, as required by the
[edge-correctness plan](edge-correctness-review-20261115.md).

## Preparation path and privacy

The helper is [prepare_calibration_20261115.py](../../scripts/adhoc/prepare_calibration_20261115.py).
It prepares source packets only. It never copies old decisions into new reviews,
classifies scientific claims, retrieves papers or admits graph assertions.
Each case is an explicit invocation; there is no automatic review fan-out.

The first cohort retains source wrappers in `source/source-records-50.json`,
indexed by occurrence ID. Its wrappers use an absolute historical raw-source
path and lack the new packet's `source_relative_path`. The derived packet adds
only that relative locator beneath the exact historical KG-Microbe raw root,
preserving the original wrapper, text, hash and source path. Fresh-cohort source
packets already use the current wrapper shape. Original archive bytes remain
unchanged. Checks rebuild each derived packet from its pinned retained inputs.

Run from the worktree using the pinned repository environment. The canonical
checkout's `.venv/bin/python` can be used if this isolated worktree has no venv.
The CLI help documents archive-root overrides and the explicit freeze, plan,
prepare and check operations. Use fresh-47 as the one real preparation canary;
verify its on-disk packet and receipt before any other case. A changed protocol,
cohort or preparation implementation invalidates that canary for later cases.

Private packets and receipts belong in ignored `.temp/edge-calibration-20261115/`
with private directory permissions. Public artifacts contain identities, hashes,
selectors, protocol and coverage receipts; source bodies and article bodies stay
outside Git. Preparation success establishes persisted input replay, not evidence
entailment or reviewer agreement.

## Evidence readiness and remaining work

The local LBNL review/literature workflow inspected retained sources before new
retrieval. No Valency, Tavily, Context7, publisher TDM or other network request was
made by this preparation. Do not count skill use as licensed-library access.

The inspected existing scientific ledgers contain evidence entries for fresh-05
and fresh-32; the retained follow-up adds a primary paper for fresh-47. Empty
historical ledger arrays for the other selected cases do not prove literature
absence. The next round must search retained provenance and then relevant legal
sources as needed, recording its actual search scope.

| Case / input | Retained evidence and preparation requirement |
| --- | --- |
| fresh-05 | DOI `10.1099/ijs.0.65010-0`, PMID `17625207`; Europe PMC JSON abstract with original-description strain context. The current profile supports JATS full text with PMCID, not this format. [#127](https://github.com/CultureBotAI/EdgeMech/issues/127) tracks an abstract adapter binding primary DOI/title/PMID metadata and literal text; never label an abstract as full text or authority evidence. |
| fresh-32 | DOI `10.1007/s00792-015-0765-y`, PMCID `PMC4546703`; retained JATS with comparative Table 1. Reinspect row/column identity and exact claim scope. Historical quotes total 26 words; select a sufficient shorter exact excerpt within the profile's 25-word publication budget rather than copying both blindly. |
| fresh-47 | DOI `10.3390/ani14101394`, PMCID `PMC11117391`; retained complete JATS and existing replay proof. The paper concerns another isolate; preserve partial scope and the unresolved original strain's complete salt range. |
| Modeling authorities | Pin suitable versions and exact term definitions before judgment. Snapshot availability does not establish semantic correctness or a release correction. |

Two suitable authority snapshots are retained in TraitMech at commit
`2ccbc22ccfb8bd00c9d9ca70e11e020f818fbc18`:

| Source path in TraitMech | Declared version | SHA-256 |
| --- | --- | --- |
| `data/raw/metpo.owl` | METPO release `2026-06-12` | `8b6f8fe0510a698579e532658c8ace05da2550093365df9ca83feb0741778415` |
| `data/raw/biolink-model.yaml` | Biolink `4.4.0` | `4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb` |

The [authority staging helper](../../scripts/adhoc/stage_calibration_authorities_20261115.py)
copies exact pinned raw bytes into private staging one at a time and checks
source/staged hashes and receipt metadata. Use its METPO canary before Biolink.
The existing authority proof adapter can inspect literal OWL/YAML text; decoded
or transformed excerpts need their own reproducible extraction provenance.

This version check matters to two historical blockers. METPO `2026-06-12` marks
`METPO:2000511` deprecated (OWL lines 1729–1732), whereas the older local
`2025-11-21` checkout does not. The selected newer snapshot also supplies
`METPO:1000471` with minimum-inclusive 3, maximum-inclusive 8, percent unit and
the `NaR_3_to_8` synonym (lines 15392–15431). Thus numerical bounds and endpoint
inclusion are available in a versioned authority. Percent basis, interpretation
of fractional BactoTraits membership, and the sampled release's actual ontology
version still require assessment. Neither finding closes #75 or #87 or proves a
corrected released edge. For the other modeling cases, the snapshot provides
the relevant phenotype/process definitions; independently bound NCBI/GTDB
identity records and the maintained minted-object mapping still need preparation.

Private literature locators relative to
`~/agent-work/EdgeMech/edge-sample-review-20261112-data/`:

- fresh-05: `phase2/literature/cache/82d96c9481a6d11eefc5976e65b2863e10bed3cedf8b02f9b09cdb92802cf807.response`
  (SHA-256 equals filename stem).
- fresh-32: `phase2/literature/cache/4e8b045ec2a2393ebe3716c9a335d5c6b21c96e239388c43a5ec45f3226e30c9.response`
  (SHA-256 equals filename stem).
- fresh-47: canonical EdgeMech
  `.temp/occurrence-canary-edge47-125-fixed-20261115/primary2024.xml`, SHA-256
  `df87ed3eabcefee07f32f61c7b909e616dd072b1cd7ee7dafff42f5872345838`.

The next evidence freeze must include copied/pinned authorities, publication raw
inputs, proof sidecars, instructions and adapter versions available identically
to both reviewers. This source-packet preparation is not an evidence-complete
review package. PR #102 remains a separate prerequisite for authenticated
general-helper retrieval; it does not block retained-evidence work.

The pinned CLAW manifest, commit
`0ca25b8ee68d1fbccb4d05dcc2002fa8a64c0c34`, SHA-256
`cd72d1648bf43a89fa112e6a8c06738af30d3d00d712cfbe3a92c5365420fe57`, still disables
EdgeMech `record_review` and `evidence_reference_validation`. This bounded local
profile does not change those flags.
