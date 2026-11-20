# M5 CLAW restart: supervisor acceptance and startup boundary

Observed 2026-11-20 04:42 UTC (November19 Pacific). This is an operational
checkpoint, not a scientific review result.

M5 CLAW accepted the [restart assignment](../plans/m5-edge-review-restart-20261120.md),
verified its SHA256
`4af8b1cc2fe98032d5ff7f1d7ddb659e491310d3dfd0bcb7a370645c97048a4d`,
and registered `workspace/tasks/edgemech_restart_20261120.yaml` in its private
supervisor workspace. The new order is unreviewed occurrences first, then the
frozen previously assessed set. Scientific and evidence gates remain unchanged.

The supervisor prepared an isolated coordinator clone on
`campaign/lbnl-restart-20261120-coordinator` at
`945c421c648fe09858eabf1f2a4447ab27f9eae3`. Its executable code matches reviewed
PR #214 at `64a1c65`; the three intervening files are Markdown. Canonical M5 main
remains at `f841b1d`. No merge or canonical checkout update was performed.

The first native launcher failed because its daemon executable was unavailable;
that failure is retained. A second native session using supported `--no-daemon`
mode reached the folder-trust screen with normal permissions. No trust decision
was supplied. The exact prompt requires the user's explicit answer under the
installed orchestration skill; a specific question has been presented.

At this checkpoint the supervisor is accepted, but the new coordinator has no
accepted task or verified thread identity, no scientific worker has started,
and no library/canonical canary has run. Campaign review coverage is **zero**.
The full target and baseline A/B partition are not yet frozen. Generic CLAW
EdgeMech review hooks remain disabled; the assignment uses the native workflow.
Other active assignments and old review environments remain preserved.

Startup audit also found that CLAW's bootstrap helpers were saved under its
ignored `.temp/` instead of tracked `scripts/adhoc/`. Issue
[#228](https://github.com/CultureBotAI/EdgeMech/issues/228) remains open for the
owning coordinator to preserve and review those helper sources. Their original
bytes and startup receipts must remain intact; the pending trust helper must not
run without the explicit decision. This finding does not alter review coverage.

Private receipts are under `restart-20261120/` in the M5 EdgeMech agent-work
directory, with local snapshots under
`.temp/content-review-20261119/restart-receipts-20261120T0442Z/`:

| Receipt | SHA256 |
|---|---|
| `ACK.md` | `3100aa1ea7895eb28af6dae6de9594e95867d7c24384c079d87ab4581c83e131` |
| `progress.json` | `d823dfecbe947a917eaa7a8ad020d24816051fa363a8a9aa339d83f3c5614d74` |
| `STARTUP-BLOCKER.json` | `4807ce70a17c812bf3486d2626e4245a6a25f17a18fd5f73ddbf13ed607da6e6` |

PR #226's initial candidate `945c421` passed automated checks in
[run 44675683681](https://github.com/CultureBotAI/EdgeMech/actions/runs/44675683681).
Separate read-only review found and repaired #223/#224 before dispatch; re-review
passed. Passing engineering checks does not change the startup boundary or the
failed historical scientific calibrations.
