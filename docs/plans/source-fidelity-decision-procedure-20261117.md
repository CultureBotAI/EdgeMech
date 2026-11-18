# Source-fidelity decision procedure

This case-neutral clarification addresses [#205](https://github.com/CultureBotAI/EdgeMech/issues/205).
It supplements the common occurrence-review rubric; it does not change the
categories, original propositions, calibration thresholds or completed results.
It must be reviewed and separately pinned before use in a future scientific
package. It is not a launch authorization.

## Establish the comparison before choosing a category

Write down the exact original assertion: subject, predicate, object, original
definitions, qualifiers, aggregation level and assertion basis. Separately write
what the identified source instance asserts. Source fidelity compares those two
meanings at the **same stated scope**. It does not test the independent truth of
the source, or merely whether the identifiers and text survived copying.

List the dependencies needed to interpret that comparison:

1. The exact source version, record, selected field and its occurrence linkage.
2. The source field's meaning, polarity, units, statistics and relevant conditions.
3. The participating identity chain, including the entity to which the source
   assigns the datum. A code-selected identifier and the actual datum's referent
   are separate dependencies when the source mixes identities.
4. The original endpoint and predicate meanings, with independent version-bound
   authorities where those meanings are necessary to the comparison.
5. Any selection, normalization, aggregation or mapping rule necessary to
   establish what was transferred or how its meaning changed.

For each dependency, record its evidence IDs, whether it is established,
conflicting or missing, and why it is necessary. Do not require an unrelated
identity, biological experiment or reconstruction of the entire build merely
because it exists elsewhere in the source record. Conversely, an exact row
hash cannot establish an ambiguous field meaning or identity association.

## Use the proof route that answers the dependency

**Direct semantic comparison** is possible when the source assertion, its
linkage to this occurrence, participating identities and original target
meaning are independently established. Compare them directly. A complete
historical execution trace is not an additional requirement when it would add
nothing to those established dependencies. This route can establish faithful
preservation of an erroneous source assertion: its independent correctness
remains a separate judgment. A coincidental matching row or a plausible source
candidate is insufficient to establish the linkage.

**Transformation-dependent comparison** is needed when the selected field,
identity, polarity handling, statistic or mapping is uncertain. Bind the
relevant rule and inputs. Inspect or replay the actual owner implementation at
a stated version, with the original source and mapping/ontology inputs needed
by that path. A later implementation, related synonym, successful ID hash or
handwritten simulation cannot alone prove the historical rule. State precisely
what a bounded replay establishes and what it omits. An unrecovered dirty build
limits a historical execution claim; it does not erase a separately established
bounded source-to-target comparison.

Both routes require a semantic comparison. Neither a successful replay nor
copied bytes establish that the translation preserves meaning. A producer rule
can itself introduce a semantic error. Do not impose a trace requirement on one
case while dispensing with the same necessary dependency in another.

## Apply the existing categories

| Category | Decision at the declared source-fidelity scope |
| --- | --- |
| `SUPPORTED` | The necessary dependencies are established, and the original assertion preserves the source's meaning, identity association, polarity, specificity and qualifiers. |
| `CONTRADICTED` | Established witnesses demonstrate a change or loss of represented meaning. Name that change and the evidence establishing the source-to-occurrence linkage. This category can describe a proven unjustified narrowing; it does not assert the narrower biological proposition is false. |
| `NOT_ASSESSABLE` | At least one necessary dependency is missing or conflicting, so the semantic comparison cannot be completed. Name the dependency and the smallest witness that could resolve it. An unproved transformation story is not a demonstrated defect. |
| `UNASSESSED` | The assessment was not performed; this cannot remain in a completed initial matrix. |

Missing support for a narrower biological claim is not evidence of its opposite.
Likewise, a generic label in a partial source view does not establish the full
meaning of the source field. Distinguish an established source meaning that an
established mapping exceeds from a source meaning or selection that remains
unknown. If both preservation and mismatch remain plausible because a necessary
dependency is unknown, retain that uncertainty.

An endpoint-category or predicate-domain defect affects source fidelity only
when it changes the represented source meaning. Explain that connection;
never copy a relation or node verdict into this axis automatically. A report-only
assertion stays report-only only when that is the original proposition. Do not
recast a biological assertion or narrow the assessed proposition to make a
resolved category save successfully. Evidence for literal transfer alone does
not establish an unqualified claim that the entire source assertion is faithful.

## Bind evidence without confusing completeness and sufficiency

Every witness used by a judgment must be explicitly bound to that axis in the
authored draft, canonical review, matrix and frozen evidence inventory. Record
the original input identity, source kind, version, case role, source locator and
inspected extent. Include relevant contrary witnesses. A rationale mentioning a
source does not bind it. Later additions belong to a separately identified stage.

Record these outcomes separately:

- **Binding completeness:** all cited witnesses and roles are present, pinned
  and replayable. This is an engineering property of the package and authored
  review, not a verdict about entailment.
- **Semantic sufficiency:** the necessary dependencies are established and the
  stated comparison follows from the evidence. This requires scientific review.
- **Calibration readiness:** the protocol's original scientific, blinding and
  operational prerequisites are met. Complete manifests or successful saves do
  not establish readiness, and unresolved dependencies remain visible.

Use missing evidence to guide recovery, not to optimize labels or replace
difficult occurrences. Do not change denominators, resolution floors or
historical ratings. A new package or replay never repairs a completed round's
exposure or outcome.
