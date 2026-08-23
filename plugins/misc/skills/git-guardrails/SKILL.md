---
name: git-guardrails
description: Set up agent hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute across Antigravity (AGY), Codex, and Claude Code. Use when user wants to prevent destructive git operations or block git push/reset.
---

# Setup Git Guardrails

Sets up a PreToolUse / execution hook that intercepts and blocks dangerous git commands before the agent executes them.

## What Gets Blocked

- `git push` (all variants including `--force`)
- `git reset --hard`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- `git checkout .` / `git restore .`

When blocked, the agent receives a refusal message indicating it lacks authority to execute the command.

## Steps

### 1. Ask scope & harness target

Ask the user:
1. Target harness: **Antigravity (`agy`)**, **Codex / Agent-Skills**, or **Claude Code**?
2. Scope: **this project only** or **all projects (global)**?

### 2. Copy the hook script

The bundled script is at: [scripts/block-dangerous-git.sh](scripts/block-dangerous-git.sh)

Copy it to the target location based on harness and scope:

- **Antigravity (`agy`)**:
  - Project: `.gemini/antigravity/hooks/block-dangerous-git.sh`
  - Global: `~/.gemini/antigravity/hooks/block-dangerous-git.sh`
- **Codex / Agent-Skills**:
  - Project: `.agents/hooks/block-dangerous-git.sh`
  - Global: `~/.agents/hooks/block-dangerous-git.sh`
- **Claude Code**:
  - Project: `.claude/hooks/block-dangerous-git.sh`
  - Global: `~/.claude/hooks/block-dangerous-git.sh`

Make it executable with `chmod +x`.

### 3. Add hook to settings

Add to the appropriate harness settings file (`.gemini/antigravity/settings.json`, `.agents/settings.json`, or `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$PROJECT_DIR\"/.gemini/antigravity/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

If the settings file already exists, merge the hook into the existing `hooks.PreToolUse` array without overwriting existing settings.

### 4. Ask about customization

Ask if user wants to add or remove any patterns from the blocked list. Edit the copied script accordingly.

### 5. Verify

Run a quick test:

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>
```

Should exit with code 2 and print a BLOCKED message to stderr.
