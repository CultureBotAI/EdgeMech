A read-only final workflow inspection found that `.github/workflows/tests.yml`
enumerates five individual test files in its Ruff command. The newer reader and
PR-readiness tests are therefore absent from the automated lint gate, even
though pytest discovers them. The README repeats the same partial command.

Use `ruff check src/edgemech tests scripts/adhoc` in both places. This keeps the
single complete pytest run and the existing `test` job/PR triggers unchanged;
it does not add a second full-suite requirement. The repair belongs in EdgeMech
PR #2 and requires a complete Ruff pass plus independent diff review.
