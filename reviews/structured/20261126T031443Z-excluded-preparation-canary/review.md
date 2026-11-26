# EXCLUDED PREPARATION CANARY: native runtime and profile engineering check

- Review: 20261126T031443Z-excluded-preparation-canary
- Repository: CultureBotAI/EdgeMech
- Started UTC: 2026-11-26T03:10:08Z
- Finished UTC: 2026-11-26T03:14:43Z
- Reviewer: native worker 01a1fd21-cd97-7601-8f2c-12268643a483 (self_review)
- Completion: completed
- Verdict: pass_with_limitations
- Scientific review: false

## Summary

Bounded engineering review of two maintained runtime/profile files. The actual worker installed the frozen environment, verified all 16 CLAW contracts, inspected the canonical source inputs, and exercised one Valency metadata/abstract retrieval with private hash/offset replay. This record exercises shared canonical persistence; it makes no occurrence assessment, scientific claim rating, calibration assertion, A/B attempt or production-readiness claim. Scientific coverage is exactly 0.

## Scope And Provenance

Exactly two maintained engineering files for one excluded preparation canary; population_size=2 counts files only. No graph occurrences are targets.

Selection: Coordinator-authorized Unit 3 runtime/profile check in the existing native preparation worker.
Coverage: full; 2 reviewed / 2 in the declared population.
Source: working_tree at Git base 945c421c648fe09858eabf1f2a4447ab27f9eae3.
Working-tree hashes do not imply those bytes were committed.

| Target | Path / selector | Kind | Label |
| --- | --- | --- | --- |
| runtime | pyproject.toml | maintained | Pinned native preparation runtime |
| profile | docs/record-review-profile.md | maintained | Native profile scope and evidence admission limits |

## Validation

| Check | Status | Required | Targets | Result |
| --- | --- | --- | --- | --- |
| Pinned installed CLAW byte contracts | passed | True | runtime | All 16 pinned files verified at CLAW 4fad8df5b2367da68faca6379ce32eb9b8f4ba9b. |
| Canonical source and target inspection | passed | True | runtime, profile | Maintained canonical inspect returned repository identity, actual Git base, exact input hashes and two engineering targets. |
| Actual-worker library access and literal replay | passed | False | profile | One Valency request returned matching metadata and abstract; saved 1209-byte abstract and four-word snippet replayed at UTF-8 offsets [197,225). No body/table/figure inspected. |
| Configured local Zotero route | failed | False | profile | Read-only local query failed: sqlite3.OperationalError: unable to open database file. The configured /Users/marcin/Zotero/zotero.sqlite path is absent on this host. No global library absence inferred. |

## Scientific And Domain Assessments

### Pinned engineering runtime available in actual worker

schema: supported. Targets: runtime.

The frozen project environment completed installation and the maintained checker verified all 16 canonical contract bytes. This verifies the shared runtime contract used by the engineering canary.

### Engineering persistence and scientific acceptance remain distinct

scope: supported. Targets: profile.

The inspected profile explicitly preserves exact occurrence, evidence replay and six-axis gates. This engineering record targets no occurrence and cannot qualify PR233 inventory candidates, alter A/B membership or claim coverage.

## Findings

No findings recorded within this review's declared scope.

## Recommended Actions And Acceptance Checks

## Category Boundaries


## Evidence

| Evidence | Reference / locator | Support | Observation |
| --- | --- | --- | --- |
| contracts-output | .temp/restart-preparation-01/commands/contracts-01/stdout; complete JSON; files=16, verified=true | supports | Actual installed byte validation passed; source pin records exact saved output. |
| inspect-output | .temp/restart-preparation-01/commands/canonical-inspect-02/stdout; source and targets | supports | Maintained canonical helper captures two engineering targets and exact current input bytes. |
| profile-contract | docs/record-review-profile.md; Evidence replay and limits; Commands and acceptance | supports | Profile distinguishes canonical persistence from six-axis scientific acceptance and admits only specific replay formats; current body extraction is not an admitted proof. |
| library-access | .temp/restart-preparation-01/library/readback-01.json; identity, abstract hash and exact literal offsets | context_only | Matching DOI 10.1099/ijs.0.65010-0 / PMID17625207. Metadata and abstract only; no scientific ratings. Valency representation is not admitted as Europe PMC/JATS. |
| local-search | .temp/restart-preparation-01/commands/local-provenance-01/stdout; 35 bounded retained provenance hits plus separate failed Zotero query receipt | context_only | Retained fresh05 report and OA dispositions inspected before the single live request. Historical private body extraction was not located in the searched paths. |
| issue220 | https://github.com/CultureBotAI/EdgeMech/issues/220; Live body retained in commands/issue220-read-02-network/stdout | context_only | Issue remains OPEN. New scientific package, fresh runtime canaries, exposure review and original-identity/lineage dependencies remain required. |

