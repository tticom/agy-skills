---
name: cleanup
description: >-
  Agent Workspace Cleanup Skill. Use this skill when the user asks to clean up the workspace, remove stale review worktrees, or prune generated artifacts across the score2gp agent environments.
---

# Agent Workspace Cleanup

This skill safely identifies and removes stale Git worktrees, prunable metadata, generated artifacts, and untracked files across the agent identities without deleting active or uncommitted work.

## Usage

When the user asks to clean up the workspace, execute the cleanup script located in the `score2gp-agentops` repository:

```bash
python3 ./scripts/agent_workspace_cleanup.py
```

### Dry Run
To preview what will be removed without actually deleting anything, run with the `--dry-run` flag:
```bash
python3 ./scripts/agent_workspace_cleanup.py --dry-run
```

## Validation & Output

After running the script, it will generate a JSON receipt in the `projects/score2gp/runs/` directory detailing every preserved and removed path. You should summarize these results for the user and provide a link to the generated receipt file.
