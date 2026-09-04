# `/go`

`go` is the explicit Score2GP author-side Antigravity dispatch command. It is
available when the `go` skill is installed in the Antigravity engineering
plugin. It is not a Codex reviewer command.

Run it only as the `tticom-automation` identity. The skill executes:

```bash
python3 scripts/score2gp_dispatch.py --product ../score2gp --agentops . --json
```

The identity-aware router selects the author bootstrap, which performs
identity, cleanliness, authoritative-state, branch, and live-PR checks before
returning the next action. It does not authorize backlog selection, review
bypass, or merging. `/go` is not a general shell alias and is not available
until the skill installation is refreshed.
