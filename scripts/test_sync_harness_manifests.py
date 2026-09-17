#!/usr/bin/env python3

import tempfile
import unittest
import importlib.util
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

    def test_codex_projection_contains_rules_dependency_and_strips_only_agy_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "skills"
            sync.build_codex_projection(target)
            self.assertTrue((target / "code-review" / "SKILL.md").is_file())
            self.assertTrue((target.parent / "rules" / "AGENTS.md").is_file())
            self.assertNotIn(
                "disable-model-invocation: true",
                (target / "ask-matt" / "SKILL.md").read_text(encoding="utf-8"),
            )

    def test_manifests_use_codex_root_and_agy_bucket_paths(self):
        codex = sync.codex_manifest()
        agy = sync.agy_manifest()
        self.assertEqual(codex["skills"], "./skills/")
        self.assertTrue(all(path.startswith("./plugins/") for path in agy["skills"]))


if __name__ == "__main__":
    unittest.main()
