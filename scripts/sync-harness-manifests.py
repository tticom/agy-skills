#!/usr/bin/env python3
"""Generate the Codex projection and AGY manifests from the bucketed sources."""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ALL_BUCKETS = ("engineering", "productivity", "misc", "in-progress")
PROMOTED_BUCKETS = ("engineering", "productivity")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def skill_dirs(bucket: str) -> list[Path]:
    return sorted(
        path
        for path in (ROOT / "plugins" / bucket / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def skill_metadata(path: Path) -> tuple[str, str]:
    contents = (path / "SKILL.md").read_text(encoding="utf-8")
    if not contents.startswith("---\n"):
        raise ValueError(f"{path}/SKILL.md has no YAML frontmatter")
    end = contents.find("\n---", 4)
    if end < 0:
        raise ValueError(f"{path}/SKILL.md needs name and description frontmatter")
    frontmatter = yaml.safe_load(contents[4:end])
    if not isinstance(frontmatter, dict):
        raise ValueError(f"{path}/SKILL.md frontmatter must be an object")
    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not isinstance(name, str) or not name.strip() or not isinstance(description, str) or not description.strip():
        raise ValueError(f"{path}/SKILL.md needs non-empty name and description frontmatter")
    return name.strip(), description.strip()


def all_skills() -> list[tuple[str, Path]]:
    result = []
    names = set()
    for bucket in ALL_BUCKETS:
        for path in skill_dirs(bucket):
            name, _ = skill_metadata(path)
            if name in names:
                raise ValueError(f"duplicate skill name: {name}")
            names.add(name)
            result.append((name, path))
    return result


def interface(display_name: str, description: str) -> dict:
    return {
        "displayName": display_name,
        "shortDescription": "Practical skills for Codex and AGY",
        "longDescription": description,
        "developerName": "TTI",
        "category": "Developer Tools",
        "capabilities": ["Code", "Write"],
        "defaultPrompt": [
            "Help me choose the right engineering workflow",
            "Debug this issue with a tight feedback loop",
            "Review this change for correctness and regressions",
        ],
    }


def codex_manifest() -> dict:
    return {
        "name": "agy-skills",
        "version": "1.0.0",
        "description": "TTI's complete skill set for Codex.",
        "author": {"name": "TTI", "url": "https://github.com/tticom"},
        "repository": "https://github.com/tticom/agy-skills",
        "license": "MIT",
        "keywords": ["engineering", "agent-skills", "codex"],
        "skills": "./skills/",
        "interface": interface("AGY Skills for Codex", "The complete AGY skill set, packaged for Codex."),
    }


def codex_marketplace() -> dict:
    return {
        "name": "agy-skills",
        "interface": {"displayName": "AGY Skills"},
        "plugins": [{
                "name": "agy-skills",
                "source": {"source": "local", "path": "./"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }] + [{
                "name": f"agy-{bucket}-kit",
                "source": {"source": "local", "path": f"./plugins/{bucket}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }
            for bucket in PROMOTED_BUCKETS
        ],
    }


def build_codex_projection(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name, source in all_skills():
        destination = target / name
        shutil.copytree(source, destination)
    rules = ROOT / "plugins" / "engineering" / "rules"
    if rules.is_dir():
        shutil.copytree(rules, target.parent / "rules")


def same_tree(left: Path, right: Path) -> bool:
    if not left.is_dir() or not right.is_dir():
        return False
    left_files = sorted(path.relative_to(left) for path in left.rglob("*") if path.is_file())
    right_files = sorted(path.relative_to(right) for path in right.rglob("*") if path.is_file())
    return left_files == right_files and all(filecmp.cmp(left / path, right / path, shallow=False) for path in left_files)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = {
        ROOT / ".codex-plugin" / "plugin.json": codex_manifest(),
        ROOT / ".agents" / "plugins" / "marketplace.json": codex_marketplace(),
    }
    if args.check:
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory) / "skills"
            build_codex_projection(generated)
            if not same_tree(generated, ROOT / "skills") or not same_tree(generated.parent / "rules", ROOT / "rules"):
                print("out of date: skills/")
                return 1
        for path, value in expected.items():
            if not path.exists() or path.read_text(encoding="utf-8") != json.dumps(value, indent=2) + "\n":
                print(f"out of date: {path.relative_to(ROOT)}")
                return 1
        return 0
    projection = ROOT / "skills"
    if projection.exists():
        shutil.rmtree(projection)
    if (ROOT / "rules").exists():
        shutil.rmtree(ROOT / "rules")
    build_codex_projection(projection)
    for path, value in expected.items():
        write_json(path, value)
    print(f"generated {len(all_skills())} Codex skills and {len(expected)} manifests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
