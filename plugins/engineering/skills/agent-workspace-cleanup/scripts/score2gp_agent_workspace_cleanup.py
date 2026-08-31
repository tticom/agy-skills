#!/usr/bin/env python3
"""Agent Workspace Cleanup Skill
Safely identifies and removes stale Git worktrees, prunable metadata, generated
artifacts, and untracked files across agent identities without deleting active
or uncommitted work.
"""
import json
import subprocess
import sys
import os
import getpass
from pathlib import Path
import datetime

ALLOWED_IDENTITIES = {"tticom", "tticom-gov", "tticom-automation", "tticom-codex", "niall"}

def run_cmd(cmd, cwd=None, check=True):
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{res.stderr}")
    return res

def is_dirty(path):
    res = run_cmd(["git", "status", "--porcelain"], cwd=path)
    return bool(res.stdout.strip())

def get_worktrees(repo_path):
    res = run_cmd(["git", "worktree", "list", "--porcelain"], cwd=repo_path)
    worktrees = []
    current_wt = {}
    for line in res.stdout.splitlines():
        if line.startswith("worktree "):
            if current_wt:
                worktrees.append(current_wt)
            current_wt = {"path": line.split(" ", 1)[1]}
        elif line.startswith("branch "):
            current_wt["branch"] = line.split(" ", 1)[1]
        elif line.startswith("locked"):
            current_wt["locked"] = line.split(" ", 1)[1] if " " in line else "locked"
        elif line.startswith("prunable"):
            current_wt["prunable"] = line.split(" ", 1)[1] if " " in line else "prunable"
        elif line == "detached":
            current_wt["detached"] = True
    if current_wt:
        worktrees.append(current_wt)
    return worktrees

def discover_repos(workspace):
    repos = []
    for d in workspace.iterdir():
        if d.is_dir() and (d / ".git").exists():
            repos.append(d)
    return repos

def resolve_workspace():
    if "SCORE2GP_WORKSPACE" in os.environ:
        return Path(os.environ["SCORE2GP_WORKSPACE"]).resolve()
    if "WORKSPACE_ROOT" in os.environ:
        return Path(os.environ["WORKSPACE_ROOT"]).resolve()
    
    script_dir = Path(__file__).resolve().parent
    workspace = script_dir.parent.parent.parent.parent.parent.parent
    return workspace

def main():
    dry_run = "--dry-run" in sys.argv
    
    user = getpass.getuser()
    if user not in ALLOWED_IDENTITIES:
        print(f"Workspace path invalid or unsafe. Identity {user} not allowed.")
        sys.exit(1)

    workspace = resolve_workspace()
    
    if not workspace.exists() or "/tmp" in str(workspace) or "/mnt/c" in str(workspace):
        print(f"Workspace path invalid or unsafe: {workspace}")
        sys.exit(1)
        
    repos = discover_repos(workspace)
    receipt = []
    
    for repo in repos:
        print(f"Scanning {repo.name}...")
        
        prune_cmd = ["git", "worktree", "prune"]
        if dry_run:
            prune_cmd.append("--dry-run")
            
        prune_res = run_cmd(prune_cmd, cwd=repo, check=False)
        if prune_res.returncode == 0 and prune_res.stdout.strip():
            receipt.append({"action": "pruned_metadata" if not dry_run else "dry_run_prune", "path": str(repo), "reason": prune_res.stdout.strip()})
        
        worktrees = get_worktrees(repo)
        
        for wt in worktrees:
            wt_path = Path(wt["path"])
            if wt_path == repo:
                continue
                
            is_review = "-review-pr-" in wt_path.name or wt_path.name.endswith("-review")
            if not is_review:
                print(f"Skipping unclassified worktree: {wt_path}")
                receipt.append({"action": "preserved", "path": str(wt_path), "reason": "unknown/unclassified worktree"})
                continue
                
            if "locked" in wt:
                print(f"Preserving locked worktree: {wt_path} ({wt['locked']})")
                receipt.append({"action": "preserved", "path": str(wt_path), "reason": f"locked worktree: {wt['locked']}"})
                continue

            try:
                if not wt_path.exists():
                    receipt.append({"action": "preserved", "path": str(wt_path), "reason": "prunable worktree directory missing"})
                    continue
                dirty = is_dirty(wt_path)
            except Exception as e:
                print(f"Error checking {wt_path}: {e}")
                receipt.append({"action": "error", "path": str(wt_path), "reason": str(e)})
                continue
                
            if dirty:
                print(f"Preserving dirty worktree: {wt_path}")
                receipt.append({"action": "preserved", "path": str(wt_path), "reason": "dirty worktree"})
                continue
                
            print(f"{'Would remove' if dry_run else 'Removing'} disposable worktree: {wt_path}")
            if not dry_run:
                try:
                    run_cmd(["git", "worktree", "remove", str(wt_path)], cwd=repo)
                    receipt.append({"action": "removed_worktree", "path": str(wt_path), "reason": "clean stale review worktree"})
                except Exception as e:
                    print(f"Failed to remove {wt_path}: {e}")
                    receipt.append({"action": "error", "path": str(wt_path), "reason": str(e)})
            else:
                receipt.append({"action": "dry_run_remove", "path": str(wt_path), "reason": "clean stale review worktree"})
                
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    receipt_file = workspace / "score2gp-agentops" / "projects" / "score2gp" / "runs" / f"{timestamp}-cleanup-receipt.json"
    receipt_file.parent.mkdir(parents=True, exist_ok=True)
    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2)
    print(f"Cleanup receipt written to {receipt_file}")

if __name__ == "__main__":
    main()
