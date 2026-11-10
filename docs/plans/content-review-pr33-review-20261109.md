# PR #33 adversarial review and triage

Review performed as a separate read-only pass over `ef0b94e`, then a read-only
follow-up over `9e70e3c`. No files or artifacts were changed during either pass.
The running preparation job was already active independently of the review.

| Finding | Record | Disposition |
|---|---|---|
| Forced DOI/quote fields and source-based verdicts confuse evidence availability with scientific support | [#31](https://github.com/CultureBotAI/EdgeMech/issues/31) | Corrected plan; preparation creates no scientific approvals. Source-specific adjudication remains subsequent work. |
| Approximate counts, wrong physical schema/names and unsupported worker/storage estimates | [#32](https://github.com/CultureBotAI/EdgeMech/issues/32) | Exact preparation and measured canaries implemented. No unmeasured remote-worker expansion. |
| Direct completion-manifest write could expose a partial marker after interruption | [#34](https://github.com/CultureBotAI/EdgeMech/issues/34) | Fixed: durable shard writes and atomic non-replacing manifest publication. Injected failure and no-replacement tests pass. Added cross-partition duplicate/coverage tests and removed the redundant Arrow copy. |
| Legacy cohort coverage is labeled as population-wide individual review | [#35](https://github.com/CultureBotAI/EdgeMech/issues/35) | Hash-bound audit confirms 593 actual decision IDs, all withheld, zero nonempty quote fields. New campaign explicitly remains unassessed. Historical artifacts preserved; corrected legacy consumer/view work remains filed. |

The follow-up found no additional blocking issue within the preparation and
single-request probe scope. Checked identifier equality and ambiguous/truncated
literature results, canonical occurrence binding, duplicate-safe joins, raw
citation preservation, exact aggregation semantics, publication failure behavior,
resource bounds and the distinction between accounting and scientific review.

The Arrow API optimization changed physical output ordering/encoding. The final
20,000-row canary and initial canary compare equal in every column after sorting
by `row_number`; neither physical ordering nor Parquet byte equality is assumed.
The full scan was launched at `ef0b94e`; successful completed artifacts are audited
independently. The atomic-publication change was separately canaried, not claimed
to have been retroactively used by that running process.

Remaining limits are explicit: the retrieval probe is not a bulk limiter/cache,
partial preparation does not verify unselected bytes, the legacy bundle audit
checks hashes and decision-ID unions rather than replaying canonical decisions,
and no operation here performs scientific entailment or quote adjudication.
No merge has been performed.
