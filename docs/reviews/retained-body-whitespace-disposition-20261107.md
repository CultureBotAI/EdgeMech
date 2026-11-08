# Retained PR-body whitespace disposition, 2026-11-07

The final staged whitespace check reports a terminal blank line in two retained
source PR-body snapshots:

- `docs/reviews/claw-962-body-admission-status-20261107.md`
- `docs/reviews/site-541-final-body-20261107.md`

Independent read-back confirmed that both still match the live submitted body
bytes. Their SHA256 values are respectively
`e19218fd1770e5308fa59302c21181464994d4a32e8ec484dcdf8108229eacb1`
and `cb853b080338bc713ee2561e25844eb394c5cb37f4eb32cef23a24ed99386b69`.

These are the retained submitted body texts, not executable code or generated
scientific artifacts. Keep their source bytes rather than silently normalizing
the provenance copies. This finding is triaged as not planned; it does not
weaken a CI gate or change the PR bodies' rendered meaning. All other final
changes are checked separately with these two exact paths excluded. No general
whitespace exclusion or repository configuration change is introduced.

The staged check's nonzero exit is therefore an explicit evidence-preservation
exception, not an all-files-clean claim. The single complete CI suite, full test
linting, artifact hashes and scientific acceptance checks remain required.
