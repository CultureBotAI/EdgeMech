const test = require("node:test");
const assert = require("node:assert/strict");
const browser = require("../src/edgemech/site_assets/browser.js");
const row = {occurrence_id: "occurrence-1", subject: "strain:1", subject_label: "Citrate strain",
  predicate: "biolink:close_match", object: "strain:2", origin_transform: "bacdive/edges.tsv",
  disposition: "retained", content_accuracy_verdict: "accurate_direct_evidence",
  review: {cohort: "2026-11-12", source_fidelity: {verdict: "SUPPORTED"},
    scientific_support: {verdict: "NOT_ASSESSABLE"}},
  curated_change: {subject: "strain:1", predicate: "biolink:same_as", object: "strain:2"}};

test("search and independent axes preserve original claim meaning", () => {
  assert(browser.matches(row, {q: "CITRATE", source: "SUPPORTED", science: "NOT_ASSESSABLE"}));
  assert(!browser.matches(row, {science: "SUPPORTED"}));
  assert(!browser.matches(row, {q: "same_as"}));
  assert(browser.matches(row, {q: "close_match"}));
  assert(!browser.matches(row, {q: "<img src=x>"}));
});
test("missing assessment is its own state, never a negative verdict", () => {
  const unreviewed = {...row, review: undefined};
  assert.equal(browser.verdict(unreviewed, "scientific_support"), "UNREVIEWED");
  assert(browser.matches(unreviewed, {cohort: "unreviewed", science: "UNREVIEWED"}));
  assert(!browser.matches(unreviewed, {cohort: "assessed"}));
  assert(!browser.matches(unreviewed, {science: "CONTRADICTED"}));
});
test("CSV preserves original and curated triples and neutralizes formulas", () => {
  const csv = browser.csv([{...row, subject_label: ' =SUM(1,2)\n"label"'}]);
  assert(csv.includes('"\' =SUM(1,2)\n""label"""'));
  assert(csv.includes("biolink:close_match") && csv.includes("biolink:same_as"));
  assert(csv.includes("NOT_ASSESSABLE"));
});
test("URL query is literal and invalid pagination is bounded", () => {
  assert.equal(browser.readState("?q=%3Cimg%3E&page=-4").q, "<img>");
  assert.equal(browser.readState("?page=-4").page, 1);
  assert.equal(browser.readState("?page=NaN").page, 1);
  assert.equal(browser.readState("?page=999999999").page, 100000);
});
