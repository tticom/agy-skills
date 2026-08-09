#!/usr/bin/env python3
"""Find obvious fixture identities embedded in production source files."""

from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


GENERIC_PRIVATE_MARKERS = (
    "score2gp-private-fixtures",
    "fixtures/private",
    "fixtures\\private",
    "onedrive/documents/guitar",
    "onedrive\\documents\\guitar",
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    token: str
    kind: str


def fixture_tokens(roots: list[Path]) -> dict[str, str]:
    tokens: dict[str, str] = {}
    for root in roots:
        if not root.is_dir():
            raise ValueError(f"fixture root is not a directory: {root}")
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            name = path.name.lower()
            stem = path.stem.lower()
            if len(name) >= 5:
                tokens[name] = "fixture-name"
            if len(stem) >= 8 and any(character.isdigit() for character in stem):
                tokens[stem] = "fixture-name"
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            tokens[digest] = "fixture-sha256"
    return tokens


def scan(production: list[Path], roots: list[Path]) -> list[Finding]:
    tokens = fixture_tokens(roots)
    findings: list[Finding] = []
    for path in production:
        if not path.is_file():
            raise ValueError(f"production path is not a file: {path}")
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for marker in GENERIC_PRIVATE_MARKERS:
                if marker in lowered:
                    findings.append(Finding(path, line_number, marker, "private-path"))
            for token, kind in tokens.items():
                if token in lowered:
                    findings.append(Finding(path, line_number, token, kind))
            if re.search(r"lesson[-_ ]?\d+\.(?:pdf|gp\d?|mxl|musicxml)", lowered):
                findings.append(Finding(path, line_number, "named lesson artifact", "fixture-name"))
    return sorted(set(findings), key=lambda item: (str(item.path), item.line, item.kind, item.token))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="append", required=True, type=Path)
    parser.add_argument("--fixture-root", action="append", required=True, type=Path)
    args = parser.parse_args()
    try:
        findings = scan(args.production, args.fixture_root)
    except (OSError, ValueError) as error:
        raise SystemExit(f"FIXTURE_COUPLING_SCAN=ERROR: {error}") from error
    if findings:
        rendered = "\n".join(
            f"{item.path}:{item.line}: {item.kind}: {item.token}" for item in findings
        )
        raise SystemExit(f"FIXTURE_COUPLING_SCAN=FAIL\n{rendered}")
    print("FIXTURE_COUPLING_SCAN=PASS")


if __name__ == "__main__":
    main()
