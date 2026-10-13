# A stamp tells a session that its skill has changed

**Decision:** setup stamps each skill with a fingerprint of its `SKILL.md`: the start of a SHA-256
of the text with this PC's paths filled in, written into the skill's own commands as
`--skill <name> --stamp <stamp>`. `prepare.py` and `facts.py` compare the stamp they're given
with the one in that `SKILL.md` on disk. When they differ, `prepare.py` prints a `RELOAD` line,
and `facts.py` an error, saying the session's steps are out of date and to ask the end user to run
the skill's command again. Neither prints any facts then, so the old steps can't carry on.

**The problem:** an agent keeps the text of a skill it has loaded. When an update changes the
skill partway through a session, the agent follows the old steps, which may run scripts that
have changed or are gone.

**Why the stamp:** every skill command that changes anything starts with `prepare.py`, after the
sync that may install the change, so this catches any change to a skill, not just renamed
scripts. It adds a file read and a comparison, and no process. Typing a skill's command again
loads its new text and its new pre-approvals, with no need for a new session (tested); an agent
that invokes the skill again itself is asked first outside auto mode, so the skill asks the end
user instead.

**Look again if:** the tools reload a skill by themselves when its file changes.
