#!/usr/bin/env python3
"""Publish APPROVE only after exact-head evidence validation succeeds."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path


def run(*args: str) -> str:
    completed = subprocess.run(args, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def load_gate(script_dir: Path):
    path = script_dir / "review_evidence_gate.py"
    spec = importlib.util.spec_from_file_location("review_evidence_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load review evidence gate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--body-file", required=True, type=Path)
    parser.add_argument("--prior-packet", type=Path)
    parser.add_argument("--prior-overturns", type=int, default=0)
    parser.add_argument("--high-risk", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    gate = load_gate(Path(__file__).resolve().parent)
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    prior = json.loads(args.prior_packet.read_text(encoding="utf-8")) if args.prior_packet else None
    expected = gate.full_sha(args.expected_head, "--expected-head")
    review_body = args.body_file.read_text(encoding="utf-8")
    if expected not in review_body:
        raise SystemExit(
            "APPROVAL_PUBLICATION=FAIL: review body does not contain the exact validated head"
        )
    live_before = run("gh", "api", f"repos/{args.repo}/pulls/{args.pr}", "--jq", ".head.sha")
    if live_before != expected:
        raise SystemExit("APPROVAL_PUBLICATION=FAIL: live head changed before evidence validation")
    required, score = gate.validate(
        packet,
        prior_overturns=args.prior_overturns,
        high_risk=args.high_risk,
        expected_head=expected,
        prior_packet=prior,
    )
    if args.dry_run:
        print(f"APPROVAL_PUBLICATION=DRY_RUN_PASS required_probes={required} score={score}")
        return
    run("gh", "pr", "review", str(args.pr), "--repo", args.repo, "--approve", "--body-file", str(args.body_file))
    live_after = run("gh", "api", f"repos/{args.repo}/pulls/{args.pr}", "--jq", ".head.sha")
    if live_after != expected:
        raise SystemExit("APPROVAL_PUBLICATION=FAIL: live head changed during publication")
    print(f"APPROVAL_PUBLICATION=PASS head={expected} required_probes={required} score={score}")


if __name__ == "__main__":
    main()
