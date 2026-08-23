#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

from fixture_coupling_scan import scan


class FixtureCouplingScanTest(unittest.TestCase):
    def test_detects_fixture_name_hash_and_private_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = root / "fixtures"
            fixtures.mkdir()
            fixture = fixtures / "Lesson-6.pdf"
            fixture.write_bytes(b"fixture-content")
            digest = __import__("hashlib").sha256(fixture.read_bytes()).hexdigest()
            production = root / "module.py"
            production.write_text(
                "NAME = 'Lesson-6.pdf'\n"
                f"DIGEST = '{digest}'\n"
                "PATH = 'score2gp-private-fixtures/fixtures/private'\n",
                encoding="utf-8",
            )
            kinds = {finding.kind for finding in scan([production], [fixtures])}
            self.assertEqual(kinds, {"fixture-name", "fixture-sha256", "private-path"})

    def test_generic_domain_code_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = root / "fixtures"
            fixtures.mkdir()
            (fixtures / "Lesson-6.pdf").write_bytes(b"fixture-content")
            production = root / "module.py"
            production.write_text(
                "def duration_ticks(beats, resolution):\n"
                "    return beats * resolution\n",
                encoding="utf-8",
            )
            self.assertEqual(scan([production], [fixtures]), [])


if __name__ == "__main__":
    unittest.main()
