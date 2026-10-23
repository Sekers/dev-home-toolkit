# dev-home

My private repo for AI-agent handoffs and a general knowledge base, kept on GitHub with its full
history as a backup, and shared by my PCs when I use more than one. My public project repos never
reference it.

The tooling that works with it lives in dev-home-toolkit, at `{{TOOLKIT_DIR}}`. Its README covers
setup, a typical day, and safety, and lists the rest of its docs.

| Path | What it is |
| --- | --- |
| `handoffs/<service>/<project path>/HANDOFF.md` | Private session state for one project, filed by where it's hosted, such as `handoffs/github/you/tool/`. Projects hosted elsewhere go in `handoffs/other/`, and projects with no remote in `handoffs/local/`, by folder name and first commit. Read and updated with `/handoff`. |
| `knowledge/` | General knowledge for coding and AI work. `knowledge/README.md` is the index. |
| `rules/` | My rules: my own always-on preferences, which every session loads after the operating rules from dev-home-toolkit. `_all-agents/mine/` holds the rules for every agent on every PC, `claude-code/mine/` and `codex/mine/` those for one agent, and `pcs/<pc>/_all-agents/mine/` and `pcs/<pc>/<agent>/mine/` the same for one PC alone, where `<pc>` is the PC's name in lowercase, with any character other than a letter or a digit as a hyphen. Setup gives each a `my-rules.md`, and joins them into a rules file for each agent, which it rewrites: edit the rules here. |
| `skills/` | My personal skills, if any. Setup links them into Claude Code and Codex. |
| `dev-home.json` | Settings every copy of this repo shares. `multiMachine` is `false` while one copy is in active use, so a sync checks GitHub only every few hours, and `true` once more are, so each command checks first. Setup asks, and commits the answer. `schemaVersion` says which layout the file has. Setup tells this repo is a dev-home by this file, so it stays. |
| `AGENTS.md`, `CLAUDE.md` | Guidance for an agent working inside this repo. Setup writes both on each PC with that PC's commands, so git ignores them, and rewrites them on every run, so my own guidance for agents goes in `rules/`. |
| `.drafts/` | Scratch space for text that leaves this repo, such as GitHub issue bodies. Git ignores it. |
