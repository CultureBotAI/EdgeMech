Advanced in [CLAW #987](https://github.com/CultureBotAI/culturebotai-claw/pull/987),
head `326bdff8c285301d7b626fb7a001f41ce15700fa`, dependent on shared contracts #962.
The proposed distribution builds 17 exact canonical files from an immutable
CLAW commit. Its base identity/artifact/native validators require only JSON
Schema; the optional review and ledger extra retains LinkML 1.10.

A fresh six-package native-only environment validated the real three-row MIM
canary, preserving one supported and two withheld assertions with zero scientific
approvals. A separate installed review environment verified all 13 Python module
origins and passed 148 canonical native/artifact/contract/ledger tests. Independent
adversarial review filed and repaired CLAW #985; support-shadowing regressions
also fail under an isolated mutation restoring the old verification gap.

The new isolated-package CI job is green. The broader CLAW suite is still running
at this update. MIM #1147 itself has all 17 CI checks green at
`8ec80235d41154e398238459d914c9fa3052a1d8`.

This issue remains open for reviewed dependency adoption and distribution policy.
No package-index release, MIM dependency change, native LinkML upgrade, or merge
has occurred. Evidence and retained receipts are in
`docs/guides/MINIMAL_CURATION_DISTRIBUTION.md` on CLAW #987.
