# Bounded chemical-scope adjudication

Policy `edgemech-chemical-scope/20261110/v1`, reviewed 2026-11-10, resolves
the three remaining product assessments from EdgeMech #41/#55. It applies only
to the exact occurrence IDs and row hashes in
`conf/literature_assessments/20261110-chemical-scope.json`. It is a finite review
policy, not a shared identity contract, chemical mapping rule or KG admission.

The review distinguishes three things: the analyte name reported in the paper,
the literal value in MicrobeDecoder's source table, and the chemical entity
identified by the graph object. The source table says `succinate` or `acetate`.
The producer preserves those words through its chemical-name mapping. The
papers describe succinic-acid or acetic-acid production. Product production is
supported; the exact chemical scope carried by the graph object needs a
qualified concern because the cited measurements do not establish that scope.
This is not a finding that anion production is false or that the producer
mistranslated an acid-valued source cell.

| Occurrence row | Source subject and value | Existing object | Reported analyte | Assessment |
|---|---|---|---|---|
| 7728857 | `lpsn:788309`, Basfia succiniciproducens, `succinate` | `CHEBI:26806` | succinic acid | concern |
| 7726784 | `lpsn:783288`, Actinobacillus succinogenes, `succinate` | `CHEBI:26806` | succinic acid | concern |
| 7726785 | `lpsn:783288`, Actinobacillus succinogenes, `acetate` | `CHEBI:30089` | acetic acid | concern |

ChEBI's current definitions distinguish these scopes. [Succinate
CHEBI:26806](https://www.ebi.ac.uk/chebi/CHEBI:26806) covers the monoanion and
dianion, rather than every acid/base form. [Succinic acid
CHEBI:15741](https://www.ebi.ac.uk/chebi/CHEBI:15741) is a separate neutral
entity. Its conjugate-base chain passes through [succinate(1-)
CHEBI:30779](https://www.ebi.ac.uk/chebi/CHEBI:30779) to [succinate(2-)
CHEBI:30031](https://www.ebi.ac.uk/chebi/CHEBI:30031). The graph's general
succinate object must not be described as a specifically selected dianion.
[Acetate CHEBI:30089](https://www.ebi.ac.uk/chebi/CHEBI:30089) has charge -1
and is the conjugate base of [acetic acid
CHEBI:15366](https://www.ebi.ac.uk/chebi/CHEBI:15366). The acid identifiers in
the decision records identify the reported names for comparison; they do not
assert that the culture contained exclusively the neutral species.

The original [Basfia species description,
DOI10.1099/ijs.0.011809-0](https://doi.org/10.1099/ijs.0.011809-0) reports
anaerobic succinic-acid production in the characterized isolates. Its retained
text describes an enzymatic UV kit and glucose-containing BHI cultures. The
species-description product sentence is retained literally at captured
lines336-338, printed page48. Neither the name used for the assay result nor
the pH of a separate isolation assay determines the measured culture's charge
distribution. The review does not transfer isolation pH to product formation.

The original [Actinobacillus species description,
DOI10.1099/00207713-49-1-207](https://doi.org/10.1099/00207713-49-1-207)
reports succinic-acid and acetic-acid co-production by type strain130Z. The
retained product phrase is at captured line402, printed page210. Its organic
acid HPLC method and buffered culture formulation are different experimental
contexts. An acidic analytical eluent does not establish culture speciation;
the product names do not establish exclusive neutral-acid production either.
This review preserves the original strain and assay bounds.

Two further primary studies corroborate the terminology and biological product
interpretation. [Van der Werf et al.1997,
DOI10.1007/s002030050452](https://pubmed.ncbi.nlm.nih.gov/9148774/) explicitly
names succinate and acetate among strain130Z's fermentation products in its
abstract. [McKinlay et al.2005,
DOI10.1128/AEM.71.11.6651-6656.2005](https://pmc.ncbi.nlm.nih.gov/articles/PMC1287747/)
identifies 130Z/ATCC55618, reports both products quantitatively, describes
initial medium pH6.9-7.1, and separates organic acids using acidic HPLC. This
supports interpreting the names as reported fermentation analytes rather than
as direct measurements of each protonation state. This interpretation is the
reviewer's inference from the methods and results. These studies are contextual
corroboration only: they do not replace the original citation, enter its quote
bindings, supply missing original-assay conditions or extend the Basfia result.

The finite decision rule is:

1. Preserve the original source row, source value, object identifier and
   citation. Require the exact row/occurrence pins before applying a revision.
2. Record product production as supported at the reported-analyte level.
   “Family” here means the named acid and its conjugate-base forms for describing
   this evidence scope; it creates no new ontology entity or equivalence edge.
3. Assign the exact occurrence assessment `concern`: its chemical scope is more
   specific than the cited measurement establishes. Use `partial` quote support
   because the quotation supports production while leaving chemical scope open.
4. Record `conflict_state=none_reported`, not a biological refutation. Retain
   `disposition=withheld`, empty native claims/observations and
   `identity_authorized=false`. A review concern does not establish a negative
   production result or require a charge-state replacement.
5. Apply no decision to citation neighbors or other acid/anion pairs. Neither
   matching labels nor this policy permits global acid/base equivalence,
   unmeasured speciation, automatic identity approval, or charge-state inference
   from a different assay, paper or organism.

This completes a bounded adjudication: all three rows have an explicit concern
and an identified reason. It does not complete native normalized-claim design.
Any later claim representing a protonation-independent analyte must state that
scope in its native interpretation and retain its observations and provenance.
It cannot inherit exact-anion approval from this review.

Existing ownership provides the implementation boundary. KG-Microbe's
`kg_microbe/transform_utils/microbedecoder/microbedecoder.py`,
`_resolve_chemical_curie`, owns the source-value-to-identifier transform; its
exact-name matches preserve these source tokens. No remapping is justified by
this review. MediaIngredientMech owns ingredient identity and species bridges.
Its [MAPPING_SEMANTICS.md, “Protonation state (bare anion labels)” and section7,
commit c79fbc41c0bc4014c68696ab941143db1a027919](https://github.com/CultureBotAI/MediaIngredientMech/blob/c79fbc41c0bc4014c68696ab941143db1a027919/MAPPING_SEMANTICS.md)
explicitly retains bare Succinate on CHEBI:26806 and distinguishes ingredient
identity from one-step protonation bridges. The associated
`IngredientCausalEdge`/`BridgeKindEnum` schema allows taxon-independent
`PROTONATION` edges using `RO:0018033` or `RO:0018034`; it does not authorize
organism production claims. Its `ingredient-scope/v1` profile likewise
distinguishes supported mapping scope from identity permission.

CLAW continues to own shared review and normalized-claim contracts. EdgeMech
records this review using their existing assessment outcome, dimensions and
source-input fields; this document and the three decision records are pinned
local review inputs. No new shared schema or scientific normalizer is created.
The original article captures remain tool-extracted primary text with their
existing extraction and publication-identity limitations; no raw PDF or
independent visual verification is claimed.
