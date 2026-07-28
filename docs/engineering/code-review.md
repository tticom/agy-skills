Quickstart:

```bash
npx skills add mattpocock/skills --skill=code-review
```

```bash
npx skills update code-review
```

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/code-review)

## What it does

`code-review` reviews a diff against a fixed point along three independent axes: **Standards**, **Spec**, and **Evidence/Falsification**. The third axis asks whether the supplied tests and artifacts could distinguish the claimed behavior from a plausible broken implementation.

It treats summaries, test names, and green suites as untrusted claims. Approval requires tracing each material claim through production code to a discriminating assertion or inspected artifact.

## When to reach for it

Type `/code-review`, or the agent reaches for it automatically when you ask to review a branch, pull request, work-in-progress change, or anything “since X”.

Reach for it when a diff needs a merge decision, especially when it carries empirical, end-to-end, boundary, scale, matching, parser, or generated-artifact claims. For building the behavior test-first, use [tdd](https://aihero.dev/skills-tdd); for implementing a complete spec, use [implement](https://aihero.dev/skills-implement).

## Prerequisites

The **Spec** axis needs an originating issue, PRD, or specification. Issue-tracker wiring comes from [setup-matt-pocock-skills](https://aihero.dev/skills-setup-matt-pocock-skills). Without a spec, that axis reports the limitation instead of inventing requirements.

## Three axes, one approval gate

**Standards** checks documented conventions and a labelled Fowler smell baseline. **Spec** checks whether the required behavior is complete and correctly implemented. **Evidence/Falsification** builds a claim ledger and asks what smallest broken mutation might still pass.

The axes run independently so a clean implementation cannot hide a spec failure and a faithful implementation cannot hide weak evidence. The primary reviewer then inspects the raw production path and assertions before issuing a verdict. A delegated report is evidence-gathering, not an approval.

## Falsification, not test counting

The leading idea is **falsification**. A test earns evidentiary weight only when its inputs reach the changed production path and its assertion changes under the relevant defect.

The skill looks for hardcoded substitutes in claimed dynamic tests, assertions that accept both success and failure, boundary samples that do not depend on the boundary, and ordering or duplicate sensitivity in collection logic. It includes an advisory assertion-smell scanner, but a clean scan never proves adequacy.

## It's working if

- Every material claim appears in a claim-to-evidence ledger.
- The review names a plausible false-success mutation and the exact test that rules it out.
- Dynamic-input claims identify where each input is derived and whether it reaches changed code.
- Approval is withheld when evidence is stale, non-discriminating, or tied to the wrong revision.
- Findings appear before the three axis reports and end in an explicit verdict.

## Where it fits

`code-review` is the review step at the tail of the main build chain:

```txt
grill-with-docs → to-spec → to-tickets → implement → code-review
```

Its closest neighbour is [implement](https://aihero.dev/skills-implement), which builds the change and invokes review before committing. Upstream specifications come from [to-spec](https://aihero.dev/skills-to-spec) and [to-tickets](https://aihero.dev/skills-to-tickets). [ask-matt](https://aihero.dev/skills-ask-matt) maps the full set.