## Limits And Additional Notes

- Scientific review coverage is exactly 0; occurrence=null; no A/B attempts. Full A/B counts and baseline cutoff remain null.
- This is self-reviewed engineering preparation. Coordinator independent artifact inspection and helper publication review remain pending.
- Shared canonical save/check readiness does not establish native occurrence production readiness, calibrated accuracy or full-text availability.
- Only the returned abstract and metadata were read live. No original article body, tables or figures were inspected. Valency JSON is not admitted by the pinned Europe PMC/JATS proof adapter.
- Configured Zotero database path is absent on this host. Retained failed publisher/Tavily/CiteSeerX/Academia routes are historical failures, not fresh worker attempts; no request sweep or authentication workaround was made.
- The original census command remains FAILED exit1 despite full JSON; attribution under review. PR233 qualification remains held pending two repairs.
- W5/W6, issue220, scientific package/exposure review, source lineage, correction verification and resource gates remain open.
- Full-suite outcomes and save/check/readback receipts are recorded separately after this authored observation; this record does not assert the full repository suite passed.
- Initial setup and GitHub read failures caused by sandbox DNS are preserved, followed by successful narrowly scoped network-enabled attempts. No credentials/auth files were read or copied.

## Complete Structured Record

The sibling review.yaml is authoritative.

