# BactoTraits mixed-strain source investigation

This investigation follows [#130](https://github.com/CultureBotAI/EdgeMech/issues/130)
for the exact fresh-05 occurrence
`urn:kg-microbe:occurrence:v1:1e9dec218a07f7e480add8ff273e3a9285f79d57746ca74041702839207a8136`:
`NCBITaxon:1123071 biolink:has_phenotype METPO:1000703`.

The source row contains identifiers for two different organisms. A replacement
subject or culture-code edit would assume which parts of the row are trustworthy.
The bounded candidate correction therefore withholds that row's BactoTraits
contribution and preserves the reason and original identity in an audit. It does
not declare the biological nonmotility claim false or remove another source's
independent evidence for that claim.

## Primary identity evidence

| Source identity | Independently checked catalog identity |
| --- | --- |
| DSM 19353 / JCM 14586 | *Thioprofundum lithotrophicum*, strain 106; BacDive 17847 and NCBITaxon 571898 |
| DSM 18772 / MBIC 08254 / NBRC 103619 | *Rubritalea squalenifaciens*, HOact 23; BacDive 17851 |

The first mapping is confirmed by [DSMZ DSM 19353](https://www.dsmz.de/collection/catalogue/details/culture/DSM-19353)
and [JCM 14586](https://www.jcm.riken.jp/cgi-bin/jcm/jcm_number?JCM=14586).
JCM documents an original-publication typo, JCM 14596; the catalog-corrected
accession is 14586. That typo is not a reason to identify either strain with
*Rubritalea*.

The second mapping is independently confirmed by [DSMZ DSM 18772](https://www.dsmz.de/collection/catalogue/details/culture/DSM-18772)
and [BacDive 17851](https://bacdive.dsmz.de/strain/17851). The BacDive page identifies
NCBITaxon 1123071 with genome GCA_900141815 and NCBITaxon 407226 with 16S sequence
AB277853. These are distinct identifiers in the source, not interchangeable
replacement subjects. The retained primary description, DOI
[10.1099/ijs.0.65010-0](https://doi.org/10.1099/ijs.0.65010-0), describes nonmotility
for HOact23/DSM 18772 in its abstract; no new full paper was inspected here.

Four anonymous catalog responses, deterministic text derivatives and capture
receipts are retained privately under `.temp/identity130/authorities/`. Raw HTML
and full text derivatives are excluded from Git. The first DSM19353 fetch was
run and inspected before the other captures. The
[capture helper](../../scripts/adhoc/capture_strain_authorities_130_20261115.py)
records response and text hashes, access time, URL, extent and its own code hash.

## Maintained owner and observed failure

The owner is `Knowledge-Graph-Hub/kg-microbe`, specifically
`download.yaml` and `kg_microbe/transform_utils/bactotraits/bactotraits.py`.
Current remote master inspected was `ef27b97a0b450767da54235c6105b5250c178adc`.
Both files have the same Git blobs as the inspected local checkout at
`e3d1213a8bf7a4408204ebd48c19e42ec2e14b5e`; the remote branch check therefore did
not establish a later correction in either owner file.

The June 2022 source CSV is SHA256
`18316d7a0b6c2bef6fcb96a7659c2e3f3734c14786f383c2a93fefe2ae226a4b`;
its MD5 matches the maintained download pin `e6bca5b947c1aa692d45ac24aa9025f3`.
Its data row 8521 contains BacDive 17851 and the *Rubritalea squalenifaciens*
name, but culture codes DSM 19353 / JCM 14586. The complete retained row text
has SHA256 `345fd2d00ee93334d975085716692dd4d4c530d5529f04c5b07af0766d5a512a`.

The current transform reads the BacDive ID and joins it through the consumed
BacDive lookup. It copies the collection-code field without checking its
agreement with that identity. The lookup itself distinguishes BacDive 17847 /
NCBITaxon 571898 from BacDive 17851 / NCBITaxon 1123071. The mixed row is already
present in the original CSV; EdgeMech's extraction did not create it.

The [CSV-aware bounded query](../../scripts/adhoc/inspect_bactotraits_owner_130_20261115.sql)
inspected rows 8517–8525. Row 8517 contains another accession mismatch, recorded
separately in [#132](https://github.com/CultureBotAI/EdgeMech/issues/132). This
supports investigating a wider alignment problem; it does not establish its
extent or authorize an automatic repair of neighboring rows. Ordinals count data
records after the two preamble records and header, not raw physical line numbers.

GitHub all-state searches for the exact terms `19353` and `17851` returned no
issues during the owner trace. The related BactoTraits lookup-freshness changes
do not resolve the source identity conflict. These are bounded search results,
not proof that no correction exists anywhere outside the examined surfaces.

## Correction boundary

The owner change in [KG-Microbe PR #1867](https://github.com/Knowledge-Graph-Hub/kg-microbe/pull/1867)
is a finite, reviewed-row quarantine with an input
policy and mandatory audit. It matches the complete original row before source
cell normalization, fails on changed/missing/duplicated reviewed identities, and
records actual consumed input hashes. It does not infer corrected accessions,
taxon IDs or phenotype cells, and does not introduce a general mismatch filter
over unreviewed rows.

The real single-row transform replay reproduced 21 assertions and 22 nodes on
baseline `ef27b97a`, including the exact reviewed nonmotility assertion. Candidate
`e24d58bf2` emitted zero assertions and nodes, and one mandatory quarantine audit
containing the complete original row, original mapped identity, actual slice
ordinal 1, reviewed ordinal 8521 and policy/source hashes. This demonstrates a
bounded producer correction before source finalization. There were no unaffected
real rows in the slice; a separate synthetic-control regression tests their
retention. No replacement taxon or phenotype values were inferred.

The same launcher and input bytes were used for both runs, including the actual
BacDive lookup and METPO templates. NCBITaxon labels came from existing read-only
database statements; the DB and OWL release agreed at `2026-07-12`. The launcher
pins the queried statements and database metadata, not a whole-database hash.
Neither run made provider calls. The first baseline attempt was stopped by the
stage-only guard on an import-time cache write; [KG-Microbe #1866](https://github.com/Knowledge-Graph-Hub/kg-microbe/issues/1866)
records the fix and fresh-process regression before the successful v2 replays.
The original failed stage remains preserved.

Private stages in the owner worktree are
`data/validation-bactotraits-130/baseline-v2-20261116/` and
`candidate-v2-20261116/`. Their receipt SHA256 values are
`588f3e50352232036ce517616add423e0a7c08b760894f8edb05ac854f697633` and
`d96f5b004961df31b91a82971122b15a6d969b8c2570edb1faabde4fde885dac`.
The launcher SHA256 is
`d058e94408498c047a4d086c8f363b8c5bdbc7b98ce083a7bd5712f333c69c86`.
See the [owner replay report](https://github.com/Knowledge-Graph-Hub/kg-microbe/blob/df6bc8d581ac88b2924cc6e81b4fc77b39d7dbe1/docs/BACTOTRAITS_IDENTITY_QUARANTINE.md)
for the implementation boundary and retained evidence.

A separate reviewer who authored neither the transform nor launcher inspected
the saved TSVs and audit directly, recomputed receipt/output/policy/original
source/lookup hashes, compared input slices byte-for-byte with each other and the
original records, and independently confirmed data-row ordinal 8521. The review
passed at owner head `df6bc8d581ac88b2924cc6e81b4fc77b39d7dbe1` with no findings;
its code is unchanged from replay candidate `e24d58bf2` (the intervening change
adds the replay report). The reviewer also checked private-stage permissions and
left all evidence unchanged. This supplies the bounded candidate-byte correction
demonstration required by [#119](https://github.com/CultureBotAI/EdgeMech/issues/119).

The source-owner PR is not merged and no graph release has been regenerated.
The frozen occurrence remains immutable. Biological claim/model judgments and
independent reviewer calibration remain separate from this source quarantine;
expansion beyond the existing 100 reviewed occurrences is still gated.

## Saved review and validation

The new [canonical identity review](../../reviews/structured/20261116T074049Z-fresh05-source-identity/review.md)
replays seven evidence records and six bounded quotations. The retained paper
quotations total 16 words; each catalog contributes at most 25 quoted words.
It records claim and source fidelity as `NOT_ASSESSABLE`, literature support as
`PARTIAL`, and relation/subject/object modeling as `UNRESOLVED`. It is a partial
technical self-review, excluded from independent reviewer calibration, with no
admission recommendation. It links the original finding without rewriting the
prior review. This review records the identity investigation, before verification
of a candidate transform correction.

The first save attempt exposed [#133](https://github.com/CultureBotAI/EdgeMech/issues/133):
the capture receipt's timezone-aware `+00:00` timestamp was incompatible with
the canonical contract's UTC `Z` form. The adapter now normalizes that field,
preserving the original receipt bytes and timestamp precision. The failed stage
and original helper snapshot remain private; a fresh v2 stage saved and checked
the canonical pair successfully without new provider calls.

Validation completed on this evidence implementation: 698 tests passed, Ruff
passed for the CI scope (`src/edgemech tests scripts/adhoc`), all 16 pinned CLAW
contract files verified, and both source distribution
and wheel were built and inspected as nonempty artifacts. These checks establish
the evidence adapter's behavior, not a corrected graph release.
The broader `ruff check .` reports two pre-existing E741 warnings in the vendored
ID-label validator, filed separately as [#134](https://github.com/CultureBotAI/EdgeMech/issues/134)
and deferred to its maintained owner.

## Services used

CBORG Tavily supplied three successful keyed calls: one search and two extraction
calls covering four catalog pages. Their request identifiers are recorded in the
private service-provenance receipt, and one complete extraction response is
retained. Four separate anonymous catalog fetches supplied the raw bytes used for
replay. An initial sandbox DNS failure preceded the successful single-fetch
canary. No Valency, Context7, publisher TDM or licensed full-text retrieval was
used for this identity check. Catalog retrieval is distinct from library access
to a full scientific paper.
