---
name: hard-review
description: Perform an exact-head hard review that includes the complete basic code review plus adversarial inspection of test-data provenance, real-world acceptance evidence, oracle independence, and production-code fixture coupling. Use for conversion fidelity, OMR, parsers, geometry, timing, matching, generated artifacts, private fixtures, empirical claims, or whenever synthetic, mocked, generated, or data-free tests could create false confidence.
---

# Hard review

First read and execute
[the complete basic review](../code-review/SKILL.md), including its exact-head
checks, code-sanity review, inline comments, mandatory PR summary, and reviewer
role firewall. This skill only adds gates; it never relaxes the basic review.

Read
[the evidence and falsification protocol](../code-review/references/evidence-falsification.md)
completely before evaluating tests or empirical claims.

## 1. Inventory changed behavior and tests

Build a claim ledger before accepting any test result:

| Material behavior | Production path | Test node | Data source | Oracle | Acceptance status |
|---|---|---|---|---|---|
| exact claim | changed seam and consumer | exact node | provenance classification | independent expected result | verified / contradicted / cannot verify |

Classify every changed or cited test as one of:

- `REAL_SOURCE_END_TO_END`: an actual real-world source artifact enters the
  production boundary under review;
- `REAL_SOURCE_EXTRACT`: data extracted from a real-world artifact with a
  reproducible extraction receipt and retained provenance;
- `SYNTHETIC_OR_MOCKED`: generated notation, invented coordinates, fabricated
  JSON, mocks, stubs, or reconstructed inputs;
- `DATA_FREE`: source existence, importability, schema shape, constant, refusal
  code, or control-flow test without representative domain data.

Synthetic and data-free tests carry zero acceptance weight for real-world
behavior. A changed domain or conversion test that substitutes synthetic,
mocked, generated, or data-free input for available real-source evidence is a
blocking finding and must be replaced. Permit such tests only for non-domain
infrastructure where real source data is genuinely inapplicable, and require an
explicit rationale. Every changed domain or conversion behavior requires a
data-bearing test derived from a genuine source and reaching the changed
production seam. A green synthetic-only suite is a blocking false-success mode.

Classify provenance by construction, not filename or author label. A PDF,
image, JSON file, or oracle created by a fixture generator for the change is
`SYNTHETIC_OR_MOCKED`; committing the generated binary does not make it a real
source. Expected output written by the same generator or derived from the
implementation is circular, not independent. When the task forbids synthetic
evidence, introducing it is itself a specification violation even if separate
real-source evidence also exists.

Inventory skips, xfails, deselections, and test deletions in the head delta.
Compare their guarded behavior with the base head. A new or broadened
suppression that hides an affected failure is blocking; a green aggregate
obtained through suppression is evidence of false success.

If a private in-situ test skips in public CI, verify the skip guard is narrow
and explicit, then personally run it in the authorized private-fixture
environment. A skipped test is not approval evidence.

## 2. Verify provenance and oracle independence

For every real-data test, trace:

```text
real source → production transformation → produced output → independent oracle → exact assertion
```

Require all links and an independent semantic oracle. In conversion systems:

- use the PDF or other source as input;
- use the reference `.gp` or equivalent only as a post-conversion oracle;
- never feed expected output, reference-derived timing, coordinates, hashes, or
  labels into the conversion path;
- compare semantic behavior such as bars, pitches, durations, tempo, tracks,
  fingering, grouping, and refusal state as applicable;
- reject output-exists, candidate-count-only, snapshot-presence, and aggregate
  pass-count assertions as fidelity proof.

When a test uses extracted real-source values, reproduce the extraction from
the pinned artifact. Hardcoded values accompanied only by a comment saying
“measured from fixture” remain synthetic evidence.

## 3. Prove production code is fixture-independent

Inspect all changed production files and their relevant callers for:

- private repository names, fixture paths, basenames, document titles, hashes,
  page numbers, exact coordinates, expected counts, or reference-output values;
- constants or branches chosen to make one named fixture pass;
- behavior selected by file identity rather than observable domain evidence;
- tests that monkeypatch away the changed production boundary;
- reference or private data copied into public source, snapshots, reports, or
  generated artifacts.

Run the fixture-coupling scanner when fixture roots are available:

```bash
python skills/engineering/hard-review/scripts/fixture_coupling_scan.py \
  --production <changed-production-file> [...] \
  --fixture-root <authorized-fixture-root> [...]
```

Treat its output as leads, not proof of safety. Manually inspect numeric and
semantic coupling that a lexical scanner cannot detect.

For every tolerance or heuristic, require a domain rationale plus examples on
both sides of the boundary from more than one real source when the claim is
general. One fixture may expose a bug but cannot establish a universal value.

## 4. Falsify the evidence

For each claim, name the smallest broken implementation that could still pass.
Verify the existing real-data assertion would fail under that defect. Inspect:

- absence versus ambiguity versus rejection;
- positive and negative controls;
- just-inside and just-outside boundaries;
- ordering, duplicate, scale, cardinality, and neighboring-item competition;
- fallback behavior and whether fallback masks loss of primary evidence;
- round-trip or semantic output, not only intermediate metadata.

For acceptance claims, explicitly challenge a constant-output implementation
and require a negative control differing only in the behavior-controlling fact.
Also inspect the changed production function and its direct caller for
undefined names, early returns, unreachable initialization, and mocked seams;
targeted green tests do not discharge this code-sanity check.

Run the assertion-smell scanner on changed tests:

```bash
python skills/engineering/code-review/scripts/assertion_smells.py \
  <changed-test-path> [...]
```

A clean scan does not justify approval.

## 5. Gate and publish

Request changes when any material behavior lacks real-source evidence, the
oracle contaminates production input, code is fixture-coupled, a skip prevents
private acceptance from running, or an assertion cannot distinguish the
claimed behavior from a plausible defect. Use `CANNOT_VERIFY` when required
private data or authority is unavailable.

For approval, the PR summary required by `$code-review` must use:

```text
<!-- reviewer-summary:hard:<full-head-sha> -->
Review level: HARD
```

It must also include the provenance classification for every material test,
the real artifacts personally exercised, the fixture-coupling result, the
strongest false-success mode tested, and specific residual risk.

For `APPROVE`, create the evidence packet outside the repository and publish
through the shared wrapper with `--level hard --packet <external-packet.json>`.
The wrapper applies the real-source and fixture-independence evidence gate
before writing any review metadata. For blocking verdicts, omit `--packet` but
still use the wrapper so the mandatory PR summary is published.

The reviewer remains comment-only. Do not add tests, reports, rules, prompts,
skills, or evidence files to the reviewed branch.
