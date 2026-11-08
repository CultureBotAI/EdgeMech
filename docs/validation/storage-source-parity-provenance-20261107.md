# Source-to-output migration proof, 2026-11-07

EdgeMech #14 closes the remaining production acceptance gap from
CultureBotAI/culturebotai-claw#951: complete-field logical hashes and row counts
are computed independently from the read-only SQLite transaction and compared
with persisted Parquet readback for all five authoritative tables before
publication. EdgeMech #15 additionally binds the evidence report to the pinned
SQLite digest and the migration receipt's unchanged input-hash maps.

The repair was prepared on `fix/storage-source-reconciliation-951-20261107`
from `1b1837a79e25241b3bd3dfb850fe8baa9687f64c`, in the isolated worktree
`/Users/marcin/Documents/VIMSS/ontology/Mechs/EdgeMech-storage-source-reconciliation-20261107`.
`check_storage_reconciliation_target_20261107.py` verified the branch and
canonical origin through CLAW's repository validator under the root-held lease.
The active census worktree was not edited. Census implementation/launcher,
Parquet read/write/schema helpers, packets and contract pins have no diff.
The migration repair adds no scientific review or publication authority.

## Review and regression checks

The initial independent acceptance review filed #14 before implementation.
Root review then filed #15 before its repair. Root and a separate native-adapter
agent reviewed the final frozen source/report changes read-only; neither found
a further blocking defect. The latter also independently rehashed all three
real migration runs and their input/output receipts.

- Focused storage/report suite: 41 passed before the additional report finding.
- Final report-specific regressions after #15: 19 passed.
- Final complete repository suite: **183 passed in 45.91 seconds**, once.
- Ruff over `src`, `tests` and `scripts/adhoc`: passed.
- Installed canonical contract check: passed at immutable CLAW
  `1b5391d083ba85ac94e5279c3cba25ac4fde243c`.

The retained
[`prove_storage_reconciliation_mutations_20261107.py`](../../scripts/adhoc/prove_storage_reconciliation_mutations_20261107.py)
ran four fresh-process negative controls. Removing each guard made its intended
regression fail: source/output comparison, missing report proof, manifest input
pin and migration input maps. The same-width header mutation remains otherwise
internally valid, so its rejection establishes the newly added boundary.
[The mutation receipt](storage-source-parity-20261107/mutation-proof.json) binds
the tested source hashes and records unchanged production files. Detailed
failure traces remain in `workspace/source-reconciliation-mutation-final-20261107/`.

## One real canary, then two layouts

An isolated `.venv` was installed with `uv sync --offline --extra dev`.
All three runs used the same `.venv/bin/python`, working directory, nonlogin
Bash shell, retained launcher and pinned input. First the default 16-bucket
canary ran end to end; its nonempty files, exact counters and five-table proof
were read from disk and accepted by the actual report driver. Only then did
the two- and 64-bucket benchmarks run, sequentially.

The launcher command was:

```sh
.venv/bin/python scripts/adhoc/run_storage_canary_20261107.py \
  --ledger /Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/culturebotai-claw-edge-curation-20261103/workspace/reports/edge-curation-20261103/snapshot-canary-review-fixes/ledger.sqlite \
  --export /Users/marcin/Documents/VIMSS/ontology/KG-Hub/KG-Microbe/culturebotai-claw-edge-curation-20261103/workspace/reports/edge-curation-20261103/snapshot-canary-review-fixes/snapshot \
  --ledger-sha256 85d0f98093a595308f9246cc9c517dbaf5ef26086d65650f0cff025609498ade \
  --output workspace/validation-20261107/storage-source-parity-canary \
  --buckets 16 --row-group-size 8192
```

Subsequent output names were `storage-source-parity-benchmark-2` with
`--buckets 2 --row-group-size 1024`, and `storage-source-parity-benchmark-64`
with `--buckets 64 --row-group-size 8192`. The source file was opened read-only
and its digest remained unchanged. All runs preserved 1,000 occurrences and
current decisions, one bundle/history/member, eleven metadata rows and five
coverage rows. Decisions remain 999 unprocessed plus one deferred, all withheld.
Empty observations, claims, reviews and evidence remain empty.

[Generated measurements](storage-source-parity-20261107.md) record exact
receipt, migration-receipt and artifact-manifest hashes. Byte-identical small
copies are retained in [the evidence directory](storage-source-parity-20261107/).
Bulk Parquet stays under each run's ignored `workspace/validation-20261107/`
directory. Prior outputs remain historical and were not overwritten. These
small-input measurements establish migration integrity and local layout costs;
they do not establish production throughput or compare old and new runtimes.
They ran on a shared host while the frozen full census was active. They do not
establish a performance improvement or select a production layout.

| Reviewed implementation | SHA256 |
| --- | --- |
| `src/edgemech/storage/__init__.py` | `cae90869b751ecae855a2c7be20bf26e24fc4e72ec36b95b11254c5f6e2e3353` |
| Storage canary launcher | `e6d942c3bd89b88c932a5212c5dc1e79c61c04fc3a94b573de39b7d3a5fadd3d` |
| Validation report driver | `f41ab7a2c52c20e1130bbbae623367525a38e6c77873ceea40782b6da46e09d3` |

## Packaging

`uv build --offline --out-dir dist/source-parity-final` built both artifacts.
The source archive was extracted into a new workspace directory; the changed
storage module and report driver matched the working files byte-for-byte, and
the retained launcher and routing configuration were present and nonempty.
Collection from the extracted archive found all **183 tests**. The complete
suite was not repeated there, and no package was published.

| Artifact | SHA256 |
| --- | --- |
| `edgemech-0.1.0-py3-none-any.whl` | `8689c9a81cb70c3a3d3ef1ec7ef186e054472c7f5409e847682114fef5141ea4` |
| `edgemech-0.1.0.tar.gz` | `d3747b30cd2a24eb66402c7a7c4308d487338d8ccb7e24f5447f072730efe909` |

Full-suite, build and extracted-collection logs remain at
`workspace/storage-source-parity-{full-pytest,build,sdist-collection}.log`.
Integration into the existing EdgeMech #2 PR is separate from approval to merge
that PR onto main.
