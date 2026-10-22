# 0003: Scripts the skills share

**Built:** yes.

**Decision:** a script that more than one skill may run, and that only agents run, lives in
`templates/shared-skill-scripts/`. Setup generates one copy into
`internal/.generated/shared-skill-scripts/`, and every skill runs that copy. The first was
`facts.py`, which reports facts about where a session is running, one topic at a time.

**Why not a copy in each skill's folder:** most published skills are built that way, so that a
skill can be installed alone. These skills come with the toolkit, so that buys little here. One
path gives each command one text to pre-approve, where copies would give the same command a
different path in every skill, and a turned-off skill leaves nothing behind.

**Why not the root:** the root holds what a person may run by hand. A script there looks like
one of those.

**Why not inside `templates/skills/`:** setup and the tests treat every folder there as a skill:
setup generates and links only the ones with a `SKILL.md`, and removes any other folder from
`internal/.generated/skills/`, and the docs test wants a page in `docs/skills/` for each. A
shared folder there would need an exception in each of those.

**Why not `internal/`, or a folder of its own, run in place:** a half-finished edit to a script
that runs in place is live at once in every session on the PC. A generated script changes only
when setup runs, in the same run that rewrites the skill text that calls it, so the two files
are never out of step. A session that loaded the skill before that run still has the old text
until the end user runs the skill's command again, and the skill's stamp tells it so (see
[0013: Telling a session its skill changed](0013-telling-a-session-its-skill-changed.md)).
`templates/` is also where everything the agents get from this repo already lives.

**Why one script with topics, not one that does everything:** `facts.py` is safe to pre-approve
because it only reports, and only from this PC. A script that also changed things would lose
that, so anything a skill needs done goes in a script of its own.

**Look again if:** the skills are shipped without the toolkit, as a plugin for example (see
[0001: Plugins](0001-plugins.md)), where each
would need the scripts bundled with it.
