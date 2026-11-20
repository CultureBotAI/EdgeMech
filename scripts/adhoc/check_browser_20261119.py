"""Render and verify Edge Pages output; local inputs/screenshots/receipt; 2026-11-19.

Requires Playwright and its Chromium runtime. No external navigation or data retrieval.
"""

from __future__ import annotations

import argparse
import functools
import gzip
import hashlib
import json
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--canary", action="store_true")
    parser.add_argument("--browser", help="Optional installed Chromium/Chrome executable")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    raw = (args.site / "sample.json").read_bytes()
    data = json.loads(raw)
    expected = 1 if args.canary else 10000
    assert len(data["records"]) == expected and data["canary"] == args.canary
    receipt = json.loads((args.site / "build-receipt.json").read_bytes())
    for path, descriptor in receipt["outputs"].items():
        payload = (args.site / path).read_bytes()
        assert len(payload) == descriptor["bytes"]
        assert hashlib.sha256(payload).hexdigest() == descriptor["sha256"]
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(
        QuietHandler, directory=str(args.site.resolve())))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/"
    checks, errors = [], []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=args.browser)
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url)
            page.wait_for_function("!document.getElementById('query').disabled")
            assert f"/ {expected:,} published sample occurrences" in page.locator(
                "#result-count").inner_text()
            assert page.locator("#results tbody tr").count() == min(expected, 50)
            checks.append("persisted outputs and sample counts")
            page.locator("#results tbody a").first.click()
            assert page.locator("#detail").is_visible()
            assert "Sample SHA-256" in page.locator("#detail-body").inner_text()
            assert page.locator("#detail .assessments article").count() == 2
            detail_url = page.url
            page.reload()
            page.wait_for_function("!document.getElementById('query').disabled")
            assert page.locator("#detail").is_visible() and page.url == detail_url
            checks.append("populated detail and stable URL refresh")
            page.locator("#query").fill('<img src=x onerror="alert(1)">')
            assert page.locator("#empty").is_visible()
            assert page.locator("#results tbody tr").count() == 0
            assert page.locator("#results img").count() == 0
            page.locator("button[type=reset]").click()
            assert page.locator("#detail").is_hidden()
            checks.append("literal markup query, empty state, reset")
            if not args.canary:
                page.locator("#cohort").select_option("assessed")
                assert page.locator("#result-count").inner_text().startswith("100 matching")
                page.locator("#science").select_option("SUPPORTED")
                expected_support = sum(row.get("review", {}).get("scientific_support", {}).get(
                    "verdict") == "SUPPORTED" for row in data["records"])
                assert page.locator("#result-count").inner_text().startswith(
                    f"{expected_support} matching")
                with page.expect_download() as download_info:
                    page.locator("#download-filtered").click()
                download = download_info.value
                destination = args.output / "filtered.csv"
                download.save_as(destination)
                assert destination.stat().st_size > 0
                checks.append("independent axis filters and persisted filtered CSV")
                page.locator("button[type=reset]").click()
                page.locator("#cohort").select_option("unreviewed")
                assert page.locator("#result-count").inner_text().startswith("9,900 matching")
                page.locator("#next").click()
                assert "Page 2" in page.locator("#page-label").inner_text()
                page.reload()
                page.wait_for_function("!document.getElementById('query').disabled")
                assert "Page 2" in page.locator("#page-label").inner_text()
                checks.append("unreviewed scope and paginated URL state")
            page.locator("button[type=reset]").click()
            page.locator("#query").focus()
            page.keyboard.press("Tab")
            assert page.locator("#transform").evaluate("el => el === document.activeElement")
            checks.append("keyboard filter navigation")
            page.screenshot(path=str(args.output / "desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(url)
            page.wait_for_function("!document.getElementById('query').disabled")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.locator("#results tbody a").first.click()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(args.output / "mobile.png"), full_page=True)
            checks.append("390px mobile layout and detail containment")
            nojs = browser.new_context(java_script_enabled=False)
            fallback = nojs.new_page()
            fallback.goto(url + "catalogue/1.html")
            assert fallback.locator("tbody tr").count() == min(expected, 100)
            assert fallback.locator("tbody a").last.get_attribute("href").startswith("https://github.com/")
            checks.append("JavaScript-disabled catalogue and exact source links")
            failed = browser.new_page()
            failed.route("**/sample.json", lambda route: route.fulfill(status=503, body="unavailable"))
            failed.goto(url)
            failed.wait_for_selector("#load-error:not([hidden])")
            assert failed.locator("#query").is_disabled()
            assert failed.locator("#results tbody tr").count() == 0
            checks.append("failed asset load gives explicit error and no inferred results")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    assert not errors, errors
    result = {"date": "2026-11-19", "source_commit": data["source_commit"],
              "canary": args.canary, "records": expected, "checks": checks,
              "browser_errors": errors, "sample_bytes": len(raw),
              "sample_gzip_bytes": len(gzip.compress(raw, mtime=0)),
              "published_output_bytes": sum(item["bytes"] for item in receipt["outputs"].values()),
              "builder": receipt["builder"],
              "sample_sha256": hashlib.sha256(raw).hexdigest()}
    (args.output / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
