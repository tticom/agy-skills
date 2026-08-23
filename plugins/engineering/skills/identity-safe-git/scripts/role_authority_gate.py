#!/usr/bin/env python3
"""Fail-closed authority gate for reviewer metadata, repo writes, and merges."""

from __future__ import annotations

import argparse
import re


REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
NEVER_MERGE = {"tticom-gov", "tticom-automation"}
REVIEW_IDENTITIES = NEVER_MERGE | {"tticom-codex", "tticom"}


class AuthorityDenied(ValueError):
    """Raised when the requested operation is outside the actor's authority."""


def normalize_login(value: str | None, field: str) -> str:
    if value is None or not value.strip():
        raise AuthorityDenied(f"{field} is required")
    return value.strip().lower()


def validate(
    *,
    actor: str,
    operation: str,
    repo: str,
    pr: int,
    pr_author: str | None = None,
    authorization_actor: str | None = None,
    authorization_repo: str | None = None,
    authorization_pr: int | None = None,
    expected_head: str | None = None,
    authorization_head: str | None = None,
    current_turn_explicit: bool = False,
) -> str:
    actor = normalize_login(actor, "actor")
    if not REPO.fullmatch(repo):
        raise AuthorityDenied("repo must be owner/name")
    if pr <= 0:
        raise AuthorityDenied("pr must be positive")

    if operation == "review-metadata":
        if actor not in REVIEW_IDENTITIES:
            raise AuthorityDenied(f"{actor} is not an authorized reviewer")
        author = normalize_login(pr_author, "pr_author")
        if actor == author:
            raise AuthorityDenied("self-review is forbidden")
        return "review metadata allowed"

    if operation == "reviewed-repo-write":
        raise AuthorityDenied("review sessions are comment-only; repository writes are forbidden")

    if operation != "merge":
        raise AuthorityDenied(f"unsupported operation: {operation}")

    if actor in NEVER_MERGE:
        raise AuthorityDenied(f"{actor} has an unconditional no-merge role")
    if actor == "tticom":
        return "maintainer merge allowed"
    if actor != "tticom-codex":
        raise AuthorityDenied(f"{actor} has no merge authority")

    authorizer = normalize_login(authorization_actor, "authorization_actor")
    if authorizer != "tticom":
        raise AuthorityDenied("tticom-codex requires authorization from tticom")
    if not current_turn_explicit:
        raise AuthorityDenied("tticom-codex requires current-turn explicit authorization")
    if authorization_repo != repo or authorization_pr != pr:
        raise AuthorityDenied("authorization must name this exact repository and PR")
    if expected_head is None or not FULL_SHA.fullmatch(expected_head):
        raise AuthorityDenied("merge requires the exact current full head SHA")
    if authorization_head != expected_head:
        raise AuthorityDenied("authorization does not match the exact current head")
    return "delegated merge allowed for this exact PR only"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", required=True)
    parser.add_argument(
        "--operation",
        required=True,
        choices=("review-metadata", "reviewed-repo-write", "merge"),
    )
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--pr-author")
    parser.add_argument("--authorization-actor")
    parser.add_argument("--authorization-repo")
    parser.add_argument("--authorization-pr", type=int)
    parser.add_argument("--expected-head")
    parser.add_argument("--authorization-head")
    parser.add_argument("--current-turn-explicit", action="store_true")
    args = parser.parse_args()

    try:
        reason = validate(
            actor=args.actor,
            operation=args.operation,
            repo=args.repo,
            pr=args.pr,
            pr_author=args.pr_author,
            authorization_actor=args.authorization_actor,
            authorization_repo=args.authorization_repo,
            authorization_pr=args.authorization_pr,
            expected_head=args.expected_head,
            authorization_head=args.authorization_head,
            current_turn_explicit=args.current_turn_explicit,
        )
    except AuthorityDenied as error:
        raise SystemExit(f"ROLE_AUTHORITY_GATE=DENY: {error}") from error
    print(f"ROLE_AUTHORITY_GATE=PASS: {reason}")


if __name__ == "__main__":
    main()
