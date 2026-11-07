Implements the EdgeMech storage scaffold and native overlap accounting for
CultureBotAI/culturebotai-claw#766 and #767, using reviewed shared contracts at
CLAW `1b5391d083ba85ac94e5279c3cba25ac4fde243c` (CLAW PR #953).

The SQLite migration preserves every authoritative value and historical bundle,
replays canonical decisions, verifies partition/logical hashes and publishes an
immutable manifest only after reconciliation. Native eligibility requires exact
inherited scope and complete payload/evidence bindings; matching endpoints alone
never grant approval. Canonical candidate packets remain deferred/withheld.

Validation so far: 54 focused storage/census/packet tests; installed contract pin
checks; real verified 1,000-row migration; three storage layout measurements;
bounded 1,000-row MIM join with complete source-member hash verification.
Full native-adapter inventory/census and final independent review are in progress.

Adversarial finding #1 (directory publication durability) is fixed and covered
by a syscall-order test. Final issue dispositions and reproducible validation
receipts will be added before requesting merge approval.

This PR is deliberately draft. It does not publish a production graph, deploy a
site, run a scientific review worker or claim new scientific approvals. Merging
remains an explicit maintainer decision.
