Run exactly one operational canary on M5 for the authorized EdgeMech review
campaign. Do the work now; do not stop at a plan. This is not a scientific rating
and must not enter either independent calibration matrix.

Read AGENTS.md and docs/record-review-profile.md. User agreements apply: no
mentions, messages, email disclosure, mail helpers, force cleanup or new-PR
merge. Save any helper code in scripts/adhoc/ on the task branch, never inline
Python or /tmp. Prefer existing replay helpers. Preserve all historical bytes.

The launch worktree contains the current reviewed runtime and a locked .venv.
Canonical retained inputs are at
/Users/marcin/Documents/VIMSS/ontology/Mechs/EdgeMech/.temp/edge-calibration-20261115/fresh-47/.
The retained-100 archive is
/Users/marcin/agent-work/EdgeMech/edge-sample-review-20261112-data.
Run the existing prepare_calibration_20261115.py --plan, then exactly one
--prepare fresh-47 followed by --check fresh-47 in THIS fresh worktree. Its
.temp/edge-calibration-20261115 must be absent before preparation. This creates
new current-runtime receipts without touching the old canonical receipts.
Also run the current pinned contract check. Inspect the persisted packet,
receipt and exact occurrence identity, not merely return codes.

Check only whether CBORG_API_KEY is present, never its value. Through an existing
read-only CBORG Tavily tool, attempt one extraction of the primary LPSN page
for Stackebrandtia nassauensis (use the URL in the retained fresh-14 source
packet). Persist the tool/service result and source URL under the output
directory, clearly separating this connectivity probe from any scientific
judgment. If a service is unavailable, report its actual error; do not falsely
claim library use. A service failure does not justify using a secret in a URL
or bypassing the sandbox. The offline packet canary may pass with an explicit
service limitation if the three mandatory checks below pass.

The launcher supplies the output directory in its appended RUN CONTEXT. Write
canary-result.json there with this shape:
{"status":"passed","checks":[{"name":"runtime_contracts","passed":true},
{"name":"fresh47_packet_replay","passed":true},
{"name":"credential_available","passed":true}],
"artifacts":[{"path":"ABSOLUTE_NONEMPTY_FILE_INSIDE_OUTPUT_DIRECTORY",
"sha256":"EXACT_SHA256"}],"limitations":[]}

Copy the new packet and receipt as output-root/packet.json and
output-root/receipt.json and include their actual hashes in artifacts. Add a
short canary report recording actual commands,
exit codes, source/occurrence identity, seven-day-old receipts being historical,
and actual service result. No computed hash may be invented. The launcher
independently rereads these files. If any mandatory check fails, emit failed
status, preserve diagnostics, and do not launch other jobs. Do not change the
launcher or weaken its checks to get a pass. Do not commit private outputs.
This canary requires no new helper code: use existing CLI commands, file copies,
hash commands and directly authored result JSON. Keep tracked runtime files and
HEAD unchanged. If an implementation fix is necessary, report that failure and
leave a new runtime/re-canary to the parent.
