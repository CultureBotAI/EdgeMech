# M5 CLAW restart: supervisor acceptance and startup boundary

## Activation after explicit approval

At 2026-11-20 05:24 UTC (November19 Pacific), the supervisor applied the user's
explicit answer to the exact coordinator folder-trust prompt once and verified
the normal composer afterward. It preserved the authorization and one-time input
receipt; other prompts and merges remain unapproved.

At 05:26:45 UTC the dedicated native coordinator accepted the exact request and
recorded its active continuation goal. Its verified native thread is
`01a1f769-d3ff-79e0-b8a5-e41b01d2e1de`, running `gpt-6-astra` with `ultra`
reasoning in the isolated `945c421` checkout. The supervisor independently read
back its acceptance and checkpoint paths. The acceptance receipt SHA256 is
`2f20adbd0bdd894e53a4dd2d6c0f5a5aff2ea504a4de10cf6d2351c5ea2a8c5b`.
This establishes actual coordinator startup; it is not scientific completion.
The first preparation worker and library/canonical canary were not yet launched
at that checkpoint, and new review coverage remained zero.

At 05:29 UTC the coordinator prepared its first separate worker checkout at
the same reviewed head and launched its native process. `FIRST-WORKER.json`
records `AWAITING_EXPLICIT_TRUST_NO_INPUT_SENT`: its new folder-trust prompt
requires a separate decision, its task was not delivered and no thread/model
identity or library/canonical success was inferred. The parent presented that
specific question while independent data recovery continued. This preparation
worker remains excluded from scientific coverage.

The exact historical census was located on the primary Mac: its manifest matches
`a2b8353349816fd067ab3a7112fd1c2f5ee9c02971591ea52f31e9b981cbdd2e`.
The transfer dry run found 904 regular files totaling 8,044,208,003 bytes,
including 882 partitions and 10 native assertion streams. A single partition
was transferred through the intended rsync/SSH path to new private M5 staging;
its readback was 1,618,896 bytes with SHA256
`aaeccbf8a53ce3bd34348fadd99e7a6592239cd7ee21fe9c3ac1e2b4b8c2c98f`,
matching the manifest. Only then did the remaining transfer begin. This canary
proves that transport and persistence path for one file.

By 05:34:25 UTC the full staging copy had completed. A subsequent checksum-based
rsync dry run over all 904 files reported zero changed, created or deleted files;
the staged manifest SHA256 also matched. The separately pinned original source
snapshot was absent at its recorded M5 path. A bounded, ignored-inclusive search
found a different existing graph archive, so it was preserved. The correct
186,790,689-byte archive was recovered from the primary Mac with SHA256
`158e7131025c7941ae98d70af5ca14d6efb69857ed019f7f61fa9b44279b2345`.
Its four regular members were extracted into new private staging. The three TSVs
matched their source-manifest SHA256 and byte-size declarations. The fourth file,
`manifest.json`, matched its independently pinned hash
`f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2`;
its observed size was 4,903 bytes. The manifest is not a self-listed data member.
This provenance distinction addresses review finding #229.

The private `CENSUS-RECOVERY-COMPLETE.json` receipt has SHA256
`2410cf50cfbe062799698fe56550cd99748d58552404583c2f2f7db689c6fc68`
on both hosts. Its supporting logs are retained locally beneath
`.temp/content-review-20261119/` and on M5 under
`restart-20261120/parent-transfer-receipts/`. These checks establish recovered
input bytes. CLAW still owns controlled restoration of the historical source to
the exact census-pinned path, the maintained full census replay, and the
exhaustive baseline A/B freeze. No frozen manifest was rewritten to avoid a
missing source path, and no scientific coverage was added.

CLAW acknowledged parent ownership of census recovery and instructed the
coordinator to continue independent worker/library readiness. The maintained
bootstrap-helper provenance repair for #228 is in unmerged
[CLAW PR #1299](https://github.com/CultureBotAI/culturebotai-claw/pull/1299) at
`ff1c879b4c1489d613f03cbf31387f0a924d5bc3`, with original helper bytes preserved.
The supervisor reports independent review and 32 focused tests; hosted checks
were still running at the observed checkpoint, so full CI acceptance is not
claimed here. No canonical checkout, historical review,
scientific gate or generic fleet capability was changed.

## Preserved pre-approval checkpoint

Observed 2026-11-20 04:42 UTC. The following preserves the earlier operational
boundary and its exact receipt hashes; it is superseded by the activation above,
not a current unresolved trust request.

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
