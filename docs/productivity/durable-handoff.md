Quickstart:

```bash
npx skills add mattpocock/skills --skill=durable-handoff
```

```bash
npx skills update durable-handoff
```

[Source](https://github.com/mattpocock/skills/tree/main/skills/productivity/durable-handoff)

## What it does

`durable-handoff` records repository-owned project state tied to exact local
and remote revisions, evidence, risks, and the next authorised action.

It does not compact a conversation. For a temporary bridge into another
session, use [handoff](https://aihero.dev/skills-handoff).

## When to reach for it

Type `/durable-handoff`, or the agent reaches for it automatically when state
must survive conversations, agent identities, PR review cycles, or unattended
development runs.

## Revision-pinned state

The leading idea is **revision-pinned state**. Existing specs, reports, diffs,
and decisions are referenced rather than copied; volatile repository and PR
facts are independently reread.

## It's working if

- every SHA is full and matches live state;
- verified evidence is distinguished from author reports;
- candidates are not presented as authority;
- a fresh agent can execute the stated next action or see the exact blocker.

## Where it fits

This is the durable close-out used by
[governed-development-loop](https://aihero.dev/skills-governed-development-loop).
Its sibling [handoff](https://aihero.dev/skills-handoff) crosses context
windows without creating project evidence. See
[ask-matt](https://aihero.dev/skills-ask-matt) for the whole map.
