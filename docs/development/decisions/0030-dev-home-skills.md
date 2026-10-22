# 0030: /dev-home skills

**Built:** yes.

**Decision:** `/dev-home skills` lists every skill: dev-home-toolkit's own, then the person's from
`skills/` in dev-home, each with whose it is, its state, and its description. The state says
whether the skill is added and why, from the result setup records in `internal/.generated/`, and
a skill setup hasn't seen yet, such as one made since the last sync, says so. A copied skill's
`compatibility` text follows its description. A program or a Python version a skill needs only
warns, and `facts.py` checks it again each time, where the agent runs, from what setup recorded
([0062: Keeping a skill off](0062-keeping-a-skill-off.md)). It says when one of the person's
skills isn't added because a dev-home-toolkit skill has its name, as setup does. The list comes
from a `skills` topic in `facts.py`, so it reads only this PC's files, never syncs, and works in
Codex too. Changed on 2026-10-16 and 2026-10-17.

**Why:** a PC adds some skills and not others, by each skill's default and the person's answers
([0035: Skills per PC](0035-skills-per-pc.md)), so some of dev-home-toolkit's skills may not be
added, and this list is where people find them. The state comes from what setup records, so
`facts.py` needs no copy of setup's rules ([0057: Requirements](0057-requirements.md)). Listing
takes no judgment, so it belongs in a script (see [skills.md](../skills.md)), and a `facts.py`
topic is one pre-approved command that costs a Python start only when someone types it. `skills`
names what it shows, and other commands about skills can sit under the same word later.

**Options set aside:**

- Also listing skills in the agents' own folders that setup didn't put there, or every skill the
  agents have, such as Anthropic's synced skills, plugins, and Codex's `.system` skills: they
  aren't dev-home's, and each agent can list its own.
- Only the person's own skills: dev-home-toolkit's skills that aren't added couldn't be found.
- `/dev-home list`: a general verb, which would need a second word once anything else is listed.
- Showing where each skill is linked: setup already reports a link problem on every sync. (The
  other reason, that `facts.py` would need a copy of setup's rules, no longer holds, since it reads
  what setup records.)

**Look again if:** people need to see where each skill is linked.
