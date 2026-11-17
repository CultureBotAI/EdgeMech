# Round02 predicate and motility authority preparation

The new private evidence captures preserve nine authority inputs. A single
Biolink 4.4.0 capture and persisted-byte replay preceded the remaining eight
captures. Two focused regression tests and Ruff passed. The helper is
`scripts/adhoc/capture_m5_relation_authorities_20261116.py`; original round01
files and canonical owner working trees were read without modification.

Biolink 4.4.0 and 4.4.2 retain the physical-entity/continuant meaning of
`capable_of`, while `OrganismTaxon` denotes a classification. Their inherited
predicate descriptions were inspected through `actively involved in`,
`participates in` and `related to at instance level`. The KG-Microbe PREGO
validation document records an existential taxon convention at commit
`d6baf5b90003a2032747559d94c00f86a7a4c615`. That document describes a project
interpretation, rather than a Biolink normative exception for the sampled
transforms. Both sources remain distinct in the package.

METPO commit `7716a56286ad49695dc79a7c68e11b57dcbd978b`, immediately preceding
removal commit `5ad46a8d51a8f43b15a58ce23cfdd7ced575f2fb`, recovers the historical
`METPO:2000511` domain and range: microbe and observation. Its definition cell
is empty; the observation class also has no textual definition in that
template. The microbe class is a material entity. Owner
[issue 371](https://github.com/berkeleybop/metpo/issues/371) explains removal
of the observation-reification layer; consumer
[issue 909](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/909)
tracks continued assay-edge use. Recovering these historical constraints does
not establish that a procedure is an observation, or that the sampled graph
was generated from this particular ontology revision. Later deprecation alone
does not decide historical semantic correctness.

The maintained METPO template at
`62e388af7ea004b2e1fd0cd2b05db0174dcaea2e` retains the positive motility parent
definition and negative nonmotile child. Its source OMP:0000001 and presence/
absence children were inspected in retained OWL and primary OMP documentation.
The isolated owner repair changes the parent definition to accommodate both
states; all child links and mappings remain unchanged. Owner
[issue 661](https://github.com/berkeleybop/metpo/issues/661) and draft
[PR 662](https://github.com/berkeleybop/metpo/pull/662) track commit
`00d2e136d9f4d4824e846c2534dae13727fe4fd6`. The candidate passed all 40 owner
tests, complete Ruff/format checks, both package builds, native ROBOT 1.9.8
generation, persisted six-term inspection and ELK reasoning. A separate agent
accepted the read-only review. The public owner bundle has an explicit
zero-paper-quotation inventory and gate. This unmerged candidate is excluded
from the original-edge scientific evidence package and does not alter its
historical verdict.

Private evidence resides under
`.temp/m5-round02-worker-20261116/relation-authorities/`. `package-inputs.json`
lists authority paths, case applicability and evidence IDs; `neutral-index.json`
contains source navigation and explicit search limits without case labels.
`service-log.json` pins the three actual CBORG Tavily requests and retained
GitHub issue responses. The search included ignored files in the scoped local
authority and owner directories. No sampled ontology revision is inferred from
an independent copy, current configuration or hash match. No general
authenticated full-text helper, paid research job or email-bearing request was
used. No paper text is included in this report.

| Authority | Version | SHA-256 |
| --- | --- | --- |
| Biolink staged | 4.4.0 | `4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb` |
| Biolink maintained | 4.4.2 | `b6a1320772a92d69e84b8c700cd6386dffe45ed635c8197d61e22b6a6fa3b35e` |
| METPO release OWL | 2026-06-12 | `8b6f8fe0510a698579e532658c8ace05da2550093365df9ca83feb0741778415` |
| Historical property template | 7716a562 | `fc232e23ad8037914a1d4c21ec3d97cf704cf1b2fa732556bf4790af108c591e` |
| Historical class template | 7716a562 | `0314be126d41f59b275f76f5635ae2526b9b536f91826b10a34db61e9080b40d` |
| Maintained class template | 62e388af | `942930ccf12757c3eb11f4cd0c7151cf64622a212178e607ddd579197418d816` |
| Maintained property template | 62e388af | `8ef8929f3f8d3ed61ba41f062548a3d4d2e058932c522b7ddb3a01d1e06cef63` |
| KG-Microbe PREGO convention | d6baf5b9 | `a36dc745ec1a2470c4f237e753736c28ef7ccd6d40976c6619411bd5d9e71935` |
| KG-Microbe download configuration | d6baf5b9 | `209669d1de7e2dfea17712a755217fd201241d2e32f763366ff0570270610153` |
