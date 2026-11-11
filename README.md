# EdgeMech

Release-occurrence accounting and inherited native-review eligibility for KG-Microbe.

EdgeMech keeps bulk rows and decision histories in immutable external Parquet artifacts and queries them with DuckDB. Shared contracts are owned by CultureBotAI/culturebotai-claw. Scientific records and decisions remain in their native Mechs.

Development scope: CLAW issues #766 and #767. No live curation worker, published site, or scientific approval is implied.

## Install and verify contracts

`uv sync --frozen --extra dev` installs the exact reviewed CLAW commit recorded
in `pyproject.toml` and `uv.lock`. Run `uv run edgemech check-contracts` to check
the installed contract bytes against `src/edgemech/contract-pins.json`.
Owner routes and their scientific boundaries are in `conf/routing.yaml`.

## External storage

```bash
uv run edgemech migrate-sqlite --ledger /path/ledger.sqlite \
  --export /path/verified-export --store workspace/new-store
uv run edgemech verify workspace/new-store/generations/GENERATION/manifest.json
uv run edgemech stats workspace/new-store/generations/GENERATION/manifest.json
uv run edgemech lookup workspace/new-store/generations/GENERATION/manifest.json OCCURRENCE_ID
```

Migration requires a frozen SQLite ledger without WAL/journal sidecars and a
new destination. It replays the canonical history from the original verified
export, compares every field of the five SQLite tables, writes partitioned
Parquet and derived indexes, then verifies physical and logical hashes before
publishing `CURRENT`. It preserves source rows, duplicate occurrences, exact
memberships, decisions and historical canonical bundles. It never changes the
input ledger. Recovery means selecting a successfully verified immutable
manifest; a failed staging directory does not become the current generation.

`verify` checks all tables and replayed decisions. `stats` reports declared
manifest counters without scanning partitions. `lookup` verifies touched
partitions and returns the exact source row, current decision and complete
history within a 2 MiB response budget; larger histories require the bulk
artifact. Neither fast operation is a replacement for a full audit.

## Native assertions and overlap

Native exporters remain in MediaIngredientMech, TraitMech, HabitatMech and
TaxonMech. Each export includes `assertions.jsonl` and a hash/count manifest.
The shared CLAW envelope preserves native locators, complete selected payloads,
evidence dependencies, native review decisions and explicit inherited scope.
Unreviewed examples and proposed taxonomic mappings remain unassessed.

```bash
uv run edgemech census --snapshot /path/pinned-snapshot \
  --source-sha256 MANIFEST_SHA256 \
  --native-export /path/native-export --native-sha256 NATIVE_MANIFEST_SHA256 \
  --output workspace/first-census --limit 1000 --workers 4
uv run edgemech verify-census workspace/first-census/census-manifest.json --workers 4
```

Repeat the two native options for each exporter. First inspect a persisted
bounded run, then use the same path without `--limit` for the full population.
Native validation uses one to four processes with bounded ordered batches; the
parent owns file hashing and database writes. Each native batch contains at most
512 rows or 4 MiB (a single larger legal envelope travels alone). One private
transaction commits its native rows and evidence/ancestry bindings together,
releasing temporary Arrow inputs before the next batch. This scratch catalogue
is separate from the final manifest publication boundary. The public verifier independently
revalidates persisted native data. Timing receipts label parent-process memory
separately from the worker pool.
Even bounded runs verify every original source member, including unselected
tails. Verification later requires that pinned source snapshot to remain
available at its recorded path. Bulk accounting rows stay outside Git.
The publisher reserves a new destination exclusively, persists verified files,
then publishes `census-manifest.json` as its final atomic marker. Interrupted
publication can leave a reserved directory without that manifest; use a new
destination for a retry. Existing destinations and filenames are never replaced.

Exact subject–predicate–object matches are candidates. `exact_eligible` requires
an identical embedded `native_assertion` envelope and explicit `native_scope`
in the KG source row; this is inherited transport conformance. It is not a
reviewed biological projection or a new scientific approval. Missing bindings,
different scope, ambiguous candidates and unavailable review remain explicit.
Shared evidence is counted separately from independent experiments; unknown
native observation, claim and experiment counts remain null.

`edgemech.packets.inherited_bundle()` creates a bounded canonical candidate
packet for explicitly selected, verified occurrence IDs. It preserves whole
native envelopes in candidate observations and leaves decisions deferred and
withheld, with no fabricated claims, reviewers or scientific reviews.

## Validation and reproducibility

The [local reader interface](docs/reader-interface-v1.md) defines bounded exact
detail, ID search, pagination and artifact downloads for a future browser.
Its pinned manifests and explicit byte budgets do not imply a hosted service.

Run `uv run --frozen pytest -q` and
`uv run --frozen ruff check src/edgemech tests scripts/adhoc`.
The retained launchers in `scripts/adhoc/` produce storage/census receipts with
hashes, persisted counters, elapsed time and peak process memory. Their outputs
belong in ignored `workspace/` or another explicitly selected artifact store.
Small canary benchmarks do not establish a production partition size or
graph-wide review quality.

The retained native packet canary checks real native envelopes in an explicitly
labeled transport fixture. Those fixture IDs are separate from KG release
occurrences and contribute no eligible-overlap counts or scientific approvals.

See the [persisted validation evidence](docs/validation/20261107.md) and the
[cross-repository milestone review](docs/milestone-status-20261107.md) for input
pins, measured results, native scope limits and the separate fleet-admission
dependency. Its policy repair is reviewed and green; protected admission remains
inactive until the required PR is explicitly approved and merged. Bulk data and
full receipts remain outside Git.

## Content-review preparation

The [corrected 17M review plan](docs/plans/content-review-20261109.md) separates
endpoint presence, evidence availability and scientific support. Prepare one
real partition before scaling, using the exact census-manifest SHA-256:

```bash
uv run python scripts/adhoc/prepare_content_inventory_20261109.py \
  --manifest workspace/validation-20261107/full-native-overlap-expanded/census-manifest.json \
  --sha256 a2b8353349816fd067ab3a7112fd1c2f5ee9c02971591ea52f31e9b981cbdd2e \
  --output workspace/content-inventory-canary
uv run python scripts/adhoc/inspect_content_inventory_20261109.py \
  workspace/content-inventory-canary/manifest.json
```

After verifying the canary, use the same preparation command with `--all` and a
new output directory. Outputs preserve occurrence identities and raw evidence
fields, join pinned nodes, and compute exact source profiles. Every content state
remains `unassessed`; these files are preparation artifacts, not scientific reviews.

The [scientific follow-up report](docs/validation/scientific-followups-20261110.md)
records revised source-level judgments, exact legacy/current coverage and distinct
node-metadata triage. The derived coverage view separates population disposition
from individual scientific assessments; it preserves the historical ledger.
Tool-extracted primary text is explicitly distinguished from retained raw provider
responses. Supported source interpretations remain withheld from KG admission.
