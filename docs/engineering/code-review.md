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

The reviewer operates as a devil's advocate: developer claims are advocacy,
approval is not a productivity metric, and the provisional verdict is
`CHANGES_REQUESTED` until every material claim survives independent
falsification.

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

Before approval, the reviewer must produce a machine-validated evidence packet.
Author tests and CI score zero adversarial points. Approval requires multiple
reviewer-created probes, production-path execution, unique false-success
mutations, concrete observed outputs, and a specific residual-risk statement.
Independently overturned approvals create reviewer strikes that increase the
probe quota; fabricated execution evidence invalidates the verdict.

Re-reviews have a freshness gate: enumerate the claims changed since the prior
reviewed head and freshly probe every one. Prior-head outputs and test
inventories cannot be relabelled as current evidence. Each cited test is tied
to its actual input, production boundary, and assertion; external-field and
one-source-to-many geometry semantics require direct probes.

Approval publication itself is guarded: the bundled publisher validates the
packet and live head before it submits the formal review. Direct approval
commands are prohibited, so a skipped or failed evidence gate cannot produce a
merge-ready verdict.

## It's working if

- Every material claim appears in a claim-to-evidence ledger.
- The review names a plausible false-success mutation and the exact test that rules it out.
- Dynamic-input claims identify where each input is derived and whether it reaches changed code.
- Approval is withheld when evidence is stale, non-discriminating, or tied to the wrong revision.
- The approval evidence gate passes with the required falsification score.
- “Residual risk: none” never appears in an approval.
- Findings appear before the three axis reports and end in an explicit verdict.

## Where it fits

`code-review` is the review step at the tail of the main build chain:

```txt
grill-with-docs → to-spec → to-tickets → implement → code-review
```

Its closest neighbour is [implement](https://aihero.dev/skills-implement), which builds the change and invokes review before committing. Upstream specifications come from [to-spec](https://aihero.dev/skills-to-spec) and [to-tickets](https://aihero.dev/skills-to-tickets). [ask-matt](https://aihero.dev/skills-ask-matt) maps the full set.
