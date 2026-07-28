# Evidence and falsification protocol

Use this protocol to decide whether evidence can support a review claim. Its purpose is to expose false-success tests: tests that pass while the claimed behavior is absent, bypassed, hardcoded, ambiguous, or order-dependent.

## Contents

1. Claim tracing
2. Discriminating assertions
3. End-to-end and dynamic-input claims
4. State distinctions
5. Boundary and scale tests
6. Collections and matching
7. Validation provenance
8. Approval questions

## 1. Claim tracing

Trace every material claim through four links:

```text
source input → production transformation → observable output → exact assertion
```

A missing link makes the claim `cannot verify`.

These are not substitutes for the chain:

- a test or function name;
- aggregate candidate counts;
- successful file creation;
- a mock that replaces the changed production seam;
- a manually reconstructed value when the claim says dynamically extracted;
- a PR or agent summary.

When only part of the chain is dynamic, state exactly which part. Do not promote “event coordinates are extracted” into “all geometry is dynamically extracted.”

## 2. Discriminating assertions

Ask: what smallest broken implementation would still pass?

Common non-discriminating patterns:

- `assert result is None or result == candidate`;
- asserting only non-`None`, truthiness, length, or file existence for a semantic claim;
- checking that a candidate was extracted but never passing it to changed production code;
- asserting a boundary “inside” input that succeeds without using the boundary;
- asserting only one ordering of a collection algorithm;
- comparing output to an oracle computed by copied implementation logic.

For each positive test, seek a negative control that differs in only the behavior-controlling fact.

Do not ban every disjunction mechanically. Reject it when the alternatives represent materially different specified outcomes.

## 3. End-to-end and dynamic-input claims

Inventory every claimed input:

| Claimed input | Actual source expression | Later overwritten or hardcoded? | Reaches changed function? |
|---|---|---|---|

Inspect unused extracted variables. Extraction followed by hardcoded substitution is not dynamic validation.

For fixture or integration claims, require the changed production function to consume the extracted values and produce the asserted semantic output. Aggregate extraction counts establish fixture presence only.

## 4. State distinctions

When the domain distinguishes states such as:

- absent;
- invalid;
- ambiguous;
- conflicting;
- fallback;
- valid;

require distinct representations and exact assertions for each. Confirm ambiguous/conflicting input cannot fall through to a valid default.

Exercise both returned-diagnostic and raised-error modes when both are public behavior.

## 5. Boundary and scale tests

For a threshold `t`, use samples whose result changes because of `t`:

- just inside: `t - ε`;
- exact boundary when inclusivity matters;
- just outside: `t + ε`.

For overlap extension, keep the candidate entirely outside the target and vary only the gap. A candidate that already crosses the target does not test the extension.

For scaled geometry:

- use non-zero offsets;
- test at least two scales plus baseline;
- distinguish normalized thresholds from absolute physical thresholds;
- test both sides at each scale;
- verify all claimed dimensions, not merely one representative dimension.

## 6. Collections and matching

For grouping, matching, assignment, and deduplication, inspect:

- input-order permutations;
- duplicate and near-duplicate values;
- one candidate competing for multiple targets;
- multiple candidates competing for one target;
- global assignment versus greedy local selection;
- ties and near-ties;
- irrelevant distant candidates;
- filtered candidates leaking into later ambiguity checks.

Fail-closed behavior is acceptable only when it is explicit and cannot be mistaken for valid evidence.

## 7. Validation provenance

For a live review, bind evidence to the exact reviewed head.

Check:

- full, exact head object ID;
- command and executable;
- test collection count;
- pass/skip/fail count;
- changed paths;
- whether the newly added tests are included in the full-suite count;
- whether the evidence comment was published after the head it pins.

Chat output is navigation, not durable evidence.

## 8. Approval questions

Before approval answer all of these with concrete locations:

1. What is the strongest plausible false-success implementation?
2. Which exact test would fail under it?
3. Does that test reach the changed production path?
4. Are its inputs derived from the claimed source?
5. Is its assertion exact and discriminating?
6. What relevant state, boundary, ordering, or conflict remains untested?
7. Does the durable evidence pin the live reviewed state?

Any unsupported material answer blocks approval.
