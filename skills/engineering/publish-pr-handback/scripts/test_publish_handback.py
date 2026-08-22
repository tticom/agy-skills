from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).with_name("publish_handback.py")
SPEC = importlib.util.spec_from_file_location("publish_handback", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

HEAD = "a" * 40
BASE = "b" * 40


def pr_state() -> dict:
    return {
        "state": "open",
        "user": {"login": "author"},
        "head": {"sha": HEAD, "ref": "feature/branch"},
        "base": {"sha": BASE},
    }


def packet() -> dict:
    return {
        "schema_version": "author-handback.v1",
        "task": "Task 1 — Exact behavior",
        "repository": "owner/repo",
        "pr": 123,
        "head": HEAD,
        "base": BASE,
        "changed_paths": ["src/a.py", "tests/test_a.py"],
        "validation_runs": [
            {
                "command": "python -m pytest",
                "status": "PASS",
                "exit_code": 0,
                "passed": 10,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "xfailed": 0,
                "deselected": 0,
            }
        ],
        "acceptance": [
            {
                "criterion": "Produces exactly 43 measures",
                "status": "PASS",
                "command": "pytest tests/test_real.py",
                "observed": "43 measures; no partial-grouping warning",
                "oracle": "reference score semantic comparator",
            }
        ],
        "review_findings": [],
        "remaining_risks": [],
    }


def validate(value: dict) -> None:
    MODULE.validate_packet(
        value,
        repo="owner/repo",
        pr=123,
        head=HEAD,
        base=BASE,
        changed_paths=["src/a.py", "tests/test_a.py"],
    )


def test_valid_live_context_and_packet() -> None:
    assert MODULE.validate_live_context(
        actor="author",
        pr_state=pr_state(),
        expected_head=HEAD,
        local_head=HEAD,
        local_branch="feature/branch",
        worktree_status="",
    ) == (HEAD, BASE)
    validate(packet())


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"expected_head": "c" * 40}, "exactly equal"),
        ({"actor": "reviewer"}, "must be the pull-request author"),
        ({"local_branch": "other"}, "local branch"),
        ({"worktree_status": " M file"}, "must be clean"),
    ],
)
def test_live_context_fails_closed(override: dict, message: str) -> None:
    args = {
        "actor": "author",
        "pr_state": pr_state(),
        "expected_head": HEAD,
        "local_head": HEAD,
        "local_branch": "feature/branch",
        "worktree_status": "",
    }
    args.update(override)
    with pytest.raises(MODULE.HandbackError, match=message):
        MODULE.validate_live_context(**args)


def test_packet_rejects_changed_path_mismatch() -> None:
    value = packet()
    value["changed_paths"] = ["src/a.py"]
    with pytest.raises(MODULE.HandbackError, match="changed paths"):
        validate(value)


@pytest.mark.parametrize("status", ["FAIL", "NOT_RUN"])
def test_packet_rejects_unmet_acceptance(status: str) -> None:
    value = packet()
    value["acceptance"][0]["status"] = status
    with pytest.raises(MODULE.HandbackError, match="is not PASS"):
        validate(value)


def test_packet_rejects_exit_code_without_observed_semantics() -> None:
    value = packet()
    value["acceptance"][0]["observed"] = ""
    with pytest.raises(MODULE.HandbackError, match="non-empty observed"):
        validate(value)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("status", "NOT_RUN", "did not complete"),
        ("exit_code", 1, "did not complete"),
        ("failed", 1, "failures or errors"),
        ("errors", 1, "failures or errors"),
    ],
)
def test_packet_rejects_incomplete_or_failing_validation(
    field: str, value: object, message: str
) -> None:
    evidence = packet()
    evidence["validation_runs"][0][field] = value
    with pytest.raises(MODULE.HandbackError, match=message):
        validate(evidence)


def test_packet_requires_validation_run() -> None:
    evidence = packet()
    evidence["validation_runs"] = []
    with pytest.raises(MODULE.HandbackError, match="at least one completed"):
        validate(evidence)


def test_changed_path_query_paginates_without_new_gh_flags(monkeypatch) -> None:
    pages = [
        [{"filename": f"path/{index}.py"} for index in range(100)],
        [{"filename": "path/final.py"}],
    ]
    calls = []

    def fake_run_json(*args, **kwargs):
        calls.append(args)
        return pages[len(calls) - 1]

    monkeypatch.setattr(MODULE, "run_json", fake_run_json)
    paths = MODULE.query_changed_paths("owner/repo", 123)
    assert len(paths) == 101
    assert calls[0][-1].endswith("page=1")
    assert calls[1][-1].endswith("page=2")


def test_rendered_handback_is_exact_head_and_complete() -> None:
    body = MODULE.render_handback(
        packet(), state="AWAITING_GOVERNANCE_REVIEW", packet_sha="d" * 64
    )
    assert f"<!-- author-handback:{HEAD} -->" in body
    assert f"- Head: `{HEAD}`" in body
    assert "## Acceptance evidence" in body
    assert "## Validation runs" in body
    assert "pass=10 fail=0 error=0" in body
    assert "43 measures; no partial-grouping warning" in body
    assert body.endswith("AWAITING_GOVERNANCE_REVIEW")
