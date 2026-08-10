---
name: publish-pr-handback
description: Validate and atomically publish a complete exact-head pull-request author handback. Use after an author pushes a new or revised PR head in a review-gated workflow, before claiming AWAITING_GOVERNANCE_REVIEW, or when repeated stale or malformed handback comments leave a dispatcher waiting.
---

# Publish PR Handback

Publish through the bundled script. Never type or paste the head SHA into a
free-form PR comment and call that a handback.

## Prepare the evidence packet

Create a JSON file with this shape:

```json
{
  "schema_version": "author-handback.v1",
  "task": "Task identifier and title",
  "repository": "owner/repo",
  "pr": 123,
  "head": "40-character SHA",
  "base": "40-character SHA",
  "changed_paths": ["path/from/live/pr"],
  "acceptance": [
    {
      "criterion": "Exact required observable",
      "status": "PASS",
      "command": "Command actually executed",
      "observed": "Exact observed result",
      "oracle": "Independent source of the expected result"
    }
  ],
  "review_findings": [
    {
      "finding": "Prior finding identifier or summary",
      "disposition": "What changed",
      "evidence": "Fresh exact-head evidence"
    }
  ],
  "remaining_risks": []
}
```

Derive `head`, `base`, and `changed_paths` from the live PR. Copy neither a
chat summary nor an earlier handback. Every acceptance item must identify the
final observable and an independent oracle. An exit code alone is not an
observable when the command is diagnostic or can succeed after partial work.

Use `FAIL` or `NOT_RUN` while diagnosing locally, but the publisher refuses
either status for a review-ready handback. Resolve the criterion or report a
blocked state without publishing `AWAITING_GOVERNANCE_REVIEW`.

## Publish atomically

Run from the clean author worktree:

```bash
python3 <skill-dir>/scripts/publish_handback.py \
  --repo owner/repo \
  --pr 123 \
  --expected-head "$(git rev-parse HEAD)" \
  --worktree "$PWD" \
  --packet /absolute/path/handback.json \
  --state AWAITING_GOVERNANCE_REVIEW
```

The script fails closed unless:

- the authenticated actor is the PR author;
- the PR is open and local branch/head equal the live branch/head;
- the worktree is clean;
- packet repository, PR, base, head, and changed paths equal live GitHub state;
- every acceptance entry is complete and `PASS`;
- the head remains unchanged through publication; and
- GitHub returns the exact generated marker and body.

The script generates the comment. Repeated execution on an unchanged head
updates the same marked comment rather than creating duplicates. Report review
readiness only after it prints `AUTHOR_HANDBACK_PUBLICATION=PASS`.

## Boundaries

This receipt proves publication integrity and packet completeness. It does not
prove that an acceptance claim is true. Independent reviewers must still run
their own probes and may overturn every author claim.
