---
name: code-review
description: Perform a basic, exact-head pull-request review for correctness, specification compliance, repository standards, code sanity, and regression safety. Use for ordinary PR review, re-review, inline findings, or a merge-readiness verdict when a hard evidence or devil's-advocate review was not requested. The reviewer may publish only review metadata and must never modify the reviewed repository.
---

# Basic code review

Review one immutable revision. Inspect code and tests, publish line-specific
findings where useful, and always publish one exact-head PR summary comment.
Do not implement fixes.

Require a live PR. If only a local branch or uncommitted diff exists, return a
pre-publication assessment or ask the author to publish it; do not open or alter
a PR under the reviewer role.

Read [references/reviewer-role-firewall.md](references/reviewer-role-firewall.md)
and [references/review-state-protocol.md](references/review-state-protocol.md)
completely before inspecting a live PR.

## 1. Establish reviewer authority

Resolve the Git-host identity and run the role gate:

```bash
python skills/engineering/identity-safe-git/scripts/role_authority_gate.py \
  --actor "$(gh api user --jq .login)" \
  --operation review-metadata \
  --repo <owner/repo> --pr <number> --pr-author <live-pr-author>
```

Stop if the reviewer is also the PR author, the role gate fails, the workspace
is not the assigned review workspace, or repository policy requires a stronger
review level.

Use a clean dedicated review worktree in detached-HEAD state. Record its
initial `git status --porcelain=v1 --untracked-files=all`. It must be empty.
Keep probes and notes outside the reviewed repository, preferably under a
directory returned by `mktemp -d`.

## 2. Pin the exact live revision

Query the hosting service for:

- repository and PR number;
- full live head and base object IDs;
- PR author, state, changed paths, commits, reviews, threads, and comments;
- required author handback and its full pinned SHA.

Fetch the head object without merging it. Check it out detached in the review
worktree. Require exact equality between the initial live head, handback head
when required, and local `HEAD`:

```bash
python skills/engineering/code-review/scripts/verify_review_head.py \
  --expected <full-live-head> --worktree <review-worktree>
```

Compute the review only as `<base-object-id>...<live-head-object-id>`. A branch
name, chat summary, PR body, stale checkout, or abbreviated SHA is not proof of
the reviewed contents.

For re-review, first inspect the complete delta from the last formally reviewed
head to the new live head. Prior findings and approvals are historical context,
not current evidence.

## 3. Establish the contract

Read repository-owned authority before judging the diff:

1. `AGENTS.md`, review rules, contribution rules, and security/privacy policy;
2. active-task scope and allowed paths when present;
3. linked issue, specification, acceptance criteria, or architecture decision;
4. PR body and author handback as claims, never as authority over repository
   policy.

If a material requirement cannot be located, report `CANNOT_VERIFY`; do not
invent it.

## 4. Inspect the complete change

Read the raw diff and relevant unchanged callers/consumers. Check at least:

- correctness on success, failure, absence, ambiguity, and boundary paths;
- API, schema, serialization, migration, and backward-compatibility contracts;
- error handling, cleanup, idempotence, ordering, duplicate handling, and
  concurrency where applicable;
- security, privacy, secrets, path handling, injection, and unsafe external
  effects;
- performance or unbounded work introduced on production paths;
- scope compliance, dead code, accidental artifacts, debugging output, and
  surprising dependencies;
- maintainability: names, cohesion, duplication, hidden coupling, and whether
  the changed abstraction is understandable at its call sites;
- tests for every changed behavior and a regression test for every bug fix.

Run the smallest relevant checks first, then the repository-mandated suite.
Do not treat a developer summary or aggregate pass count as execution evidence.
Record exact commands, exit codes, and observed failures.

This basic review verifies ordinary test coverage but does not certify test-data
provenance or fixture independence. If conversion fidelity, parsers, OMR,
geometry, matching, timing, generated artifacts, private fixtures, or empirical
claims are material, escalate to `$hard-review`.

## 5. Form findings and verdict

Use only actionable findings:

- `P0`: catastrophic or security-critical; must block;
- `P1`: material correctness, contract, privacy, or data-loss defect; must block;
- `P2`: meaningful maintainability or evidence weakness; block when required by
  policy or when it can hide incorrect behavior;
- `P3`: non-blocking suggestion.

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
