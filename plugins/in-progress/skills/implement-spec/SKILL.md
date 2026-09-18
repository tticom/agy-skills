---
name: implement-spec
description: "Implement a specification in code."
disable-model-invocation: true
---

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The goal is a PR which implements the entire spec on a single branch.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

For the initial job definition, use `$agy-skills:to-spec` to synthesize the
approved conversation into a specification, then `$agy-skills:to-tickets` to
turn it into a dependency-aware ticket graph. `implement-spec` consumes those
artifacts; it does not invent product scope or replace the specification phase.

**Implementer subagents** should be run in the background where possible for **maximum concurrency**.

## Steps

1. Read the spec and tickets. Read enough to understand the task graph.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files - it should save its markdown notes in a directory outside the repo, accessible by all future subagents. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create a branch, and a draft PR. The PR should be marked as 'closing' the spec issue and tickets.

4. Use **implementer subagents** to implement each ticket. Each implementer subagent should work in its own worktree, on its own branch.

5. Once an **implementer subagent** completes, merge its work to the PR branch with a **merger subagent**.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete, run /code-review on the PR branch. Fix all issues raised by the code review in a single **implementer subagent**.

8. Mark the PR as ready for review.

9. Clean up all **implementer subagent** worktrees.

## Orca mode

When the target repository uses Orca, treat the repository's executable
authority and current live-state resolver as the control plane. The spec and
ticket graph are planning input. Before dispatching a ticket, Orca must
promote that ticket into its versioned authority and generate the bounded
assignment from fresh live state. Pass workers only that assignment and the
referenced prompt.

In Orca mode, preserve these boundaries:

- the job manifest may resolve the ready frontier but cannot authorise work;
- a worker edits only its assigned worktree and ticket scope;
- workers do not choose successors, change roles, review, approve, or merge;
- the controller rereads live state after every worker return and before every
  review or merge decision;
- exact-head validation, independent review, governance, and merge-controller
  policy remain in force.

If the repository provides a deterministic spec-job resolver, run it before
choosing the frontier. For Score2GP AgentOps the command is:

```bash
python3 scripts/agy_spec_job.py <job-manifest.yaml> --json
```

The resolver's output is a planning handoff to Orca, not a replacement for
`ORCHESTRATION_STATE.json` or `score2gp_orca_control.py`. The current Score2GP
policy remains one bounded task, one worker assignment, and one PR per cycle;
do not silently turn the integration-branch concept into merge authority.
