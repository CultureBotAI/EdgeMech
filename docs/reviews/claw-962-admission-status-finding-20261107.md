# Refresh contracts PR admission-status metadata

Final read-only cross-PR review found a stale status statement in CLAW #962's
description at unchanged contract head
`6031604c3b24a1a47a0b15a1ec1d46db47d73e1e`:

> EdgeMech admission stays in draft #953 and depends on #960.

CLAW #953 is now ready for review at
`85a69ee2164a3c9e70e0ffd8a9c33038ab84d716`, with all five checks passing.
It implements the bounded post-cutoff admission tracked by #960. Both PRs
remain unmerged, and protected admission remains inactive until an explicitly
approved merge. The contracts-only #962 remains independent of admission.

Correct the active #962 description to distinguish implemented, reviewed
admission from approved activation. Retain the corrected body with the review
evidence. This is metadata only: contract bytes, immutable runtime pins,
canaries and validation results remain unchanged; no test rerun or deployment
is required.

Disposition: the active #962 body was corrected and read back successfully on
2026-11-07. Its source head remains
`6031604c3b24a1a47a0b15a1ec1d46db47d73e1e`; it remains ready and unmerged.
The exact corrected body is retained in
`docs/reviews/claw-962-body-admission-status-20261107.md` in EdgeMech #2's worktree.
Issue #990 remains open as the metadata review record pending final evidence
integration; the described text defect is fixed.
