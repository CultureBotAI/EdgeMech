# Primary abstract replay canary

Issue [#127](https://github.com/CultureBotAI/EdgeMech/issues/127), run on
2026-11-15 America/Los_Angeles (2026-11-16 UTC).

The Europe PMC adapter verifies a primary MED record's PMID, DOI and title before
extracting its abstract. It rejects ambiguous or malformed identities, incomplete
result lists, altered quote spans and abstract/full-text substitution. Verified
DOI/PMID/PMCID aliases share the publication's 25-word quotation budget across
abstract and JATS representations. Shared CLAW contracts remain unchanged.

## Single retained case

The [committed launcher](../../scripts/adhoc/run_abstract_canary_20261115.py)
passed `--plan`, then ran exactly one `--run` through canonical save/readback.
The [saved review](../../reviews/structured/20261116T052355Z-fresh05-abstract-adapter/review.md)
also passed a separate `edgemech.occurrence_review check` invocation.

| Persisted result | Observed value |
| --- | --- |
| Case | fresh-05, original occurrence ending `07a8136` |
| Primary paper | DOI `10.1099/ijs.0.65010-0`, PMID `17625207`; no PMCID |
| Inspected extent | Complete retained abstract, not full paper |
| Raw response | 9,717 bytes, SHA256 `82d96c9481a6d11eefc5976e65b2863e10bed3cedf8b02f9b09cdb92802cf807` |
| Verified evidence | One source packet and two literal abstract quotations |
| Quotation budget | 16 words total from that publication |
| Claim / literature | `NOT_ASSESSABLE` / `PARTIAL` |
| Relation / subject / object | All `UNRESOLVED` |
| Source fidelity | `NOT_ASSESSABLE` |
| Completion / verdict | `partial` / `needs_curation` |
| Provider calls / graph admissions | 0 / 0 |

The private directory `.temp/abstract-canary-fresh05-127-20261115/` contains eight
nonempty files, including the raw abstract, source inputs, proofs, authored review
and persisted receipt. The directory is mode 0700 and files are 0600. The saved
public YAML and Markdown are nonempty; their source section pins all replay inputs
and the implementation. Historical preparation bytes and receipts were preserved.

The primary abstract describes nonmotility in the nominal DSM 18772 strain. The
complete source inspection also found that BactoTraits row 8521 carries DSM 19353
and JCM 14586, whereas its linked BacDive 17851 record identifies DSM 18772. This
inconsistency is tracked in [#130](https://github.com/CultureBotAI/EdgeMech/issues/130).
Its maintained owner, correct identity join and any existing fix/quarantine remain
to be established. The paper does not resolve that conflict or certify the graph's
NCBI/METPO/Biolink/RO modeling.

This is an explicitly disclosed self-review adapter canary. It is excluded from
both independent ten-case calibration matrices, supplies no gold label, adds no
population coverage and verifies no graph correction. It proves retained-input,
abstract-identity, quotation, persistence and replay behavior for one case. It
does not exercise a provider, authenticated library access or batch concurrency.

## Validation

- 687 tests passed in the complete suite; 98 focused occurrence-review tests.
- Ruff passed for `src/edgemech`, `tests` and `scripts/adhoc`; diff whitespace checks passed.
- All 16 pinned CLAW contract files verified at `0ca25b8ee68d1fbccb4d05dcc2002fa8a64c0c34`.
- `uv build` produced a source distribution and wheel. The sandboxed attempt
  could not resolve PyPI; the retry with network access succeeded.
- The live canary and separate canonical replay each verified three evidence
  items and two quotes, with native capability disabled and zero graph admissions.

Before independent scoring, assemble the remaining scoped authority/evidence
proofs and freeze a new package. PR #128 preparation receipts retain their original
code/document hashes and must be replayed under that historical revision; do not
rewrite them to conceal implementation changes.
