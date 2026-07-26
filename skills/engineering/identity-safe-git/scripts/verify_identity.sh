#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: verify_identity.sh --os-user USER --home PATH --host-login LOGIN --git-name NAME --git-email EMAIL --repo-prefix PATH" >&2
  exit 64
}

os_user=
expected_home=
host_login=
git_name=
git_email=
repo_prefix=

while (($#)); do
  case "$1" in
    --os-user) os_user=${2-}; shift 2 ;;
    --home) expected_home=${2-}; shift 2 ;;
    --host-login) host_login=${2-}; shift 2 ;;
    --git-name) git_name=${2-}; shift 2 ;;
    --git-email) git_email=${2-}; shift 2 ;;
    --repo-prefix) repo_prefix=${2-}; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$os_user" && -n "$expected_home" && -n "$host_login" &&
   -n "$git_name" && -n "$git_email" && -n "$repo_prefix" ]] || usage

fail() {
  echo "identity gate failed: $1" >&2
  exit 1
}

actual_user=$(whoami)
[[ "$actual_user" == "$os_user" ]] ||
  fail "OS user is '$actual_user', expected '$os_user'"

[[ "$HOME" == "$expected_home" ]] ||
  fail "HOME is '$HOME', expected '$expected_home'"

command -v git >/dev/null || fail "git is unavailable"
command -v gh >/dev/null || fail "gh is unavailable"

root=$(git rev-parse --show-toplevel 2>/dev/null) ||
  fail "current directory is not inside a Git worktree"
root=$(realpath "$root")
prefix=$(realpath "$repo_prefix")
case "$root" in
  "$prefix"|"$prefix"/*) ;;
  *) fail "repository '$root' is outside '$prefix'" ;;
esac

remote_login=$(gh api user --jq .login 2>/dev/null) ||
  fail "cannot read authenticated Git host identity"
[[ "$remote_login" == "$host_login" ]] ||
  fail "Git host login is '$remote_login', expected '$host_login'"

actual_name=$(git config --get user.name || true)
[[ "$actual_name" == "$git_name" ]] ||
  fail "Git author name is '$actual_name', expected '$git_name'"

actual_email=$(git config --get user.email || true)
[[ "$actual_email" == "$git_email" ]] ||
  fail "Git author email is '$actual_email', expected '$git_email'"

branch=$(git branch --show-current)
head=$(git rev-parse HEAD)

printf 'identity gate passed\n'
printf 'os_user=%s\n' "$actual_user"
printf 'home=%s\n' "$HOME"
printf 'host_login=%s\n' "$remote_login"
printf 'git_name=%s\n' "$actual_name"
printf 'git_email=%s\n' "$actual_email"
printf 'repo_root=%s\n' "$root"
printf 'branch=%s\n' "$branch"
printf 'head=%s\n' "$head"
