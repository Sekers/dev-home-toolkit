# 0006: Commands as a skill loads

**Built:** nothing to build.

**Decision:** no skill uses Claude Code's `` !`command` `` lines, which run a command as the
skill loads and put its output in the skill's text.

**The option:** run `prepare.py` that way, saving one more turn per skill command in Claude Code.
Codex would get the line as text, and run the command itself.

**Why not:** when the command can't run cleanly, the whole skill aborts before the model sees
it, with a raw error and nothing to explain it. Tested on 2026-10-02 with Claude Code 2.1.284,
through `claude -p` and probe skills:

- It runs for a typed command and when the model starts the skill, again at each use, in the
  session's folder, and the model sees the output.
- A command that exits non-zero, or one no rule allows, aborts the skill.
- With the PowerShell tool on, as it is by default on Windows with a claude.ai account, a Claude
  Code that can't find Git Bash runs the command through the PowerShell tool, which refuses one
  that starts `pwsh`, and the skill aborts. That happened with `claude` started from a Git Bash
  terminal. With `shell: bash` in the frontmatter it aborts too, saying Git Bash wasn't found.
- A slow command holds the skill back until it finishes, and Claude Code's docs give it 2
  minutes.

Without it, each of those cases still works, with a prompt or a slow call. Knowledge lookups
couldn't use it either, since they never sync.

**Look again if:** Claude Code passes a failed command's output to the model instead of
aborting, or finds Git Bash however it was started. Since `prepare.py` always exits 0, each
skill would need only the one line.
