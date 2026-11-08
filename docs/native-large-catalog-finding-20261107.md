# Increase bounded catalogue batches after the real inventory canary

The four-adapter production canary exposed SQL overhead beyond the initial
1,000-native-row benchmark. At 6m57s it had copied 676,323,743 of the Taxon
export's 1,270,205,665 bytes; the parent used 763,888 KiB RSS while workers were
intermittently idle. The executor identified catalogue insertion as the dominant
phase. No complete census manifest had been published.

The 64-row/512-KiB batches require thousands of small catalogue operations for
322,327 Taxon assertions. Increase the bounded input to 512 rows/4 MiB while
retaining at most four queued batches and ordered canonical validation. A single
larger legal envelope still stands alone, so the existing 16-MiB per-envelope
limit and worst-case oversized-line bound remain unchanged. The ordinary queued
input bound becomes 16 MiB; output objects and database memory are additional.

Retain exact hashing, duplicate/evidence accounting, independent public replay
and manifest-last publication. Measure the new bounded path, rerun the relevant
tests, and require independent review. Run a fresh small real MIM production
canary with four workers, inspect its persisted outputs, then repeat the combined
inventory canary before the full snapshot census. Preserve previous receipts and
report the measured stage separately rather than extrapolating prefix throughput.
