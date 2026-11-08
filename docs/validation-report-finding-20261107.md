# Bind validation prose to checked receipts

Review of `summarize_validation_20261107.py` found that it accepts any verified
1,000-row migration receipt but prints a fixed SQLite canary provenance and
999-unprocessed/one-deferred decision claim without checking those values across
all supplied receipts. Its census prose similarly assumes the historical
snapshot pin. A substituted valid receipt could produce misleading evidence.

Validate receipt contracts, exact input pins and expected counters before
generating this experiment-specific report. Verify the referenced persisted
manifest hash and reconcile selected rows/classification totals for census
receipts. Reject mixed inputs instead of labeling them as the same experiment.
