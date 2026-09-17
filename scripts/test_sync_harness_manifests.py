#!/usr/bin/env python3

import tempfile
import unittest
import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("sync-harness-manifests.py")
MODULE_SPEC = importlib.util.spec_from_file_location("sync_harness_manifests", MODULE_PATH)
sync = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(sync)


class HarnessManifestTest(unittest.TestCase):
    def test_frontmatter_parser_preserves_folded_description(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: example\ndescription: >-\n  first line\n  second line\n---\n",
                encoding="utf-8",
            )
            name, description = sync.skill_metadata(skill)
        self.assertEqual(name, "example")
        self.assertEqual(description, "first line second line")

    def test_codex_projection_contains_rules_dependency_and_preserves_frontmatter(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "skills"
            sync.build_codex_projection(target)
            self.assertTrue((target / "code-review" / "SKILL.md").is_file())
            self.assertTrue((target.parent / "rules" / "AGENTS.md").is_file())
            self.assertIn(
                "disable-model-invocation: true",
                (target / "ask-matt" / "SKILL.md").read_text(encoding="utf-8"),
            )

    def test_emitted_manifests_match_active_generators(self):
        codex_path = sync.ROOT / ".codex-plugin" / "plugin.json"
        marketplace_path = sync.ROOT / ".agents" / "plugins" / "marketplace.json"
        self.assertEqual(json.loads(codex_path.read_text(encoding="utf-8")), sync.codex_manifest())
        self.assertEqual(json.loads(marketplace_path.read_text(encoding="utf-8")), sync.codex_marketplace())
        self.assertEqual(sync.codex_manifest()["skills"], "./skills/")
        self.assertIn("agy-skills", {plugin["name"] for plugin in sync.codex_marketplace()["plugins"]})


if __name__ == "__main__":
    unittest.main()
