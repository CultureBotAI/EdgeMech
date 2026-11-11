Adversarial review of PR #59 found a provenance race in
`src/edgemech/chemical_scope_review.py`: the revision JSON is parsed before its
first hash is captured. A concurrent edit between parsing and final input-pin
construction can produce annotations from version A while recording version B's
hash. The final check sees B unchanged, and canonical adjudication and coverage
accept the incorrect provenance binding.

Hash the exact bytes read for parsing before applying revisions, then retain the
post-build drift check. Add a mutation regression that changes the revisions file
during cohort loading and verifies that no annotations are published. Priority P2.
