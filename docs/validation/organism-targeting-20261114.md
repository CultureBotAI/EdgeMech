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
before making requests. Legacy packets remain available to the offline replay
tools; new retrieval requires rebuilding the targeting plan.

## Retained edge 47 check

The real retained source packet for *Weissella halotolerans* was rebound offline.
Its accepted names are *W. halotolerans*, *Lactobacillus halotolerans*, and
*L. viridescens subsp. halotolerans*. The broader *L. viridescens* and
*W. viridescens*, strain ATCC 12706, and DOI `10.1128/jb.73.6.758-759.1957`
are withheld as candidates. Two previously selected organism-bound primary
references remain in the new one-edge plan. The launcher dry-run passes.

The new private plan SHA-256 is
`f605bfc1bb8e176ae9f9d4f07656875e8ee8e8fd543a0569e61aa2629bade9f5`.
The selected manifest SHA-256 is
`a8b1967729398e3d50922f00fe28aca35b41d2d00bef556b566d0ffee1c85b54`.
Private outputs are under `.temp/targeting-88-91/` in the implementation worktree.
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
