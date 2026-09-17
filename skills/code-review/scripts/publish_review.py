#!/usr/bin/env python3
"""Publish an exact-head formal review and mandatory PR summary comment."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


LEVELS = {"basic", "hard", "devils-advocate"}
VERDICTS = {"APPROVE", "CHANGES_REQUESTED", "CANNOT_VERIFY"}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_json(*args: str, stdin: dict[str, Any] | None = None) -> Any:
    completed = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        input=None if stdin is None else json.dumps(stdin),
    )
    return json.loads(completed.stdout)


def validate_publication_text(
    *, level: str, verdict: str, expected_head: str, review_body: str, summary: str
) -> str:
    if level not in LEVELS:
        raise ValueError(f"unsupported review level: {level}")
    if expected_head not in review_body:
        raise ValueError("formal review body must contain the exact reviewed head")
    if verdict not in VERDICTS:
        raise ValueError(f"unsupported verdict: {verdict}")
    if f"Verdict: {verdict}" not in review_body:
        raise ValueError("formal review body must contain the exact verdict")
    marker = f"<!-- reviewer-summary:{level}:{expected_head} -->"
    if marker not in summary:
        raise ValueError(f"summary is missing marker {marker}")
    if expected_head not in summary:
        raise ValueError("summary must contain the exact reviewed head")
    if f"Verdict: {verdict}" not in summary:
        raise ValueError("summary must contain the exact verdict")
    return marker


def load_inline_comments(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("inline comments file must contain a JSON list")
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"inline comment {index} must be an object")
        required = {"path", "line", "side", "body"}
        if not required.issubset(item):
            raise ValueError(f"inline comment {index} lacks {sorted(required - set(item))}")
        if item["side"] not in {"LEFT", "RIGHT"}:
            raise ValueError(f"inline comment {index} has invalid side")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--level", required=True, choices=sorted(LEVELS))
    parser.add_argument("--verdict", required=True, choices=sorted(VERDICTS))
    parser.add_argument("--review-body-file", required=True, type=Path)
    parser.add_argument("--summary-file", required=True, type=Path)
    parser.add_argument("--inline-comments-file", type=Path)
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--prior-packet", type=Path)
    parser.add_argument("--prior-overturns", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    engineering_dir = script_dir.parent.parent
    role_gate = load_module(
        engineering_dir / "identity-safe-git" / "scripts" / "role_authority_gate.py",
        "role_authority_gate",
    )
    evidence_gate = load_module(script_dir / "review_evidence_gate.py", "review_evidence_gate")

    expected = evidence_gate.full_sha(args.expected_head, "--expected-head")
    review_body = args.review_body_file.read_text(encoding="utf-8")
    summary = args.summary_file.read_text(encoding="utf-8")
    marker = validate_publication_text(
        level=args.level,
        verdict=args.verdict,
        expected_head=expected,
        review_body=review_body,
        summary=summary,
    )
    inline_comments = load_inline_comments(args.inline_comments_file)

    actor = run_json("gh", "api", "user")["login"]
    pr_state = run_json("gh", "api", f"repos/{args.repo}/pulls/{args.pr}")
    live_before = pr_state["head"]["sha"]
    if live_before != expected:
        raise SystemExit("REVIEW_PUBLICATION=FAIL: live head changed before publication")
    role_gate.validate(
        actor=actor,
        operation="review-metadata",
        repo=args.repo,
        pr=args.pr,
        pr_author=pr_state["user"]["login"],
    )

    if args.verdict == "APPROVE" and args.level != "basic":
        if args.packet is None:
            raise SystemExit("REVIEW_PUBLICATION=FAIL: hard approval requires --packet")
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        prior = (
            json.loads(args.prior_packet.read_text(encoding="utf-8"))
            if args.prior_packet else None
        )
        evidence_gate.validate(
            packet,
            prior_overturns=args.prior_overturns,
            high_risk=True,
            expected_head=expected,
            prior_packet=prior,
            devils_advocate=args.level == "devils-advocate",
        )

    if args.dry_run:
        print(f"REVIEW_PUBLICATION=DRY_RUN_PASS level={args.level} head={expected}")
        return

    event = "APPROVE" if args.verdict == "APPROVE" else "REQUEST_CHANGES"
    review = run_json(
        "gh", "api", "--method", "POST",
        f"repos/{args.repo}/pulls/{args.pr}/reviews", "--input", "-",
        stdin={
            "commit_id": expected,
            "body": review_body,
            "event": event,
            "comments": inline_comments,
        },
    )

    comments = run_json("gh", "api", f"repos/{args.repo}/issues/{args.pr}/comments?per_page=100")
    existing = next(
        (
            comment for comment in comments
            if comment.get("user", {}).get("login", "").lower() == actor.lower()
            and marker in comment.get("body", "")
        ),
        None,
    )
    if existing:
        summary_comment = run_json(
            "gh", "api", "--method", "PATCH",
            f"repos/{args.repo}/issues/comments/{existing['id']}", "--input", "-",
            stdin={"body": summary},
        )
    else:
        summary_comment = run_json(
            "gh", "api", "--method", "POST",
            f"repos/{args.repo}/issues/{args.pr}/comments", "--input", "-",
            stdin={"body": summary},
        )

    live_after = run_json("gh", "api", f"repos/{args.repo}/pulls/{args.pr}")["head"]["sha"]
    if live_after != expected:
        raise SystemExit("REVIEW_PUBLICATION=FAIL: live head changed during publication")
    if review.get("commit_id") != expected or marker not in summary_comment.get("body", ""):
        raise SystemExit("REVIEW_PUBLICATION=FAIL: remote publication proof mismatch")
    print(
        f"REVIEW_PUBLICATION=PASS level={args.level} verdict={args.verdict} "
        f"head={expected} review_id={review['id']} comment_id={summary_comment['id']}"
    )


if __name__ == "__main__":
    main()
