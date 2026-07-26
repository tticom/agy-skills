---
name: research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
---

Spin up a **background subagent** to do the research so the parent session stays available while it reads:

- **In Antigravity (`agy`)**: Call `invoke_subagent` using `TypeName: "research"` (or `TypeName: "self"`) with `Model: "flash"` or `"pro"`.
- **In Codex & Agent-Skills harnesses**: Spawn a background research subagent or sub-task.
- **In Claude Code**: Launch a background agent (`claude --bg`).

Its job:

1. Investigate the question against **primary sources** — official docs, source code, specs, first-party APIs — not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it under `docs/research/` or a sensible repo location and state the path.
