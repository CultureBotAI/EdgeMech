# M5 calibration failed-round results, 2026-11-16

**Round01 failed.** Initial object-node agreement was **7/10**, below the fixed
minimum **8/10**. Separate adjudication found **eight unsupported initial
modeling judgments**, resolved source fidelity **7/10** against a minimum of
8/10, and two blocking unresolved disagreements. Neither initial matrix was
rewritten. The remaining retained 90 and the other 9,900 have not been launched.

Round `m5-calibration-20261116-round01` freezes the original ten occurrences,
six axes, seven-case experimental-literature denominator and unchanged thresholds.
Its [manifest](../../artifacts/m5-calibration-20261116/round-01-manifest.json) has
SHA-256 `14175634b794a90124bb66a458af3c30f23ca40e10731c4ba89226134a89f4ab`.
The [input replay](../../artifacts/m5-calibration-20261116/round-01-input-replay.json)
verifies 124 input pins, ten packets and twenty endpoint roles. These transport
checks do not establish scientific correctness or calibration passage.

Two fresh CLI sessions used the identical frozen package without conversation
forks or access to one another's ratings. Their actual runtime models were both
`gpt-6-astra`; session IDs and unavoidable prior-context exposure are recorded in
the [execution accounting](../../artifacts/m5-calibration-20261116/round-01-execution.json).
Both exited 0. They sealed their [initial matrix A](../../artifacts/m5-calibration-20261116/reviewer-a-initial.json)
and [initial matrix B](../../artifacts/m5-calibration-20261116/reviewer-b-initial.json)
before comparison. Same-model sessions provide an operational agreement check,
not independent expert validation.

The [six confusion tables](../../artifacts/m5-calibration-20261116/round-01-initial-comparison.json)
retain every original category and disagreement:

| Axis | Initial exact agreement | Required |
| --- | ---: | ---: |
| Claim | 9/10 | 9/10 |
| Literature | 10/10 | 8/10 |
| Relation | 10/10 | 8/10 |
| Subject node | 10/10 | 8/10 |
| Object node | 7/10 — failed | 8/10 |
| Source fidelity | 10/10 | 8/10 |
| All axes | 56/60 | 54/60 |

The separate [adjudication report](../../artifacts/m5-calibration-20261116/round-01-adjudication.md),
[label-by-label audit](../../artifacts/m5-calibration-20261116/round-01-adjudication-audit.json)
and [computed gates](../../artifacts/m5-calibration-20261116/round-01-gates.json)
assess all 60 final axes and all 53 initial resolved claim/model labels, including
agreements. Unsupported initial labels comprise **6/33 CORRECT** and
**2/14 INCORRECT** modeling judgments. The two supported-claim and four
contradicted-claim labels were supported within their explicit scopes. No
conflicting-evidence label was emitted; that critical class remains untested.
All 23 final resolved claim/model labels were audited, with zero unsupported.
This does not erase the eight initial critical errors.

Final resolution is claim **3/10**, source fidelity **7/10**, relation **7/10**,
subject **7/10**, object **6/10**. Unresolved agreement is excluded from every
resolution numerator. Four initial disagreements are preserved; fresh-05 and
fresh-47 object judgments remain blocking. All ten literature categories remain
reported, with exact directional coverage **1/7** and no denominator change.

