# Round03 source-report evidence contract

Coordinator preparation, 2026-11-16; EdgeMech #182, #180 and #181. This is a
transport and evidence-binding repair. Historical ratings, original occurrences,
cohort membership, seven-case experimental-literature denominator and every
preregistered calibration threshold remain unchanged. It does not resolve the
remaining source-fidelity provenance gaps or authorize expansion.

## Shared contract and ownership

CLAW owns the optional assessment fields, validation and canonical Markdown:

```yaml
assertion_basis: source_report
report_witnesses:
  scope: Exact original source-attributed proposition
  source_instance_evidence_ids: [original-instance]
  identity_evidence_ids: [versioned-identity-authority]
  definition_evidence_ids: [versioned-definition-authority]
```

Omitting `assertion_basis` retains the independent-claim rule. The explicit
`source_report` basis is allowed only when the original proposition concerns
what an identified source reports. It cannot turn an independent biological
claim into a report, replace the original endpoint, infer measurement units,
or erase identity uncertainty. A broad category such as NamedThing supplies
neither the original term's identity nor its definition.

Shared validation binds every witness to the assessment, enforces witness kinds,
source hashes and precise locators, and requires all three groups for resolved
outcomes. Supported reports require a supporting source instance and no refuting
instance. Authorities cannot supply the instance's direction. Concern/unknown
outcomes remain representable without positive source evidence; Edge enforces
the corresponding categorical direction. The canonical Markdown states that
source-report support does not establish independent biological truth and shows
the exact scope and each witness group. YAML readback preserves them unchanged.

The candidate starts at CLAW `0710413e8bbb057e943aa0629b1f15d377b19bda`.
Compared with Edge's previous `0ca25b8ee68d1fbccb4d05dcc2002fa8a64c0c34`
pin, the consumed pre-candidate changes are governance `__init__.py` and
`artifacts/scripts/check_vendored_sync.py`; record-review schema/helper semantics
were unchanged. The final immutable candidate is
`5ca474ea8bd6ca40852a93177fe2d4a7e896776b` (CLAW PR #1289). Its dependency,
lockfile, 16 contract hashes and complete governed artifacts are pinned
deliberately before any reviewer launch; no installed dependency is patched.

Normal complete governance sync also carries four maintained upstream updates
since Edge's older vendored-artifact pin: the vendored checker, backlog-loop
prompt, shared Mech schema, and merge admission controller. These are copied
byte-for-byte from the immutable owner candidate alongside the report
schema/helper/guide and canonical pin; no Edge-specific changes are made to them.

## Edge replay and meaning

Only the claim assessment may carry the new fields. Its report scope must equal
its `assertion_scope` dimension. A source instance remains `record_content` backed
by the verified original packet. It is never paper evidence. Independent
identity and definition witnesses remain literal, versioned authority proofs.
Each authority sidecar proof declares the original entities it establishes:

```json
{"original_entities": {"subject": "original subject ID", "predicate": "original predicate ID", "object": "original object ID"}}
```

Identity witnesses collectively cover both original endpoints; definition
witnesses cover both endpoints and the predicate. One exact authority may
legitimately supply both roles. All resolved authorities require exact scope and
supporting evidence. The source-instance IDs cannot serve as authority IDs, and
authority bytes must differ from the original packet and every original input
hash. Copying a raw record under another path or evidence ID cannot satisfy this
independence check. Producer code alone cannot establish the particular reported
instance. Mechanical checks cannot decide whether a quotation truly defines the
term: an independent semantic audit must confirm original identity, generating
version, exact meaning, organism/strain and relevant conditions.
Every authority linked to the source-report claim must enter its identity or
definition witness groups, including contrary authorities (#189). Deleting an
entity declaration does not make an authority exempt. This prevents selected
supporting witnesses from concealing contrary identity/definition evidence;
separate biological paper counterevidence remains a literature judgment.

Only source-instance witnesses supply support/refutation for the report itself.
Paper text, if inspected, retains its separate literature assessment. Report-only
support is excluded by code from the exact-paper-backed directional-claim gate.
Default independent claims still require independent paper/authority evidence;
literature still requires replayable paper text. Report fields cannot leak into
literature or modeling axes. A supported report may coexist with incorrect or
unresolved modeling, partial completion and needs-curation, as in #152. It cannot
waive an unavailable required check or an aggregate pass gate. Every receipt
retains the claim's basis and scope and reports zero KG admissions.

## Seal before adaptation

Initial assessments must list every source-instance, identity and definition
witness in both the axis evidence set and its explicit role group. Missing
bindings cannot be repaired after sealing without a fresh assessment. Initial
matrix validation checks complete group bindings and scope. Canonical-pair
parity maps proof IDs to the manifest IDs and compares the basis, report scope,
and each witness group in addition to existing category/dimension/evidence
parity. Merely mentioning a source in prose is not a binding.

Fresh reviewer-visible authority views must be bounded evidence excerpts, with
private retained source bytes, version, offsets and hashes. Do not expose the
historical benchmark/evaluation prose found in round02 PREGO material (#175).
Before scoring, run one real save/readback/check canary through the actual
reviewer clone, launcher, shell, environment and output path, verify persisted
YAML/Markdown and receipts, then run the second reviewer readiness path.

## Separate source-fidelity judgment

Source-fidelity `CONTRADICTED` can denote a demonstrated unfaithful translation
from an exactly bound source field to the original graph assertion. It does not
necessarily mean that biology proves the opposite property. For example, a
bound generic sporulation field cannot justify a more specific endospore
translation. Missing specificity alone does not establish a biological negation;
missing provenance alone does not prove an unfaithful transformation. Without
the exact identity-to-datum/field binding, retain `NOT_ASSESSABLE`. This maintains
the separate claim and fidelity axes and cannot be used to reach the 8/10 floor
by relabeling unresolved cases.

## Consumer verification

At shared pin `5ca474ea8bd6ca40852a93177fe2d4a7e896776b` in an isolated
Edge virtual environment, the focused occurrence-review, calibration-round,
adjudication-gate and canonical-pair replay suites pass: **246 tests**. This
includes real canonical save/readback/render, copied-raw-source rejection,
role/axis leakage, original-entity binding, sealed witness parity, strict
completion/pass rules and exclusion from the independent paper gate.
The #189 regressions first demonstrated that omitted counterauthorities were
accepted, both with and without an original-entity annotation; both are now
rejected. A separate biological paper may still refute the biology while an
exact source report remains supported.
`edgemech check-contracts` verifies all 16 pinned files; canonical governance
check reports no drift. The changed implementation/tests pass Ruff. `uv build`
produces nonempty wheel and source archives in
`.temp/round03-integration-dist/`. Full shared CI, final M5 suite and actual
reviewer-clone readiness canaries remain separate launch prerequisites.
