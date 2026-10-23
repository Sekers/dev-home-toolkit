# dev-home: guidance for AI agents

This is my private repo for project handoffs and a general knowledge base, shared by my PCs
through GitHub. The tooling that works with it (the skills, the always-on operating rules,
setup.py, and sync.py) lives in my clone of dev-home-toolkit, at `{{TOOLKIT_DIR}}`.

## Privacy

- This repo is private. Treat my project repos as public.
- Never copy, quote, paraphrase, or mention anything from this repo in a project's files,
  commits, PRs, or issues. The one exception is an issue I approve word for word through the
  handoff skill's `issue` command, and even that never mentions this repo.
- No secrets, credentials, tenant or account IDs, or personal information about anyone other
  than me, anywhere here. Say where a secret is kept, never its value.

## What's here

- `handoffs/<service>/<project path>/HANDOFF.md`: one per project, filed by where it's hosted,
  such as `handoffs/github/you/tool/`. Projects hosted elsewhere go under `handoffs/other/`,
  and projects with no remote under `handoffs/local/`, by folder name and first commit. The
  handoff skill finds, reads, and updates them.
- `knowledge/`: my general knowledge base. `knowledge/README.md` is its index; the rules for
  files come with the knowledge skill.
- `rules/`: my rules, my own always-on preferences, which every session loads after the
  operating rules from dev-home-toolkit. `_all-agents/mine/` holds those for every agent on every
  PC, `<agent>/mine/` those for one agent (`claude-code`, `codex`), and
  `pcs/<pc>/_all-agents/mine/` and `pcs/<pc>/<agent>/mine/` the same for one PC alone, where
  `<pc>` is the PC's name in lowercase, with any character other than a letter or a digit as a
  hyphen. Add a rule to `my-rules.md` in the right folder, never to the rules file setup joins
  them into for each agent. Keep them short: every line costs tokens in every session.
- `skills/`: my personal skills, if any. Setup links them into Claude Code and Codex.
- `.drafts/`: git-ignored scratch space for text that leaves this repo, such as GitHub issue
  bodies. Nothing in it is ever committed.

## Personal skills (skills/)

- Frontmatter uses only standard fields: `name`, `description`, and `allowed-tools`. The name
  matches the folder name.
- After adding, renaming, or removing one, run
  `{{PYTHON}} -I {{TOOLKIT_DIR}}/setup.py --quiet`.

## Git

- Sessions in several projects, and Codex, use this repo at the same time, so a file you didn't
  change may be someone's work in progress. Never stage, commit, stash, reset, or discard it.
- Run git here only through `{{PYTHON}} -I {{TOOLKIT_DIR}}/sync.py`. It syncs with GitHub; add
  `--message "<area>: <what>"` and the paths to commit exactly those paths first. Show its
  `PROBLEM` lines to me.
- Never delete a lock file such as `.git/index.lock`. If sync.py says git stayed busy, ask me.
- Commit messages read `<area>: <what>`, for example `handoff: you/tool` or
  `knowledge: powershell/pipeline-binding`.
- Commit signing is turned off in this repo's own config on purpose. That is not bypassing
  signing; my project repos keep signing.
