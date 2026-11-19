# Content-review implementation adversarial review

PR [#214](https://github.com/CultureBotAI/EdgeMech/pull/214), 2026-11-19.
These were separate read-only passes; every material finding was filed before
repair. No reviewer edited files during its review pass.

| Finding | Evidence and disposition |
| --- | --- |
| [#213](https://github.com/CultureBotAI/EdgeMech/issues/213): stale execution plan and overstated gold set | The November9 plan omitted the implemented six-axis profile, failed rounds and binding thresholds. The new current section preserves the historical design, distinguishes purposive challenges from a gold standard, and registers dependency-ordered M5 stages. Independent re-review passed. |
| [#215](https://github.com/CultureBotAI/EdgeMech/issues/215): unbound native executable | The npm JavaScript entrypoint could remain unchanged while its native dependency changed. The launcher now requires the actual regular executable Mach-O/ELF binary, puts its directory first on PATH and checks wrapper resolution before execution. Node/symlink entrypoints and changed binaries are rejected. Independent re-review passed before the live canary. |
| [#216](https://github.com/CultureBotAI/EdgeMech/issues/216): disappearing startup failure | Startup replay ran outside durable failure handling. It now retains stage/type in a private completion record after verifying the owned destination. A regression changes the prompt after staging and confirms failure persists without provider execution. Independent re-review passed before the live canary. |
| [#217](https://github.com/CultureBotAI/EdgeMech/issues/217): incomplete initial readiness lineage | The first #209 implementation accepted an initial envelope with only two runtime fields and a nonexistent production receipt. The repair requires complete maintained runtime fields, retained readiness metadata/validators/canonical pair and original clone/commit lineage. The actual adjudicator must also use the frozen original commit, checked before preparation writes and at launch entry/exit. Independent re-review passed;46 final focused tests passed. No live scientific phase has run with this implementation. |
| [#218](https://github.com/CultureBotAI/EdgeMech/issues/218): access-report provenance overstatement | Current Valency calls omitted abstracts and supplied metadata only. The report now says so and distinguishes earlier abstract evidence. Its Zotero base-file hash is explicitly a live fingerprint, not a retained transactional database/WAL snapshot. Observed access results and their limits remain unchanged. |

The final launcher candidate passed11 focused tests, Ruff, shell syntax and
whitespace checks. An intermediate added test failed because two existing
assertions were accidentally placed in the new startup-failure test; the test
layout was corrected before the final11-test pass. This was a test-edit defect,
not a passed live canary. The final production path still requires its actual M5
run and independent task-artifact inspection.

Plan review and launcher checks do not certify source semantics, scientific
readiness, provider/library access, independent expert agreement or expansion.
Final implementation review and complete-suite results are recorded separately
in the [execution record](content-review-execution-20261119.md).
