# Native restart preparation launch

One dedicated native preparation worker was launched from accepted candidate
`945c421c648fe09858eabf1f2a4447ab27f9eae3` through the installed work-account
wrapper and supported standalone mode. It stopped at a new checkout trust
prompt. No task input or prompt answer was sent. Scientific review coverage is
zero; A/B population counts remain unresolved. Worker library retrieval and
canonical save/readback have not been established.

The exact original executed helper and actual receipt remain private and
unchanged. Their [digest mapping](../../scripts/adhoc/provenance/restart-20261120/launch-summary.json)
preserves issue [#228](https://github.com/CultureBotAI/EdgeMech/issues/228)
provenance without publishing operational logs or private bindings. The original
coordinator bootstrap provenance remains a separate parent-owned repair.

The maintained [launcher](../../scripts/adhoc/launch_restart_preparation_20261120.py)
is a successor, not the producer of the historical launch receipt. It now uses
the CLAW-required lease context manager, revalidates canonical ownership under
the short lease, and refuses native execution if a repository/global lock remains.
Private tmux executable/socket/session bindings are explicit invocation inputs.
It inventories the existing server, refuses existing sessions or retained attempts,
sets pane retention before startup, and contains no prompt-input operation.
No native mutation was rerun to produce evidence for this successor.

Independent static review identified `EDGE-RESTART-PRIVATE-LOG-001`: proposed
tracked provenance exposed operational bindings. The actual receipt and executed
helper were kept privately intact; only sanitized hashes and aggregate state are
tracked. The successor also removes hardcoded private tmux bindings. Separate
read-only review of the corrected final bytes is required before publication.

Five focused offline tests cover launch after context release, retained-attempt
refusal, clone failure and release, lock refusal, residual-lock refusal, and
exclusive receipt preservation. They use synthetic execution and do not launch
agents. Final complete-suite results are recorded with the reviewed candidate.

The parent owns census recovery. A transfer receipt is staging evidence; complete
census and producer-pin verification plus exhaustive historical assessment
reconciliation are still required before A/B freeze. The W5/W6, issue #220,
candidate-correction, source-family, evidence and resource gates remain unchanged.
