# Independent review finding and resolution — issue 227

The separate read-only review of PR #225 at
`0c21d316fac03ee92ee337c64d64481e95653878` identified one P2 finding:
[issue #227](https://github.com/CultureBotAI/EdgeMech/issues/227). The source links
promised an exact row through a GitHub blob line anchor, but GitHub does not render
the 7,851,103-byte JSONL manifest as an addressable line view (`rawLines: null`).

The fix replaces those anchors with commit-pinned `raw.githubusercontent.com`
URLs. Interactive details label the link “Open full source manifest (JSONL)” and
display the 1-based source line and SHA-256 beside it. Each no-JavaScript catalogue
row links to the full manifest and displays its source line; the hash and explicit
full-file scope are visible above the table. The source index also links to raw
files. No link claims GitHub can display the individual row. Original occurrences,
original triples, curated changes and assessment axes are unchanged. Long hashes
wrap within a 390px mobile catalogue.

`scripts/adhoc/verify_browser_source_link_227_20261119.py` fetched exactly one real
advertised source artifact and verified HTTP 200, `text/plain; charset=utf-8`,
the full 7,851,103-byte length, and SHA-256
`1457df4e1528d7749f39bc47b6a00d06571ea215e39934216f4bc75a2dc6c4f4`.
It parsed all 10,000 source lines, checked the canary's occurrence ID and original
subject/predicate/object at its displayed line, and reopened the persisted
download. The receipt is `source-link-227.json`; the downloaded file remains
under `.temp/source-link-227/`, outside Git. No credentials or email identifiers
were sent with this public GET request.

The new regression uses the real large manifest, verifies the pinned raw URL and
line-to-occurrence mapping, and checks that the rendered catalogue visibly
contains the source line and hash with no `#L` anchors or exact-row promise.
Browser QA checks the actual interactive and static links plus mobile containment.
The one-record canary passed before the complete build. The full run passed
712 Python tests, four Node tests, Ruff, all 16 contract checks, offline package
build, and desktop/mobile browser checks without JavaScript errors. Updated
canary, full-build and browser receipts are retained alongside this record.

This is the implementation response to the finding. The corrected PR head is
being returned for independent read-only verification; no merge or deployment
has been performed.
