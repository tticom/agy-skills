import json
import os
from pathlib import Path
from unittest import mock

import pytest

from scripts.score2gp_agent_workspace_cleanup import (
    resolve_workspace,
    get_worktrees,
    is_dirty,
    discover_repos,
    ALLOWED_IDENTITIES,
)

def test_allowed_identities():
    assert "tticom" in ALLOWED_IDENTITIES
    assert "tticom-gov" in ALLOWED_IDENTITIES
    assert "tticom-automation" in ALLOWED_IDENTITIES
    assert "tticom-codex" in ALLOWED_IDENTITIES

def test_resolve_workspace(monkeypatch, tmp_path):
    monkeypatch.setenv("SCORE2GP_WORKSPACE", str(tmp_path))
    assert resolve_workspace() == tmp_path.resolve()

def test_discover_repos(tmp_path):
    repo1 = tmp_path / "repo1"
    repo1.mkdir()
    (repo1 / ".git").mkdir()
    
    repo2 = tmp_path / "repo2"
    repo2.mkdir()
    
    repos = discover_repos(tmp_path)
    assert len(repos) == 1
    assert repos[0] == repo1

@mock.patch("scripts.score2gp_agent_workspace_cleanup.run_cmd")
def test_get_worktrees(mock_run_cmd):
    porcelain_output = """worktree /path/to/canonical
branch refs/heads/main

worktree /path/to/review-1
branch refs/heads/review-1
locked in-progress manual review

worktree /path/to/review-2
detached

worktree /path/to/pruned
prunable missing directory
"""
    mock_run_cmd.return_value.stdout = porcelain_output
    
    wts = get_worktrees(Path("/path/to/repo"))
    assert len(wts) == 4
    
    assert wts[0]["path"] == "/path/to/canonical"
    assert wts[0]["branch"] == "refs/heads/main"
    assert "locked" not in wts[0]
    
    assert wts[1]["path"] == "/path/to/review-1"
    assert wts[1]["branch"] == "refs/heads/review-1"
    assert wts[1]["locked"] == "in-progress manual review"
    
    assert wts[2]["path"] == "/path/to/review-2"
    assert wts[2]["detached"] is True
    
    assert wts[3]["path"] == "/path/to/pruned"
    assert wts[3]["prunable"] == "missing directory"

@mock.patch("scripts.score2gp_agent_workspace_cleanup.run_cmd")
def test_is_dirty(mock_run_cmd):
    mock_run_cmd.return_value.stdout = " M file.txt\n"
    assert is_dirty(Path("/path/to/repo")) is True
    
    mock_run_cmd.return_value.stdout = ""
    assert is_dirty(Path("/path/to/repo")) is False
