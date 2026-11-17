Run exactly one operational replay canary for this task's current committed
runtime. This worktree already contains the parent's freshly verified fresh-47
preparation receipt and the frozen ten-case evidence package. Preserve all of
them. Do not run --prepare or require an empty preparation directory: this is
the seeded replay path explicitly authorized by the user, not initial staging.

Read AGENTS.md and docs/record-review-profile.md. Run the existing
scripts/adhoc/prepare_calibration_20261115.py --plan and --check fresh-47,
plus PYTHONPATH=src .venv/bin/python -m edgemech check-contracts. Inspect the
actual persisted fresh-47 packet/receipt and its exact frozen occurrence ID.
Only test whether CBORG_API_KEY is present; never print or inspect its value.
No network retrieval, new evidence preparation, scientific ratings, other
case review, messages, Git changes or helper code is needed or authorized here.

Use the supplied invocation output root for all results. Copy the existing
.temp/edge-calibration-20261115/fresh-47/packet.json and receipt.json there
as packet.json and receipt.json, preserving their exact bytes. Save actual
commands/exit statuses and hashes in that output root. Existing CLI, cp and
shasum suffice; do not create a new execution helper or alter tracked files.
Use the maintained CLI and parent validators for identity/hash replay (#192).
Do not add supplemental inline Python, jq analysis filters or shell drivers.
Read the existing validation outputs directly; record any unmet requirement as
a limitation for a new reviewed runtime, rather than inventing analysis code.

Write canary-result.json with:
{"status":"passed","checks":[{"name":"runtime_contracts","passed":true},
{"name":"fresh47_packet_replay","passed":true},
{"name":"credential_available","passed":true}],
"artifacts":[{"path":"ABSOLUTE_NONEMPTY_FILE_INSIDE_OUTPUT_ROOT",
"sha256":"ACTUAL_FILE_SHA256"}],"limitations":[]}

Include the copied packet/receipt and actual command/check log in artifacts.
Use passed only when all three checks pass; otherwise record failed and preserve
the exact failure. Parent launcher independently verifies current runtime bindings,
exact copied bytes, contract validity and actual packet replay. A seeded receipt
is accepted only after current independent replay. Successful execution certifies
the operational path only, never scientific calibration. Finish without starting
other jobs or claiming any process continues after you end.
