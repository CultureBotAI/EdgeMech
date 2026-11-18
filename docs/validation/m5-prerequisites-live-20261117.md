# M5 prerequisite verification — 2026-11-17

This record covers engineering checks for [PR #211](https://github.com/CultureBotAI/EdgeMech/pull/211).
The frozen executable runtime is `2f99a16e7752d2dbe31471781b31ceb5aa90c8a0`,
stacked on round03 delivery `d0ed406`. No new scientific calibration has started.
The failed round03 result, original packages, seals, reviews and clones remain
unchanged. The new checks do not review the retained 90 or expand to 9,900.

## Code and independent review

[Exact-runtime CI](https://github.com/CultureBotAI/EdgeMech/actions/runs/44234472702)
passed all **1,345 tests**, all 16 pinned CLAW contract payloads, full Ruff scope,
and source/wheel builds. The shared dependency remains the reviewed, unmerged
CLAW candidate `4fad8df5b2367da68faca6379ce32eb9b8f4ba9b`.

Separate read-only reviews covered the clone/environment setup, package staging,
invocation/launcher integration and actual fresh-32 definition bytes. Findings
#207–#210 were filed before remediation. Re-review and a final complete-PR pass
found no additional material issue. The [review record](prerequisite-adversarial-review-20261117.md)
distinguishes fixes from the intentionally unsupported adjudication phase.

## Actual M5 environments

Fresh clone roots are beneath
`/Users/marcin/agent-work/EdgeMech/m5-prerequisite-reviewers-20261117`.
Both are intended to use the same exact runtime and canonical GitHub origin;
results below are recorded only after their artifacts are checked.

| Binding | reviewer-a | reviewer-b |
| --- | --- | --- |
| Setup | Passed six real provisioning steps | Pending |
| Interpreter | Clone-local `.venv`, Python 3.14.7 | Pending |
| Provisioning receipt SHA256 | `8c6a9bdbfc4e1aef0fe3af5eb1b96483a88a20ca7c2b62ed955f0594debec4ab` | Pending |
| New engineering manifest SHA256 | `e3536cb66bb01badd2360228e7c99ae59034c4ec0c674c21a59cda5d19980964` | Pending |
| Verified input bindings / original packets | 378 / 10 | Pending |
| Real native worker and production save/readback | Failed bootstrap; no save attempted | Not started |

Reviewer-a's preparation receipt is
`0a3092569231c22b05fd2534a153d702b812a47c0ef07513bfd642bd4680b859`.
It records a validated conservative draft, with no canonical save yet claimed.
The actual scientific-invocation CLI rejected this engineering manifest before
writing any invocation, with the expected engineering-purpose error. The
separate same-clone production launch plan passed before real execution.

The first live canary failed before production save under #212. Its package had
complete declared bindings but omitted the bootstrap receipt outside that
manifest; the copied seed files also had mode 0400 where the maintained bootstrap
checker requires 0600. The child correctly reported failure, and the parent
rejected it despite child exit code 0. The failure result SHA256 is
`8364a86fb72b75e23a3a2b6c95b0733f0fbcd42ffba1649d549b763b15a4b4c9`.
It finished at `2026-11-18T04:07:36Z`; the failed clone and all logs remain intact.
Direct path checks found neither a canonical review directory nor a passing
canary receipt, and tracked runtime files stayed clean. A repaired runtime must
pass a new clone canary before the second environment is provisioned.

The maintained provisioner and package/worker CLIs were used throughout. Exactly
one clone is checked end to end before another is provisioned. The native worker
uses configured defaults without a model override or a new credential copy.
The parent executes the production save/check and compares authored content and
on-disk YAML/Markdown hashes; worker prose is not the acceptance criterion.

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
