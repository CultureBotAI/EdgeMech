# Define bounded reader, search and download responses

Read-only acceptance review for CultureBotAI/culturebotai-claw#766 found that
EdgeMech exposes bounded exact-ID storage lookup and immutable partition
manifests, but has no versioned search, pagination or download-response contract.
The milestone explicitly requires bounded browser/search payloads and
downloadable artifacts before a later viewer can reuse those interfaces.

The search included ignored files in the maintained `src`, `docs`, `conf`,
`tests`, `scripts` and README source trees. It did not treat a missing deployed
viewer as a defect: deploying a service or generating pages is outside this
milestone.

Add a local, versioned interface with a required manifest digest, bounded exact
occurrence-ID/prefix search, stable artifact/query-bound pagination, serialized
response and scan budgets, and descriptors for real immutable artifact files.
Download reads must be allowlisted by the pinned manifest, stream bounded chunks,
check declared bytes and hashes, and reject traversal, symlinks and changes.
Keep exact source identities and actual review state; search and successful
transport must never imply scientific approval or publication authority.

Conformance tests should exercise a real migrated ledger, repeated biological
edges with distinct occurrence IDs, pagination, negative cursors, response and
scan budgets, immutable file bindings, damaged artifacts and download limits.
No per-edge HTML files, host URLs, new scientific projection or shared release
publication policy are needed.
