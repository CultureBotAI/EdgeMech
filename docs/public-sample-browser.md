# Public occurrence sample browser

The static browser publishes a projection of the **10,000-occurrence sample
selected on 2026-11-12**, with 8,500 occurrences retained in the curated derivative
and 1,500 omitted. It searches the original subject, predicate, object, labels,
transform and occurrence identifier. It does not search the complete KG-Microbe
graph. Occurrence multiplicity is preserved; matching triples are not collapsed.

The two committed 50-occurrence cohorts from November 12 and 13 contribute
separate historical source-fidelity and scientific-support fields. Missing
assessment is explicit for the other 9,900 occurrences. The canaries are purposive,
their automated assessments are historical, and independent calibration is not
claimed. Open review branches are not incorporated. Inherited rule labels such as
`accurate_direct_evidence` are displayed as recorded provenance, never converted
into scientific approval. Original triples and recorded curated changes remain
distinct. Assessments retain their own recorded claim targets.

A separate dated section summarizes the November 7 native-overlap census of
17,637,435 occurrences in the September 29 snapshot. Its zero `exact_eligible`
count means no exact inherited-scope transfers in that census. It does not mean
that the graph has no valid biology. The census population is not the sample's
assessment denominator. External Parquet partitions are not hosted or advertised
as downloadable. This browser does not extend the local reader's publication
authority or imply remote access to its private artifacts.

## Publication boundary

`python -m edgemech.site` uses only seven named, committed public inputs. Every
input must be byte-identical to the full `--source-ref` Git commit (default:
`HEAD`), and the sample digest must also match its retained sampling metadata.
Unknown or duplicate occurrence IDs, mismatched original claims, overlapping
cohorts, incomplete assessment axes, and inconsistent census counts fail the
build before the destination is published. No external service is called.

The JSON/CSV projection allowlists identifiers, labels, sampling fields, recorded
states, authored rationales, model attribution, source paths and hashes. It omits
retrieved quotations, private paths, full source records, evidence packets and
bulk graph files. Original sampling metadata explicitly says full private input
SHA-256 hashes were not computed; hashes of public derivatives do not repair that
limitation. Downloads and details expose immutable repository source links.

No repository-wide license declaration was present when this browser was added.
The browser does not invent or grant one; upstream source terms still apply.
CSV cells starting with spreadsheet-formula characters (including after
whitespace) are prefixed with an apostrophe. JSON retains their exact text.

## Build and canary

The builder itself requires only the Python standard library. From this repository:

```sh
PYTHONPATH=src uv run --frozen python -m edgemech.site --plan
PYTHONPATH=src uv run --frozen python -m edgemech.site --canary --output build/pages
```

The canary traverses the same projection, file-writing, verification and staging
path as the full build, using one real assessed occurrence. It reopens the
persisted JSON and checks exact bytes and record count. The output is prominently
marked as a one-record canary. Inspect `build/pages/build-receipt.json`, verify the
nonempty JSON/CSV/catalogue outputs, and run the browser check below with `--canary`.
Then preserve the canary and use the same output path for the full build:

```sh
mv build/pages build/canary
PYTHONPATH=src uv run --frozen python -m edgemech.site --output build/pages
```

An existing output destination is refused; archive it under a new name before
rebuilding. Staging is private to the new build and published by a directory
rename after validation. Generated site files stay under ignored `build/`.
`sample.json`, `sample.csv`, `build-receipt.json`, and the paginated static
catalogue are deterministic for the same input revision and builder sources.
The site uses no CDN, remote JavaScript, analytics, embeddings or graph API.

The optional render check needs Playwright and an installed Chromium/Chrome.
Use the same Python launcher, browser and output path for canary and full checks:

```sh
python scripts/adhoc/check_browser_20261119.py --site build/pages \
  --output .temp/browser-qa --canary --browser /path/to/chrome
# Archive the canary receipt/screenshots before the full check.
python scripts/adhoc/check_browser_20261119.py --site build/pages \
  --output .temp/browser-qa --browser /path/to/chrome
uv run --frozen pytest -q
uv run --frozen ruff check src/edgemech tests scripts/adhoc
node --test tests/browser.test.cjs
```

The render check verifies desktop and 390px mobile layouts, detail permalink
reload, filter counts, independent assessment axes, empty/reset behavior, literal
markup queries, keyboard movement, CSV persistence, no-JavaScript catalogue,
asset-load failure, and every generated output hash. It writes screenshots and a
JSON receipt. The one-record canary does not exercise full-corpus filter counts or
pagination; the full check does.

## GitHub Pages

The Pages workflow checks PR builds and publishes **only from `main`** after a
reviewed merge. Repository Settings → Pages must select **GitHub Actions** before
the first deployment. This PR does not itself enable Pages or authorize a merge.
The intended URL after a successful deployment is
`https://culturebotai.github.io/EdgeMech/`. Do not advertise it as live before
verifying the actual deployment and served page. The workflow deploys only
`build/pages`, never the source checkout or `workspace/`.

Query parameters preserve search/filter/page state. `?id=<occurrence_id>#detail`
opens a stable detail within this fixed sample. Every table and detail value is
rendered as text; no content becomes HTML. A paginated catalogue, source links,
and downloads remain available with JavaScript disabled.
