---
name: handoff-bg
description: Hand the current conversation off to a fresh background subagent that picks up the work immediately across Antigravity (AGY), Codex, and Claude Code.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Write a handoff summary of the current conversation so a fresh agent can continue the work immediately in the background:

- **In Antigravity (`agy`)**: Call `invoke_subagent` with `Role: "<descriptive name>"` and `Prompt: "<handoff summary>"`.
- **In Codex & Agent-Skills harnesses**: Launch a background agent or sub-task seeded with the handoff summary.
- **In Claude Code**: Execute `claude --bg --name "<descriptive name>" "<handoff summary>"`.

Always set a descriptive name (e.g., `"Fix login bug"`) — it identifies the session in task managers and status indicators.

Include a "suggested skills" section in the summary, naming which skills the next agent should call the Skill tool for.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information, since the summary becomes the agent's prompt.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the summary accordingly.
