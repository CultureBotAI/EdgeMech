/* Public sample browser. Plain-text rendering; no external services or graph inference. */
"use strict";
(() => {
  const pageSize = 50;
  const verdictLabels = {SUPPORTED: "Supported", CONTRADICTED: "Contradicted", NOT_FOUND: "Not found",
    NOT_ASSESSABLE: "Not assessable", NOT_APPLICABLE: "Not applicable", UNREVIEWED: "Outside retained cohorts"};
  const stateKeys = ["q", "transform", "disposition", "cohort", "source", "science", "id", "page"];
  function verdict(row, axis) { return row.review?.[axis]?.verdict || "UNREVIEWED"; }
  function matches(row, state) {
    const query = (state.q || "").trim().toLowerCase();
    const text = ["subject", "subject_label", "predicate", "predicate_label", "object", "object_label",
      "occurrence_id", "origin_transform"].map(key => row[key] || "").join(" ").toLowerCase();
    return (!query || text.includes(query)) && (!state.transform || row.origin_transform === state.transform)
      && (!state.disposition || (state.disposition === "retained" ? row.disposition === "retained" : row.disposition !== "retained"))
      && (!state.cohort || (state.cohort === "assessed" ? !!row.review : state.cohort === "unreviewed" ? !row.review : row.review?.cohort === state.cohort))
      && (!state.source || verdict(row, "source_fidelity") === state.source)
      && (!state.science || verdict(row, "scientific_support") === state.science);
  }
  function csvCell(value) {
    let text = value == null ? "" : String(value);
    if (/^[\s]*[=+@-]/u.test(text)) text = "'" + text;
    return '"' + text.replaceAll('"', '""') + '"';
  }
  function csv(records) {
    const keys = ["occurrence_id", "subject", "subject_label", "predicate", "predicate_label", "object",
      "object_label", "origin_transform", "disposition", "presence_verdict", "content_accuracy_verdict",
      "row_number", "transform_row_number", "source_line"];
    const header = [...keys, "source_fidelity", "scientific_support", "historical_cohort",
      "curated_subject", "curated_predicate", "curated_object"];
    const rows = records.map(row => [...keys.map(key => row[key]), verdict(row, "source_fidelity"),
      verdict(row, "scientific_support"), row.review?.cohort || "",
      ...["subject", "predicate", "object"].map(key => row.curated_change?.[key] || "")]);
    return [header, ...rows].map(row => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
  }
  function readState(search) {
    const params = new URLSearchParams(search);
    const state = Object.fromEntries(stateKeys.map(key => [key, params.get(key) || ""]));
    state.page = Math.max(1, Math.min(100000, parseInt(state.page, 10) || 1));
    return state;
  }
  const api = {matches, verdict, csv, csvCell, readState};
  if (typeof module !== "undefined") module.exports = api;
  if (typeof document === "undefined") return;

  const byId = id => document.getElementById(id);
  const node = (tag, text, className) => {
    const element = document.createElement(tag);
    if (text != null) element.textContent = String(text);
    if (className) element.className = className;
    return element;
  };
  function link(text, href) { const a = node("a", text); a.href = href; return a; }
  let data, filtered = [], state = readState(location.search);
  const controls = {q: "query", transform: "transform", disposition: "disposition", cohort: "cohort", source: "source", science: "science"};
  function syncControls() {
    for (const [key, id] of Object.entries(controls)) {
      const control = byId(id);
      control.value = state[key];
      if (control.tagName === "SELECT" && control.selectedIndex < 0) { control.value = ""; state[key] = ""; }
    }
  }
  function updateUrl(replace = false) {
    const url = new URL(location.href);
    url.search = "";
    for (const key of stateKeys) if (state[key] && !(key === "page" && state.page === 1)) url.searchParams.set(key, state[key]);
    url.hash = state.id ? "detail" : "browse";
    history[replace ? "replaceState" : "pushState"](null, "", url);
  }
  const sourceUrl = path => `https://github.com/CultureBotAI/EdgeMech/blob/${data.source_commit}/${path}`;
  function field(list, label, value) {
    list.append(node("dt", label), node("dd", value));
  }
  function claim(row, curated = false) {
    const section = node("div", null, "claim");
    for (const key of ["subject", "predicate", "object"]) {
      const cell = node("div");
      cell.append(node("small", `${curated ? "Curated" : "Original"} ${key}`));
      if (!curated && row[`${key}_label`]) cell.append(node("strong", row[`${key}_label`]));
      cell.append(node("code", row[key]));
      section.append(cell);
    }
    return section;
  }
  function showDetail(focus = false) {
    const section = byId("detail"), body = byId("detail-body");
    section.hidden = !state.id;
    body.replaceChildren();
    if (!state.id) return;
    const row = data.records.find(item => item.occurrence_id === state.id);
    if (!row) { body.append(node("p", "This occurrence ID is not in the published sample. The full graph is not searched.", "notice")); return; }
    body.append(node("p", row.occurrence_id), claim(row));
    if (row.curated_change) {
      body.append(node("h3", "Separately recorded curated change"), claim(row.curated_change, true),
        node("p", row.curated_change.curation_action),
        node("p", "The historical assessments below concern their recorded claim target. They do not automatically validate this curated change."));
    }
    const metadata = node("dl");
    field(metadata, "Transform", row.origin_transform);
    field(metadata, "Release disposition", row.disposition);
    field(metadata, "Recorded presence label", row.presence_verdict);
    field(metadata, "Recorded rule label", row.content_accuracy_verdict);
    field(metadata, "Native-review transfer", "Not recorded for this sample occurrence; cannot be inferred from the separate census.");
    field(metadata, "Source location", `row ${row.row_number}; transform row ${row.transform_row_number}; partition ${row.partition_id}`);
    field(metadata, "Sampling stratum", `${row.stratum_quota} selected / ${row.stratum_population} occurrences; weight ${row.sampling_weight}`);
    body.append(metadata, node("p", "Presence and rule labels are inherited provenance. They are not independent scientific approval."));
    const panels = node("div", null, "assessments");
    for (const [axis, title] of [["source_fidelity", "Source fidelity"], ["scientific_support", "Scientific support"]]) {
      const article = node("article"), assessment = row.review?.[axis];
      article.append(node("h3", title), node("span", verdictLabels[verdict(row, axis)], "badge"));
      article.append(node("p", assessment?.rationale || "No assessment in either retained historical cohort. This does not mean the claim is false or lacks evidence elsewhere."));
      if (assessment?.claim_target) article.append(node("p", `Recorded target: ${assessment.claim_target}`));
      if (assessment?.scientific_applicability) article.append(node("p", `Applicability: ${assessment.scientific_applicability}. ${assessment.applicability_reason || ""}`));
      if (assessment?.adjudicating_model) article.append(node("small", `Recorded reviewer: ${assessment.adjudicating_model}`));
      panels.append(article);
    }
    body.append(panels);
    if (row.review) {
      body.append(node("p", `Historical cohort ${row.review.cohort}, occurrence ${row.review.ordinal}. Purposive assessment, not a population accuracy estimate.`));
      for (const path of row.review.source_paths) {
        const paragraph = node("p");
        paragraph.append(link(`Retained assessment: ${path.split("/").pop()} ↗`, sourceUrl(path)));
        body.append(paragraph);
      }
    }
    const sample = data.provenance.find(item => item.path.endsWith("/manifest.jsonl"));
    const original = node("p");
    original.append(link("Open full source manifest (JSONL) ↗", sample.download_url));
    body.append(original);
    body.append(node("p", `The link opens the complete pinned file. Source line: ${row.source_line} (1-based). Sample SHA-256: ${sample.sha256}`));
    if (focus) { byId("detail-title").focus(); section.scrollIntoView({block: "start"}); }
  }
  function render() {
    filtered = data.records.filter(row => matches(row, state));
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    state.page = Math.min(state.page, pages);
    const tbody = byId("results").querySelector("tbody");
    tbody.replaceChildren();
    for (const row of filtered.slice((state.page - 1) * pageSize, state.page * pageSize)) {
      const tr = node("tr");
      for (const key of ["subject", "predicate", "object"]) {
        const td = node("td");
        if (key === "subject") {
          const url = new URL(location.href); url.searchParams.set("id", row.occurrence_id); url.hash = "detail";
          const a = link(row.subject_label || row.subject, url.toString());
          a.addEventListener("click", event => {
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            event.preventDefault(); state.id = row.occurrence_id; updateUrl(); showDetail(true);
          }); td.append(a);
        } else td.append(node("span", row[`${key}_label`] || row[key]));
        if (row[`${key}_label`]) td.append(node("small", row[key]));
        tr.append(td);
      }
      const origin = node("td", row.origin_transform.replace("/edges.tsv", ""));
      origin.append(node("small", row.disposition)); tr.append(origin);
      for (const axis of ["source_fidelity", "scientific_support"]) {
        const td = node("td"); td.append(node("span", verdictLabels[verdict(row, axis)], "badge")); tr.append(td);
      }
      tbody.append(tr);
    }
    byId("result-count").textContent = `${filtered.length.toLocaleString()} matching / ${data.records.length.toLocaleString()} published sample occurrences`;
    byId("page-label").textContent = `Page ${state.page} of ${pages}`;
    byId("previous").disabled = state.page <= 1;
    byId("next").disabled = state.page >= pages;
    byId("empty").hidden = filtered.length !== 0;
    byId("download-filtered").disabled = filtered.length === 0;
    showDetail();
  }
  async function load() {
    try {
      const response = await fetch("sample.json");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.text();
      data = JSON.parse(payload);
      if (data.schema !== "edgemech-public-sample-browser/v1" || !Array.isArray(data.records)
          || data.records.length !== data.counts.published_occurrences) throw new Error("Unexpected public sample schema");
      for (const transform of Object.keys(data.counts.transforms)) byId("transform").append(new Option(transform.replace("/edges.tsv", ""), transform));
      for (const id of ["source", "science"]) for (const [value, label] of Object.entries(verdictLabels)) byId(id).append(new Option(label, value));
      byId("filters").querySelectorAll("input,select,button").forEach(control => { control.disabled = false; });
      syncControls(); render();
      const list = node("dl");
      for (const [key, value] of Object.entries(data.census.counts)) { list.append(node("dt", key.replaceAll("_", " ")), node("dd", value.toLocaleString())); }
      byId("census-counts").append(list);
      for (const source of data.provenance) {
        const p = node("p"); p.append(link(`Raw source file: ${source.path}`, source.download_url), node("code", source.sha256)); byId("provenance").append(p);
      }
      byId("payload-size").textContent = `Public JSON size before HTTP compression: ${new TextEncoder().encode(payload).length.toLocaleString()} bytes. Source files and generated outputs are hashed in the build receipt.`;
      if (state.id) showDetail(false);
    } catch (error) {
      const message = byId("load-error"); message.hidden = false;
      message.textContent = `The public sample could not be loaded (${error.message}). Use the static catalogue or downloads below; no results are being inferred.`;
      byId("result-count").textContent = "Sample unavailable";
    }
  }
  byId("filters").addEventListener("submit", event => event.preventDefault());
  for (const [key, id] of Object.entries(controls)) byId(id).addEventListener(key === "q" ? "input" : "change", () => {
    state[key] = byId(id).value; state.page = 1; updateUrl(key === "q"); render();
  });
  byId("filters").addEventListener("reset", event => { event.preventDefault(); state = readState(""); syncControls(); updateUrl(); render(); });
  byId("previous").addEventListener("click", () => { state.page--; updateUrl(); render(); });
  byId("next").addEventListener("click", () => { state.page++; updateUrl(); render(); });
  byId("close-detail").addEventListener("click", () => { state.id = ""; updateUrl(); showDetail(); byId("query").focus(); });
  window.addEventListener("popstate", () => { if (data) { state = readState(location.search); syncControls(); render(); } });
  byId("download-filtered").addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([csv(filtered)], {type: "text/csv;charset=utf-8"}));
    const a = link("", url); a.download = "edgemech-filtered-sample.csv"; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  load();
})();
