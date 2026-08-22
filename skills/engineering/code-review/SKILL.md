---
name: code-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\"."
---

# Basic code review

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

Require a live PR. If only a local branch or uncommitted diff exists, return a
pre-publication assessment or ask the author to publish it; do not open or alter
a PR under the reviewer role.

The issue tracker should have been provided to you. If `docs/agents/issue-tracker.md` is missing, tell the user to run `/setup-matt-pocock-skills`.

## 1. Establish reviewer authority

Resolve the Git-host identity and run the role gate:

Whatever the user said is the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). If they didn't specify one, ask for it.

Stop if the reviewer is also the PR author, the role gate fails, the workspace
is not the assigned review workspace, or repository policy requires a stronger
review level.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here, not inside two parallel sub-agents.

## 2. Pin the exact live revision

Query the hosting service for:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.), fetched via the workflow in `docs/agents/issue-tracker.md`.
2. A path the user passed as an argument.
3. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user where the spec is. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".

Fetch the head object without merging it. Check it out detached in the review
worktree. Require exact equality between the initial live head, handback head
when required, and local `HEAD`:

```bash
python skills/engineering/code-review/scripts/verify_review_head.py \
  --expected <full-live-head> --worktree <review-worktree>
```

Require a clean checkout before validation. List untracked files and compare
every fixture or artifact used by tests with `git ls-files`; an input that
exists only in the author's dirty worktree is absent from the reviewed change.
Run tests only from the detached exact-head checkout, never from the author's
working directory. If the clean checkout cannot reproduce the claimed command,
request changes or return `CANNOT_VERIFY` as appropriate.

On top of whatever the repo documents, the Standards axis always applies the
[code-smell contract](references/code-smell-contract.md). Read it completely.
A smell candidate is not automatically a violation: investigate it and classify
it as `NOT_PRESENT`, `SUSPECTED`, `CONFIRMED`, or `EXEMPT`. Under a repository
or user no-code-smells policy, every diff-introduced or materially worsened
`CONFIRMED` smell blocks approval. A repository rule may provide an explicit
exemption, but passing tests, subjective disagreement, or calling the smell
"residual risk" may not.

## 3. Establish the contract

1. `AGENTS.md`, review rules, contribution rules, and security/privacy policy;
2. active-task scope and allowed paths when present;
3. linked issue, specification, acceptance criteria, or architecture decision;
4. PR body and author handback as claims, never as authority over repository
   policy.

**Standards sub-agent prompt** should include:

- The full diff command and commit list.
- The list of standards-source files found in step 3, plus the complete
  code-smell contract (the sub-agent has no other access to it).
- The brief: "Report every documented-standard violation and every smell
  candidate per changed file/hunk. For each smell, apply the supplied
  definition and classify it `NOT_PRESENT`, `SUSPECTED`, `CONFIRMED`, or
  `EXEMPT`; record exact evidence, concrete impact, and correction or cited
  exemption. Under a no-code-smells policy, treat every diff-introduced or
  materially worsened confirmed smell as blocking. Do not report aesthetic
  preference as a smell and do not waive a smell merely because tests pass."

**Spec sub-agent prompt** should include:

Run the smallest relevant checks first, then the repository-mandated suite.
Do not treat a developer summary or aggregate pass count as execution evidence.
Record exact commands, exit codes, and observed failures.

Independently enumerate the mandated commands from the spec and repository
rules. Record each as `COMPLETED`, `FAILED`, `NOT_RUN`, or `TIMED_OUT`, with its
exit code and pass/fail/error/skip/xfail totals. Never translate a partial
selection, collection-only output, skipped module, still-running process, or
missing receipt into success. A required failure/error blocks approval.

Run `git diff --check` and the repository's declared compile, lint, type, and
static-analysis checks. For Python changes, `python -m compileall` is a useful
syntax baseline when available, but it does not replace production-path
execution or justify inventing an undeclared mypy gate.

Build a requirement-conformance matrix before the verdict. Every obligation
and prohibition must map to the actual diff, a final observable, and executed
evidence. A clean implementation of behavior that deviates from the contract
is `CHANGES_REQUESTED`.

This basic review verifies ordinary test coverage but does not certify test-data
provenance or fixture independence. If conversion fidelity, parsers, OMR,
geometry, matching, timing, generated artifacts, private fixtures, or empirical
claims are material, escalate to `$hard-review`.

## 5. Form findings and verdict

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings, because the two axes are deliberately separate (see _Why two axes_).

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

Each blocking finding must identify the exact path and line/hunk, observed or
deduced failure, governing requirement, and smallest acceptable correction.
Publish line-specific findings as inline PR review comments whenever a precise
changed line exists. Put cross-cutting findings in the formal review body.

Include the code-smell ledger defined by the smell contract whenever a
candidate was found. Under a no-code-smells policy, `APPROVE` is forbidden while
any diff-introduced or materially worsened smell remains `CONFIRMED` without a
cited repository exemption.

Choose exactly one verdict:

- `APPROVE`
- `CHANGES_REQUESTED`
- `CANNOT_VERIFY`

Re-query the live head immediately before publication. If it differs from the
reviewed head, publish nothing and restart.

## 6. Publish and prove the result

Prepare the formal body, summary, and optional inline-comment JSON outside the
reviewed repository. Publish them together through the guarded publisher:

```bash
python skills/engineering/code-review/scripts/publish_review.py \
  --repo <owner/repo> --pr <number> --expected-head <full-head-sha> \
  --level basic --verdict <APPROVE|CHANGES_REQUESTED|CANNOT_VERIFY> \
  --review-body-file <external-review-body.md> \
  --summary-file <external-summary.md> \
  [--inline-comments-file <external-inline-comments.json>]
```

The publisher creates the formal review and then always creates or updates one
PR issue comment containing:

```text
<!-- reviewer-summary:basic:<full-head-sha> -->
Review level: BASIC
Reviewed head: <full-head-sha>
Base: <full-base-sha>
Verdict: <APPROVE|CHANGES_REQUESTED|CANNOT_VERIFY>
Findings: <count and concise list>
Validation: <commands and observed results>
Residual risk: <specific remaining uncertainty>
```

Do not substitute a chat response, task-state update, committed review report,
or local Markdown file for this PR comment. On an unchanged head, update or
reuse the existing marked summary instead of creating comment spam.

Re-query reviews and comments and prove the formal verdict, inline comments,
and marked summary exist on the expected head.

Finally require:

- local `HEAD` still equals the reviewed head;
- `git status --porcelain=v1 --untracked-files=all` is still empty;
- no commit, push, ref update, merge, auto-merge, branch deletion, release, or
  repository-content API mutation was performed by the reviewer.

If a reusable process weakness was found, describe the proposed skill or rule
change in the mandatory PR summary. Never implement that improvement in the
reviewed repository or during the review session.
