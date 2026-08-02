---
name: code-review
description: Review a branch, pull request, or work-in-progress diff against a fixed point along three independent axes — Standards, Spec, and Evidence/Falsification. Use when the user asks to review code or a PR, review since a commit, validate an implementation claim, or decide whether work is ready to merge. Treat summaries and green tests as untrusted claims; trace material claims through production code and discriminating tests before approval.
---

Review the diff between `HEAD` and a fixed point along three independent axes:

- **Standards** — does the code follow documented repository standards?
- **Spec** — does it implement the originating requirement without scope creep?
- **Evidence/Falsification** — could the supplied tests and artifacts distinguish the claimed behavior from a plausible broken implementation?

Run the axes in separate parallel sub-agents, then independently verify every blocking finding and every fact used to approve. Delegation gathers evidence; it does not transfer reviewer responsibility.

## Devil's advocate contract

Assume every developer, PR, handback, test name, and green check is an
unverified advocacy document. Your job is not to confirm it. Your job is to
find the smallest realistic way it could be false.

- Begin with the provisional verdict `CHANGES_REQUESTED`.
- Make the implementation earn its way out claim by claim.
- Treat a test that reconstructs desired inputs below the claimed boundary as
  evidence of that helper only, never of the upstream pipeline.
- Treat “end-to-end”, “full corpus”, “no leakage”, “100%”, and “no residual
  risk” as hostile claims requiring direct disconfirmation.
- Never repeat a claimed probe unless you personally ran it and can report the
  concrete input and observed differentiator.
- Prefer one real counterexample over ten confirmations.

The reviewer's success metric is accuracy, not approval throughput. Finding a
valid blocker before merge is positive progress. An approval later overturned
by independent evidence is a reviewer strike; each active strike raises the
minimum probe quota. Fabricated, inferred, or unreproducible “executed”
evidence invalidates the verdict and counts as two strikes.

Read [references/evidence-falsification.md](references/evidence-falsification.md) completely before reviewing tests, empirical claims, generated artifacts, geometry/threshold logic, parsers, matching algorithms, or a live pull request.
Read [references/review-state-protocol.md](references/review-state-protocol.md)
before consuming or publishing live PR review state.

## Process

### 1. Pin the reviewed state

Resolve the fixed point supplied by the user. If absent, ask for it.

Capture once:

```bash
git rev-parse <fixed-point>
git rev-parse HEAD
git diff <fixed-point>...HEAD
git log <fixed-point>..HEAD --oneline
```

Fail on a bad ref or empty diff.

For a live pull request, also query the hosting service immediately before review:

- live head object ID;
- base object ID;
- changed paths;
- current review threads and comments;
- latest author handback/evidence comment when the project requires one.

If a project requires an exact-head handback, compare the parsed full SHA to the live head using exact string equality. Missing, abbreviated, stale, or unparsable values stop the review. A PR body, chat summary, local branch, or earlier review is not a substitute.

Then materialize the exact live head before inspecting any diff:

1. fetch the live head object without merging it into an existing task branch;
2. check it out detached or in a dedicated review worktree;
3. require `git rev-parse HEAD` to equal the full live head object ID exactly;
4. compute the review diff as `<base-object-id>...<live-head-object-id>`, never as `<fixed-point>...HEAD` until equality has been proved.

Fail closed if the object cannot be fetched, checked out, or matched. A local
branch name that matches the PR branch is insufficient.

Re-query the live head before publishing the verdict and re-run:

```bash
python skills/engineering/code-review/scripts/verify_review_head.py \
  --expected <re-queried-live-head-object-id> \
  --worktree <review-worktree>
```

Approval requires all three full SHAs to be identical: initial live head,
reviewed local `HEAD`, and final live head. If any differ, discard the verdict
and restart at the new head.

### 2. Identify authority sources

Find the originating spec in this order:

1. issue references in commits;
2. a user-supplied path;
3. the PR body or linked issue;
4. matching files under `docs/`, `specs/`, or `.scratch/`.

