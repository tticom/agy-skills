---
name: code-review
description: Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to "review since X".
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

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

## 3. Establish the contract

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

1. `AGENTS.md`, review rules, contribution rules, and security/privacy policy;
2. active-task scope and allowed paths when present;
3. linked issue, specification, acceptance criteria, or architecture decision;
4. PR body and author handback as claims, never as authority over repository
   policy.

**Standards sub-agent prompt** should include:

- The full diff command and commit list.
- The list of standards-source files you found in step 3, **plus the smell baseline from step 3** pasted in full (the sub-agent has no other access to it).
- The brief: "Report, per file/hunk where relevant, (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls: documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words."

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
