# Fresh05 primary-paper access check — 2026-11-19

This bounded W4 check found and inspected a public web extraction spanning the
body of the exact 2007 paper, but **did not obtain a replayable original PDF or
publisher full-text body**. Figures were not visually inspected. No new canonical
evidence proof, six-axis judgment, calibration pass or source-identity resolution
is claimed. The earlier abstract-only round03 result remains unchanged.

Target: DOI [10.1099/ijs.0.65010-0](https://doi.org/10.1099/ijs.0.65010-0),
[PMID 17625207](https://pubmed.ncbi.nlm.nih.gov/17625207/), Kasai and colleagues,
IJSEM 57:1630–1634 (2007). Title, DOI and PMID agree in the retained Valency and
[OpenAlex work](https://openalex.org/W2099390002) metadata. A catalogue match or
access badge does not establish that full text was delivered.

## Access sequence and results

| Route | Actual result and retained scope |
| --- | --- |
| Local Zotero | Read-only SQLite search of item metadata values for the exact DOI, PMID or species phrase returned zero matching items. Thus no matching attachment was identified by this query. This is not an assertion that every local PDF or every alternate library has been searched. |
| Retained EdgeMech evidence | Existing fresh05 abstract/provenance and round reports were located. Ignore-independent filename checks covered the canonical EdgeMech `.temp` and retained sample archive; these filename checks do not search the contents of every PDF or compressed object. |
| CBORG Valency | Coordinator retained two successful discovery/detail responses identifying the exact paper. Both requests omitted abstracts; these calls supplied metadata only. The earlier retained abstract is separate evidence, and neither current call delivered the paper body. |
| Publisher | The public landing page labels the paper free, but its extracted page contains the abstract and a deferred body-loading URL. The coordinator's direct body request returned HTTP403; its CBORG Tavily body extraction failed. The retained HTML is a challenge response, not article text. |
| Anonymous OpenAlex | One HTTP200 response, 22,338 bytes, exactly matches DOI/PMID. Listed locations are the DOI publisher destination and PubMed; no PDF URL or OA location was supplied. This describes this response, not universal unavailability. |
| Anonymous public discovery | Exact DOI/title searches found a CiteSeerX PDF index and an Academia page. Targeted University of Tokyo and Japan Women's University repository searches produced no matching downloadable copy in the returned results. Search results are discovery leads, not source proofs. |
| CiteSeerX | The indexed PDF matches the title/DOI, but the direct anonymous request returned HTTP404 with HTML; the web tool's open returned403. Neither response is a retained PDF. |
| Academia direct / CBORG Tavily | Direct anonymous page retrieval returned403. One advanced Tavily extraction failed, request ID `d3e8173b-801d-4dcb-a37a-31672defb7af`. No credential or access-control workaround was attempted. |
| Public web extraction | The web reader returned text from the [Academia article page](https://www.academia.edu/7167183/Rubritalea_squalenifaciens_sp_nov_as_a_squalene_producing_marine_bacterium_belonging_to_subdivision_1_of_Verrucomicrobia), including page markers1630–1634, methods/results, figure captions, Table1 text, species description and references. The exact tool response is retained privately. It has two-column interleaving and unit/OCR defects, and does not contain inspectable figure pixels or independently retained original PDF bytes. |

The Zotero lookup used the local database at `/Users/marcin/Zotero/zotero.sqlite`,
SHA256 `b89eb79c57a03133fe1054d812386629b2fe1a2cbf728fac4e1498ab899d2392`.
This is a fingerprint of the live base file read after the query, not a retained
transactional snapshot. It does not bind SQLite WAL state or prove the query can
be replayed later against identical database bytes. The observed query and its
result are retained; no stronger database-reproducibility claim is made.
These extent/provenance corrections address
[#218](https://github.com/CultureBotAI/EdgeMech/issues/218).
Ignored and hidden paths were included in the bounded filename checks. No
licensed publisher TDM, authenticated general full-text helper, email request,
Context7 or paid research job was used. This was a local access investigation;
it does not certify the corresponding route inside an M5 worker environment.

## What was inspected and what remains missing

The body extraction associates HOact23 with MBIC08254 and DSM18772 and repeats
nonmotility in the species description. Its microscopy section describes TEM
and SEM and reports no visible flagella. General phenotypic methods and culture
conditions are present, but a distinct direct motility assay was not identified
in the inspected extraction. Lack of visible flagella alone cannot establish
absence of motility. These are provisional inspection notes from the
[public body extraction](https://www.academia.edu/7167183/Rubritalea_squalenifaciens_sp_nov_as_a_squalene_producing_marine_bacterium_belonging_to_subdivision_1_of_Verrucomicrobia),
not replacement categorical judgments.

A future evidence package still needs retained original publisher/PDF bytes,
reproducible extraction and identity/locator verification. Visual inspection is
needed before using microscopy figures or ambiguous table alignment. The public
extraction provides a concrete recovery lead rather than an exhaustive access
failure. Even a complete matching paper would not identify which culture
supplied the phenotype cell in the mixed BactoTraits row; that source-lineage
dependency remains separate.

No additional verbatim article quotation is published here. The existing
publication-level quotation budget and historical snippets remain unchanged.
Full article bodies, extraction text and failed HTTP bodies stay outside Git.

## Durable artifacts and verification

The helper [`fresh05_fulltext_20261119.py`](../../scripts/adhoc/fresh05_fulltext_20261119.py)
was written before execution. It uses read-only Zotero SQL or one anonymous HTTPS
request per invocation, bounds response bytes/time, refuses existing output
directories, writes private artifacts and verifies their readback. It never
authors scientific assessments. Ruff passes; the actual local query and the
OpenAlex request exercised its two paths. Subsequent fetches used the same helper
after the persisted OpenAlex response was inspected.

Private root: `.temp/content-review-20261119/literature/`.

| Artifact relative to private root | SHA256 |
| --- | --- |
| `valency-search.json` | `a60d1174f890d92f7a02b5bd038ae1629d4443f23c172eff5bc20ffd22c05aee` |
| `valency-detail.json` | `0d5d8508ea47aa4685375d869ec1ecfe7bc16161aa80a1f2bb2828d757a57934` |
| `tavily-fulltext-attempt.json` | `48f605d53c81e09b1caf280a8912065997c0813c7e0df713409047d0d77652bc` |
| `publisher-fulltext.html` (failed body) | `b46fd116bc374bf0eb5311c538a426679d53beb74db022eb4349743303c7998e` |
| `fresh05-access/local-zotero-01/receipt.json` | `4e0ae7e024db2e564899288c56eb2fe10cf935e105a61e6a97d28f4c2bb9b4eb` |
| `fresh05-access/openalex-01/response` | `ce6832b37029463f6d367ff3c9f8555241cf1b82f2f92f4dc1496e2956e31771` |
| `fresh05-access/openalex-01/receipt.json` | `8397c6919bdb286b3797f9b50390fe107d704e8c23c051f411300767c7dadb26` |
| `fresh05-access/citeseer-pdf-01/receipt.json` | `86134e0009c67c12712fd06752c8193718f37837e0b86546239dbf6a63b7a6db` |
| `fresh05-access/academia-page-01/receipt.json` | `45c29731653c6cf5fc2634399f3180bb481683ddfc695681ef08b04e66b2a850` |
| `fresh05-access/tavily-academia-attempt.json` | `2a58145733fabfb3bb2b9a3e0a9342c86faeb3e305e99ec78353f1ac95ded257` |
| `fresh05-access/academia-web-extraction.txt` (tool response, not original PDF) | `bd398a13768293f7db970b851f1a0eaff1b6a5a2eea2c6f2eee1b9e6846bee52` |

Each HTTP receipt records the requested/final URL, status, content type, response
size/hash, UTC time and helper hash. The web extraction is a separately retained
tool response with its source URL and capture metadata, not a successful direct
HTTP receipt. No request is relabeled successful merely because a related
indexed representation was readable.
