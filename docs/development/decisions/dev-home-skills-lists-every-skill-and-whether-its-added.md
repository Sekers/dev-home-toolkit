# /dev-home skills lists every skill and whether it's added

**Decision:** `/dev-home skills` lists every skill: dev-home-toolkit's own, then the person's from
`skills/` in dev-home, each with whose it is and its description. It says when one of theirs
isn't added because a dev-home-toolkit skill has its name, as setup does.
The list comes from a `skills` topic in `facts.py`, so it reads only this PC's files, never syncs,
and works in Codex too.

**Why:** turning skills on and off is planned, with a default set that dev-home-toolkit chooses,
so some of its skills may ship turned off, and this list is where people find them. Listing takes
no judgment, so it belongs in a script (see [skills.md](../skills.md)), and a `facts.py` topic is
one pre-approved command that costs a Python start only when someone types it. `skills` names what
it shows, and turning skills on and off can sit under the same word later.

**Options set aside:**

- Also listing skills in the agents' own folders that setup didn't put there, or every skill the
  agents have, such as Anthropic's synced skills, plugins, and Codex's `.system` skills: they
  aren't dev-home's, and each agent can list its own.
- Only the person's own skills: dev-home-toolkit's skills that ship turned off couldn't be found.
- `/dev-home list`: a general verb, which would need a second word once anything else is listed.
- Showing where each skill is linked: `facts.py` would need a second copy of setup's rules for
  which Claude Code folders it sets up, and setup already reports a link problem on every sync.

Later changed, on 2026-10-16: with skills added per PC and requirements checked per skills
folder, the list shows each skill's state, added or not and why, and a copied skill's
`compatibility` text, from the result setup records in `internal/.generated/`. So `facts.py`
needs no copy of setup's rules, which was the reason for not showing where each skill is linked
([Skills and releases declare their requirements as facts](skills-and-releases-declare-their-requirements-as-facts.md)).
Both are built: each line shows the state beside whose the skill is, and a skill setup hasn't
seen yet, such as one made since the last sync, says so; the `compatibility` text follows the
description. Changed on 2026-10-17: a program or a Python version a skill needs only warns, and
`facts.py` checks it again each time, where the agent runs, from what setup recorded
([Setup keeps a skill off only for its operating system or agent](setup-keeps-a-skill-off-only-for-its-operating-system-or-agent.md)).

**Look again if:** people need to see where each skill is linked.
