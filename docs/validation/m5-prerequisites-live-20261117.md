# M5 prerequisite verification — 2026-11-17

This record covers engineering checks for [PR #211](https://github.com/CultureBotAI/EdgeMech/pull/211).
The repaired executable runtime is `3057bb2bae6c38ba8b588659da023a42a3bfe6b9`,
stacked on round03 delivery `d0ed406`. The first attempted runtime `2f99a16`
and its live failure remain preserved. No new scientific calibration has started.
The failed round03 result, original packages, seals, reviews and clones remain
unchanged. The new checks do not review the retained 90 or expand to 9,900.

## Code and independent review

[Exact repaired-runtime CI](https://github.com/CultureBotAI/EdgeMech/actions/runs/44235602842)
passed all **1,352 tests**, all 16 pinned CLAW contract payloads, full Ruff scope,
and source/wheel builds. The shared dependency remains the reviewed, unmerged
CLAW candidate `4fad8df5b2367da68faca6379ce32eb9b8f4ba9b`.
The initial candidate separately passed 1,345 local/CI tests; the real canary
then found #212. Its repair passed 22 focused tests before the full CI run.

Separate read-only reviews covered the clone/environment setup, package staging,
invocation/launcher integration and actual fresh-32 definition bytes. Findings
#207–#210 were filed before remediation. Re-review and a final complete-PR pass
found no additional material issue. The [review record](prerequisite-adversarial-review-20261117.md)
distinguishes fixes from the intentionally unsupported adjudication phase.

## Actual M5 environments

Fresh clone roots are beneath
`/Users/marcin/agent-work/EdgeMech/m5-prerequisite-reviewers-20261117`.
Both use the same exact runtime and canonical GitHub origin. Their artifacts
were checked on disk, and production readback was repeated using each clone's
own interpreter after its worker finished.

| Binding | reviewer-a-retry-01 | reviewer-b |
| --- | --- | --- |
| Setup | Passed six real provisioning steps | Passed six real provisioning steps |
| Interpreter | Clone-local `.venv`, Python 3.14.7 | Separate clone-local `.venv`, Python 3.14.7 |
| Provisioning receipt SHA256 | `043c88b6406795a9a7b1b925cb2df6d5fd56f77d65dcff10b74d18267a790c33` | `0637f9dfbd1ef6ee651ac83fd7d1a1731aafb2abca763bb035af9a4e047b5ef2` |
| New engineering manifest SHA256 | `336136476ea5fe68f6f3bde715031360bf59840ab992f9600d6501e4c27ac6ed` | `8e1c5ac5bfd08ebcaaa5072ed4275c5a03d1c4ccbeb14f4835beeb25504c6afa` |
| Verified input bindings / original packets | 380 / 10 | 380 / 10 |
| Real bootstrap checker / required modes | Passed / 0700 directory, four 0600 files | Passed / same required modes |
| Real native worker and production save/readback | Passed, exit 0 | Passed, exit 0 |
| Worker completion, UTC | `2026-11-18T04:17:57Z` | `2026-11-18T04:22:20Z` |
| Production receipt SHA256 | `58025aa5fc9ea8e47a84587c61579eee551efc1d5a7741cb946ce4862e325873` | `3b47ad8114f75ae792cf66438a6167d12053a22bfe9c79f54f36038aba59077c` |
| Canonical YAML SHA256 | `3270bdfbcd3c9a273ab29d39a6a1e5372304c04711116d5dbdc5cb53fc96666f` | `40fc541bda56e960ce154c2bb96bcbd8db90f4b432e2ee9240470e3ecb8f7496` |
| Canonical Markdown SHA256 | `fc59826ed03f5a13310f7d75b60e05f171ad0de3e947e0fb4cd93e2b0be80597` | `3905236e4209616a2f3020e0264e2f744d8078a3179b373a3a3d1f7a4ae86b61` |

Reviewer-a-retry-01's preparation receipt is
`65c2e9e172716c3d71a37eb7d6c0a630387fc0353823d7c563f68012142e26be`.
Reviewer-b's preparation receipt is
`a68754a81fd868a537b14d18b35137f57f6b2119b6264ddd84dd328a34d1cd3d`.
These preparation receipts record validated conservative drafts; the distinct
production receipts above prove the subsequent saves. The canonical review IDs
are `20261118T041135Z-prerequisite-a-retry01-fresh47` and
`20261118T041822Z-prerequisite-b-fresh47`, each beneath its own clone's
`reviews/structured/`. Actual readback returns one verified context witness,
zero quotations, all six unresolved categories, zero graph admissions and
`native_capability_enabled: false` for each pair.
The actual scientific-invocation CLI rejected the first engineering manifest before
writing any invocation, with the expected engineering-purpose error. The
separate same-clone production launch plan passed before real execution.

The first live canary in `reviewer-a` at runtime `2f99a16` failed before production
save under #212. Its manifest `e3536cb66bb01badd2360228e7c99ae59034c4ec0c674c21a59cda5d19980964`
verified 378 declared inputs. Its package had
complete declared bindings but omitted the bootstrap receipt outside that
manifest; the copied seed files also had mode 0400 where the maintained bootstrap
checker requires 0600. The child correctly reported failure, and the parent
rejected it despite child exit code 0. The failure result SHA256 is
`8364a86fb72b75e23a3a2b6c95b0733f0fbcd42ffba1649d549b763b15a4b4c9`.
It finished at `2026-11-18T04:07:36Z`; the failed clone and all logs remain intact.
Direct path checks found neither a canonical review directory nor a passing
canary receipt, and tracked runtime files stayed clean. The repaired first
canary passed at `04:17:57.089357Z`, before reviewer-b provisioning began at
`04:18:53.405253Z`. No failed output or receipt was overwritten.

The maintained provisioner and package/worker CLIs were used throughout. Exactly
one repaired clone was checked end to end before the second was provisioned. The native worker
uses configured defaults without a model override or a new credential copy.
The parent executes the production save/check and compares authored content and
on-disk YAML/Markdown hashes; worker prose is not the acceptance criterion.
Separate read-only audits of both actual environments confirmed the runtime,
380 bindings, installed contracts, modes, canonical pairs and exclusion from
scientific scoring. Both workers exited successfully; this task launched no
scientific worker or expansion job.

## Scientific boundary

The new package freezes complete **available byte bindings** and preserves
unresolved scientific dependencies explicitly. The [neutral fidelity procedure](../plans/source-fidelity-decision-procedure-20261117.md)
distinguishes direct source-to-assertion comparison from cases needing a trace
to establish field selection, identity or meaning. The coordinator-only
[ten-case witness map](../plans/m5-source-fidelity-witness-map-20261117.md) records
what remains missing.

The new fresh-32 view preserves 778 substantive bytes and removes only 27 bytes
of review-status wording. Definitions, scope limits, provenance and the unknown
generating-version caveat remain. This repairs future evidence visibility; it
does not turn inherited text into independent ontology authority or repair the
completed round's exposure.

The operational fixture remains non-scientific and unresolved on all six axes,
outside scientific matrices and graph-admission denominators. A full future
round still needs missing original witnesses and a reviewed typed adjudication
contract for initial matrices, seals and comparison (#209). The concrete next
source recovery is the bounded MetaTraits mapping/polarity path with exact
loader/template/source pins. No new LBNL/CBORG literature query or primary
full-paper inspection occurred in these prerequisite checks.

Every production receipt applies only to its recorded clone, package and
runtime. A later delivery/documentation commit does not retroactively authorize
that commit or a different scientific package.
