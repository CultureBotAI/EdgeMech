Adversarial review of PR #59 found that `source_value` is checked against the
derived ontology object label rather than `fields.value`, the original source
value. A pinned source row whose literal is `succinic acid` but whose mapped
node is labeled `succinate` could pass a revision falsely declaring its source
value as `succinate`. Current three production rows do match, so this does not
invalidate those results.

Validate the original source value and applicable value encoding separately from
the display label. Add a regression with unchanged derived label and mismatched
raw value, plus an encoding mismatch. Priority P2.