Use `docs/agents/issue-tracker.md` when present. If no spec exists, report that limitation; never invent requirements.

Find repository standards such as `AGENTS.md`, `CONTRIBUTING.md`, coding standards, review rules, evidence contracts, and active-task scope. Project rules override this reusable skill when stricter.

### 3. Build the claim ledger

For every re-review, first compute the delta from the last formally reviewed
head to the current live head. Build a separate **head-delta ledger** for every
changed claim, discriminator, representation, test oracle, and previous-finding
disposition. Prior-head conclusions are historical context only. Never reuse
their probe output, hashes, test inventory, or approval prose as current evidence.

Before reading conclusions from tests, list each material claim made by the spec, PR body, handback, or implementation. At minimum include claims about:

- changed behavior and failure behavior;
- dynamic or end-to-end data flow;
- ambiguity, absence, fallback, or conflict handling;
- boundary, scale, ordering, deduplication, and idempotence;
- regression safety and full-suite validation;
- changed-path scope and exact reviewed revision.

For every claim record:

| Claim | Production path | Evidence path | Strongest false-success mutation | Status |
|---|---|---|---|---|
| exact behavior asserted | function/module reached | test/artifact/assertion | smallest broken implementation that might still pass | verified / contradicted / cannot verify |

Do not mark a claim verified from a test name, comment, aggregate count, snapshot existence, or agent summary.

For every cited test, inspect and record its exact node, behavior-controlling
input, production boundary, exact assertion, and supported claim. A green node
without this semantic attribution has zero weight. An obsolete or renamed test
node is a hard evidence-integrity failure.

### 4. Run the assertion-smell scan

Run:

```bash
python skills/engineering/code-review/scripts/assertion_smells.py <changed-test-path> [...]
```

Treat output as review leads, not automatic findings. Inspect every reported assertion in context. The scanner cannot prove semantic adequacy and a clean scan cannot justify approval.

### 4a. Set the falsification quota

Determine the active reviewer-strike count from the project scorecard. If the
project has no scorecard, use zero and report that accountability is not yet
persistent.

Minimum reviewer-created probes:

- ordinary review: 2;
- timing, grouping, parser, privacy, fail-closed, or end-to-end claims: 3;
- add 1 for each active strike, capped at 2 additional probes.

Author-authored tests, CI, linters, schema export, and `agent_verify.py` score
zero adversarial points. A reviewer-created probe scores 2 only when it has a
unique false-success mutation, runs the claimed production boundary, records
the exact command/input/output, and kills or exposes that mutation.

### 5. Spawn three independent review axes

Run all applicable axes in parallel. Give each sub-agent the pinned diff command, commit list, changed paths, and only its relevant authority/evidence inputs.

#### Standards brief

Report documented-standard violations with rule citations and baseline smells with quoted hunks. Repository standards override the smell baseline. Skip rules already enforced by tooling.

Use this smell baseline as judgement-call prompts:

- Mysterious Name
- Duplicated Code
- Feature Envy
- Data Clumps
- Primitive Obsession
- Repeated Switches
- Shotgun Surgery
- Divergent Change
- Speculative Generality
- Message Chains
- Middle Man
- Refused Bequest

#### Spec brief

Report:

- missing or partial requirements;
- behavior not requested;
- requirements that look implemented but are semantically wrong.

Quote the governing requirement for each finding.

#### Evidence/Falsification brief

Give the sub-agent the claim ledger, changed implementation and tests, validation evidence, and [references/evidence-falsification.md](references/evidence-falsification.md). Ask it to:

1. trace each claim through the changed production path to an exact assertion or inspected artifact;
2. propose the smallest plausible broken mutation;
3. decide whether the existing evidence would fail under that mutation;
4. identify hardcoded substitutes for claimed dynamic inputs;
5. inspect absence, ambiguity, conflict, ordering, duplicate, boundary, scale, and negative-control behavior when relevant;
6. report unsupported handback or PR claims;
7. return `verified`, `contradicted`, or `cannot verify` per claim.

