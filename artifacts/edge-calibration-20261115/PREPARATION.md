# Calibration input preparation receipt

Prepared 2026-11-16 UTC (2026-11-15 America/Los_Angeles) from baseline
`c446cf5440c7c4d764459f3ed82aae3901e09d1d`.

Result: **10/10 source packets replayed, 20/20 endpoint roles retained, two
authority snapshots copied and replayed. Zero new scientific ratings, zero new
retrieval requests, zero graph admissions.** This is not a calibration pass.
The [protocol](protocol.json) and [readiness plan](../../docs/plans/edge-calibration-20261115.md)
identify the evidence preparation and independent scoring still required.

Public input pins:

- Cohort: `1dc756b0ba628756baf544cacf36f0a1ab2e4c68eed6724ee281205f22d606ee`.
- Protocol: `d24b9e1e9833d70407bf06a04ae6c0ff92f5564149a3b51e6402e5416e866517`.
- Packet helper: `0a62014d3fae61bbd6506197bf44be807633c11b53f45f5b2d44661fcb21195a`.

`--freeze` wrote the public cohort; `--plan` checked all ten retained bindings
without writes. The real `--prepare fresh-47` canary persisted occurrence,
source, complete packet and receipt files, then `--check fresh-47` independently
reread them. The nonempty files had mode 0600 beneath a 0700 directory.
Canary receipt SHA-256:
`496716051460bbe69913d9bd4dc046de5dac02067f6c7e5d9b78d2be2a079556`.

Only after that replay did nine separate `--prepare CASE` invocations prepare
the remaining cases. Every invocation replayed the unchanged canary and its own
persisted packet before returning. All freeze/plan/prepare/check commands exited
0. The same Python environment, helper, working directory and output root were
used throughout. This proves the local source-preparation path; it does not
exercise a scientific-review worker, external services, concurrent writes or
provider behavior.

This is the corrected run after adversarial finding
[#129](https://github.com/CultureBotAI/EdgeMech/issues/129). Both reviewers found
that a valid packet from another case could pass the old checker if its receipt
hash and validation result were also replaced. No such corruption was observed
in the retained run. The corrected checker reconstructs and compares the entire
packet against the selected case's exact input pins. Two substitution regressions
failed on the old code and passed after the fix.

The original 40 preparation files were moved intact to
`.temp/edge-calibration-20261115-before-129/`; all 40 hashes passed verification
against its `SHA256SUMS`. Their historical canary receipt hash is
`76508edecc17344ef09818f00338eb3c8583c98959511b8384d896757ce0751b`, and their helper
version is retained in commit `b307f482c7f6a196be089f7e209e22f0f6c152de`.
Restore that historical code and original relative staging location to replay
the old run. A new plan, one corrected live canary and its separate replay
preceded all nine subsequent corrected preparations. The protocol, cohort and
all ten packet hashes remained unchanged; the helper and receipts changed.

Private paths are `.temp/edge-calibration-20261115/CASE/`. Each contains
`occurrence.json`, `source.json`, `packet.json` and `receipt.json`. Receipts bind
the protocol/cohort, implementation/profile/contract files, original archive
inputs and derivation, and the three prepared artifacts. They retain zero
admission and unassessed scientific status.

| Case | `packet.json` SHA-256 | Measurement presentation |
| --- | --- | --- |
| first-01 | `b516c976dbdb13900c8e6e83f740c7fa962afa23af6f5aa293f846cdfa768926` | Explicit unresolved context |
| first-28 | `eb5e38bf636fed915f15ee9bd2ce9f1d4d010eb8c1e8d815a17e1de265bcd527` | Explicit unresolved context |
| first-30 | `68ae9cbdb5c02a160c3497977ce191924e9aed8c89321f3da7924770df3ffc82` | Explicit unresolved context |
| first-32 | `32cb804b4f6e0f678f01faf3ecf351146101d1beb0abe6e77ecbffedd470ded2` | Explicit unresolved context |
| first-43 | `70decffa3ed755ad913171964494b4edfcf84b2341a34a76a925837f1565befc` | Explicit unresolved context |
| fresh-04 | `5249d3331588e1973f5c19414cb5aff171b13d510499567a29954b3059fa716e` | Explicit unresolved context |
| fresh-05 | `9a456958680990e4d6742b2bc012579d6e48d5d2adefdfcd24c6f0b6ab56b34b` | Explicit unresolved context |
| fresh-14 | `c1c4a61470174802cfdbc08f31fd0e83b273270906111f5a4ef587ae973bd012` | Explicit unresolved context |
| fresh-32 | `14b21623a1726591121ea2882d9168e081f832e22143a58cad438163551326f7` | Explicit unresolved context |
| fresh-47 | `c64b42e5bf6dd8c081ab49b4faa935ae769af8dedcbd40c23c196dae083accf9` | Existing exact-source salt adapter |

An unresolved measurement presentation means the initial generic adapter did
not decode this source field; the raw source remains available for review. It
does not mean that all nine cases are quantitative claims or that their source
records lack evidence. Fresh-47's source-bound measurement does not establish
biological truth, percent basis or linked assay conditions.

Authority staging used a separate `--plan`, one real `--stage metpo` followed by
`--check metpo`, then `--stage biolink` and `--check biolink`. All exited 0 with
nonempty raw copies and receipts. Staged inputs are under
`.temp/edge-calibration-authorities-20261115/`:

- `metpo/metpo.owl`: version `2026-06-12`, 1,115,523 bytes,
  `8b6f8fe0510a698579e532658c8ace05da2550093365df9ca83feb0741778415`.
- `biolink/biolink-model.yaml`: version `4.4.0`, 511,381 bytes,
  `4955709e1cac1d26fd657f7a0c29d6c8390f42e41f9ebfab859c82b102f2bebb`.

The existing JATS and authority adapters can use these retained formats. The
primary-abstract gap is filed as [#127](https://github.com/CultureBotAI/EdgeMech/issues/127).
Identity authorities and scoped proof authoring remain incomplete. No new
independent rating matrices or canonical scientific review bundles were created.
