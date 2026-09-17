import os
from pathlib import Path
from unittest import mock
import pytest

import agent_workspace_cleanup as cleanup

def test_allowed_identities(monkeypatch):
    # Test default
    monkeypatch.delenv("CLEANUP_ALLOWED_IDENTITIES", raising=False)
    allowed = cleanup.get_allowed_identities()
    assert "tticom" in allowed
    assert "tticom-gov" in allowed
    
    # Test env override
    monkeypatch.setenv("CLEANUP_ALLOWED_IDENTITIES", "test-user,another-user")
    allowed = cleanup.get_allowed_identities()
    assert allowed == {"test-user", "another-user"}

def test_resolve_workspace_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SCORE2GP_WORKSPACE", str(tmp_path))
    assert cleanup.resolve_workspace() == tmp_path.resolve()

def test_resolve_workspace_default(monkeypatch, tmp_path):
    monkeypatch.delenv("SCORE2GP_WORKSPACE", raising=False)
    monkeypatch.delenv("WORKSPACE_ROOT", raising=False)
    monkeypatch.delenv("AGY_WORKSPACE_DIR", raising=False)
    
    # We patch __file__ in the module to be inside our tmp_path to test the climbing logic
    fake_script = tmp_path / "workspace" / "agy-skills" / "plugin" / "scripts" / "agent_workspace_cleanup.py"
    fake_script.parent.mkdir(parents=True)
    fake_git = tmp_path / "workspace" / "agy-skills" / ".git"
    fake_git.mkdir(parents=True)
    
    with mock.patch.object(cleanup, "__file__", str(fake_script)):
        resolved = cleanup.resolve_workspace()
        assert resolved == (tmp_path / "workspace").resolve()

def test_discover_repos(tmp_path):
    repo1 = tmp_path / "repo1"
    repo1.mkdir()
    (repo1 / ".git").mkdir()
    
    repo2 = tmp_path / "repo2"
    repo2.mkdir()
    
    repos = cleanup.discover_repos(tmp_path)
    assert len(repos) == 1
    assert repos[0] == repo1

@mock.patch("agent_workspace_cleanup.run_cmd")
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
    
    wts = cleanup.get_worktrees(Path("/path/to/repo"))
    assert len(wts) == 4
    
    assert wts[0]["path"] == "/path/to/canonical"
    assert wts[0]["branch"] == "main"
    assert "locked" not in wts[0]
    
    assert wts[1]["path"] == "/path/to/review-1"
    assert wts[1]["branch"] == "review-1"
    assert wts[1]["locked"] == "in-progress manual review"
    
    assert wts[2]["path"] == "/path/to/review-2"
    assert wts[2]["detached"] is True
    
    assert wts[3]["path"] == "/path/to/pruned"
    assert wts[3]["prunable"] == "missing directory"

@mock.patch("agent_workspace_cleanup.run_cmd")
def test_is_dirty(mock_run_cmd):
    mock_run_cmd.return_value.stdout = " M file.txt\n"
    assert cleanup.is_dirty(Path("/path/to/repo")) is True
    
    mock_run_cmd.return_value.stdout = ""
    assert cleanup.is_dirty(Path("/path/to/repo")) is False

@mock.patch("agent_workspace_cleanup.run_cmd")
def test_is_stale_review_active(mock_run_cmd):
    # If the branch is not merged and the PR is OPEN, it's NOT stale
    def side_effect(cmd, **kwargs):
        res = mock.Mock()
        if "branch" in cmd:
            res.returncode = 0
            res.stdout = "main\n" # Branch not in merged list
        elif "gh" in cmd:
            res.returncode = 0
            res.stdout = '{"state": "OPEN"}'
        return res
    mock_run_cmd.side_effect = side_effect
    
    assert cleanup.is_stale_review(Path("/repo"), "my-active-review") is False

@mock.patch("agent_workspace_cleanup.run_cmd")
def test_is_stale_review_merged(mock_run_cmd):
    # If the branch is merged to main, it's stale
    def side_effect(cmd, **kwargs):
        res = mock.Mock()
        if "branch" in cmd:
            res.returncode = 0
            res.stdout = "main\nmy-merged-review\n" 
        return res
    mock_run_cmd.side_effect = side_effect
    
    assert cleanup.is_stale_review(Path("/repo"), "my-merged-review") is True

def test_is_stale_review_detached():
    # A detached head (no branch) must be preserved
    assert cleanup.is_stale_review(Path("/repo"), "") is False
    assert cleanup.is_stale_review(Path("/repo"), None) is False