Each reviewer saved and replayed fresh-47 before the remaining cases. Eighteen
canonical pairs were saved and independently replayed: **18/18 available passed**,
but availability is only **18/20**. Both fresh-05 saves failed with the preserved
claim/model acceptance error tracked in [#152](https://github.com/CultureBotAI/EdgeMech/issues/152).
All 18 saved reviews remain partial; **zero completed scientific reviews** are
claimed. The adjudicator reproduced both failed validations. Evidence integrity
fails despite valid literal/identity replay: unavailable pairs, missing required
version/evidence checks and unsupported semantic proof roles remain visible.

Fresh-05's support is limited to the original NCBITaxon:1123071 named-strain
nonmotility characterization in the identity-verified abstract, independent of
the mixed BactoTraits source row. It does not certify the formal ontology closure
or a correct typed edge. The claim/model policy must be settled prospectively;
the failed save is neither biological refutation nor permission to change ratings.

Final publication review found that combining both reviewers' canonical quotes
would exceed the 25-word budget for Biolink 4.4.2. [#157](https://github.com/CultureBotAI/EdgeMech/issues/157)
preserves that finding. All exact canonical pairs and quote-bearing author helpers
remain private at their original replay paths, with hashes in public accounting.
The public bundle contains bounded matrices, audits and metadata rather than those
quotation-bearing bodies. No original proof or rating was changed.

Final tool review also found [#158](https://github.com/CultureBotAI/EdgeMech/issues/158)
(missing final-assessment scope/dimension guards) and
[#159](https://github.com/CultureBotAI/EdgeMech/issues/159)
(ancestor redirects in publication paths). Both are repaired with focused
regressions. Actual adjudication records already contained the required fields;
recomputing with the repaired helper preserved every gate result. Prior helper,
audit and gate-result bytes remain privately retained with verified hashes.
The [final verification record](../../artifacts/m5-calibration-20261116/round-01-final-verification.json)
records **830 tests passed**, full Ruff scope passed, all 16
pinned CLAW contract files verified, and source/wheel builds passed. The first
build attempt's sandbox cache-access failure remains preserved; the normal
approved retry succeeded. Separate read-only rereview accepted the repaired
candidate with no new material findings, reproduced the public accounting,
passed 51 focused repair tests and checked publication privacy/quotation limits.

The seeded current-runtime fresh-47 receipt was preserved and replayed before
the other source packets. Reviewer views retain exact original assertions, both
endpoint records, full source wrappers and measurement context while excluding
historical authored judgment fields. Original packets remain pinned for mechanical
replay. Evidence researchers saw historical selection/source metadata; neither
will serve as a blinded reviewer.

The package contains five publication candidates with replayed primary identities
and bounded literal excerpts, five newly retrieved NCBI records, catalog snapshots,
separately identified Biolink 4.4.0 and 4.4.2, METPO 2026-06-12 and SKOS 2009.
Abstracts remain abstracts. Fresh-32's comparative table cites an earlier target
study; fresh-47's paper concerns another isolate. Literal replay is not entailment.

Fresh-14's sampled ontology provenance remains incompletely bound. A local
producer fingerprint names Biolink 4.4.2, but the sampling archive lacks a complete
hash chain to its full inputs. The local physical row at the sampled ordinal
differs; historical selector semantics remain unresolved. The staged 4.4.0
snapshot cannot supply that missing provenance. Maintained KG-Microbe commit
`2d94ed094167d94402f21400a9ad7dc4f7f20438` uses strain `subclass_of` taxon with an
explicit domain/range exception; that convention does not prove strict correctness.

The LBNL workflows used actual CBORG Valency/Tavily calls and anonymous Europe
PMC/NCBI requests. A sandbox DNS failure was retained; the normal approved network
path then supplied raw responses. No authenticated general full-text helper or
paid research job was used. Article/source bodies and exact calls remain private.

Fresh-04 exposed another accession conflict, filed as
[#145](https://github.com/CultureBotAI/EdgeMech/issues/145): BactoTraits names
Paludifilum halophilum/BacDive 132033 with DSM 102218, while BacDive and its original
description's abstract identify DSM 102817. The current DSM 102218 catalog identifies
Clostridium sp. This does not decide the NaCl claim or authorize a replacement identity.

Independent read-only review drove repairs for
[#144](https://github.com/CultureBotAI/EdgeMech/issues/144),
[#148](https://github.com/CultureBotAI/EdgeMech/issues/148) and
[#149](https://github.com/CultureBotAI/EdgeMech/issues/149): canary runtime/input
binding, required adapter pins and pre-access path guards. Original artifacts remain
unchanged; v2 views and assembly outputs are separate. Fresh-47 was canaried and
checked before the remaining views and before full frozen-package replay.
Independent re-review verified the fixes, 124 pins, ten views and absence of old
rating fields. Pre-launch focused tests: **52 passed**; complete suite: **779 passed**.
Limited inherited prior-review prose remained inside required source/definition
fields and was disclosed by both reviewers; [#156](https://github.com/CultureBotAI/EdgeMech/issues/156)
requires stronger content-level separation in the next package.

The production replay canary passed at committed runtime `ad902ca`; an earlier
initial-staging canary was stopped because its empty-directory prerequisite did
not fit the already seeded packet. Its failed receipt remains preserved. No job
continues after the completed reviewer sessions.

New findings are tracked in [#153](https://github.com/CultureBotAI/EdgeMech/issues/153)
(predicate meaning and deprecation), [#154](https://github.com/CultureBotAI/EdgeMech/issues/154)
(METPO nonmotile hierarchy), [#155](https://github.com/CultureBotAI/EdgeMech/issues/155)
(exact local-vocabulary definitions), and #156 (semantic source fidelity and
reviewer exposure), alongside #152 and #157. Existing #72 and #86 retain the
sporulation/endospore and taxon/type-strain mapping defects. Maintained owners and
required regenerated-candidate checks are specified in each issue. These are
correction proposals and evidence blockers, not verified scientific corrections.

[Round02 is separately registered](../../artifacts/m5-calibration-20261116/round-02-registration.json)
with a concrete [revised common rubric and prerequisites](../plans/m5-calibration-round02-20261116.md).
The original cohort, axes, denominators and thresholds are unchanged. No package
hash or reviewers are assigned yet. The next executable work is evidence/authority
repair and the shared claim/model acceptance clarification, followed by new
single-unit canaries and a fresh freeze. Round01 remains failed.

Coverage accounting: the ten original calibration occurrences received two
initial six-axis reviews and separate adjudication; the remaining retained 90
received no new six-axis assessment in this run; the other 9,900 remain unreviewed
by this track. This is additional depth on retained occurrences, not new population
coverage or all-100 completion. A separate worker owns BactoTraits release
verification. Its candidate work does not establish a corrected published release;
publication status remains separately unresolved here.
