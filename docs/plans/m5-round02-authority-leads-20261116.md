# Round02 coordinator authority leads — 2026-11-16

This is a preparation note for the coordinator, excluded from blinded reviewer
views. It records independently inspected leads and remaining verification;
it supplies neither case labels nor a frozen source-to-producer binding.

## Maintained authorities and code owners

- Biolink's [capable_of](https://biolink.github.io/biolink-model/capable_of/)
  definition concerns a physical bearer, whereas
  [OrganismTaxon](https://biolink.github.io/biolink-model/OrganismTaxon/) denotes
  classification. Compare exact frozen 4.4.0 and maintained versions. KG-Microbe
  `docs/PREGO_SCORE_VALIDATION.md` describes an existential taxon-level
  interpretation; pin and assess that interpretation rather than treating it
  as proof of strict ontology conformance.
- Historical `METPO:2000511` domain/range is recoverable in
  `git show 5ad46a8^:src/templates/metpo-properties.tsv`: microbe to observation,
  without a textual definition. Commit
  `5ad46a8d51a8f43b15a58ce23cfdd7ced575f2fb` removed it. Inspect the explanation in
  [METPO #371](https://github.com/berkeleybop/metpo/issues/371) and the unresolved
  consumer [KG-Microbe #909](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/909).
  An assay/procedure is distinct from its observation. No replacement or
  sampled-version match is established by this lead alone.
- METPO commit `62e388af7ea004b2e1fd0cd2b05db0174dcaea2e`,
  [metpo_sheet.tsv](https://github.com/berkeleybop/metpo/blob/62e388af7ea004b2e1fd0cd2b05db0174dcaea2e/src/templates/metpo_sheet.tsv),
  retains a positively defined motility parent `1000701` and a nonmotile child
  `1000703`. Inspect descendants and mappings before proposing a parent
  definition or hierarchy repair; regenerate and test the owner candidate.
  Existing local METPO working files may be dirty and stale; use isolated
  version-pinned source and preserve historical authority bytes.
- KG-Microbe `microbedecoder/observation_audit.py::source_attribute_curie`
  uses compact JSON of source name, column and literal, SHA-256 and a column
  slug. `process_scopes.py` uses an analogous process identity, with the
  maintained definition table at
  `mappings/canonical/microbedecoder_process_scope_definitions.tsv`.
  Reproduce original IDs and nodes against the sampled generator/input chain.
  A FAPROTAX 1.2.12 vocabulary witness does not establish the generating
  version of the organism-assignment CSV.
- KG-Microbe `kg_microbe/utils/mapping_file_utils.py::generate_assay_nodes`
  builds assay IDs from the prefix, assay name and well label. `download.yaml`
  routes the input to CultureBotAI/assay-metadata. Compare API20E CIT's current
  utilization/fermentation wording with the manufacturer's
  [API20E insert, revision 07584J, page 8](https://jeulin.com/media/akeneo_connector/asset_files/F/i/Fiche_Biomerieux_Galerie_API_20E_117389_FR_3910.pdf).
  Verify the candidate wording defect separately from any organism outcome.

The audit searched ignored files within scoped source, mapping, raw-data and
evidence directories. It did not establish the historical graph-to-producer
binding. Recover and hash raw authoritative sources in private preparation
before freezing new evidence; an external link or this prose is not a proof
adapter or a substitute for the exact source bytes.
