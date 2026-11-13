"""2026-11-12: print edge-specific canary claims for manual query planning; no writes."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
for line in (root / 'artifacts/edge-sample-review-20261112/canary.jsonl').read_text().splitlines():
    row = json.loads(line)
    src = row.get('curated_source_record') or row.get('omitted_source_record') or {}
    print(json.dumps({k: row.get(k) for k in ('canary_ordinal', 'origin_transform', 'subject', 'subject_label', 'predicate', 'predicate_label', 'object', 'object_label', 'disposition')}))
    print(json.dumps({k: src.get(k) for k in ('value', 'has_percentage', 'source_column', 'source_record', 'enriched_record_dois', 'enriched_pmids', 'enriched_taxon_authority_dois', 'taxon_authority_doi', 'curation_action')}))
