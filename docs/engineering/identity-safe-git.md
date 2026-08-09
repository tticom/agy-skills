Quickstart:

```bash
npx skills add mattpocock/skills --skill=identity-safe-git
```

```bash
npx skills update identity-safe-git
```

[Source](https://github.com/mattpocock/skills/tree/main/skills/engineering/identity-safe-git)

## What it does

`identity-safe-git` verifies the operating-system user, home, Git-host login,
commit identity, workspace root, and branch permissions before mutations.

It permits explicitly authorised feature-branch work while keeping protected
branches, force pushes, self-approval, merges, and destructive operations as
separate permissions.

The role authority gate makes reviewer sessions comment-only, permanently
denies merge authority to `tticom-gov` and `tticom-automation`, and permits
`tticom-codex` to merge only after a current explicit instruction from `tticom`
identifies the exact repository and PR.

## When to reach for it

Type `/identity-safe-git`, or the agent reaches for it automatically in
multi-account workspaces, automation clones, protected repositories, or
governed PR workflows.

## Identity before authority

The leading rule is **identity before authority**. A valid task does not make
the wrong account or wrong clone safe. A mismatch stops writes rather than
triggering an in-place account switch.

## It's working if

- the deterministic gate reports one canonical identity and workspace;
- branch pushes and merges are evaluated separately;
- published remote state is re-read and matched to local `HEAD`;
- credentials never cross account homes.

## Where it fits

This is the identity gate used by
[governed-development-loop](https://aihero.dev/skills-governed-development-loop).
It complements setup-time hooks without replacing project policy. See
[ask-matt](https://aihero.dev/skills-ask-matt) for the whole map.
