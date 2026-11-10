# Corrected 17M content-review implementation plan

Reviewed 2026-11-09 against EdgeMech main `47bcaec` and the pinned census.
Original (retained unchanged in ignored workspace):
`PLAN_17M_EDGE_CONTENT_AND_DOI_SNIPPET_REVIEW_20261109.md`, SHA-256
`57a56a66625363fd3cfce30cd7b815bddd2ca47b8ad9ac06133b9d623dcdc423`.
Review findings: [#31](https://github.com/CultureBotAI/EdgeMech/issues/31),
[#32](https://github.com/CultureBotAI/EdgeMech/issues/32).

## Assessment and corrections

The objective is useful; the proposed completion test is scientifically invalid.
Complete accounting is achievable. Complete positive support is not guaranteed.
A DOI identifies a work, a verbatim excerpt establishes what a text says, and an
edge-level judgment additionally needs organism/strain, predicate, object,
conditions, direction, modality, and provenance to match. A database paper cannot
substitute for experimental support for every assertion that database contains.

1. Preserve separate endpoint-presence, source-fidelity, retrieval, quote-match,
   entailment, and decision states. Allow `unassessed`, `unavailable`,
   `not_applicable`, `contradicted`, and `insufficient_evidence`. A null citation or
   quote with an explicit reason is a valid outcome. Never require invented text.
   Do not label all PREGO/FAPROTAX assertions inaccurate or all ontology edges
   accurate simply from their source. Non-exact mappings can be valid as written.
2. Presence means an ID is in the pinned node table. Missing labels/categories are
   separate quality failures. Predicate validity and domain/range require their
   own versioned checks. Hash-backed attribute IDs are not intrinsically invalid;
   assess their represented value and semantics. `Other` is not automatically false.
3. Exact source rows and occurrence multiplicity remain authoritative. The census
   stores binary `source_row` and canonical IDs, not top-level subject/evidence
   columns. Actual names are `partitions/rows-000000000001-000000020000.parquet`,
   not `part-00000.parquet`. The source TSVs are in the census's pinned snapshot,
   not the census output directory.
4. Approximate cardinality estimates can exceed true row counts; the original
   distinct counts are not trustworthy exact counts. Use exact SQL distinct tuple
   counts and an OR across evidence fields (not their sum). DOI counts must
   distinguish rows, identifiers, works, packets, and independent experiments.
   Counts grouped by `(source,predicate,object)` omit organism and conditions and
   cannot define equivalent scientific claims. The asserted 593 earlier reviews
   need an exact ID union and assessment of scope; cohort anchors are not coverage
   of their entire cohorts. Do not subtract 593 from verified-review work yet.
5. Keep canonical identities and shared review schemas in pinned CLAW. This PR's
   local preparation inventory is an analysis product, not a replacement review
   contract. Compile/cache schemas once per process or worker image; run tests in
   CI/final validation, and validate contracts and content on ingestion/publication.
   Removing correctness gates entirely trades speed for silent corruption.
6. The 32-worker recommendation, I/O percentages, per-worker RSS, and 2.2 GiB
   output size have no reproducible supporting measurement here. An
   ignore-independent search of `scripts/` and `workspace/` found neither named
   profiling helper. Reported 14.6 GiB swap use does not establish safe spare RAM.
   This execution host has about 23 GiB free; the M5's reported 70 GiB is not a
   transferable budget. 17,637,435 allocations of 4096 bytes alone are about
   67.28 GiB (72.24 GB), before metadata. Measure actual columnar outputs instead.
7. Do not kill purported orphan processes without ownership and liveness evidence.
   Use a bounded queue with leases, immutable results, and idempotent task keys.
   Agent sessions, CPU cores, DuckDB threads, and provider requests are separate
   concurrency budgets. A single writer owns each DuckDB catalogue. Start at one
   process, then measure 2 and 4 before considering more; never assume 32 is best.

## Research and alternatives

- [Crossref access and limits](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/)
  currently documents public concurrency one and response-header rate limits.
  Use anonymous access, one shared provider queue, caching, retry/backoff and
  server-directed limits. Never add an email to obtain a higher pool.
- [Crossref retrieval guidance](https://www.crossref.org/documentation/retrieve-metadata/rest-api/tips-for-using-the-crossref-rest-api/)
  recommends caching and considering data dumps for very large workloads.
  Compare a deduplicated DOI queue against a local metadata snapshot after exact
  citation counts are known. A whole Crossref dump is not justified for a small
  set of works or this machine's disk budget.
- [Crossref full-text guidance](https://www.crossref.org/documentation/retrieve-metadata/rest-api/text-and-data-mining-for-researchers/)
  distinguishes metadata and links from the actual full text. Abstracts may be
  missing; metadata availability never establishes claim support or full-text rights.
- [Europe PMC service reference](https://europepmc.org/docs/EBI_Europe_PMC_Web_Service_Reference.pdf)
  distinguishes abstracts from the open-access full-text subset. Preserve the
  response, identifiers, retrieval URL/time, text extraction version and content
  hash; verify exact identifier matches, not the first search hit. Record access
  failures explicitly. Reuse the repository's `scripts/fulltext_access.py` access
  ladder where suitable, but add durable caching, exact-match verification and
  scheduler limits before bulk use; its current first-hit helper alone is insufficient.
- [DuckDB aggregation documentation](https://duckdb.org/docs/stable/sql/functions/aggregates.html)
  distinguishes exact distinct aggregation from approximate estimates. Use
  columnar staging, bounded memory/spill, exact reconciliation, and source hashes.

## Implementation sequence and acceptance criteria

### A. Deterministic preparation (implemented in this branch)

`src/edgemech/content_inventory.py` and the retained launcher
`scripts/adhoc/prepare_content_inventory_20261109.py`:

- Require the census SHA-256; verify the copied source manifest and node member.
- Check partition bounds, selected bytes, exact raw-row digests, canonical
  occurrence IDs, ordering, row counts, and persisted ID parity in both directions.
- Reject duplicate/empty node IDs so joins cannot multiply occurrences. Preserve
  original evidence columns verbatim as candidates, including base64 payloads.
- Write one Zstd Parquet preparation shard per selected input partition, with
  endpoint states and `content_status=unassessed`. Do not create scientific reviews.
- Compute exact source profiles across persisted shards. On a complete population,
  reconstruct and verify the original edge-file SHA-256, including header bytes.
- Refuse existing output directories; publish the manifest last after checks.
  A failure leaves an unpublished directory for diagnosis; retry at a new path.
- Default to one whole partition; full execution uses the same command with `--all`.
  Check a 10 GiB free-space reserve, 512 MB DuckDB memory and 4 GB spill cap.
  These are operating limits, not guarantees for total Python/Arrow RSS or final size.

Partial preparation verifies selected bytes only and does not replay native review
history. The established `verify-census` command remains the native-contract audit.
Preparation output is explicitly not a public scientific approval artifact.

### B. Evidence catalogue and source-specific fidelity adapters

Deduplicate retrieval by normalized publication identifier, but preserve every raw
citation and occurrence binding. Keep a many-to-many occurrence/evidence table;
store documents once and quotations by stable document hash plus text offsets.
Claim keys must include taxon/strain, normalized relation, object, units,
conditions, polarity/modality, source record, and normalization version. Unknown
context prevents unsafe grouping. Never propagate one reviewed cohort anchor to
all occurrences. Decode base64 only with the source's documented encoding and
retain the original bytes and decoder version.

Reconcile previous-wave IDs against the frozen census and keep prior decisions
with their actual scope. Harvest native exports with pinned repository commits,
locators, payload/evidence hashes, and review status; citation coincidence is only
a candidate binding. Develop source-fidelity adapters separately for taxonomy,
ontology relations, aggregated traits, measured observations, mappings and mined
claims. Validate a single representative case of each before scaling that adapter.

### C. Retrieval and quote verification

Run one actual anonymous DOI/PMID request with the future production launcher,
verify nonempty durable response and exact identifier equality, then test missing
abstracts, wrong identifiers, ambiguous results, rate limits and retry exhaustion.
Use a process-shared provider limiter; obey Retry-After, bounded exponential
backoff with jitter, bounded payloads/timeouts, and negative-cache expiry. Keep
abstract/full-text/metadata distinctions and access/license restrictions explicit.
Do not execute an unbounded paid retrieval or LLM sweep from a CPU-only estimate.

Verify quote substrings against a versioned text extraction of retained source
bytes. Store raw and normalized forms, offsets, retrieval hash and locator.
A verbatim match is an integrity test, not an entailment verdict. Distinguish
assertion-specific evidence, source-background evidence, and definition evidence.

### D. Scientific adjudication and measured expansion

Use canonical CLAW/native contracts for decisions, after any needed shared schema
extension is reviewed upstream. Record direct support, contradiction, missing
context and not-applicable cases independently of transport validity. Calibrate
reviewers on a stratified gold set including negative controls and source-specific
failure cases. Audit agreement and false-support rate before propagating any
explicitly scoped decision. Route unresolved cases to the native owner.

One partition is a transport/performance canary, not a scientifically representative
sample. Add canaries across all source families and evidence failure modes. Measure
peak parent/child RSS, swap pressure, API throttling, persisted bytes, wall time and
failure rate. Use those measurements to set process and provider concurrency.
Prefer dynamic cost-aware tasks over 27/28 fixed partitions per worker. Separate
network retrieval from local joins and scientific review.

### E. Publication and sync

Verify exact occurrence parity, one accounting state per occurrence, immutable
hashes and full manifest coverage. Report unresolved counts alongside positive
judgments; never use nonempty DOI/snippet as a completion criterion. Validate
shared review contracts at the publication boundary and run the full test suite.
Sync by content hashes to a new destination, then independently verify it before
publishing its manifest. Preserve source, evidence and prior decision identities.
No merge, remote worker-pool expansion, or scientific approval is implied by this PR.
