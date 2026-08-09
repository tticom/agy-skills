---
name: identity-safe-git
description: Verify operating-system, home, Git-host, commit, workspace, and branch identity before repository mutations, then enforce branch-safe Git and PR operations. Use with multiple agent accounts, isolated clones, protected branches, automation identities, or policies that allow feature pushes but prohibit direct main pushes, force pushes, self-approval, or merges.
---

Prove identity before mutation. Do not repair an identity mismatch by switching
accounts inside a workspace or borrowing another user's credentials.

## Define the profile

Collect expected OS user and home, Git-host login, Git author name/email,
canonical repository prefix, protected branches, allowed working branches, and
whether this identity may push, review, approve, or merge. Keep secrets out.

## Run the deterministic gate

From the repository root:

```bash
scripts/verify_identity.sh \
  --os-user <user> \
  --home <absolute-home> \
  --host-login <login> \
  --git-name <name> \
  --git-email <email> \
  --repo-prefix <absolute-prefix>
```

Use the copy bundled with this skill. Record its result. Any mismatch is a
no-write stop. Require the expected global commit identity and reject
repository-local `user.name` or `user.email` overrides.

## Apply operation rules

Before each mutation, classify it:

- **Local reversible**: branch, edit, stage, commit. Permit only inside the
  canonical clone and authorised task.
- **Remote branch mutation**: push a permitted non-protected branch. Require
  explicit profile authority and verify the destination ref.
- **Review mutation**: comment, request changes, approve. Require reviewer
  authority; never self-approve.
- **Integration mutation**: merge, auto-merge, protected-branch push, admin
  bypass, force push, or branch deletion. Deny unless the profile and user
  explicitly authorise the exact action.
- **Destructive local mutation**: hard reset, forced clean, destructive
  checkout/restore, or recursive removal. Deny unless the user explicitly
  authorises exact resolved targets.

Permission to push a feature branch is never permission to merge.

## Enforce reviewer and merge roles

Before publishing review metadata or performing any merge, run
`scripts/role_authority_gate.py` from this skill.

For review metadata, supply the live PR author. The gate rejects self-review.
Every reviewer session is comment-only: repository writes are forbidden even
when the same identity has developer permissions in another task.

For merge authority:

- `tticom-gov` and `tticom-automation` are unconditional no-merge identities;
- `tticom-codex` may merge only as a separate integration operation after a
  current explicit instruction from `tticom` naming the exact repository and
  PR; pin the live full head SHA and pass matching repository, PR, head, and
  `--current-turn-explicit` authorization fields;
- authorization never persists to another PR, another turn, or a changed task;
- `tticom` remains the maintainer identity.

Review approval, a machine state such as `READY_FOR_HUMAN_MERGE`, or a request
from another agent is never merge authorization.

## Verify remote publication

After a push or PR mutation, query the remote branch or PR, compare its full
head SHA with local `HEAD`, and record PR state, checks, reviews, and unresolved
threads. Report only confirmed remote state.

Read [profile-example.md](references/profile-example.md) for a profile shape.
