# Public browser validation — 2026-11-19

Public inputs were read from commit
`f841b1dff874e78d1a14075413be6a92c90f1378`. The builder and generated output hashes
are recorded in `build-receipt.json`; this source commit identifies the retained
data, not the later browser implementation commit.

The one-record canary used the first real retained occurrence, including both
historical assessment axes, through the same Python launcher, builder, output
path (`build/pages`), local HTTP server, installed Chrome and browser-check output
path (`.temp/browser-qa`) as the full run. Canary output and its render evidence
were archived before the full run. Persisted bytes, output hashes, record count,
stable detail reload, literal markup search, empty/reset behavior, keyboard
navigation, mobile containment, the no-JavaScript catalogue and load failure
passed. The full run additionally checked 100 assessed / 9,900 unassessed cohort
filter counts, independent science filtering, a persisted filtered CSV download,
and pagination restored by URL.

The full payload has 10,000 occurrences; 100 retain historical assessments.
The JSON is 7,771,182 bytes, or 1,225,128 bytes under deterministic gzip.
The 106 generated files total 18,138,164 bytes before the receipt itself.
The site includes 100 static catalogue pages. No external graph, model or
scientific API calls were made. There were no browser JavaScript errors.

Receipts:

- `canary-browser.json`: one-record persisted/rendered canary.
- `full-browser.json`: complete sample and render verification.
- `build-receipt.json`: exact public inputs and every generated output hash.

Desktop and mobile screenshots remain in the isolated clone under
`.temp/browser-qa/`; they were visually inspected. The retained checker is
`scripts/adhoc/check_browser_20261119.py`. It accepts an explicit installed
`--browser` executable and does not modify the shared EdgeMech checkout or Python environment.
It opens the local built site only.

Validation commands used the existing EdgeMech Python environment with
`PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=src`, without modifying that environment:

```sh
python -m edgemech.site --plan
python -m edgemech.site --canary --output build/pages
# Run the browser checker with --canary and archive its outputs.
python -m edgemech.site --output build/pages
python scripts/adhoc/check_browser_20261119.py --site build/pages \
  --output .temp/browser-qa --browser /path/to/installed/chrome
python -m pytest -q -p no:cacheprovider
ruff check src/edgemech tests scripts/adhoc --no-cache
python -m edgemech check-contracts
node --test tests/browser.test.cjs
UV_CACHE_DIR=.temp/uv-cache uv build --offline --no-build-isolation --python /path/to/python
```

The complete suite passed 711 tests (13 browser-publication tests included),
all four Node behavior tests passed, Ruff passed, and all 16 pinned CLAW contract
files verified. Source and wheel distributions built offline; the wheel contains
the builder and all three HTML/CSS/JavaScript assets. Existing-output rejection
and deterministic two-build canary reproduction are covered by the Python tests.

This validates a local build. It does not claim a successful GitHub Pages
deployment or authorize merging the browser PR.
