#!/usr/bin/env python3
"""Fetch and parse review findings from GitHub for an open PR with CHANGES_REQUESTED."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REVIEWER_SUMMARY_PATTERN = re.compile(
    r"<!--\s*reviewer-summary:(?P<level>[a-zA-Z0-9_-]+):(?P<head>[0-9a-fA-F]{40})\s*-->"
)


def run_json(*args: str) -> Any:
    completed = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def parse_summary_comment(comments: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find and parse the latest marked reviewer summary comment."""
    for comment in reversed(comments):
        body = comment.get("body", "")
        match = REVIEWER_SUMMARY_PATTERN.search(body)
        if match:
            return {
                "id": comment.get("id"),
                "author": comment.get("user", {}).get("login"),
                "level": match.group("level"),
                "reviewed_head": match.group("head"),
                "body": body,
                "created_at": comment.get("created_at"),
            }
    return None


def extract_inline_findings(comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract inline comments, filtering down to primary threads."""
    findings = []
    for comment in comments:
        # We record all review comments with path and line
        findings.append({
            "id": comment.get("id"),
            "path": comment.get("path"),
            "line": comment.get("line") or comment.get("original_line"),
            "author": comment.get("user", {}).get("login"),
            "body": comment.get("body", "").strip(),
            "commit_id": comment.get("commit_id"),
            "pull_request_review_id": comment.get("pull_request_review_id"),
            "in_reply_to_id": comment.get("in_reply_to_id"),
        })
    return findings


def build_remediation_ledger(
    pr_data: dict[str, Any],
    reviews: list[dict[str, Any]],
    inline_comments: list[dict[str, Any]],
    issue_comments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble structured review findings and remediation ledger."""
    summary_data = parse_summary_comment(issue_comments)
    inline_findings = extract_inline_findings(inline_comments)

    changes_requested_reviews = [
        r for r in reviews if r.get("state") == "CHANGES_REQUESTED"
    ]
    latest_review = changes_requested_reviews[-1] if changes_requested_reviews else (
        reviews[-1] if reviews else {}
    )

    reviewed_head = (
        (summary_data or {}).get("reviewed_head")
        or latest_review.get("commit_id")
        or pr_data.get("head", {}).get("sha", "")
    )

    ledger_items = []
    # Add inline comments
    for index, finding in enumerate(inline_findings, start=1):
        ledger_items.append({
            "index": index,
            "source": "inline_comment",
            "id": finding["id"],
            "location": f"{finding['path']}:{finding['line']}",
            "author": finding["author"],
            "finding": finding["body"],
            "defect_class": "unclassified",
            "reviewed_head_test": "TODO: add failing reproduction test on reviewed head",
            "remediation_status": "OPEN",
            "disposition": "",
            "evidence": "",
        })

    # If there is a formal review body with text, add it as a primary finding if not empty
    review_body = latest_review.get("body", "").strip()
    if review_body:
        ledger_items.insert(0, {
            "index": 0,
            "source": "review_body",
            "id": latest_review.get("id"),
            "location": "PR Review Body",
            "author": latest_review.get("user", {}).get("login"),
            "finding": review_body,
            "defect_class": "review_summary",
            "reviewed_head_test": "TODO: verify against review summary requirements",
            "remediation_status": "OPEN",
            "disposition": "",
            "evidence": "",
        })

    return {
        "repository": pr_data.get("base", {}).get("repo", {}).get("full_name"),
        "pr": pr_data.get("number"),
        "pr_branch": pr_data.get("head", {}).get("ref"),
        "reviewed_head": reviewed_head,
        "author": pr_data.get("user", {}).get("login"),
        "review_state": latest_review.get("state", "UNKNOWN"),
        "reviewer": latest_review.get("user", {}).get("login"),
        "summary": summary_data,
        "findings": ledger_items,
    }


def render_markdown_ledger(data: dict[str, Any]) -> str:
    lines = [
        f"# Review Remediation Ledger: {data.get('repository')} PR #{data.get('pr')}",
        "",
        f"- **PR Branch**: `{data.get('pr_branch')}`",
        f"- **Reviewed Head**: `{data.get('reviewed_head')}`",
        f"- **Review State**: `{data.get('review_state')}`",
        f"- **Reviewer**: `{data.get('reviewer')}`",
        "",
        "## Review Findings to Address",
        "",
    ]
    if not data.get("findings"):
        lines.append("No unresolved review findings recorded.\n")
        return "\n".join(lines)

    for item in data["findings"]:
        lines.extend([
            f"### Finding {item['index']} ({item['location']})",
            f"- **Source**: `{item['source']}` (ID: {item['id']})",
            f"- **Author**: `{item['author']}`",
            f"- **Finding**: {item['finding']}",
            f"- **Status**: `{item['remediation_status']}`",
            f"- **Reproduction Test**: `{item['reviewed_head_test']}`",
            "- **Disposition**: (fill in how this is addressed)",
            "- **Exact-Head Evidence**: (fill in pass/fail command output)",
            "",
        ])

    return "\n".join(lines)


def fetch_remote_data(repo: str, pr: int) -> dict[str, Any]:
    pr_data = run_json("gh", "api", f"repos/{repo}/pulls/{pr}")
    reviews = run_json("gh", "api", f"repos/{repo}/pulls/{pr}/reviews")
    inline_comments = run_json("gh", "api", f"repos/{repo}/pulls/{pr}/comments?per_page=100")
    issue_comments = run_json("gh", "api", f"repos/{repo}/issues/{pr}/comments?per_page=100")
    return build_remediation_ledger(pr_data, reviews, inline_comments, issue_comments)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch and format review findings for an open PR with changes requested."
    )
    parser.add_argument("--repo", required=True, help="Repository owner/name (e.g. tticom/example)")
    parser.add_argument("--pr", required=True, type=int, help="Pull request number")
    parser.add_argument("--json", action="store_true", help="Output raw JSON ledger")
    parser.add_argument("--output", type=Path, help="Write output to specified file path")
    args = parser.parse_args(argv)

    try:
        data = fetch_remote_data(args.repo, args.pr)
    except Exception as error:
        print(f"ERROR: failed to fetch review data: {error}", file=sys.stderr)
        return 1

    content = json.dumps(data, indent=2) if args.json else render_markdown_ledger(data)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n", encoding="utf-8")
        print(f"Review findings written to {args.output}")
    else:
        print(content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
