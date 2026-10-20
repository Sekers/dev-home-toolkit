# The skills are not shipped as plugins

**Decision:** not for now. Setup keeps filling in the skills and rules for each PC and linking
them into Claude Code and Codex.

**The option:** ship the skills, and perhaps hooks, as Claude Code and Codex plugins. That could
bring each agent's own install and updates, no junctions or Windows-only steps, and hooks that
enforce a rule instead of asking agents to follow it, such as blocking an edit under
`internal/.generated/`.

**Why not:** Codex would gain nothing, and Claude Code would gain little that setup can't
already do. Checked on 2026-09-30 against both agents' plugin docs, and with a test plugin in
Claude Code 2.1.284. Claude Code's mods docs were read on 2026-10-03, for 2.1.287:

- **Claude Code.** `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_SKILL_DIR}` are filled in inside
  `Bash(...)` pre-approvals (tested). The dev-home path could be a `userConfig` option, but that
  is filled in only in the skill's text. `sync.py` has to run from the clone, so the plugin
  would have to load in place, from the clone added as a local-directory marketplace; a plugin
  installed from GitHub is copied into a versioned cache. Commands become
  `/dev-home-toolkit:handoff`, though a bare `/handoff` still works while nothing else uses the
  name (tested).
- **Codex.** Its docs say "Plugins aren't available in the IDE extension." It copies even a
  local plugin into `~/.codex/plugins/cache/` and loads the copy, so each change needs a
  reinstall and a restart, and its docs name no path substitution in `SKILL.md`. Setup would
  still have to fill in and link the skills for Codex.
- **Always-on rules.** Codex doesn't load instruction files from a plugin, and Claude Code
  ignores a plugin's `CLAUDE.md`. Since Claude Code 2.1.287, though, a mod (a plugin with code
  that runs inside Claude Code) can add instruction files through its `prompt.context` event, as
  the built-in `agents-md` mod does for `AGENTS.md`. Its docs name no size limit. Whether a mod
  can add files that apply in every project, as these rules do, is untested. Either way, a mod
  would only match what the links setup makes already do at no cost, and it would bring
  downsides:
  - `--safe-mode` and `"disableAllHooks": true` turn installed mods off.
  - Mods don't run in the Desktop app's WSL sessions.
  - A mod runs with full access and no consent prompt.

  Without a mod, only a SessionStart hook could print the rules: capped at 10,000 characters in
  Claude Code and about 2,500 tokens by default in Codex, which also asks the end user to trust the
  hook again after every change.
- **What setup would still do.** Nearly everything, plus registering the plugin in each Claude
  config folder, and `update.py` would still pull the clone. Hooks don't need a plugin: setup
  could add them to `settings.json`, with the same consent as its other settings changes.

**Look again if:** Codex plugins work in its IDE extension and can load in place, or hooks
become worth having.
