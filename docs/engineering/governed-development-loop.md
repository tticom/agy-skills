Quickstart:

```bash
npx skills add mattpocock/skills --skill=governed-development-loop
```

```bash
npx skills update governed-development-loop
```

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/governed-development-loop)

## What it does

`governed-development-loop` executes one authorised task from pinned starting
state to an independently reviewable remote head.

It does not decide what a project permits. A project profile owns policy; the
skill owns the reusable execution, evidence, publication, and stop sequence.

## When to reach for it

Type `/governed-development-loop`, or the agent reaches for it automatically
when a project has an active-task pointer, fixed scope, separate reviewer, or
one-PR-at-a-time governance.

Use [implement](https://aihero.dev/skills-implement) when an ordinary settled
spec needs no external governance profile.

## Pinned authority

The loop's leading idea is **pinned authority**: exact task, base revision,
skills revision, identity, and permitted paths are fixed before a write.
Backlogs and suggested next steps remain information, not permission.

## It's working if

- one task produces one bounded PR;
- evidence names the exact remote head;
- author and reviewer responsibilities remain separate;
- the agent stops at the declared review gate.

## Where it fits

This is a governed alternative to the ordinary implementation chain. It
composes [identity-safe-git](https://aihero.dev/skills-identity-safe-git),
[durable-handoff](https://aihero.dev/skills-durable-handoff), and
[code-review](https://aihero.dev/skills-code-review). See
[ask-matt](https://aihero.dev/skills-ask-matt) for the whole map.
