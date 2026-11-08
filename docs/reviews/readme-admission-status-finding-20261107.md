The final README paragraph still describes the fleet-admission policy as a
blocker. That is stale: CLAW PR #953 at
`85a69ee2164a3c9e70e0ffd8a9c33038ab84d716` implements CLAW #960 and has passed
all five checks and its final adversarial review. The historical DUF release
bytes remain unchanged.

This was found in a separate read-only pass over the user-facing README after
the milestone and PR-body reviews. Update the entry-point wording to the
separate fleet-admission dependency. Do not imply that admission is active or
that any PR has been merged; those still require explicit human approval.

The repair is documentation-only and belongs in EdgeMech PR #2. Its validation
is a read-back against the reviewed admission state and a whitespace check.
