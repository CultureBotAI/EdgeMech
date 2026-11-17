# Round02 local authority recovery

The fresh-47 source-attribute node and fresh-32 process node were regenerated
from KG-Microbe `d6baf5b90003a2032747559d94c00f86a7a4c615`; identifier, category,
name and description match the original nodes. The historical M5 report names
that commit, but a cryptographic receipt linking the complete sampled graph
build to the commit was not recovered. This is a precise remaining provenance
limit. Matching a generated identifier does not independently support biology.

The retained MicrobeDecoder rows 5072 and 20904 exactly match the current
`database.csv`, read with the original extractor's Latin-1 encoding. The raw
file SHA-256 is
`0c6ff730a108720a5d6972400f2bccf2eca8621713b62736abdf5df0fb188c95`.
No units, percentage basis, assay conditions or complete growth range were
inferred from tokens.

The independent FAPROTAX 1.2.12 archive and exact vocabulary member were fetched
anonymously. Both hashes match the maintained process-definition table:
archive `87e229e5201c23f8286aeb5f092f50a95bfe6281c7746d89a50c0aac11a5923c`,
member `e5b9eead9f936316410c1a3d58aaa5fe4c2fafb8e859d250796ac70486c12963`.
This establishes the vocabulary witness, not the generating FAPROTAX version
of the organism-assignment CSV.

The API20E CIT manufacturer procedure definition was inspected through CBORG
Tavily and compared with the maintained assay metadata and KG generator.
The owner correction is isolated in
[assay-metadata draft PR5](https://github.com/CultureBotAI/assay-metadata/pull/5),
commit `b68bbc7bcffd79e28af38f6e42bbe51a78090d3d`. It changes one kit-specific
description and remains unmerged. Historical sampled metadata is preserved.
Three owner tests, the actual CLI canary, pinned KG generator replay, API/data
validators, helper lint and both builds passed. A separate read-only reviewer
accepted the candidate. The fast ontology validator's 62 errors are identical
on clean owner main and are deferred in
[owner issue4](https://github.com/CultureBotAI/assay-metadata/issues/4).

The EdgeMech capture helper passed its two focused tests and a fresh-47 live
canary; all persisted pins were inspected before the other two cases. The
private output is `.temp/m5-round02-worker-20261116/local-authorities/`.
`package-inputs.json` lists sixteen versioned authority files. `FACT_INDEX.json`
records source identities, search scope including ignored files, service calls
and explicit limits. These inputs were finalized before round02 scoring.
No paper bodies or literal paper excerpts are added by this report.
