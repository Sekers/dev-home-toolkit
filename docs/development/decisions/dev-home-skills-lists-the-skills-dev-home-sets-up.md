# /dev-home skills lists the skills dev-home sets up

**Decision:** `/dev-home skills` lists every skill setup sets up: dev-home-tools' own, then the
person's from `skills/` in dev-home, each with whose it is and its description. It says when one
of theirs isn't set up because a dev-home-tools skill has its name, as setup does. The list comes
from a `skills` topic in `facts.py`, so it reads only this PC's files, never syncs, and works in
Codex too.

**Why:** turning skills on and off is planned, with a default set that dev-home-tools chooses,
so some of its skills may ship turned off, and this list is where people find them. Listing takes
no judgment, so it belongs in a script (see [skills.md](../skills.md)), and a `facts.py` topic is
one pre-approved command that costs a Python start only when someone types it. `skills` names what
it shows, and turning skills on and off can sit under the same word later.

**Options set aside:**

- Also listing skills in the tools' own folders that setup didn't put there, or every skill
  installed, such as Anthropic's synced skills, plugins, and Codex's `.system` skills: they
  aren't dev-home's, and each tool can list its own.
- Only the person's own skills: dev-home-tools' skills that ship turned off couldn't be found.
- `/dev-home list`: a general verb, which would need a second word once anything else is listed.
- Showing where each skill is linked: `facts.py` would need a second copy of setup's rules for
  which Claude folders it sets up, and setup already reports a link problem on every sync.

**Look again if:** skills can be turned on and off, when the list should show each one's state,
or people need to see where each skill is linked.
