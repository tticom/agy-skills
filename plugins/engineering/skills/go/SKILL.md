---
name: go
description: Start the Score2GP author-side governed dispatcher for the tticom-automation identity. Use only when the user explicitly asks to start or continue the next governed implementation action.
metadata:
  short-description: Run the Score2GP author dispatcher
---

# Score2GP author dispatch

This skill is the `/go` command for the Score2GP automation worker.

Run only in the dedicated `tticom-automation` Linux workspace. Verify the
identity and workspace against the Score2GP AgentOps profile before any
mutation. A mismatch is a no-write stop; never switch accounts or borrow
another identity's checkout.

From the `score2gp-agentops` repository, execute the identity-aware router:

```bash
python3 scripts/score2gp_dispatch.py --product ../score2gp --agentops . --json
```

The router selects the author bootstrap for `tticom-automation`. Treat its
result as authoritative. Follow only its returned action;
do not select a backlog item, replay a cached prompt, bypass a review or merge
gate, or run implementation from a Codex/reviewer workspace.
