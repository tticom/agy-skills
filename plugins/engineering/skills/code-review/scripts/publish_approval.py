#!/usr/bin/env python3
"""Removed unsafe approval-only publisher; use publish_review.py."""

raise SystemExit(
    "APPROVAL_PUBLICATION=FAIL: publish_approval.py cannot guarantee the "
    "mandatory PR summary or role firewall; use publish_review.py"
)
