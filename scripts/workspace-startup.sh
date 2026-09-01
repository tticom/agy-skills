#!/usr/bin/env bash
set -u

# Fetch every immediate checkout and fast-forward only clean checkouts already
# on main. Set WORKSPACE_ROOT when the script is installed outside the workspace.
workspace_root="${WORKSPACE_ROOT:-$(pwd)}"
workspace_root="$(cd "$workspace_root" && pwd)"
state_dir="$workspace_root/agy-logs/workspace-state"
state_file="$state_dir/latest.tsv"
mkdir -p "$state_dir"

printf 'repository\tbranch\thead\tstatus\taction\tremote\n' > "$state_file"

for repo_path in "$workspace_root"/*; do
  [ -d "$repo_path" ] || continue
  [ -e "$repo_path/.git" ] || continue

  repo_name="$(basename "$repo_path")"
  branch="$(git -C "$repo_path" branch --show-current 2>/dev/null || true)"
  remote="$(git -C "$repo_path" remote get-url origin 2>/dev/null || echo none)"
  status="clean"
  action="not-main"

  if [ -n "$(git -C "$repo_path" status --porcelain=v1 2>/dev/null)" ]; then
    status="dirty"
  fi

  if [ "$branch" = "main" ] && [ "$status" = "clean" ] && [ "$remote" != "none" ]; then
    if git -C "$repo_path" fetch --prune origin >/dev/null 2>&1; then
      if git -C "$repo_path" show-ref --verify --quiet refs/remotes/origin/main; then
        if git -C "$repo_path" merge --ff-only origin/main >/dev/null 2>&1; then
          action="updated-or-current"
        else
          action="diverged-or-not-fast-forward"
        fi
      else
        action="no-origin-main"
      fi
    else
      action="fetch-failed"
    fi
  elif [ "$branch" = "main" ] && [ "$status" = "dirty" ]; then
    action="skipped-dirty"
  elif [ -z "$branch" ]; then
    action="skipped-detached"
  fi

  head="$(git -C "$repo_path" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$repo_name" "${branch:-detached}" "$head" "$status" "$action" "$remote" >> "$state_file"
  printf '%-42s %-35s %-8s %-24s %s\n' "$repo_name" "${branch:-detached}" "$head" "$action" "$remote"
done

printf '\nState manifest: %s\n' "$state_file"
