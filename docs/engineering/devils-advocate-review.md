Quickstart:

```bash
npx skills add tticom/agy-skills --skill=devils-advocate-review
```

## What it does

`devils-advocate-review` performs both the basic and hard reviews, starts from
`CHANGES_REQUESTED`, and treats every developer and prior-reviewer assertion as
unverified advocacy.

It builds a contradiction ledger, creates independent probes outside the
reviewed repository, replays earlier counterexamples at the current exact head,
and attacks each remediation for adjacent failures. It approves only when it
cannot disprove any material claim and all remaining claims have complete
real-source production-and-oracle traces.

The reviewer remains comment-only and records findings through inline comments,
a formal verdict, and a mandatory exact-head PR summary.
