#!/usr/bin/env python3

import unittest

from role_authority_gate import AuthorityDenied, validate


COMMON = {"repo": "tticom/score2gp", "pr": 514}
HEAD = "a" * 40


class RoleAuthorityGateTest(unittest.TestCase):
    def test_governance_identity_can_review_another_author(self):
        result = validate(
            actor="tticom-gov",
            operation="review-metadata",
            pr_author="tticom-automation",
            **COMMON,
        )
        self.assertEqual(result, "review metadata allowed")

    def test_self_review_is_denied(self):
        with self.assertRaisesRegex(AuthorityDenied, "self-review"):
            validate(
                actor="tticom-automation",
                operation="review-metadata",
                pr_author="tticom-automation",
                **COMMON,
            )

    def test_reviewed_repository_write_is_always_denied(self):
        for actor in ("tticom-gov", "tticom-automation", "tticom-codex", "tticom"):
            with self.subTest(actor=actor), self.assertRaisesRegex(
                AuthorityDenied, "comment-only"
            ):
                validate(actor=actor, operation="reviewed-repo-write", **COMMON)

    def test_governance_and_automation_can_never_merge(self):
        for actor in ("tticom-gov", "tticom-automation"):
            with self.subTest(actor=actor), self.assertRaisesRegex(
                AuthorityDenied, "unconditional no-merge"
            ):
                validate(
                    actor=actor,
                    operation="merge",
                    authorization_actor="tticom",
                    authorization_repo=COMMON["repo"],
                    authorization_pr=COMMON["pr"],
                    expected_head=HEAD,
                    authorization_head=HEAD,
                    current_turn_explicit=True,
                    **COMMON,
                )

    def test_codex_requires_current_exact_maintainer_authorization(self):
        denied_cases = (
            {},
            {"authorization_actor": "tticom"},
            {
                "authorization_actor": "tticom",
                "authorization_repo": COMMON["repo"],
                "authorization_pr": COMMON["pr"],
                "expected_head": HEAD,
                "authorization_head": HEAD,
            },
            {
                "authorization_actor": "tticom",
                "authorization_repo": "tticom/other",
                "authorization_pr": COMMON["pr"],
                "expected_head": HEAD,
                "authorization_head": HEAD,
                "current_turn_explicit": True,
            },
            {
                "authorization_actor": "tticom",
                "authorization_repo": COMMON["repo"],
                "authorization_pr": COMMON["pr"],
                "expected_head": HEAD,
                "authorization_head": "b" * 40,
                "current_turn_explicit": True,
            },
        )
        for extra in denied_cases:
            with self.subTest(extra=extra), self.assertRaises(AuthorityDenied):
                validate(actor="tticom-codex", operation="merge", **COMMON, **extra)

        result = validate(
            actor="tticom-codex",
            operation="merge",
            authorization_actor="tticom",
            authorization_repo=COMMON["repo"],
            authorization_pr=COMMON["pr"],
            expected_head=HEAD,
            authorization_head=HEAD,
            current_turn_explicit=True,
            **COMMON,
        )
        self.assertIn("exact PR", result)

    def test_maintainer_and_unknown_identity(self):
        self.assertEqual(
            validate(actor="tticom", operation="merge", **COMMON),
            "maintainer merge allowed",
        )
        with self.assertRaisesRegex(AuthorityDenied, "no merge authority"):
            validate(actor="unknown-agent", operation="merge", **COMMON)


if __name__ == "__main__":
    unittest.main()
