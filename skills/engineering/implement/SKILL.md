---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, run an author self-check against the specification and repository
validation contract. Do not invoke a reviewer skill, publish a formal review,
or approve your own work.

Commit and publish the authorized branch, then stop for an independent
`/code-review`, `/hard-review`, or `/devils-advocate-review` by another identity.
