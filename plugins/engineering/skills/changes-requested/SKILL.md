---
name: changes-requested
description: Address CHANGES_REQUESTED review verdicts on open pull requests. Ingest reviewer findings, reproduce defects on the reviewed head, apply minimal safe fixes, verify regressions, and hand back with evidence.
---

# Changes-Requested Remediation

Execute a disciplined remediation loop for an open pull request that received a `CHANGES_REQUESTED` review verdict from `/code-review`, `/hard-review`, `/devils-advocate-review`, or human maintainers.

## Core Rules

1. **Never amend or force-push** published review heads. Follow-up commits must be added on top of the branch.
2. **Never dismiss or self-resolve** a reviewer finding without a reproducing test and code evidence.
3. **Reproduce before fixing**: Write a discriminating negative test or minimal probe proving the defect on the reviewed head before modifying production code.
4. **Preserve task boundaries**: Fix only the cited defects and adjacent regressions. Do not widen task scope or invent architecture.
5. **Publish via handback**: Atomically return the PR to `AWAITING_GOVERNANCE_REVIEW` using `publish-pr-handback`.

---

## Remediation Workflow

```
Fetch Findings → Pin Reviewed Head → Reproduce Red → Fix Green → Pre-Flight → Handback
```

### 1. Ingest Review Findings

Query GitHub for the latest review and open comments on the PR:

```bash
python3 plugins/engineering/skills/changes-requested/scripts/fetch_review_findings.py \
  --repo <owner/repo> \
  --pr <number> \
  --output scratch/review-remediation-ledger.md
```

Verify:
- PR is open and branch matches.
- `Reviewed Head` equals the commit SHA evaluated in the latest review.
- Every inline comment and contradiction ledger item is accounted for.

### 2. Pin the Author Worktree

Ensure the local worktree is clean and on the exact PR branch:

```bash
git checkout <pr-branch>
git pull --ff-only
test "$(git rev-parse HEAD)" = "<reviewed-head-sha>"
git status --porcelain=v1
```

If local commits exist beyond the reviewed head, inspect them before proceeding. Do not build fixes on uncoordinated branch state.

### 3. Build the Remediation Plan

For each unresolved finding, identify:
1. **Root cause**: The exact condition causing failure (e.g. empty collection passing `all()`, dropped status filter, branch contamination).
2. **Reproduction**: A focused test that fails at the current reviewed head (`RED`).
3. **Minimal fix**: The smallest safe change satisfying the requirement and preserving fail-closed behavior.
4. **Negative controls**: Values that must remain rejected.

### 4. Execute Red-to-Green Remediation

For each finding:

1. **Write the reproduction test**:
   - Place tests at the public interface/production seam.
   - Run the test against the unmodified code; confirm it **fails** as expected.
2. **Apply the minimal correction**:
   - Modify only authorized files inside task scope.
   - Run the test again; confirm it **passes** (`GREEN`).
3. **Check adjacent boundaries**:
   - Test zero, one, many cases.
   - Test boundary values (`t - ε`, `t`, `t + ε`).
   - Check that valid inputs are not broken and invalid inputs do not fall through to defaults.

### 5. Clean-Head Pre-Flight

Before committing:

```bash
# 1. No untracked junk
git status --porcelain=v1 --untracked-files=all

# 2. No whitespace or formatting errors
git diff --check origin/main...HEAD

# 3. Linter and typechecker
# (Run repository-mandated lint and type checks)

# 4. Full test suite
# (Run repository-mandated full test suite)
```

Every mandated test command must complete with exit code 0, with 0 failures and 0 unexpected errors. Skips or xfails must be explicitly justified.

### 6. Commit and Push

Stage and commit follow-up changes with clear message tracing to review findings:

```bash
git add <modified-files>
git commit -m "fix: address review findings on <finding-summary>"
git push origin <pr-branch>
```

Record the new branch head SHA (`NEW_HEAD=$(git rev-parse HEAD)`).

### 7. Publish PR Handback

Construct an `author-handback.v1` packet (see `publish-pr-handback`) populating `review_findings`:

```json
{
  "schema_version": "author-handback.v1",
  "task": "<task-id>",
  "repository": "<owner/repo>",
  "pr": <pr-number>,
  "head": "<new-head-sha>",
  "base": "<base-sha>",
  "changed_paths": [...],
  "validation_runs": [...],
  "acceptance": [...],
  "review_findings": [
    {
      "finding": "Inline comment 4043924108: allowed_paths [] accepted",
      "disposition": "Enforced non-empty list and stripped string validation in _as_strings()",
      "evidence": "tests/test_agy_spec_job.py::test_empty_contracts_rejected PASS"
    }
  ],
  "remaining_risks": ["..."]
}
```

Publish atomically using `publish_handback.py`:

```bash
python3 plugins/engineering/skills/publish-pr-handback/scripts/publish_handback.py \
  --repo <owner/repo> \
  --pr <pr-number> \
  --expected-head "$NEW_HEAD" \
  --worktree "$PWD" \
  --packet /path/to/handback.json \
  --state AWAITING_GOVERNANCE_REVIEW
```

Confirm `AUTHOR_HANDBACK_PUBLICATION=PASS` is printed. Stop and wait for independent re-review.
