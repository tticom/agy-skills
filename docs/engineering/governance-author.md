Quickstart:

```bash
npx skills add mattpocock/skills --skill=governance-author
```

```bash
npx skills update governance-author
```

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/governance-author)

## What it does

Governance Author turns a maintainer decision into a bounded, executable task
promotion. It chooses the repository that owns the durable output before it
writes authority, preventing product design from leaking into governance and
preventing one role from activating its own successor.

## When to reach for it

Type `/governance-author`, or let the agent reach for it automatically when a
project has active-task records, fixed identities, repository ownership rules,
or candidate-to-task promotion. For executing the promoted work instead, use
[governed-development-loop](https://aihero.dev/skills-governed-development-loop).

## The authority packet

The skill produces one narrow authority packet: identity, role, repository,
branch, base, allowed files, acceptance, validation, non-goals, and a stop
condition. Its leading idea is **durable ownership**: the control record and
the work it authorises may belong in different repositories.

## It's working if

- a candidate is recorded without becoming executable by accident;
- durable product design lands in the product repository;
- governance tests distinguish the intended failure from malformed mocks;
- the governance author publishes one exact-head handback and stops.

## Where it fits

This is the governance step immediately before
[governed-development-loop](https://aihero.dev/skills-governed-development-loop)
and alongside [identity-safe-git](https://aihero.dev/skills-identity-safe-git).
See [ask-matt](https://aihero.dev/skills-ask-matt) for the complete map.
