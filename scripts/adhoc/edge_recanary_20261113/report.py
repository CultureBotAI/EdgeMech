"""2026-11-13 PR76: report the fresh canary, measured intervals and bounded projections.

Inputs: two completed ledgers, frozen applicability, grouped scan receipts, HTTP
attempt log and original 10k manifest. Outputs: public report/summary and requested
private report. Full-manifest classification is bookkeeping only, never retrieval.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / "artifacts/edge-recanary-20261113"
FIRST = ROOT / "artifacts/edge-sample-review-20261112"
SPEC = importlib.util.spec_from_file_location("recanary_applicability", Path(__file__).with_name("applicability.py"))
APP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(APP)
APP_SOURCE_SHA256 = hashlib.sha256(Path(SPEC.origin).read_bytes()).hexdigest()
VERDICTS = ("SUPPORTED", "CONTRADICTED", "NOT_FOUND", "NOT_ASSESSABLE")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def relative_private(data, reference):
    part = Path(reference["path"])
    if part.is_absolute() or ".." in part.parts:
        raise ValueError("Private reference must be relative")
    path = data / part
    if not path.resolve().is_relative_to(data.resolve()) or sha(path) != reference["sha256"]:
        raise ValueError("Private input path/hash mismatch")
    return path


def count_verdicts(rows):
    values = Counter(row["verdict"] for row in rows)
    return {key: values[key] for key in (*VERDICTS, "NOT_APPLICABLE")}


def resolved(rows):
    return sum(row["verdict"] in {"SUPPORTED", "CONTRADICTED"} for row in rows)


def timed_seconds(row):
    value = row.get("adjudication_timing")
    if not value or not math.isfinite(value["elapsed_seconds"]) or value["elapsed_seconds"] < 0:
        raise ValueError("Missing or invalid actual per-edge adjudication timing")
    return value["elapsed_seconds"]


def validate_applicability(fresh, science):
    """Issue90: bind report denominators and remaining counts to frozen rules."""
    metadata = json.loads((ART / "applicability-metadata.json").read_text())
    pins = metadata["hashes"]
    sidecar = ART / "applicability.jsonl"
    classifier = ROOT / "scripts/adhoc/edge_recanary_20261113/applicability.py"
    required = (sidecar, ART / "canary.jsonl", classifier, classifier.with_name("APPLICABILITY.md"))
    if not metadata.get("classification_precedes_scientific_retrieval"):
        raise ValueError("Applicability must have been frozen before retrieval")
    if any(str(path.relative_to(ROOT)) not in pins for path in required):
        raise ValueError("Missing required frozen applicability pin")
    for relative, expected in pins.items():
        part = Path(relative)
        path = ROOT / part
        if part.is_absolute() or ".." in part.parts or not path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("Applicability provenance path must remain repository-relative")
        if sha(path) != expected:
            raise ValueError("Applicability provenance differs from its frozen hash")
    if pins[str(classifier.relative_to(ROOT))] != APP_SOURCE_SHA256:
        raise ValueError("Loaded classifier differs from frozen applicability code")
    applied = lines(sidecar)
    claims = {row["occurrence_id"]: row for row in fresh}
    if len(applied) != 50 or len(claims) != 50 or {row["occurrence_id"] for row in applied} != set(claims):
        raise ValueError("Frozen applicability must cover exactly 50 original claims")
    by_id = {row["occurrence_id"]: row for row in applied}
    for item in applied:
        claim = claims[item["occurrence_id"]]
        if any(item[key] != claim[key] for key in ("canary_ordinal", "origin_transform", "predicate", "object")):
            raise ValueError("Frozen applicability is attached to a changed claim")
        if item["scientific_applicability"] not in {"APPLICABLE", "NOT_APPLICABLE"}:
            raise ValueError("Invalid frozen applicability")
    if dict(Counter(row["scientific_applicability"] for row in applied)) != metadata["counts"]:
        raise ValueError("Frozen applicability count mismatch")
    if len(science) != 50 or {row["occurrence_id"] for row in science} != set(claims):
        raise ValueError("Scientific ledger must cover exactly the frozen cohort")
    for row in science:
        if any(row.get(key) != by_id[row["occurrence_id"]][key]
               for key in ("scientific_applicability", "applicability_rule")):
            raise ValueError("Scientific ledger changed frozen applicability")
    return by_id


def validation_summary(data):
    """Expose only check outcomes; omit private paths and self-referential hashes."""
    path = data / "validation.json"
    if not path.exists():
        return None
    receipt = json.loads(path.read_text())
    expected = {"pytest", "ruff", "sampling", "packets", "staged_whitespace"}
    checks = receipt["checks"]
    privacy = receipt["staged_privacy_matches"]
    if (set(checks) != expected or any(item["exit_code"] for item in checks.values())
            or receipt["status"] != "passed" or any(privacy.values())):
        raise ValueError("Final validation receipt is incomplete or failed")
    for name, item in checks.items():
        if sha(data / "validation" / (name + ".log")) != item["log_sha256"]:
            raise ValueError("Final validation log hash mismatch")
    return {"status": "passed", "check_exit_codes": {name: checks[name]["exit_code"] for name in sorted(expected)},
            "staged_privacy_matches": privacy}


def remaining_counts(full, first, fresh):
    first_ids = {row["occurrence_id"] for row in first}
    fresh_ids = {row["occurrence_id"] for row in fresh}
    if len(first_ids) != 50 or len(fresh_ids) != 50 or first_ids & fresh_ids:
        raise ValueError("Require two disjoint 50-edge canaries")
    ids = {row["occurrence_id"] for row in full}
    if len(full) != 10000 or len(ids) != 10000 or not first_ids | fresh_ids <= ids:
        raise ValueError("Invalid parent manifest or canary membership")
    remaining = [row for row in full if row["occurrence_id"] not in first_ids | fresh_ids]
    by_transform = defaultdict(lambda: Counter(source=0, scientific_applicable=0, not_applicable=0, unresolved_class=0))
    by_rule = Counter()
    for row in remaining:
        classified = APP.classify(row)
        group = by_transform[row["origin_transform"]]
        group["source"] += 1
        field = "scientific_applicable" if classified["scientific_applicability"] == "APPLICABLE" else "not_applicable"
        group[field] += 1
        group["unresolved_class"] += classified["applicability_rule"] == "unresolved_class"
        by_rule[classified["applicability_rule"]] += 1
    return dict(by_transform), dict(by_rule)


def project(source, science, remaining):
    """Stratify measured means by transform; leave unobserved cells unestimated."""
    projection = {}
    for transform, counts in sorted(remaining.items()):
        src = [row for row in source if row["origin_transform"] == transform]
        sci = [row for row in science if row["origin_transform"] == transform
               and row["scientific_applicability"] == "APPLICABLE"]
        item = {**counts, "source_observed": len(src), "science_observed_applicable": len(sci)}
        item["source_adjudication_seconds"] = counts["source"] * sum(timed_seconds(r) for r in src) / len(src) if src else None
        for name, getter in (("science_adjudication_seconds", timed_seconds),
                             ("science_retrieval_seconds", lambda row: row["retrieval_seconds"])):
            item[name] = (counts["scientific_applicable"] * sum(getter(r) for r in sci) / len(sci)
                          if sci else (0 if not counts["scientific_applicable"] else None))
        services = Counter()
        for row in sci:
            services.update(row["api_attempts_by_service"])
        item["science_api_attempts_by_service"] = (
            {service: count * counts["scientific_applicable"] / len(sci) for service, count in services.items()}
            if sci else ({} if not counts["scientific_applicable"] else None))
        projection[transform] = item
    return projection


def format_seconds(value):
    return "unmeasured" if value is None else f"{value:.2f}"


def worked_examples(fresh, source, science, selected=None):
    """Show five completed claim/proof pairs; source proofs stay on their own axis."""
    src = {row["occurrence_id"]: row for row in source}
    sci = {row["occurrence_id"]: row for row in science}
    by_ordinal = {row["canary_ordinal"]: row for row in fresh}
    if selected is None:
        candidates = []
        for row in fresh:
            a, b = src[row["occurrence_id"]], sci[row["occurrence_id"]]
            if b.get("evidence") and b["verdict"] in {"SUPPORTED", "CONTRADICTED"}:
                priority = 0
            elif a.get("evidence") and a["verdict"] == "CONTRADICTED":
                priority = 1
            elif a.get("evidence"):
                priority = 2
            else:
                continue
            candidates.append((priority, row["canary_ordinal"]))
        selected = [ordinal for _, ordinal in sorted(candidates)[:5]]
    if len(selected) != 5 or len(set(selected)) != 5 or not set(selected) <= set(by_ordinal):
        raise ValueError("Require five distinct completed worked examples")
    result = ["", "## Five worked examples", "",
              "Each excerpt is literal evidence already verified in its ledger. Source-record quotations establish only the source-fidelity axis; they are not promoted to independent scientific support.", ""]
    for ordinal in selected:
        row = by_ordinal[ordinal]
        a, b = src[row["occurrence_id"]], sci[row["occurrence_id"]]
        use_science = bool(b.get("evidence")) and b["verdict"] in {"SUPPORTED", "CONTRADICTED"}
        judgment = b if use_science else a
        if not judgment.get("evidence"):
            raise ValueError("Worked example lacks a verified quote")
        result += [f"### Edge {ordinal}: {row['origin_transform']}", "",
                   f"Original claim: `{row['subject']}` ({row.get('subject_label') or 'unlabelled'}) — `{row['predicate']}` — `{row['object']}` ({row.get('object_label') or 'unlabelled'}).", "",
                   f"Source: **{a['verdict']}**. Science: **{b['verdict']}**.", "",
                   judgment["rationale"], ""]
        # Issue93: complementary excerpts jointly establish identity and claim.
        for proof in judgment["evidence"]:
            quote = proof["quote"]
            if len(quote) > 600:
                raise ValueError("Worked-example quote must be short")
            reference = proof.get("reference") or proof.get("doi") or proof.get("pmid")
            if not reference:
                raise ValueError("Worked example requires an identified source")
            result += ["\n".join("> " + line if line else ">" for line in quote.splitlines()), "",
                       f"Evidence axis: {'scientific support' if use_science else 'source fidelity'}. Reference: `{reference}`. Text SHA-256: `{proof['text_sha256']}`.", ""]
    return result


def generate(data, report, pr, recommendation, example_ordinals=None):
    if not recommendation.strip():
        raise ValueError("An authored scale/no-scale recommendation is required")
    sampling = json.loads((ART / "sampling-metadata.json").read_text())
    fresh = lines(relative_private(data, sampling["private_original_canary"]))
    public = lines(ART / "canary.jsonl")
    if sha(ART / "canary.jsonl") != sampling["hashes"][str((ART / "canary.jsonl").relative_to(ROOT))]:
        raise ValueError("Public canary differs from sampling pin")
    if any(a[key] != b[key] for a, b in zip(fresh, public, strict=True)
           for key in ("occurrence_id", "canary_ordinal", "subject", "predicate", "object")):
        raise ValueError("Public sanitization changed a claim")
    first = lines(FIRST / "canary.jsonl")
    full_path = data.parent / "sample/manifest.jsonl"
    if sha(full_path) != sampling["parent_manifest_sha256"] or sha(FIRST / "canary.jsonl") != sampling["excluded_canary_sha256"]:
        raise ValueError("Parent manifest or excluded canary changed")
    full = lines(full_path)
    source = json.loads((ART / "source-adjudications.json").read_text())
    science = lines(ART / "scientific-ledger.jsonl")
    ids = {row["occurrence_id"] for row in fresh}
    for axis in (source, science):
        if len(axis) != 50 or {row["occurrence_id"] for row in axis} != ids:
            raise ValueError("Each axis must cover all 50 occurrences exactly once")
    validate_applicability(fresh, science)
    applicable = [row for row in science if row["scientific_applicability"] == "APPLICABLE"]
    for row in source + applicable:
        timed_seconds(row)
    if any(row["verdict"] not in VERDICTS for row in source + applicable):
        raise ValueError("Invalid applicable verdict")
    if any(row["verdict"] != "NOT_APPLICABLE" for row in science if row not in applicable):
        raise ValueError("Excluded scientific rows require NOT_APPLICABLE")
    remaining, rules = remaining_counts(full, first, fresh)
    projections = project(source, science, remaining)
    extraction = json.loads((data / "source/extraction-50.json").read_text())
    first_extraction = json.loads((data / "source-canary/extraction-1.json").read_text())
    if extraction["canary_sha256"] != sampling["private_original_canary"]["sha256"]:
        raise ValueError("Source extraction claim pin mismatch")
    if any(count != 1 for count in extraction["source_scan_counts"].values()):
        raise ValueError("Grouped extraction scanned an upstream source more than once")
    attempts_path = data / "literature/http-attempts.jsonl"
    attempts = lines(attempts_path) if attempts_path.exists() else []
    if any(event["occurrence_id"] not in ids for event in attempts):
        raise ValueError("HTTP log includes an edge outside the fresh canary")
    services = Counter(event["service"] for event in attempts)
    identifiers_path = data / "identifiers/identifier-resolution.json"
    identifiers = json.loads(identifiers_path.read_text()) if identifiers_path.exists() else []
    identifier_services = Counter(item["service"] for item in identifiers)
    identifier_seconds = sum(item["seconds"] for item in identifiers)
    for item in identifiers:
        if item.get("response_sha256") and sha(identifiers_path.parent / (item["response_sha256"] + ".response")) != item["response_sha256"]:
            raise ValueError("Supplemental identifier response hash mismatch")
    ledger_services = Counter()
    for row in science:
        ledger_services.update(row["api_attempts_by_service"])
    if services != ledger_services:
        raise ValueError("Retrieval stages do not account for every actual HTTP attempt")
    summary = {
        "fresh_edges": 50, "previous_edges": 50, "remaining_edges": 9900,
        "source": {"counts": count_verdicts(source), "applicable": 50,
                   "resolved": resolved(source), "resolution_rate": resolved(source) / 50,
                   "adjudication_seconds": sum(timed_seconds(row) for row in source),
                   "grouped_extraction_seconds": extraction["elapsed_seconds"],
                   "first_transport_canary_seconds": first_extraction["elapsed_seconds"]},
        "scientific": {"counts": count_verdicts(science), "applicable": len(applicable),
                       "resolved": resolved(applicable),
                       "resolution_rate": resolved(applicable) / len(applicable) if applicable else None,
                       "adjudication_seconds": sum(timed_seconds(row) for row in applicable),
                       "retrieval_seconds": sum(row["retrieval_seconds"] for row in applicable),
                       "api_attempts_by_service": dict(services)},
        "remaining_class_counts_by_transform": remaining,
        "remaining_class_counts_by_rule": rules, "projections_by_transform": projections,
        "identifier_resolution": {"requests_by_service": dict(identifier_services),
                                  "elapsed_seconds": identifier_seconds,
                                  "request_records": len(identifiers)},
        "recommendation": recommendation,
        "validation": validation_summary(data),
        "projection_limitations": "Lower-bound measured-work scenarios from this purposive small canary, not completion estimates. Targeting-plan construction, manual reference selection, software engineering and issue handling were not separately metered and are excluded. Per-transform means assume similar remaining applicable claims and provider/cache behavior. Unobserved applicability cells remain unestimated. Grouped source scan time is shared, not measured per edge. Manual alias and source-association checks remain necessary; unattended expansion is not supported.",
    }
    text = ["# Fresh 50-edge re-canary report — 2026-11-13", "",
            "**STOP: this phase reviewed exactly 50 fresh occurrences. Together with the first canary, 100 have been reviewed and 9,900 remain. No expansion or merge was performed.**", "",
            f"Draft PR: {pr}", "", recommendation, "",
            "## Separate axes and denominators", "",
            f"Source fidelity: {count_verdicts(source)}. Resolution: {resolved(source)}/50 = {resolved(source)/50:.1%}.", "",
            f"Scientific support: {count_verdicts(science)}. Resolution: {resolved(applicable)}/{len(applicable)} = {resolved(applicable)/len(applicable):.1%}. The {50-len(applicable)} NOT_APPLICABLE edges are excluded from this denominator; NOT_FOUND and NOT_ASSESSABLE applicable edges remain in it.", "",
            "Applicability was frozen by transform, predicate and object prefix before searches. Identity, taxonomy, crosswalk, recipe composition and reaction-participant classes were excluded. Unknown classes default conservatively to NOT_APPLICABLE. Class applicability does not establish scientific support. Source fidelity still covers all 50.", "",
            "The fresh selection preserves 39 retained edges (three per transform) and 11 omitted edges covering all five omission reasons, with no prior-canary occurrence overlap. Original manifest strata and N_h/n_h weights remain attached. Both 50-edge canaries are purposive coverage samples, so rates below are descriptive and do not estimate population accuracy.", "",
            "The parent 10,000 manifest contains 8,500 retained occurrences balanced over 13 transforms and verdict strata, plus 1,500 omitted occurrences balanced across five reasons. [Original allocation and stratum weights](../edge-sample-review-20261112/allocation.csv) are unchanged. Fresh SHA-256 selection uses seed `20261113-helper3-fresh-recanary-v1`, excluding the first 50; `sampling-metadata.json` pins both fresh representations.", "",
            "## Counts by transform", "", "S/C/F/A denotes supported/contradicted/not found/not assessable.", "",
            "| Transform | n | Source S/C/F/A | Source resolved/n | Science applicable | Science S/C/F/A | Science excluded | Science resolved/applicable |",
            "|---|---:|---|---|---:|---|---:|---|"]
    by_source = {row["occurrence_id"]: row for row in source}
    by_science = {row["occurrence_id"]: row for row in science}
    for transform in sorted({row["origin_transform"] for row in fresh}):
        src = [row for row in source if row["origin_transform"] == transform]
        sci = [row for row in applicable if row["origin_transform"] == transform]
        source_counts, science_counts = count_verdicts(src), count_verdicts(sci)
        text.append("| " + " | ".join((transform, str(len(src)),
            "/".join(str(source_counts[v]) for v in VERDICTS), f"{resolved(src)}/{len(src)}",
            str(len(sci)), "/".join(str(science_counts[v]) for v in VERDICTS),
            str(len(src)-len(sci)), f"{resolved(sci)}/{len(sci)}" if sci else "not applicable")) + " |")
    text += ["", "## Measured work per edge", "",
             "Adjudication clocks start before packet reading and stop after persisting the authored decision. Scientific time sums primary-sufficiency and final-review intervals, excluding intervening network time. Source extraction is one grouped scan per input, so its per-edge allocation is explicitly amortized, not individually measured. Excluded science rows have no scientific adjudication.", "",
             "The query/reference plan was manually curated within these 50 claims after grouped source-name enrichment. Plan construction and manual reference selection were not separately metered. Software engineering and issue handling are also excluded from measured retrieval and judgment intervals.", "",
             "| # | Transform | Source verdict | Source adjudication s | Source extraction s (amortized) | Science verdict | Science retrieval s | Science adjudication s | HTTP calls |",
             "|---:|---|---|---:|---:|---|---:|---:|---:|"]
    for row in fresh:
        src, sci = by_source[row["occurrence_id"]], by_science[row["occurrence_id"]]
        scientific_time = timed_seconds(sci) if sci["scientific_applicability"] == "APPLICABLE" else None
        text.append("| " + " | ".join((str(row["canary_ordinal"]), row["origin_transform"],
            src["verdict"], f"{timed_seconds(src):.2f}", f"{extraction['elapsed_seconds']/50:.2f}",
            sci["verdict"], f"{sci['retrieval_seconds']:.2f}",
            format_seconds(scientific_time) if scientific_time is not None else "not applicable",
            str(sci["api_attempts"]))) + " |")
    text += ["", f"Grouped source extraction: {extraction['elapsed_seconds']:.2f} seconds across {len(extraction['source_scan_counts'])} source files, each scanned once in the 50-edge invocation. The first single-record transport canary took another {first_extraction['elapsed_seconds']:.2f} seconds, reported separately as setup verification overhead. Source adjudication: {summary['source']['adjudication_seconds']:.2f} summed seconds. Scientific retrieval: {summary['scientific']['retrieval_seconds']:.2f} summed seconds; scientific adjudication: {summary['scientific']['adjudication_seconds']:.2f} summed active-review seconds.", "",
             f"Paper-retrieval API attempts count actual HTTP hops, including redirects and failures; cache hits add no attempt. Supplemental identifier resolution made {len(identifiers)} separately recorded taxonomy/ontology requests in {identifier_seconds:.2f} seconds. These metadata lookups are not paper retrieval or scientific evidence. Requests were anonymous and serialized. Source extraction used no literature API.", "",
             "| Service | Paper-retrieval HTTP attempts | Supplemental identifier requests |", "|---|---:|---:|"]
    text += [f"| {service} | {services[service]} | {identifier_services[service]} |"
             for service in sorted(set(services) | set(identifier_services))]
    text += worked_examples(fresh, source, science, example_ordinals)
    text += ["", "## Projection for the remaining 9,900", "",
             "Only the hash-pinned class rules were applied to the remaining manifest for these counts; no additional edge was retrieved or adjudicated. Projections multiply each transform's measured per-edge mean by its remaining count. They are lower-bound measured-work scenarios, not completion-time estimates or confidence intervals: unmetered targeting setup, manual reference selection, engineering and issue handling remain additional work. Unobserved cells are left unestimated. Actual cost depends on cache sharing, paper accessibility and provider limits.", "",
             "| Transform | Source remaining | Science applicable remaining | Source adjudication s | Science retrieval s | Science adjudication s |",
             "|---|---:|---:|---:|---:|---:|"]
    for transform, item in projections.items():
        text.append("| " + " | ".join((transform, str(item["source"]), str(item["scientific_applicable"]),
            format_seconds(item["source_adjudication_seconds"]), format_seconds(item["science_retrieval_seconds"]),
            format_seconds(item["science_adjudication_seconds"]))) + " |")
    fallback_count = rules.get("unresolved_class", 0)
    text += ["", f"The conservative unresolved-class fallback excludes {fallback_count} of the remaining 9,900 from scientific retrieval. Those rows require a separately reviewed applicability change before searching; their exclusion must not be interpreted as nonbiological truth. Per-rule counts and projected API calls by service are in `recanary-summary.json`.", "",
             f"A scenario that repeats a comparable 50-edge grouped source scan for each of 198 batches adds approximately {198*extraction['elapsed_seconds']:.2f} source-extraction seconds; this assumes comparable source coverage and scan performance. A single larger grouped scan has different selector costs and has not been benchmarked or authorized.", "",
             "Model token billing was not exposed, so no dollar estimate is reported. Measured adjudication, retrieval and service-call counts remain separate; source and science resolution rates must not be pooled.", "",
             "## Reproducibility and limits", "",
             "Fresh/private and public canary hashes, fixed selection seed, original weights, applicability table and decisions, source snapshots, literal quote hashes, packet/decision-bound timing receipts and HTTP attempt logs are retained. Public artifacts contain identifiers, short quotations and hashes; raw source records, full texts, credentials and machine-specific receipts stay private. Directional science requires a verified quote tied to raw-bound DOI/PMID. A retrieved paper or faithful source record alone is not scientific approval.", "",
             "Manual screening removed broad wrong-organism names and primary references, but did not eliminate every contaminated strain alias ([issue 88](https://github.com/CultureBotAI/EdgeMech/issues/88)). For edge 47, an ATCC 12706 fallback query still returned Weissella viridescens literature for a Weissella halotolerans claim; those papers were rejected as evidence and the claim remained NOT_ASSESSABLE. Other fallback queries used ambiguous numeric-only strain aliases and returned unrelated papers ([issue 91](https://github.com/CultureBotAI/EdgeMech/issues/91)). Frozen plans, packets and measured decisions preserve these actual targeting errors. Organism/source binding and query specificity still require manual checks. These defects block unattended review of the remaining manifest, regardless of the observed resolution rate.", "",
             "Scientific expansion is a NO-GO. After fixes for issues 88 and 91, any future work should require separate authorization for a small manually targeted set of cases, potentially in BactoTraits, MicrobeDecoder or PREGO. The few resolved canary claims do not justify transform-wide accuracy or scalability conclusions.", "",
             "No scientific extrapolation is claimed for NOT_APPLICABLE classes. A failed request or unresolved exact strain/trait binding remains an assessment limitation, not biological contradiction. Final test/privacy receipts and independent review findings are recorded in the PR; no merge is authorized.", ""]
    if summary["validation"]:
        checked = ", ".join(summary["validation"]["check_exit_codes"])
        text += [f"Final offline checks passed: {checked}. All recorded staged privacy-match counts were zero. The private receipt retains command-log hashes; the public report omits the staged-diff hash to avoid self-reference.", ""]
    body = "\n".join(text)
    if re.search(r"/(?:[Uu]sers|home)/|Mac[Bb]ook|\.[l]ocal\b|ttys\d+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|BEGIN [A-Z ]*PRIVATE KEY", body):
        raise ValueError("Public report contains a private identifier")
    (ART / "RECANARY-REPORT.md").write_text(body)
    (ART / "recanary-summary.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(body)
    print(json.dumps({"report_rows": 50, "remaining": 9900,
                      "scientific_applicable": len(applicable), "public_report_sha256": sha(ART / "RECANARY-REPORT.md")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, type=Path, help="Private phase2 directory")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--pr-url", required=True)
    parser.add_argument("--recommendation", required=True, help="Authored interpretation of whether and where science should scale")
    parser.add_argument("--examples", help="Five comma-separated canary ordinals; otherwise prioritize completed directional evidence")
    args = parser.parse_args()
    selected = [int(value) for value in args.examples.split(",")] if args.examples else None
    generate(args.data_dir, args.report, args.pr_url, args.recommendation, selected)
