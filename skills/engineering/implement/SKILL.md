---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the repository's
mandated full test suite once at the end. A test command counts as run only
after it finishes and its exit code and complete pass/fail/error/skip/xfail
totals are captured. Starting it, collecting tests, running a smaller subset,
relying on CI, or citing an earlier head does not count.

Do not claim completion, success, green status, or review readiness when a
required command was not run, did not finish, exited non-zero, or contains an
unexpected failure/error. Report `FAILED`, `NOT_RUN`, `BLOCKED`, or `TIMED_OUT`
literally and stop. Never add or widen skips/xfails merely to turn a failing
aggregate green.

Classify acceptance inputs as real-source, real-source extract,
synthetic/mocked, or data-free. If the contract requires genuine-source
evidence or forbids synthetic data, generated PDFs, invented coordinates or
JSON, reconstructed inputs, and generator-authored expected output are not
permitted substitutes. If the genuine source or independent oracle is
unavailable, report `BLOCKED`; do not manufacture one.

## Prove external data assumptions first

Before implementing a heuristic that depends on an external library, file
format, API, parser, or downstream schema, inspect representative live data at
the exact production boundary. Use a disposable scratch probe outside tracked
source, record the library/runtime version, input provenance, command, and
observed field values, types, units, cardinalities, and absent/degenerate cases.
Derive the implementation rule from those observations and the authoritative
contract. Documentation or intuition alone is insufficient when the behavior
is cheaply observable.

Do not promote one observation into a universal heuristic. Exercise multiple
genuine sources or cite a domain invariant, and test both sides of every chosen
boundary. If live data contradicts the proposed design, stop and return the
evidence rather than coding around the discrepancy.

## Trace the final production effect

A passing helper or unit test does not complete a user-facing feature. Trace
the changed value through each production handoff to its final consumer and
user-visible artifact. Verify that the normal entrypoint consumes the new
value, no later transformation drops or overwrites it, and the final output
contains the exact required semantic result. Include a closest negative control
that reaches the same path but must not produce that result.

For pipeline, parser, conversion, serialization, or integration work, run at
least one genuine-source end-to-end acceptance test unless the contract
explicitly says otherwise. When authority or required private data prevents
that run, the result is `BLOCKED` or `NOT_RUN`, never complete.

Once done, run an author self-check against the specification and repository
validation contract. Do not invoke a reviewer skill, publish a formal review,
or approve your own work.

Build a requirement ledger before handback. For every obligation record the
changed production path, final observable, test node, input provenance,
independent oracle, exact-head command, and observed result. A deviation,
missing production-path test, unexecuted command, synthetic-only evidence
where real-source evidence is required, or non-independent oracle leaves the
requirement unmet. Do not relabel it as a limitation while claiming completion.

Immediately before publication, run a clean-head pre-flight:

1. `git status --porcelain=v1 --untracked-files=all`; every required source,
   fixture, oracle, and generated input must be intentionally tracked, and no
   unexplained local file may contribute to a passing test.
2. `git diff --check` against the review base.
3. Repository-declared formatting, lint, type, static-analysis, schema, and
   artifact checks.
4. For Python, `python -m compileall` when appropriate as a syntax baseline;
   do not misrepresent it as undefined-name analysis.
5. Focused production-path tests followed by the complete mandated suite.
6. Repeat the final-output acceptance assertion from the clean committed head.

Any failure returns the task to implementation. Do not publish a handback and
promise that CI or the reviewer will discover the remaining defects.

Commit and publish the authorized branch, then stop for an independent
`/code-review`, `/hard-review`, or `/devils-advocate-review` by another identity.
