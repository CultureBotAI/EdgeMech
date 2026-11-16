-- 2026-11-15: read-only BactoTraits identity-owner trace for EdgeMech issue #130.
-- Input: unchanged KG-Microbe Jun-2022 raw CSV, converted losslessly from
-- ISO-8859-1 to UTF-8 because the installed DuckDB CLI has no encoding option.
-- Conversion command from EdgeMech worktree:
-- iconv -f ISO-8859-1 -t UTF-8 /Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/kg-microbe/data/raw/BactoTraits_databaseV2_Jun2022.csv > .temp/identity130/owner-trace/BactoTraits_databaseV2_Jun2022.utf8.csv
-- Expected raw SHA256: 18316d7a0b6c2bef6fcb96a7659c2e3f3734c14786f383c2a93fefe2ae226a4b.
-- Output: bounded identity fields for source data row 8521, its four neighbors
-- on either side, and either implicated BacDive identifier. No graph mutation.
-- Run from the EdgeMech worktree with duckdb -json -init /dev/null < this file;
-- retain stdout only under ignored .temp/identity130/owner-trace/.

WITH source_rows AS (
    SELECT row_number() OVER () AS source_data_row, *
    FROM read_csv(
        '.temp/identity130/owner-trace/BactoTraits_databaseV2_Jun2022.utf8.csv',
        delim = ';', skip = 2, header = true, all_varchar = true
    )
)
SELECT source_data_row, "Bacdive_ID", "culture collection codes",
       "Genus", "Species", "Full_name", "non-motile", "motile"
FROM source_rows
WHERE source_data_row BETWEEN 8517 AND 8525
   OR "Bacdive_ID" IN ('17847', '17851')
ORDER BY source_data_row;
