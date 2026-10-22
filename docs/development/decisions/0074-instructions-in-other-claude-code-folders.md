# 0074: Instructions in other Claude Code folders

**Built:** yes.

**Decision:** setup adds two patterns to `claudeMdExcludes` in the `settings.json` of each Claude
Code folder it sets up other than `~/.claude`: `**/<profile folder name>/.claude/CLAUDE.md` and
`**/<profile folder name>/.claude/rules/**`, with `?` in place of each character a pattern reads
as more than itself. A folder whose `settings.json` is really `~/.claude`'s, through a link, gets
none: setup compares the real paths of the folder and its `settings.json` with `~/.claude`'s on
every run, about 0.3 ms per Claude Code folder (measured on Windows, 2026-10-19). The yes to
setting up the folder approves them, as it approves the folder's other settings change
([0053: What a folder's yes approves](0053-what-a-folders-yes-approves.md)),
and the question says what they do and why. A no to the folder takes them back out, and leaves
any other pattern. Every run, quiet ones included, adds them when they're missing.

**Why:** Claude Code loads `CLAUDE.md`, `.claude/CLAUDE.md`, and `.claude/rules/` from every folder
above where a session starts. A session of another account, run with `CLAUDE_CONFIG_DIR` set to
that account's folder, started anywhere in the profile folder, reaches the profile folder on the
way up, and loads `~/.claude`'s `CLAUDE.md` and rules as "project instructions, checked into the
codebase": another account's instructions, presented as the project's own. Anthropic reproduced
both halves:
[anthropics/claude-code#80580](https://github.com/anthropics/claude-code/issues/80580) for
`CLAUDE.md`, and [#79233](https://github.com/anthropics/claude-code/issues/79233) for the rules,
where they said the walk will skip `~/.claude/`. Under
[0064: Each agent's rules file](0064-each-agents-rules-file.md),
each folder gets a rules file of its own, so every such session would also load the rules twice.
The tests behind the patterns' form are on the research page
[claudeMdExcludes for another Claude Code folder](../research/claude-md-excludes.md).

**Options set aside:**

- A question of its own, or a recommended setting the end user can turn down: the patterns grant
  nothing and only keep out files a session shouldn't load, and the question would come to every
  end user with a second account (the developer's choice, 2026-10-19).
- Full paths, such as `C:/Users/<you>/.claude/CLAUDE.md`: they stop matching when the session's
  folder starts with the drive letter in the other case, as VS Code sometimes starts sessions.
- Escaping special characters with a backslash: on Windows, it stops the pattern matching at all.
- Leaving it to each end user, with the workarounds Anthropic gives on those issues (the patterns
  by hand, starting sessions outside the profile folder, or keeping shared instructions in an
  imported file): most end users with two accounts wouldn't know they need them.
- Patterns in `~/.claude` too: nothing leaks into its own sessions, since the walk reaches the
  same files as its own user instructions, and a pattern there could keep those out.
- Checking for a link first, and comparing real paths only when one of the four paths is a link
  (about 0.12 ms per folder), or reading the attribute Windows sets on every kind of link (about
  0.07 ms, Windows only): both miss a link in a folder above, and save under half a millisecond
  (the developer's choice, 2026-10-19).

Not covered: a session started in the profile folder itself also reads `~/.claude/settings.json`
as the project's settings
([anthropics/claude-code#80791](https://github.com/anthropics/claude-code/issues/80791)), which
`claudeMdExcludes` can't change.

**Look again if:** Claude Code's walk skips `~/.claude/`: then setup takes the patterns back out of
every folder, as after a no. Also if a session started from a path with the profile folder's name
in another case gets past them, which the research page's limits leave open.
