---
name: durable-handoff
description: Write a durable, repository-owned handoff tied to exact revisions and evidence without duplicating specs, diffs, or reports. Use when work must survive conversation loss, cross agent or identity boundaries, accompany a PR, or record the state of a governed development task.
---

Create durable project state. Do not use this skill merely to compact a
conversation; use `handoff` for a temporary session bridge.

## Choose the destination

Prefer the repository and path declared by the project profile. Never write
durable operational state into a product repository when a separate governance
or operations repository owns it. If no durable destination is configured, ask
before creating one.

## Verify state

Read live state rather than copying an agent summary:

- repository, branch, base SHA, local HEAD, and remote HEAD;
- worktree status and changed paths;
- PR URL, state, checks, reviews, and unresolved threads;
- exact validation commands and results;
- active task, authority source, and required next gate.

If local and remote heads differ, label the work unpublished and do not claim
the PR represents it.

## Write a compact record

Include purpose and outcome, exact repository revisions including the skills
revision, verified versus reported evidence, changed and frozen paths,
unresolved risks and comments, and the exact next authorised action.

Reference existing specs, decisions, reports, PRs, and commits by path or URL.
Do not paste their contents. Redact credentials, private paths, personal data,
and private input details.

Use [template.md](references/template.md) as the minimum shape.

## Verify the handoff

Reread it as a fresh agent. Confirm every next action is executable or
explicitly blocked, no candidate is presented as authority, and every SHA is
full and matches live remote state.
