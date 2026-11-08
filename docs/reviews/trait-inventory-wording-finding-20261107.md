# Distinguish unpopulated Trait records from absent schema fields

The final read-only milestone/PR-body review found one factual wording defect
in `docs/milestone-status-20261107.md`: the Trait inventory paragraph says
there are no "observation-count/dataset fields." The pinned Trait schema at
`0c20b4c82a8b5ae4a883cbc536abfd6fdca6380a` explicitly defines
`observation_count` and `datasets` (`src/traitmech/schema/traitmech.yaml`,
lines 194 and 252).

The verified inventory result is narrower: among 1,130 pinned records, zero
carry `observation_count` and zero have populated dataset references. It also
finds zero exact canonical-example review selectors. Those record-level
results must not imply that the schema lacks the fields or that notes and
cited literature contain no experimental evidence.

Correct the milestone paragraph to state those instance-level counts while
preserving TraitMech #2083's open observation-extraction and assertion-review
scope. No exporter or source record needs changing or rerunning.

An ignore-independent search (`rg -uu`) over EdgeMech `docs/`, including the
pending PR bodies, found this wording only in the milestone paragraph. The
review found no additional scientific-scope or completion overclaim: full
census verification, isolated storage-repair integration and Taxon QC are
explicitly pending, and native transport remains separate from scientific
approval. This finding was filed after the read-only pass; the reviewer has
not edited the milestone wording.
