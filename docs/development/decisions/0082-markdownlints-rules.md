# 0082: markdownlint's rules

**Built:** yes.

**Decision:** `.markdownlint.jsonc`, in the root, holds markdownlint's rules for this repo: prose
and headings wrap at 100 characters, and code blocks and tables have no limit (rule MD013). Every
other rule keeps markdownlint's default. A command in a skill stays on one line, even past 100.
Decided by the developer on 2026-10-22.

**Why:**

- markdownlint checks lines at 80 characters by default, and this repo wraps at 100, so about half
  its Markdown lines warned (4,262 of 8,422 on 2026-10-22), and Claude Code's VS Code extension
  hands an edited file's warnings to the agent after each edit: from a few KB to about 400 KB of
  text per edit (seen 2026-10-22). At 100, with code blocks and tables left out, 18 lines warned.
  Once 12 were rewrapped, and a sample output line moved into a code block, 5 did: commands in
  the skills, which stay on one line because agents copy them and the tests match them word for
  word.
- In the root: markdownlint looks for its rules in a Markdown file's folder and the folders above
  it, so only the root covers every Markdown file in the repo with no setting, for every program
  that runs markdownlint: VS Code's extension and editors built on VS Code, other editors'
  integrations, most of which run markdownlint-cli2, and a pre-commit hook or a check on GitHub,
  if one is added. It's where developers look for it, and one file does it all. The development
  tools' `pyproject.toml` stays in `internal/development/`
  ([0016: The root](0016-the-root.md)) because the development commands name it and its
  environment and caches would come with it; no command could name this file, and nothing comes
  with it.
- In the repo, rather than in each developer's own config file: every developer and every PC gets
  the same rules, with no step by hand.

**Costs:** one more file in the root. The markdownlint extension isn't one of the development
tools: a developer without it gets nothing from the file, and needs nothing from it.

**Options set aside:**

- The file in `internal/development/`, named by `markdownlint.configFile` in
  `.vscode/settings.json`: only VS Code and editors built on it would find it, and it takes a file
  and a setting.
- `markdownlint.config` in `.vscode/settings.json`: the extension's documentation (version 0.62.1,
  read 2026-10-22) calls it deprecated.
- Only each developer's own config file, named in their user settings: it covers only their PCs,
  and nobody else who works on the repo.
- markdownlint's default of 80 characters: nearly every file would need rewrapping.
- A comment turning MD013 off on each command line in the skills: agents read HTML comments in a
  skill's body, so each would cost tokens on every skill command.
- Leaving the skills out of the check: their prose would go unchecked too.

**Look again if:** markdownlint gains a way to leave inline code out of MD013, or the tests start
checking the repo's Markdown with markdownlint.
