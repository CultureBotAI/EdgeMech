# Reviewer clone setup and retained save/readback audit — 2026-11-17

Issue [#206](https://github.com/CultureBotAI/EdgeMech/issues/206) makes the
documented fresh-clone setup reproducible. The retained round03 environments
already corrected round02's local-origin defect. This change supplies a maintained
setup path for future reviewers; it does not change old clones or authorize a new
scientific round.

## Read-only audit of retained round03

Both actual reviewer clones beneath
`/Users/marcin/agent-work/EdgeMech/m5-round03-reviewers-20261116` were inspected on M5:

| Binding | reviewer-a | reviewer-b |
| --- | --- | --- |
| Exact HEAD | `fa67837be82cf0244678e564071beb9a2e2203b3` | Same |
| Origin | `https://github.com/CultureBotAI/EdgeMech.git` | Same |
| Python prefix | `reviewer-a/.venv` | `reviewer-b/.venv` |
| Venv base | M5 Miniforge Python 3.14.7, system packages excluded | Same |
| Installed CLAW commit | `4fad8df5b2367da68faca6379ce32eb9b8f4ba9b` | Same |
| Recorded reviewer completion, UTC | `2026-11-17T03:45:51.949027` | `2026-11-17T03:47:14.400608` |

The retained production receipt hashes match their recorded bindings:

- A: `4d0be8fc15da46edbd8b6dc2443afc772e7b9fefcdff7593f0707c9b7639e80e`.
- B: `7b4ee1ac97b88f73769c04139c25bc5a700f46ea53c54ef2572102db3859d830`.

Both canonical operational pairs at
`reviews/structured/20261117T030400Z-round03-operational-fresh47/` are nonempty
and match their receipt hashes: `review.yaml` is
`c099b3ec493ec5a2e912ec6363a4a0f19b89be2e6fb4266b5c257b1ed7b0f7a7`, and
`review.md` is `4c60af4b45be3da1b697ac28ce5931a58a2760fa09bda28132715191d7b7b195`.
Each clone's own `.venv/bin/python -B -m edgemech.occurrence_review check` was
replayed against that pair, its fresh47 packet, and the original operational
proofs; both passed. The conservative fixture still admits zero graph edges.
Both clones' tracked working files remained clean. The checks read retained
outputs and used `-B`; no old reviews or receipts were rewritten.

An ignored-inclusive (`rg -uu`) filename and content search across `scripts/`,
`src/`, `tests/`, and `docs/` found the launcher identity/save guards and manual
setup instructions. The Python/shell implementation search in `scripts/` and
`src/` found no existing clone/venv provisioning helper. This bounded search
does not assert absence elsewhere on either machine.

## Fresh clone provisioning

Run one setup end to end and inspect its receipt before provisioning additional
clones. Use the exact reviewed commit containing this helper. The parent
directory must exist; the destination must not. The helper rejects local and
alternate origins by fixing the canonical HTTPS URL, checks out the full commit
detached, creates an isolated venv on the executing machine, installs with
`uv sync --locked --extra dev`, and runs dependency, import-location, exact CLAW
commit, and installed-contract checks inside that venv. The interpreter path is
explicit; it must exist locally. `uv` may be supplied explicitly as below.

```bash
python3 scripts/adhoc/provision_reviewer_clone_20261117.py \
  --revision FULL_REVIEWED_40_CHARACTER_COMMIT \
  --destination /Users/marcin/agent-work/EdgeMech/NEW_REVIEWER_CLONE \
  --python /opt/homebrew/Caskroom/miniforge/base/bin/python3 \
  --uv /Users/marcin/.local/bin/uv \
  --plan
```

Inspect the read-only plan, then use the same arguments with `--run`. Inspect
`NEW_REVIEWER_CLONE/.temp/reviewer-provisioning/receipt.json` on disk. It records
the clone, exact revision, helper/tool hashes, host, Python/venv, lockfile and
installed distribution identities. Provisioning does not copy credentials;
dependency child processes receive no inherited CBORG key. Existing machine
credentials used later by the worker launcher remain a separate concern.

A failure retains its partial clone and failure receipt when a clone directory
was reserved. Retry at a fresh destination; the helper neither cleans up nor
overwrites attempts. A successful receipt has capability
`clone-and-dependency-setup-only`, `authorizes_reviewer_launch: false`, and
`scientific_gate_passed: false`.

Freeze and verify the complete new evidence package next. Then use the existing
durable launcher to run a real production save/readback canary in **each** actual
reviewer clone before its reviewer session. The provisioning receipt cannot
substitute for that launcher receipt. The reviewed invocation contract and
scientific calibration thresholds still apply. Retained round03 readiness does
not establish fresh readiness after a runtime or package change.

## Verification boundary

Focused tests exercise real Git checkout identity, exact revision rejection,
read-only planning, destination preservation, failed installs, credential and
environment isolation, venv boundaries, and non-authorizing receipt readback.
They stub dependency installation; root's real M5 one-clone provisioning and
production save/readback canary provide the network and actual runtime evidence.
This document records only the retained round03 readback until that new run is
separately recorded.
