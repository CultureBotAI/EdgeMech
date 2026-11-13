-- Population strata, helper-3 sample, 2026-11-12.
-- Paths are relative to the input root; build_sample.py accepts --input-root.
SET threads=2;
SET memory_limit='4GB';
SET max_temp_directory_size='1GB';
SELECT r.origin_transform,r.content_accuracy_verdict,
 coalesce(o.omission_reason,'retained') AS disposition,count(*) AS population
FROM read_parquet('non_ontology_transform_edge_reviews_all_16.37M.parquet') r
LEFT JOIN read_parquet('post-merge-curated/omitted_edges_audit_log.parquet') o USING(occurrence_id)
GROUP BY ALL ORDER BY ALL;
