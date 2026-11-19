# 0013: Telling a session its skill changed

**Built:** yes.

**Decision:** setup stamps each skill with a fingerprint of its `SKILL.md`: `s`, then the first
12 hex digits of a SHA-256 of the text with this PC's paths filled in, written into the skill's
own commands as `--skill <name> --stamp <stamp>`. `prepare.py` and `facts.py` compare the stamp
they're given with the one in that `SKILL.md` on disk. When they differ, `prepare.py` prints a
`RELOAD` line, and `facts.py` an error, saying the session's steps are out of date and to ask the
end user to run the skill's command again. Neither prints any facts then, so the old steps can't
carry on. Changed by the developer on 2026-11-19 (the `s`).

**The problem:** an agent keeps the text of a skill it has loaded. When an update changes the
skill partway through a session, the agent follows the old steps, which may run scripts that
have changed or are gone.

**Why the stamp:** every skill command that changes anything starts with `prepare.py`, after the
sync that may install the change, so this catches any change to a skill, not just renamed
scripts. It adds a file read and a comparison, and no process. Typing a skill's command again
loads its new text and its new pre-approvals, with no need for a new session (tested); an agent
that invokes the skill again itself is asked first outside auto mode, so the skill asks the end
user instead.

**Why the `s`:** on Windows, Codex's command rules don't match a command with an unquoted word
that starts with a digit, unless the word is a whole number, and about 10 stamps in 16 would
start with one ([0094: Pre-approved commands](0094-pre-approved-commands.md)). A letter first
keeps every stamp a plain word in every shell, so neither a command nor an agent has to quote it.

**Options set aside:**

- The stamp in single quotes: it works in every shell, but every command, and every agent that
  copies one, has to keep the quotes, and the tests' helpers split commands at spaces.
- `--stamp=<stamp>` as one word: a second spelling of the option
  ([0017: Command-line options](0017-command-line-options.md)).

**Look again if:** the agents reload a skill by themselves when its file changes.
