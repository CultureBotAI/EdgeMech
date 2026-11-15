# Exact organism targeting for subsequent canaries

Issues [#88](https://github.com/CultureBotAI/EdgeMech/issues/88) and
[#91](https://github.com/CultureBotAI/EdgeMech/issues/91) concern retrieval scope.
The November 13 plans, packets, timed judgments, and public ledgers remain frozen.
The implementation is based on PR #76 head `3fb97af` and is a separate stacked change.

Name normalization now preserves subspecies, strain, and Candidatus qualifiers.
Source enrichment reconstructs exact organism bindings from retained record bytes,
checks their hashes, and follows explicit LPSN basonym/correct-name IDs. It does not
trust the older combined `resolved_names` list. Candidate names, strains, and
references remain separate from those bound to the claim organism. Source citation
presence, organism targeting, publication identity, and scientific support are
different checks; none substitutes for another.

Every new strain fallback includes its organism-name anchor, including numeric
aliases and collection-prefixed aliases. Repeated aliases are deduplicated before
the four-alias budget is applied. The retrieval launcher rejects legacy plans,
missing alias/reference bindings, and queries outside the bounded anchored forms
before making requests. The launcher also replays the companion private
`.sources.json` packets against the selected claim rows and reconstructs every
name, strain, and primary-reference binding. Claim comparison reuses the exact
recursive `public_canary` projection that produced the frozen public manifests;
it does not maintain a second list of fields to strip. Legacy packets remain available to the offline replay
tools; new retrieval requires rebuilding the targeting plan.

## Retained edge 47 check

The real retained source packet for *Weissella halotolerans* was rebound offline.
Its accepted names are *W. halotolerans*, *Lactobacillus halotolerans*, and
*L. viridescens subsp. halotolerans*. The broader *L. viridescens* and
*W. viridescens*, strain ATCC 12706, and DOI `10.1128/jb.73.6.758-759.1957`
are withheld as candidates. Two previously selected organism-bound primary
references remain in the new one-edge plan. The launcher dry-run passes.

The new private plan SHA-256 is
`79c1059ad7588eeefb3fd2c17ee47aea2392379827b92ca0f8e986fdfbc00e10`.
The selected manifest SHA-256 is
`a8b1967729398e3d50922f00fe28aca35b41d2d00bef556b566d0ffee1c85b54`.
The source-packet sidecar SHA-256 is
`865d2c0688df2da37fa73628c20ec6b3eaf59b8e863b4eca6d84606987ae9a38`.
Private final outputs are under `.temp/targeting-88-91/review-fixed/` in the implementation worktree.
They contain no newly retrieved literature and assign no scientific verdict.

To prepare a future single-unit retrieval without altering old evidence:

```bash
python scripts/adhoc/edge_recanary_20261113/source_adjudicate.py targeting \
  --source-dir "$RETAINED_SOURCE_DIR" --ordinal 47 --output "$NEW_DIR/enrichment-47.json"
python scripts/adhoc/edge_recanary_20261113/build_targeting.py \
  --enrichment "$NEW_DIR/enrichment-47.json" --ordinal 47 --output "$NEW_DIR/plan-47.json"
python scripts/adhoc/edge_recanary_20261113/retrieve_targeted.py \
  --manifest "$NEW_DIR/plan-47.manifest.jsonl" --plan "$NEW_DIR/plan-47.json" \
  --output "$NEW_DIR/retrieval-47" --dry-run
```

A subsequent live canary must use the same retrieval launcher and intended worker
environment, inspect persisted paper identities and useful content, and separately
adjudicate the claim. This offline check does not authorize or establish readiness
for expanding the 10,000-edge review.

## Independent review and disposition

Read-only review at `7c887c9` identified three further defects, filed separately:

- [#95](https://github.com/CultureBotAI/EdgeMech/issues/95): LPSN type strains could
  become aliases of a non-type strain. Now a retained exact culture identifier
  must intersect the LPSN type-strain list. Same-species references remain
  explicitly scoped candidates. The real edge 22 rebind retains its strain scope
  and yields no strain-bound primary references; the species description is withheld.
- [#96](https://github.com/CultureBotAI/EdgeMech/issues/96): truthy proof objects
  were accepted without replay. The source sidecar and exact reconstructed
  targeting fields are now required before retrieval.
- [#97](https://github.com/CultureBotAI/EdgeMech/issues/97): filename identity could
  override a mismatched LPSN response. Record ID, source filename, and locator
  must now agree; missing and mismatched IDs are refused.

The initial complete suite passed 431 tests. The final candidate adds regressions
for all three findings and is revalidated before handoff. No issue is silently
dropped or treated as scientific validation of an edge.

A second read-only pass at `ac473dc` found two integration defects, also fixed:

- [#98](https://github.com/CultureBotAI/EdgeMech/issues/98): the fallback selector
  now preserves the raw source sidecar under the fallback plan's filename. A
  selector-to-launcher regression verifies the resulting plan passes preflight.
- [#99](https://github.com/CultureBotAI/EdgeMech/issues/99): claim comparison now
  calls the existing publication projection directly, including nested PREGO
  source prose, while all non-projected IDs, values, and source-row fields remain
  exact. `scripts/adhoc/audit_targeting_compatibility_20261114.py` checks both
  retained 50-edge cohorts without network access and reports projection/hash
  mismatches separately from any unavailable organism targeting.
