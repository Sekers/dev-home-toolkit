# Syncing at session start

Whether a sync run by an agent's session-start hook can give that session the rules it brings in,
and how similar projects keep a second PC current. Researched on 2026-10-20 for
[0076: A PC catching up](../decisions/0076-a-pc-catching-up.md).

## Test: a session-start hook that rewrites instruction files

- **How:** Claude Code 2.1.301, run as `claude -p` on Haiku, in a throwaway project whose
  `CLAUDE.md` and `.claude/rules/word.md` each held an old test word. A `SessionStart` hook
  (matcher `startup`, without `async`, so Claude Code waits for it) waited 2 s, then wrote a new
  word into both files. The prompt asked for both words.
- **Result:** the session answered with the old words, while both files held the new ones by the
  time it ended. Instruction files load before a session-start hook finishes, even one Claude Code
  waits for.
- **Limits:** only `claude -p` was tested. An interactive session runs these hooks in the
  background, and its first response waits for them; it's expected to load the old files too,
  since instruction files load at launch, but that's untested. Codex wasn't tested.
- **Redo when:** Claude Code's hooks docs describe a hook or setting that runs before instruction
  files load.

## What the docs say (read 2026-10-20)

- [Claude Code's hooks](https://code.claude.com/docs/en/hooks) and
  [memory](https://code.claude.com/docs/en/memory) pages: `CLAUDE.md` files, and rules without
  `paths`, load "at launch". Skill discovery "normally runs before SessionStart hooks finish", so a
  hook can return `reloadSkills` to rescan skills; nothing like it exists for instruction files.
  Interactive sessions run `SessionStart` hooks in the background, and Claude's first response
  waits for them. A hook with `"async": true` doesn't block, and its output arrives on the next
  turn. In `claude -p`, Claude Code kills an async hook still running at teardown. A hook's plain
  stdout goes into the session's context.
- [Codex's hooks](https://learn.chatgpt.com/docs/hooks) page: hooks are on by default.
  `SessionStart` fires at startup, resume, clear, compact, and fork, and its stdout goes into the
  session as developer context, about 2,500 tokens at most by default. A hook runs only once it's
  trusted, by its hash, so a changed hook waits for review in the CLI's `/hooks`. The page doesn't
  say whether hooks run inside the sandbox, or whether the IDE extension or the app runs them. An
  open issue, [openai/codex#35863](https://github.com/openai/codex/issues/35863), reports that the
  desktop app lists `SessionStart` hooks but never runs them.

## Similar projects (from their READMEs and docs, not their code)

| Project | When another PC gets the changes |
| --- | --- |
| [chezmoi](https://www.chezmoi.io/user-guide/daily-operations/) | When the person runs `chezmoi update`. `autoCommit` and `autoPush` act only where the change was made |
| [claude-nomad](https://github.com/funkadelic/claude-nomad) | When the person runs `nomad sync`. Its optional plugin only warns at session start that the setup has drifted |
| [claude-code-dotfiles](https://github.com/elizabethfuentes12/claude-code-dotfiles) | A shell function around `claude` pulls before Claude Code starts, and pushes after it exits |
| [Obsidian Git](https://github.com/vinzent03/obsidian-git) | Optional pull when Obsidian starts, and sync on an interval |

**Redo when:** this decision is looked at again.
