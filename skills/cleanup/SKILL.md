---
name: cleanup
description: >-
  Agent Workspace Cleanup Skill. Use this skill when the user asks to clean up the workspace, remove stale review worktrees, or prune generated artifacts across the score2gp agent environments.
---

# Agent Workspace Cleanup

This skill safely identifies and removes stale Git worktrees, prunable metadata, generated artifacts, and untracked files across the agent identities without deleting active or uncommitted work.

## Usage

When the user asks to clean up the workspace, execute the cleanup script from the `agy-skills` repository root:

```bash
python3 plugins/engineering/skills/agent-workspace-cleanup/scripts/agent_workspace_cleanup.py
```

### Dry Run
To preview what will be removed without actually deleting anything, run with the `--dry-run` flag:
```bash
python3 plugins/engineering/skills/agent-workspace-cleanup/scripts/agent_workspace_cleanup.py --dry-run
```

## Validation & Output

After running the script, it will generate:

- a JSON receipt in `<workspace>/agy-logs/cleanup-receipts/` (or the path
  defined by `CLEANUP_RECEIPT_DIR`) detailing every preserved and removed path;
- a human-readable checkout map at
  `<workspace>/agy-logs/workspace-state/latest.md`, including branch, HEAD,
  cleanliness, and the active-task pointer.

Summarize the receipt and provide links to both artifacts.
