Quickstart:

```bash
npx skills add tticom/agy-skills --skill=code-review
```

## What it does

`code-review` is the basic reviewer contract. It pins the exact live PR head,
checks the originating specification and repository standards, inspects the
complete production diff and callers, runs relevant validation, and reports
actionable code-sanity findings.

It publishes inline comments for line-specific defects, one formal verdict,
and one marked exact-head PR summary. It never modifies the reviewed repository.

Use `hard-review` when real-world data, generated artifacts, parsers, OMR,
timing, geometry, or fixture independence matter. Use
`devils-advocate-review` for high-risk or disputed work.

## Role safety

All reviewer levels are comment-only. Reviewers may fetch, inspect, test, and
create external temporary probes. They may not patch, commit, push, update the
PR branch, store review reports on it, or merge during the review.

`tticom-gov` and `tticom-automation` can never merge. `tticom-codex` requires a
current explicit instruction from `tticom` naming the exact repository and PR,
and performs that merge as a separate integration operation.
