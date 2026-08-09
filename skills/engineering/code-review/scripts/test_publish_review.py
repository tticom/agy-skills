#!/usr/bin/env python3

import json
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from publish_review import load_inline_comments, main, validate_publication_text


HEAD = "a" * 40


class PublishReviewTest(unittest.TestCase):
    def test_summary_and_review_must_bind_exact_head(self):
        marker = validate_publication_text(
            level="hard",
            verdict="APPROVE",
            expected_head=HEAD,
            review_body=f"Reviewed head: {HEAD}\nVerdict: APPROVE",
            summary=f"<!-- reviewer-summary:hard:{HEAD} -->\nReviewed head: {HEAD}\nVerdict: APPROVE",
        )
        self.assertEqual(marker, f"<!-- reviewer-summary:hard:{HEAD} -->")
        with self.assertRaisesRegex(ValueError, "exact reviewed head"):
            validate_publication_text(
                level="hard", verdict="APPROVE", expected_head=HEAD,
                review_body="stale", summary=f"<!-- reviewer-summary:hard:{HEAD} -->",
            )

    def test_verdict_must_match_body_and_summary(self):
        with self.assertRaisesRegex(ValueError, "exact verdict"):
            validate_publication_text(
                level="basic", verdict="CHANGES_REQUESTED", expected_head=HEAD,
                review_body=f"Reviewed head: {HEAD}\nVerdict: APPROVE",
                summary=(
                    f"<!-- reviewer-summary:basic:{HEAD} -->\n"
                    f"Reviewed head: {HEAD}\nVerdict: CHANGES_REQUESTED"
                ),
            )

    def test_inline_comment_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "comments.json"
            path.write_text(json.dumps([
                {"path": "src/x.py", "line": 12, "side": "RIGHT", "body": "finding"}
            ]), encoding="utf-8")
            self.assertEqual(load_inline_comments(path)[0]["line"], 12)
            path.write_text(json.dumps([{"path": "src/x.py"}]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "lacks"):
                load_inline_comments(path)

    def test_publication_always_posts_formal_review_and_summary_comment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review_body = root / "review.md"
            summary = root / "summary.md"
            review_body.write_text(
                f"Reviewed head: {HEAD}\nVerdict: CHANGES_REQUESTED\n",
                encoding="utf-8",
            )
            marker = f"<!-- reviewer-summary:basic:{HEAD} -->"
            summary_text = (
                f"{marker}\nReviewed head: {HEAD}\nVerdict: CHANGES_REQUESTED\n"
            )
            summary.write_text(summary_text, encoding="utf-8")
            calls = []

            def fake_run_json(*args, stdin=None):
                calls.append((args, stdin))
                endpoint = args[-1]
                if args == ("gh", "api", "user"):
                    return {"login": "tticom-codex"}
                if endpoint == "repos/tticom/score2gp/pulls/514":
                    return {
                        "head": {"sha": HEAD},
                        "user": {"login": "tticom-automation"},
                    }
                if endpoint == "-" and any("pulls/514/reviews" in arg for arg in args):
                    return {"id": 10, "commit_id": HEAD}
                if endpoint.endswith("comments?per_page=100"):
                    return []
                if endpoint == "-" and any("issues/514/comments" in arg for arg in args):
                    return {"id": 20, "body": summary_text}
                raise AssertionError(f"unexpected call: {args}")

            argv = [
                "publish_review.py", "--repo", "tticom/score2gp", "--pr", "514",
                "--expected-head", HEAD, "--level", "basic",
                "--verdict", "CHANGES_REQUESTED",
                "--review-body-file", str(review_body),
                "--summary-file", str(summary),
            ]
            with patch("publish_review.run_json", side_effect=fake_run_json), patch.object(
                sys, "argv", argv
            ), patch("sys.stdout", new_callable=io.StringIO) as output:
                main()

            self.assertIn("REVIEW_PUBLICATION=PASS", output.getvalue())
            endpoints = [call[0] for call in calls]
            self.assertTrue(any(
                any("pulls/514/reviews" in arg for arg in args) for args in endpoints
            ))
            self.assertTrue(any(
                any("issues/514/comments" in arg for arg in args) for args in endpoints
            ))


if __name__ == "__main__":
    unittest.main()
