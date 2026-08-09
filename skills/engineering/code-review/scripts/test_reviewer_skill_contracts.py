#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


ENGINEERING = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ENGINEERING / relative).read_text(encoding="utf-8")


class ReviewerSkillContractTest(unittest.TestCase):
    def test_all_levels_are_comment_only_and_publish_summary(self):
        basic = read("code-review/SKILL.md")
        hard = read("hard-review/SKILL.md")
        devil = read("devils-advocate-review/SKILL.md")
        firewall = read("code-review/references/reviewer-role-firewall.md")

        self.assertIn("publish_review.py", basic)
        self.assertIn("reviewer-summary:basic", basic)
        self.assertIn("reviewer-summary:hard", hard)
        self.assertIn("reviewer-summary:devils-advocate", devil)
        self.assertIn("reviewed repository", firewall.lower())
        self.assertIn("must not", firewall.lower())

        forbidden_commands = re.compile(
            r"^\s*(?:git\s+(?:add|commit|push)|gh\s+pr\s+merge|apply_patch)\b",
            re.MULTILINE,
        )
        for name, contents in (("basic", basic), ("hard", hard), ("devil", devil)):
            with self.subTest(level=name):
                self.assertIsNone(forbidden_commands.search(contents))

    def test_hard_and_devil_contracts_cannot_collapse_to_basic(self):
        hard = read("hard-review/SKILL.md")
        devil = read("devils-advocate-review/SKILL.md")
        for phrase in (
            "SYNTHETIC_OR_MOCKED",
            "DATA_FREE",
            "REAL_SOURCE_END_TO_END",
            "fixture_coupling_scan.py",
            "independent semantic oracle",
        ):
            self.assertIn(phrase, hard)
        self.assertIn("contradiction ledger", devil.lower())
        self.assertIn("prior reviewer", devil)
        self.assertIn("provisional verdict `CHANGES_REQUESTED`", devil)

    def test_merge_roles_are_explicit(self):
        firewall = read("code-review/references/reviewer-role-firewall.md")
        self.assertIn("`tticom-gov`", firewall)
        self.assertIn("`tticom-automation`", firewall)
        self.assertIn("unconditional no-merge", firewall)
        self.assertIn("current, explicit instruction from `tticom`", firewall)


if __name__ == "__main__":
    unittest.main()