No claim may pass solely because tests are green.

### 6. Perform the primary-reviewer challenge

After sub-agents return, inspect the raw diff yourself.

For each proposed approval fact and each P0/P1 finding:

- locate the exact production branch;
- locate the exact test input and assertion;
- check whether the assertion is discriminating;
- check whether the test reaches changed production code;
- check whether claimed dynamic inputs are actually derived rather than hardcoded later;
- check at least one false-success mutation mentally or by a safe local mutation/test when practical.

Reject assertions that permit both material outcomes, such as `assert failure or success`, unless both outcomes are explicitly equivalent under the spec.

For thresholds, verify both sides with geometry/data that depends on the threshold. An “inside” sample that already overlaps without tolerance does not test tolerance.

For collection logic, check permutation invariance, duplicate handling, competition, and global assignment rather than only isolated elements.

Never infer external-library or serialized-field semantics from a name. Inspect
authoritative documentation or run a minimal direct API probe in the pinned
environment. Record units and distinguish pen width, bounding-box width, filled
area, source identity, and derived segments where applicable.

When one source expands into several candidates, or several sources merge into
one, trace stable source identity end to end. Probe representation invariance
with at least two supported encodings of the same semantic object.

### 7. Gate the verdict

Approval is allowed only when:

- Standards has no blocking violation;
- Spec has no missing or incorrect requirement;
- every material claim in Evidence/Falsification is `verified`;
- required negative controls and false-success disconfirmation are present;
- exact-head and scope evidence are coherent;
- initial live head, reviewed local `HEAD`, and final live head are exactly equal;
- unresolved relevant review threads are dispositioned.

Use `cannot verify` when evidence is unavailable. Use `changes requested` when evidence contradicts claims or implementation is wrong. Do not convert uncertainty into approval.

Before approval, write one sentence naming the strongest plausible false-success mode and the exact check that ruled it out. If that sentence cannot be written with concrete evidence, do not approve.

Before publishing `APPROVE`, create a JSON evidence packet using the schema in
[references/evidence-falsification.md](references/evidence-falsification.md)
and run:

```bash
python skills/engineering/code-review/scripts/review_evidence_gate.py \
  review-evidence.json \
  --expected-head <full-reviewed-head> \
  [--prior-packet previous-head-review-evidence.json] \
  --prior-overturns <active-strikes> \
  [--high-risk]
```

The command must print `APPROVAL_EVIDENCE_GATE=PASS`. Any failure forces
`CHANGES_REQUESTED` or `CANNOT_VERIFY`. Do not weaken the packet, relabel an
author test as reviewer-created, or omit a material claim to pass the gate.

On a re-review, `--prior-packet` is mandatory. Every probe must name the exact
current `executed_head`, declare `fresh_execution: true`, carry a new execution
receipt, and target a current head-delta claim. Every delta claim requires a
fresh reviewer probe. Copying prior observed output or its hash is fabrication.

### 8. Report

Report findings first, ordered by severity, with file/hunk references and the violated requirement or unsupported claim.

Then present:

## Standards

Hard violations and labelled judgement-call smells.

## Spec

Missing, extra, or incorrect behavior with requirement citations.

## Evidence/Falsification

The completed claim ledger, disconfirmation attempts, contradictions, and residual uncertainty.

Include the validator's required probe count, achieved falsification score,
active strike count, and evidence-integrity attestation.

End with one verdict:

- `APPROVE`
- `CHANGES_REQUESTED`
- `CANNOT_VERIFY`

Never publish, approve, merge, or change a pull request unless the user or governing workflow authorizes that action.

When publication is authorized, publish the formal hosting-service verdict
before reporting a machine-actionable state. Re-query the review timeline and
prove the verdict exists on the exact head. A local task update, chat response,
or issue comment is not a substitute for a formal review.
