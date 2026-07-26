# Identity profile example

```yaml
os_user: automation
home: /home/automation
host_login: automation-bot
git_name: automation-bot
git_email: automation@example.invalid
repo_prefix: /home/automation/work/example
protected_branches:
  - main
allowed_working_branches:
  - automation/*
permissions:
  push_working_branch: true
  submit_review: false
  approve: false
  merge: false
```

Store policy only. Never store tokens, credential paths, passwords, or private
keys.
