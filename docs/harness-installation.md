# Harness installation and maintenance

`plugins/` is the single source of truth. Do not hand-edit generated harness
manifests or the generated Codex `skills/` projection.

## Create or refresh the manifests

From the repository root, run:

```bash
python3 scripts/sync-harness-manifests.py
python3 scripts/sync-harness-manifests.py --check
```

The generator validates every `SKILL.md`, then creates:

- `skills/<name>/` as a flattened, generated copy of every source skill;
- `.codex-plugin/plugin.json`, pointing Codex at the single generated root;
- `.agents/plugins/plugin.json` for AGY, listing the promoted engineering and
  productivity skills;
- `.agents/plugins/marketplace.json` for installing the Codex plugin.

Add, rename, move, or remove skills only under `plugins/<bucket>/skills/`, then
rerun the generator. Keep the generated files in the same commit as the skill
change. CI should run the `--check` command so drift fails visibly.

## Install in Codex

Add this repository as a local marketplace once:

```bash
codex plugin marketplace add /absolute/path/to/agy-skills
```

Then install the plugin shown by `codex plugin list`:

```bash
codex plugin add agy-skills@agy-skills
```

Start a new Codex session after installing or updating a plugin. The `/` menu
is not the authoritative skill registry; skills are loaded from the installed
plugin and can be invoked by their skill name.

## Install in AGY

AGY consumes `.agents/plugins/plugin.json`. Validate the generated promoted
manifest with the AGY plugin validator, then install or reload the repository
plugin using the AGY plugin workflow. The `misc` and `in-progress` buckets are
kept in the Codex projection but remain outside AGY's promoted manifest.
