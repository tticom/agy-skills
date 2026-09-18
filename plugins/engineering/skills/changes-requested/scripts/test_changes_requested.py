#!/usr/bin/env python3
"""Unit tests for fetch_review_findings in changes-requested skill."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import fetch_review_findings as frf


class TestFetchReviewFindings(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_pr = {
            "number": 123,
            "base": {"repo": {"full_name": "tticom/test-repo"}},
            "head": {"ref": "feature/my-fix", "sha": "1111111111111111111111111111111111111111"},
            "user": {"login": "author-user"},
        }
        self.sample_reviews = [
            {
                "id": 1,
                "state": "CHANGES_REQUESTED",
                "commit_id": "1111111111111111111111111111111111111111",
                "user": {"login": "reviewer-user"},
                "body": "Please fix boundary conditions.",
            }
        ]
        self.sample_inline_comments = [
            {
                "id": 101,
                "path": "src/module.py",
                "line": 42,
                "user": {"login": "reviewer-user"},
                "body": "Off by one error here.",
                "commit_id": "1111111111111111111111111111111111111111",
                "pull_request_review_id": 1,
            }
        ]
        self.sample_issue_comments = [
            {
                "id": 201,
                "user": {"login": "reviewer-user"},
                "body": "<!-- reviewer-summary:devils-advocate:1111111111111111111111111111111111111111 -->\nReview level: DEVILS_ADVOCATE\nVerdict: CHANGES_REQUESTED",
                "created_at": "2026-09-18T00:00:00Z",
            }
        ]

    def test_parse_summary_comment(self) -> None:
        summary = frf.parse_summary_comment(self.sample_issue_comments)
        self.assertIsNotNone(summary)
        assert summary is not None
        self.assertEqual(summary["level"], "devils-advocate")
        self.assertEqual(summary["reviewed_head"], "1111111111111111111111111111111111111111")
        self.assertEqual(summary["author"], "reviewer-user")

    def test_parse_summary_comment_missing(self) -> None:
        comments = [{"id": 1, "body": "regular comment", "user": {"login": "someone"}}]
        self.assertIsNone(frf.parse_summary_comment(comments))

    def test_extract_inline_findings(self) -> None:
        findings = frf.extract_inline_findings(self.sample_inline_comments)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["id"], 101)
        self.assertEqual(findings[0]["path"], "src/module.py")
        self.assertEqual(findings[0]["line"], 42)
        self.assertEqual(findings[0]["body"], "Off by one error here.")

    def test_build_remediation_ledger(self) -> None:
        ledger = frf.build_remediation_ledger(
            self.sample_pr,
            self.sample_reviews,
            self.sample_inline_comments,
            self.sample_issue_comments,
        )
        self.assertEqual(ledger["repository"], "tticom/test-repo")
        self.assertEqual(ledger["pr"], 123)
        self.assertEqual(ledger["pr_branch"], "feature/my-fix")
        self.assertEqual(ledger["reviewed_head"], "1111111111111111111111111111111111111111")
        self.assertEqual(ledger["review_state"], "CHANGES_REQUESTED")
        self.assertEqual(ledger["reviewer"], "reviewer-user")

        # Two items: 1 review body + 1 inline comment
        self.assertEqual(len(ledger["findings"]), 2)
        self.assertEqual(ledger["findings"][0]["source"], "review_body")
        self.assertEqual(ledger["findings"][1]["source"], "inline_comment")
        self.assertEqual(ledger["findings"][1]["location"], "src/module.py:42")

    def test_render_markdown_ledger(self) -> None:
        ledger = frf.build_remediation_ledger(
            self.sample_pr,
            self.sample_reviews,
            self.sample_inline_comments,
            self.sample_issue_comments,
        )
        md = frf.render_markdown_ledger(ledger)
        self.assertIn("# Review Remediation Ledger: tticom/test-repo PR #123", md)
        self.assertIn("Off by one error here.", md)
        self.assertIn("Please fix boundary conditions.", md)
        self.assertIn("src/module.py:42", md)


if __name__ == "__main__":
    unittest.main()