```yaml
schema_version: 1.0.0
review_id: 20261126T031443Z-excluded-preparation-canary
kind: repository
repository: CultureBotAI/EdgeMech
title: 'EXCLUDED PREPARATION CANARY: native runtime and profile engineering check'
started_at: '2026-11-26T03:10:08Z'
finished_at: '2026-11-26T03:14:43Z'
reviewer:
  identity: native worker 01a1fd21-cd97-7601-8f2c-12268643a483
  kind: agent
  model: gpt-6-astra / ultra
  independence: self_review
  independence_basis: Actual worker checks its own preparation runtime; coordinator
    inspection remains separate and pending. No fresh scientific reviewer independence
    is claimed.
skill: lbnl-literature-and-db-access; lbnl-mech-record-review; named native EdgeMech
  preparation authorization
completion: completed
verdict: pass_with_limitations
native_verdict: EXCLUDED_PREPARATION_CANARY
scientific_review: false
summary: Bounded engineering review of two maintained runtime/profile files. The actual
  worker installed the frozen environment, verified all 16 CLAW contracts, inspected
  the canonical source inputs, and exercised one Valency metadata/abstract retrieval
  with private hash/offset replay. This record exercises shared canonical persistence;
  it makes no occurrence assessment, scientific claim rating, calibration assertion,
  A/B attempt or production-readiness claim. Scientific coverage is exactly 0.
source:
  git_revision: 945c421c648fe09858eabf1f2a4447ab27f9eae3
  state: working_tree
  inputs:
  - path: .temp/restart-preparation-01/commands/contracts-01/stdout
    sha256: a80e6516af4e7e300d6fc9083cb590092f2773bb9498f29a0f20077323af7c13
    role: context
  - path: .temp/restart-preparation-01/commands/issue220-read-02-network/stdout
    sha256: 3977c3621953cc85eacf3c38675c76d96b764d6fa3f06ca36ad96e3fbeaa0091
    role: context
  - path: .temp/restart-preparation-01/library/readback-01.json
    sha256: beeb8b6de2e444987ff07271381f387d8bbc5c387c3c3323215c0ead265c4c06
    role: context
  - path: docs/record-review-profile.md
    sha256: c472d9a4910f40028eff2e0912e9b4ea8dadcc0b1173cefdb6f933db40345c34
    role: target
  - path: docs/record-reviews.md
    sha256: 386a517e75c45b3229217ceed481a7028cdf29de8f927ecb9f06de7b0746a69e
    role: context
  - path: docs/validation/fresh05-access-20261119.md
    sha256: 3ba4972e3d8bbe0b3d97906ddcc4502cd480a8896d3cfb88f9869231d7bd6190
    role: context
  - path: pyproject.toml
    sha256: 54b8a153dca2b941ad1add1abf7cb7408324eba3457e519aa8e1bd87c70c63cb
    role: target
  - path: schema/record_review.yaml
    sha256: 6fd8191b6c039b822b23245a0ab312697df9c2ff1c6c27989ce7b1f62d00e6d3
    role: context
  - path: scripts/record_review.py
    sha256: 292ab82fecd0b01ef2760d0b251f30ae27263aa0e65a789dfd25e4530bed0da0
    role: context
  - path: src/edgemech/contract-pins.json
    sha256: e15d37c98777e6eeac5c2d24389d22f26fc3b601ba1b1873855f19d93e77bcbd
    role: context
  - path: uv.lock
    sha256: ffdec65db5f8ff7e6b32fd751f655eea1881d0305553c5bb154e3195a70f1033
    role: context
scope:
  description: Exactly two maintained engineering files for one excluded preparation
    canary; population_size=2 counts files only. No graph occurrences are targets.
  selection: Coordinator-authorized Unit 3 runtime/profile check in the existing native
    preparation worker.
  coverage: full
  population_size: 2
  reviewed_target_ids:
  - runtime
  - profile
  exclusions:
  - target: all scientific occurrences and A/B queues
    reason: Occurrence=null; A/B counts and cutoff unfrozen/null; no attempt or scientific
      coverage.
  - target: Unit 1 launcher review, census and source restoration
    reason: Explicitly excluded by current dispatch; retained original receipts preserved.
targets:
- target_id: runtime
  path: pyproject.toml
  label: Pinned native preparation runtime
  kind: maintained
  owner_paths:
  - repository: CultureBotAI/EdgeMech
    path: pyproject.toml
    role: Owns the exact CLAW dependency and native runtime requirements
- target_id: profile
  path: docs/record-review-profile.md
  label: Native profile scope and evidence admission limits
  kind: maintained
  owner_paths:
  - repository: CultureBotAI/EdgeMech
    path: docs/record-review-profile.md
    role: Owns the documented native acceptance and scientific proof limits
checks:
- check_id: contracts
  name: Pinned installed CLAW byte contracts
  status: passed
  required: true
  summary: All 16 pinned files verified at CLAW 4fad8df5b2367da68faca6379ce32eb9b8f4ba9b.
  target_ids:
  - runtime
  command: .temp/restart-preparation-01/venv/bin/python -m edgemech check-contracts
  exit_code: 0
  expected_exit_code: 0
  evidence_ids:
  - contracts-output
- check_id: inspect
  name: Canonical source and target inspection
  status: passed
  required: true
  summary: Maintained canonical inspect returned repository identity, actual Git base,
    exact input hashes and two engineering targets.
  target_ids:
  - runtime
  - profile
  command: .temp/restart-preparation-01/venv/bin/python scripts/record_review.py inspect
    --targets .temp/restart-preparation-01/targets.yaml (complete argv in commands/canonical-inspect-02/receipt.json)
  exit_code: 0
  expected_exit_code: 0
  evidence_ids:
  - inspect-output
- check_id: abstract-replay
  name: Actual-worker library access and literal replay
  status: passed
  required: false
  summary: One Valency request returned matching metadata and abstract; saved 1209-byte
    abstract and four-word snippet replayed at UTF-8 offsets [197,225). No body/table/figure
    inspected.
  target_ids:
  - profile
  command: .temp/restart-preparation-01/venv/bin/python scripts/adhoc/preparation_readback_20261126.py
    library --output .temp/restart-preparation-01/library/readback-01.json
  exit_code: 0
  expected_exit_code: 0
  evidence_ids:
  - library-access
- check_id: zotero
  name: Configured local Zotero route
  status: failed
  required: false
  summary: 'Read-only local query failed: sqlite3.OperationalError: unable to open
    database file. The configured /Users/marcin/Zotero/zotero.sqlite path is absent
    on this host. No global library absence inferred.'
  target_ids:
  - profile
  command: python3 scripts/adhoc/fresh05_fulltext_20261119.py local --unit preparation20261126local01
  exit_code: 1
  expected_exit_code: 0
  evidence_ids:
  - local-search
evidence:
- evidence_id: contracts-output
  kind: validation
  reference: .temp/restart-preparation-01/commands/contracts-01/stdout
  locator: complete JSON; files=16, verified=true
  accessed_at: '2026-11-26T03:14:43Z'
  support: supports
  summary: Actual installed byte validation passed; source pin records exact saved
    output.
- evidence_id: inspect-output
  kind: validation
  reference: .temp/restart-preparation-01/commands/canonical-inspect-02/stdout
  locator: source and targets
  accessed_at: '2026-11-26T03:14:43Z'
  support: supports
  summary: Maintained canonical helper captures two engineering targets and exact
    current input bytes.
- evidence_id: profile-contract
  kind: record_content
  reference: docs/record-review-profile.md
  locator: Evidence replay and limits; Commands and acceptance
  accessed_at: '2026-11-26T03:14:43Z'
  support: supports
  summary: Profile distinguishes canonical persistence from six-axis scientific acceptance
    and admits only specific replay formats; current body extraction is not an admitted
    proof.
- evidence_id: library-access
  kind: validation
  reference: .temp/restart-preparation-01/library/readback-01.json
  locator: identity, abstract hash and exact literal offsets
  accessed_at: '2026-11-26T03:14:43Z'
  support: context_only
  snapshot_sha256: beeb8b6de2e444987ff07271381f387d8bbc5c387c3c3323215c0ead265c4c06
  summary: Matching DOI 10.1099/ijs.0.65010-0 / PMID17625207. Metadata and abstract
    only; no scientific ratings. Valency representation is not admitted as Europe
    PMC/JATS.
- evidence_id: local-search
  kind: search
  reference: .temp/restart-preparation-01/commands/local-provenance-01/stdout
  locator: 35 bounded retained provenance hits plus separate failed Zotero query receipt
  accessed_at: '2026-11-26T03:14:43Z'
  support: context_only
  summary: Retained fresh05 report and OA dispositions inspected before the single
    live request. Historical private body extraction was not located in the searched
    paths.
  search_scope: Ignored-inclusive local-provenance search of docs and artifacts with
    30 hits/root bound; rg --no-ignore --hidden filename searches in agent-work/EdgeMech,
    Documents, CloudStorage and canonical EdgeMech .temp; direct configured Zotero
    path check. No exhaustive PDF/archive content search.
- evidence_id: issue220
  kind: record_content
  reference: https://github.com/CultureBotAI/EdgeMech/issues/220
  locator: Live body retained in commands/issue220-read-02-network/stdout
  accessed_at: '2026-11-26T03:14:43Z'
  support: context_only
  summary: Issue remains OPEN. New scientific package, fresh runtime canaries, exposure
    review and original-identity/lineage dependencies remain required.
assessments:
- assessment_id: runtime-engineering
  area: schema
  topic: Pinned engineering runtime available in actual worker
  outcome: supported
  summary: The frozen project environment completed installation and the maintained
    checker verified all 16 canonical contract bytes. This verifies the shared runtime
    contract used by the engineering canary.
  target_ids:
  - runtime
  evidence_ids:
  - contracts-output
  - inspect-output
- assessment_id: profile-boundary
  area: scope
  topic: Engineering persistence and scientific acceptance remain distinct
  outcome: supported
  summary: The inspected profile explicitly preserves exact occurrence, evidence replay
    and six-axis gates. This engineering record targets no occurrence and cannot qualify
    PR233 inventory candidates, alter A/B membership or claim coverage.
  target_ids:
  - profile
  evidence_ids:
  - profile-contract
  - inspect-output
  dimensions:
  - name: literature_channel
    value: valency metadata/abstract access only
    definition: Observed access extent, not scientific evidence admission or full-text
      readiness.
    evidence_ids:
    - library-access
findings: []
actions: []
limitations:
- Scientific review coverage is exactly 0; occurrence=null; no A/B attempts. Full
  A/B counts and baseline cutoff remain null.
- This is self-reviewed engineering preparation. Coordinator independent artifact
  inspection and helper publication review remain pending.
- Shared canonical save/check readiness does not establish native occurrence production
  readiness, calibrated accuracy or full-text availability.
- Only the returned abstract and metadata were read live. No original article body,
  tables or figures were inspected. Valency JSON is not admitted by the pinned Europe
  PMC/JATS proof adapter.
- Configured Zotero database path is absent on this host. Retained failed publisher/Tavily/CiteSeerX/Academia
  routes are historical failures, not fresh worker attempts; no request sweep or authentication
  workaround was made.
- The original census command remains FAILED exit1 despite full JSON; attribution
  under review. PR233 qualification remains held pending two repairs.
- W5/W6, issue220, scientific package/exposure review, source lineage, correction
  verification and resource gates remain open.
- Full-suite outcomes and save/check/readback receipts are recorded separately after
  this authored observation; this record does not assert the full repository suite
  passed.
- Initial setup and GitHub read failures caused by sandbox DNS are preserved, followed
  by successful narrowly scoped network-enabled attempts. No credentials/auth files
  were read or copied.
tags:
- excluded-preparation-canary
- engineering-only
- issue228
- zero-scientific-coverage
```
