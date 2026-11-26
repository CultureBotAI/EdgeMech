# Bounded reconciliation of the retained census terminal evidence

Status: proposed for independent review; no new census verification is authorized
by this plan. It does not restore source files, contact a source host, classify
scientific occurrences or freeze A/B.

The original maintained full-census command has a retained terminal **FAILED,
exit 1**. Its complete result JSON equals the pinned input manifest. The resource
log contains `time: sysctl kern.clockrate: Operation not permitted`. Attribution
to `/usr/bin/time -l` is supported by these observations but the child process's
exit status was not separately captured and remains null.

Preserved identities:

| Evidence | SHA-256 |
| --- | --- |
| Original terminal event line | f302bff651aef901a7c9bf1b531117af3081ce70f318ec85818048c05f43fb6b |
| Complete result JSON | 03193a3abb8a1403bc6791e20ba224c17db337c859b4b2ca599358c4e879817e |
| Stderr and resource log | fca4de1bec8cb614b69a0c4cde121bbee5f6d1edd0f5a6c6f115f2dde1828c0c |
| Census manifest | a2b8353349816fd067ab3a7112fd1c2f5ee9c02971591ea52f31e9b981cbdd2e |
| Maintained CLI source | 35944cd3a5430f879e73f9d749fa752216cc2a42cf36e02d41459776367066db |
| Maintained census source | 2b90886fb21d1f42d3d718d936e1a09e37c935b1b23d5ff6cf4b266abfa73793 |

The inspected source matches the reviewed restoration head
`e3d63b0984382b5df4f3f1ada23d66db99e1f54d`. In that source, `verify_census` returns
the manifest only after source/native-export replay, all partition occurrence and
classification checks, exact source-prefix hash reconciliation and DuckDB counter
reconciliation. The CLI prints the returned object, then returns zero. That
supports completion of the verifier's checks at the original run, but cannot
establish the unobserved child termination status or current immutability of every
large input after that run.

Proposed units, each bounded to 90 seconds and small retained metadata:

1. Read the exact original terminal event and pin its raw bytes, result and stderr.
   Strictly parse and compare the complete result to the pinned census manifest;
   confirm contract, complete-export flag, row sums and zero scientific counts.
   Read back the two maintained source files against their reviewed Git blobs.
   Preserve failures and discrepancies without altering any original receipt.
2. In the same normal sandbox policy, run `/usr/bin/time -l /usr/bin/true` once
   against synthetic execution only, retaining stdout, stderr and observed outer
   status. A separate direct `/usr/bin/true` control records its own observed
   exit. Do not infer the original child's exit from either probe or modify the
   sandbox to make the resource wrapper succeed. If the current environment no
   longer reproduces the warning, retain that difference without retrying.
3. Independently review the retained terminal, complete artifact and source-path
   evidence. Record a typed disposition distinguishing (a) original failed outer
   command, (b) complete verifier-return artifact, (c) unobserved child exit and
   (d) whether that evidence is accepted for the original full replay gate. A
   discrepancy or insufficient provenance keeps the gate unresolved. Any further
   verification would require a separately reviewed plan, not automatic retry.

Any new producer used for these units must be tracked in `scripts/adhoc/` before
use, have issue #228 provenance, offline failure coverage and independent review.
It must write exclusively to a new private evidence directory. Actual invocation
bindings and the original operational terminal record stay private; public output
contains only bounded findings, counts and hashes.

Even an accepted replay disposition does not qualify historical assessments or
freeze the target population. Exact baseline membership, source/version binding,
cutoff, exhaustive archive reconciliation, full A/B parity, W5/W6, issue #220,
runtime/evidence, correction and resource gates remain separate requirements.
