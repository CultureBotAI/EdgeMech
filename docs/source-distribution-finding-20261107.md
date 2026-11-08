# Retain helper dependencies in the source distribution

The final package build includes `tests/test_validation_report.py` and vendored
ID/label tests but omits their `scripts/` dependencies. An extracted source
distribution therefore cannot collect the same validation tests that passed in
the repository. Include retained Python/shell helpers and routing configuration
in the source archive, then verify the archive contents and test collection.
The native runtime wheel does not need test-only helpers.
