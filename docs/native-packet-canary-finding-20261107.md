# Exercise canonical packets with the real pinned native slice

The initial packet tests use synthetic native assertions while the real MIM
canary currently stops at native JSONL publication. Add a persisted transport
conformance run through `inherited_bundle` using the pinned three-row MIM slice.
Verify complete envelope preservation, native supported/withheld scope and
deferred/withheld canonical decisions after reloading the saved bundle.

The transport fixture must explicitly identify its occurrence domain as native
export rows, separate from KG-Microbe release occurrences. It must not fabricate
matches to unrelated KG rows or count fixture membership as eligible overlap.
The actual pinned-snapshot census remains the source of overlap accounting.
