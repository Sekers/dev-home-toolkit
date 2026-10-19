# claudeMdExcludes for another Claude Code folder

On 2026-10-19, these tests checked whether `claudeMdExcludes` in a second Claude Code folder's
`settings.json` keeps `~/.claude`'s instructions out of that account's sessions, and which form of
pattern works on Windows. They are the evidence for the decision
[Other Claude Code folders skip ~/.claude's instructions](../decisions/other-claude-code-folders-skip-claudes-instructions.md).

## Results

- **The leak:** with no pattern, a session of a second account (`CLAUDE_CONFIG_DIR` set to its
  own folder), started in a folder under the profile folder, loaded both `~/.claude/CLAUDE.md` and
  a file in `~/.claude/rules/`, each labeled "project instructions, checked into the codebase" (2
  runs).
- **The profile folder by name:** `**/<profile folder name>/.claude/CLAUDE.md` and
  `**/<profile folder name>/.claude/rules/**` kept both files out, whether the session's folder
  started with `C:` or `c:` (2 runs each).
- **Full paths:** `C:/Users/<you>/.claude/CLAUDE.md` and the matching rules pattern kept both out
  only when the drive letter's case matched the session's folder. A pattern starting `C:` let both
  in for a session in `c:\...`, and one starting `c:` did for a session in `C:\...`. VS Code
  starts sessions with either case.
- **Special characters** in a folder's name, tested on test folders above the session's folder,
  each with its own `.claude/CLAUDE.md`: written as they are, `{`, `}`, `!`, `@`, and a space
  matched, but `(` and `)` didn't. Escaped with a backslash, none matched but the space. With `?`
  in place of each special character, all five matched.
- **The 8.3 short name:** a session started from the short form of the profile folder's path,
  such as `C:\Users\<short name>\...`, saw the files under that form, so no pattern with the long
  name matched them.
- A pattern in the account's own `settings.json` kept `~/.claude/CLAUDE.md` out the same way as
  one passed with `--settings`.

## How it was run

- Claude Code 2.1.301, the build in the VS Code extension, on Windows 11. Each run was a
  `claude -p` session on Sonnet, with the file tools turned off, asked for the made-up marker words
  in the files in its context, and the header line of each file that held one.
- Each marker file held one made-up word, and nothing else on the way up from the session's folder
  had a `CLAUDE.md`.
- To test one pattern alone, a run left out the account's own settings
  (`--setting-sources project,local`) and passed the pattern with `--settings`.
- A run's drive-letter case came from the working folder its process was started in.
- The special characters were tested on test folders, since a profile folder can't be renamed for
  a test. The walk treats every folder above the session's folder the same way.

## Limits

- The case of the profile folder's own name wasn't tested. A session started from a path typed in
  another case, such as `c:\users\YOU\...`, may get past the patterns, since the drive letter's
  case matters.
- Two runs in a first batch, which started from the short name by mistake, didn't see the files
  even with no pattern. That wasn't explained, and the later runs from the long name were
  consistent.
- One PC, Windows only, and one or two runs for each case.

## When to redo it

When Claude Code changes how it walks up from a session's folder: Anthropic said on
[anthropics/claude-code#79233](https://github.com/anthropics/claude-code/issues/79233) that the
walk will skip `~/.claude/`. Also when it changes how `claudeMdExcludes` matches, and before setup
supports macOS or Linux.
