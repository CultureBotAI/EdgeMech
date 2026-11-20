"""Build the public, bounded occurrence sample browser without external graph access."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

REPOSITORY = "https://github.com/CultureBotAI/EdgeMech"
RAW_REPOSITORY = "https://raw.githubusercontent.com/CultureBotAI/EdgeMech"
SAMPLE = "artifacts/edge-sample-review-20261112/manifest.jsonl"
SAMPLING = "artifacts/edge-sample-review-20261112/sampling-metadata.json"
FIRST = "artifacts/edge-sample-review-20261112/canary-ledger.jsonl"
FRESH = "artifacts/edge-recanary-20261113/canary.jsonl"
FIDELITY = "artifacts/edge-recanary-20261113/source-adjudications.json"
SCIENCE = "artifacts/edge-recanary-20261113/scientific-ledger.jsonl"
CENSUS = "docs/validation/full-native-overlap-20261107/census-manifest.json"
INPUTS = (SAMPLE, SAMPLING, FIRST, FRESH, FIDELITY, SCIENCE, CENSUS)
FIELDS = (
    "occurrence_id", "subject", "subject_label", "predicate", "predicate_label", "object",
    "object_label", "origin_transform", "disposition", "presence_verdict",
    "content_accuracy_verdict", "row_number", "transform_row_number", "partition_id",
    "sample_hash", "hash_rank", "sampling_weight", "stratum_population", "stratum_quota",
)
VERDICTS = {"SUPPORTED", "CONTRADICTED", "NOT_FOUND", "NOT_ASSESSABLE", "NOT_APPLICABLE"}
OCCURRENCE = re.compile(r"urn:kg-microbe:occurrence:v1:[a-f0-9]{64}\Z")


def encode(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def read_inputs(root: Path, source_ref: str) -> tuple[dict, list[dict]]:
    """Only publish tracked bytes identical to the immutable source revision."""
    if not re.fullmatch(r"[a-f0-9]{40}", source_ref):
        raise ValueError("source revision must be a full Git commit SHA")
    values, provenance = {}, []
    for name in INPUTS:
        raw = (root / name).read_bytes()
        if raw != git(root, "show", f"{source_ref}:{name}"):
            raise ValueError(f"uncommitted or mismatched input: {name}")
        values[name] = ([json.loads(line) for line in raw.splitlines()]
                        if name.endswith("jsonl") else json.loads(raw))
        provenance.append({"path": name, "sha256": digest(raw), "bytes": len(raw),
                           "url": f"{REPOSITORY}/blob/{source_ref}/{name}",
                           "download_url": f"{RAW_REPOSITORY}/{source_ref}/{name}"})
    expected = values[SAMPLING]["hashes"][SAMPLE]
    if provenance[0]["sha256"] != expected:
        raise ValueError("sample hash differs from retained sampling metadata")
    return values, provenance


def indexed(rows: list[dict], name: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        identifier = row["occurrence_id"]
        if not OCCURRENCE.fullmatch(identifier) or identifier in result:
            raise ValueError(f"invalid or duplicate occurrence in {name}")
        result[identifier] = row
    return result


def assessment(row: dict) -> dict:
    """Publish authored assessment fields, never retrieved quotations or private paths."""
    if row["verdict"] not in VERDICTS:
        raise ValueError("unknown historical assessment verdict")
    result = {key: row[key] for key in (
        "verdict", "rationale", "claim_target", "adjudicating_model",
        "scientific_applicability", "applicability_reason",
    ) if key in row}
    if not isinstance(result.get("rationale"), str) or not result["rationale"]:
        raise ValueError("historical assessment has no rationale")
    return result


def project(values: dict, provenance: list[dict], source_ref: str, canary: bool = False) -> dict:
    """Keep occurrence identities, original claims and both review axes independent."""
    sample = indexed(values[SAMPLE], SAMPLE)
    first = indexed(values[FIRST], FIRST)
    fresh = indexed(values[FRESH], FRESH)
    fidelity = indexed(values[FIDELITY], FIDELITY)
    science = indexed(values[SCIENCE], SCIENCE)
    if len(sample) != values[SAMPLING]["sample_size"]:
        raise ValueError("sample count differs from retained metadata")
    if set(first) & set(fresh) or set(fresh) != set(fidelity) or set(fresh) != set(science):
        raise ValueError("historical cohorts overlap or their assessment axes differ")
    if not (set(first) | set(fresh)) <= set(sample):
        raise ValueError("historical review refers outside the public sample")
    if len(first) != 50 or len(fresh) != 50:
        raise ValueError("expected two retained fifty-occurrence historical cohorts")
    transforms = dict(sorted(Counter(row["origin_transform"] for row in sample.values()).items()))
    if transforms != values[SAMPLING]["transforms"]:
        raise ValueError("sample transforms differ from retained metadata")
    retained = sum(row["disposition"] == "retained" for row in sample.values())
    if (len(sample), retained, len(transforms)) != (10000, 8500, 13):
        raise ValueError("dated browser scope must be updated before publishing a changed sample")
    records = []
    for line, row in enumerate(values[SAMPLE], 1):
        record = {key: row[key] for key in FIELDS}
        record["source_line"] = line
        identifier = row["occurrence_id"]
        for key in ("subject", "predicate", "object", "origin_transform"):
            for cohort in (first, fresh):
                if identifier in cohort and cohort[identifier][key] != row[key]:
                    raise ValueError("historical review claim differs from the original sample")
        if "curated_change" in row:
            record["curated_change"] = {key: row["curated_change"][key]
                                        for key in ("subject", "predicate", "object",
                                                    "curation_action")}
        if identifier in first:
            if any(first[identifier][axis]["occurrence_id"] != identifier
                   for axis in ("source_fidelity", "scientific_support")):
                raise ValueError("historical assessment is bound to a different occurrence")
            record["review"] = {
                "cohort": "2026-11-12", "ordinal": first[identifier]["canary_ordinal"],
                "source_fidelity": assessment(first[identifier]["source_fidelity"]),
                "scientific_support": assessment(first[identifier]["scientific_support"]),
                "source_paths": [FIRST],
            }
        elif identifier in fresh:
            record["review"] = {
                "cohort": "2026-11-13", "ordinal": fresh[identifier]["canary_ordinal"],
                "source_fidelity": assessment(fidelity[identifier]),
                "scientific_support": assessment(science[identifier]),
                "source_paths": [FIDELITY, SCIENCE],
            }
        records.append(record)
    if canary:
        records = [next(row for row in records if row.get("review"))]
    census = values[CENSUS]
    if sum(census["counts"].values()) != census["source"]["source_rows"]:
        raise ValueError("census categories do not reconcile to the dated population")
    if (census["source"]["source_rows"], census["counts"]["exact_eligible"],
            census["independent_scientific_reviews"]) != (17637435, 0, 0):
        raise ValueError("dated browser summary must be updated before publishing a changed census")
    return {
        "schema": "edgemech-public-sample-browser/v1", "source_commit": source_ref,
        "canary": canary, "sample_date": "2026-11-12", "records": records,
        "counts": {"public_sample": len(sample), "published_occurrences": len(records),
                   "retained": retained,
                   "omitted": sum(row["disposition"] != "retained" for row in sample.values()),
                   "historically_assessed": len(first) + len(fresh), "transforms": transforms},
        "sampling": {key: values[SAMPLING][key] for key in (
            "method", "seed", "inference", "input_identity_limitation", "source_representation",
        )},
        "census": {"date": "2026-11-07", "source_snapshot_date": "2026-09-29",
                   "occurrences": census["source"]["source_rows"], "counts": census["counts"],
                   "eligibility_semantics": census["eligibility_semantics"],
                   "independent_scientific_reviews": census["independent_scientific_reviews"],
                   "kg_occurrences_approved": census["kg_occurrences_approved"],
                   "edge_member_sha256": census["source"]["edge_member_sha256"],
                   "source_path": CENSUS},
        "provenance": provenance,
        "rights": "No repository-wide license is declared. Upstream source terms still apply.",
    }


def safe_csv(value: object) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def csv_bytes(records: list[dict]) -> bytes:
    columns = list(FIELDS) + ["source_line", "source_fidelity", "scientific_support", "historical_cohort",
                              "curated_subject", "curated_predicate", "curated_object"]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(columns)
    for row in records:
        review = row.get("review", {})
        values = [row[key] for key in FIELDS]
        values += [row["source_line"]]
        values += [review.get(axis, {}).get("verdict", "NOT_REVIEWED_IN_RETAINED_COHORTS")
                   for axis in ("source_fidelity", "scientific_support")]
        values += [review.get("cohort", "")]
        values += [row.get("curated_change", {}).get(key, "")
                   for key in ("subject", "predicate", "object")]
        writer.writerow([safe_csv(value) for value in values])
    return stream.getvalue().encode()


def catalogue(data: dict, output: Path) -> None:
    """Readable paginated HTML remains available without JavaScript."""
    records = data["records"]
    source = next(item for item in data["provenance"] if item["path"] == SAMPLE)
    page_size = 100
    pages = (len(records) + page_size - 1) // page_size
    target = output / "catalogue"
    target.mkdir()
    for page in range(pages):
        body = []
        for row in records[page * page_size:(page + 1) * page_size]:
            identifier = row["occurrence_id"]
            cells = [f'<a href="../index.html?id={identifier}#detail">'
                     f'{html.escape(row["subject_label"] or row["subject"])}</a>',
                     html.escape(row["predicate_label"] or row["predicate"]),
                     html.escape(row["object_label"] or row["object"]),
                     html.escape(row["origin_transform"]), html.escape(row["disposition"])]
            for axis in ("source_fidelity", "scientific_support"):
                cells.append(html.escape(row.get("review", {}).get(axis, {}).get(
                    "verdict", "Not in retained review cohorts")))
            cells.append(f'<a href="{source["download_url"]}">Full source manifest (JSONL)</a>'
                         f'<small>Source line {row["source_line"]} (1-based)</small>')
            body.append("<tr>" + "".join(f"<td>{value}</td>" for value in cells) + "</tr>")
        navigation = " ".join(f'<a href="{number}.html">{label}</a>' for number, label in (
            (page, "Previous"), (page + 2, "Next")) if 1 <= number <= pages)
        text = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EdgeMech sample catalogue · {page + 1}</title><link rel="stylesheet" href="../site.css">
<body><main><a href="../index.html">EdgeMech sample browser</a>
<h1>Occurrence sample catalogue</h1><p>Page {page + 1} of {pages} ·
{len(records):,} published sample occurrences. Historical assessment states are separate from
release presence and inherited transport eligibility. Not a search of the full graph.</p>
<p><a href="../sample.csv" download>Download this public sample as CSV</a></p>
<p>Provenance links open the complete pinned source manifest, not an individual row.
Source SHA-256: <code>{source["sha256"]}</code></p>
<div class="table-scroll" tabindex="0" aria-label="Occurrence sample table"><table>
<thead><tr><th>Original subject</th><th>Original predicate</th><th>Original object</th>
<th>Transform</th><th>Disposition</th><th>Source fidelity</th><th>Scientific support</th>
<th>Provenance</th></tr></thead><tbody>{''.join(body)}</tbody></table></div>
<nav aria-label="Catalogue pages">{navigation}</nav></main></body></html>'''
        (target / f"{page + 1}.html").write_text(text)


def build(root: Path, output: Path, source_ref: str, *, canary: bool = False) -> dict:
    if output.exists():
        raise ValueError("output already exists; choose an empty destination or archive the old build")
    values, provenance = read_inputs(root, source_ref)
    data = project(values, provenance, source_ref, canary)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".edge-pages-", dir=output.parent))
    try:
        raw = encode(data)
        (staging / "sample.json").write_bytes(raw)
        (staging / "sample.csv").write_bytes(csv_bytes(data["records"]))
        assets = Path(__file__).with_name("site_assets")
        for name in ("index.html", "site.css", "browser.js"):
            text = (assets / name).read_text()
            text = text.replace("SOURCE_COMMIT", source_ref)
            text = text.replace("BUILD_SCOPE", "ONE-RECORD CANARY — " if canary else "")
            (staging / name).write_text(text)
        (staging / ".nojekyll").write_text("")
        catalogue(data, staging)
        receipt = {
            "schema": data["schema"], "source_commit": source_ref, "canary": canary,
            "builder": {"path": "src/edgemech/site.py", "sha256": digest(Path(__file__).read_bytes())},
            "counts": data["counts"], "inputs": provenance,
            "outputs": {str(path.relative_to(staging)): {
                "bytes": path.stat().st_size, "sha256": digest(path.read_bytes()),
            } for path in sorted(staging.rglob("*")) if path.is_file()},
        }
        (staging / "build-receipt.json").write_bytes(encode(receipt))
        # Re-read actual persisted output, including cardinality and exact bytes, before publishing.
        persisted = (staging / "sample.json").read_bytes()
        if persisted != raw or len(json.loads(persisted)["records"]) != len(data["records"]):
            raise ValueError("persisted browser payload failed verification")
        staging.rename(output)
        return receipt
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("build/pages"))
    parser.add_argument("--source-ref", help="Immutable commit; defaults to HEAD")
    parser.add_argument("--plan", action="store_true", help="Validate inputs without writing")
    parser.add_argument("--canary", action="store_true", help="Publish exactly one real review row")
    args = parser.parse_args()
    source_ref = args.source_ref or git(args.root, "rev-parse", "HEAD").decode().strip()
    if args.plan:
        values, provenance = read_inputs(args.root, source_ref)
        result = project(values, provenance, source_ref, args.canary)
        print(json.dumps({"source_commit": source_ref, "counts": result["counts"],
                          "canary": args.canary, "writes": False}, sort_keys=True))
    else:
        result = build(args.root, args.output, source_ref, canary=args.canary)
        print(json.dumps({"source_commit": source_ref, "counts": result["counts"],
                          "canary": args.canary, "files": len(result["outputs"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
