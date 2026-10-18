# Setup keeps a skill off only for its operating system or agent

**Decision:** of what a skill's `dev-home-skill.json` lists, only its `supportedOn`, the
operating system (`os`) and the agent it works in (`agent`), keeps it off a PC or out of a skills
folder. What its `dependsOn` lists, a program (`program`) or a Python version (`python`), never
does when this PC seems to lack it: setup adds the skill, and warns.
Decided by the developer on 2026-10-17; for Python, later that day. The research and the whole
discussion are in [Skill requirements](../research/skill-requirements.md).

- The warning comes in three places:
  - Once, in the `NEW` line for a new skill, such as "'jira' (added to your agents; jira isn't
    on the PATH, and the skill uses it for filing and reading Jira issues)", where the program
    entry's `description` says what the skill uses it for. Setup looks where a newly started
    shell would: in its own `PATH`, and on Windows also in the saved one, read from the registry
    with no process, so a program installed after the agents started still counts. It's wrong
    only for a program that one shell alone adds, such as Git Bash's tools, and a wrong hint
    never changes a link.
  - In `/dev-home skills`, checked again each time in the agent's own shell. Setup records each
    skill's programs and Python minimum in `internal/.generated/skill-states.json`, and
    `facts.py` looks for each program on its own `PATH`, and compares the Python it runs with,
    the skills' own. It decides nothing: it says what's missing where the agent runs, which can
    differ from setup's hint, and that's the answer that counts.
  - In the skill itself: its first step that uses a program runs the program's version command,
    and says how to get it. The reference page asks this of anyone writing a skill, and
    `/handoff issue` already checks for `gh`.
- The warning is only for a skill that's added somewhere on this PC. One that isn't, by an
  answer, its default, or its `supportedOn`, gets none, since no agent uses it.
- A skill lists its programs for the skill as a whole, with no map of which feature needs which.
- For Python, setup checks the Python it runs on, which only dev-home-toolkit's own skills run, and,
  once the opt-in is built, the skills that opt in to being generated. For any other skill the
  check is a guess, as for a program, so keeping the skill off could hide one that works.
- Anything in `supportedOn` that the reader can't use keeps the skill off: an entry with a
  mistake, such as an `anyOf` that isn't a list, a type the list doesn't take, or a field the
  reader doesn't know, which may narrow the limit, such as a minimum agent version. Its writer
  meant to limit where the skill goes, so when setup can't read the limit, it assumes the limit
  applies. Anything in `dependsOn` that the reader can't use is ignored, and so is a field it
  doesn't know anywhere else in the file.
- Each is a `PROBLEM` line naming the file and the word, said once however often its word
  appears, which says what setup did: kept the skill off, or ignored it. Setup can't tell a
  misspelled word from one a newer dev-home-toolkit knows, or one made up, so the line gives every
  fix that may apply: for a type, update dev-home-toolkit, or describe the need in the skill's
  `compatibility` text; for a field, check its spelling, or update. When a word known in that
  place is close, such as a type the same list takes, the line first asks "Did you mean ...?",
  as git and Python suggest a near match, and keeps the rest of its advice. No skill declares a
  minimum dev-home-toolkit version.
- `/dev-home skills` shows a skill's `compatibility` text too: the Agent Skills standard's free
  text for what setup can't check.

**Why:**

- Whether a program can run is a fact about the shell the agent runs it in, not about the PC.
  Each shell has its own copy of `PATH`: on 2026-10-17, Claude Code's Bash tool had 29 folders
  and its PowerShell tool 23, `grep` was found from one and not the other, and `git` and `ssh`
  were different files from each. Setup can't see the agent's shell, so links decided by a
  program check flip a skill in and out between syncs started from different shells, and after
  an install until the agents restart.
- A skill kept off is invisible to the agent. In a live test, an agent with a skill whose program
  was missing said exactly what was missing; without the skill, it improvised in the wrong
  direction.
- Parts of a skill may work without a program, and the agent can work around what isn't blocked.
- The operating system and the agent are known exactly, and nobody can work around them.
- The end user's answer for each PC stays the switch for whether a PC wants a skill, and a skill
  that suits only some setups, such as one for a single work tracker, ships with
  `recommended: false`.
- Reporting an unknown word catches a misspelling, which the reader used to skip without a word,
  and tells the end user when a skill is newer than their copy. Keeping a skill off for a need no
  copy will ever know, such as a VPN under `dependsOn`, would be wrong; a limit setup can't read
  is kept, as above.

Established practice: the platform decides what's installed, while what the end user can fix only
warns. npm leaves out an optional dependency that can't run on the platform, while a package's
required Node.js version, its `engines`, only warns unless `engine-strict` is set (npm's
documentation, read 2026-10-17). Suggesting the closest known word for a misspelled one follows
git's and Python's own error messages. The three places for the warning, where setup looks, and the
recorded needs that `/dev-home skills` checks again are dev-home-toolkit's own design.

**Options set aside:**

- Keeping a skill off for a missing program, with setup looking:
  - in each run's own `PATH`, as first built: it flips between syncs from Bash and from
    PowerShell, and after an install;
  - in Windows' saved `PATH` alone: it misses Git Bash's tools, and works only on Windows;
  - in both: the flip between Bash and PowerShell stays;
  - wherever it once found the program: new stored state, and still a guess about the agent's
    shell.
- Adding a skill once its program is found, and never removing it: it keeps a skill after its
  program is uninstalled, and reverses the decided removal.
- Setup not checking programs at all: it tells the end user nothing up front.
- A skill offering to take itself off when its program is missing: a few lines in each such
  skill, for what the end user's answer already covers.
- Fixed paths for programs: see
  [Skills run programs by name, through the PATH](skills-run-programs-by-name-through-the-path.md).
- For Python, keeping the skill off: reliable only for skills that run dev-home-toolkit's Python,
  and it would treat two needs the end user can fix differently. Keeping off only the skills that
  run dev-home-toolkit's Python: the rule would depend on the opt-in's flag, is harder to explain to
  people writing skills, and applies to no skill today.
- An unknown type counting as not met, "needs a newer dev-home-toolkit", as first built: wrong for
  a type the skill's writer invented, which no copy will ever know.
- For a misspelled type, adding "Check the spelling" to the type's line: noise for an invented
  type, such as "vpn". And the line with no hint: it points a typo, such as "progam", to updating,
  or to moving a need setup can check into `compatibility`.
- The "Did you mean" suggestion in place of the rest of the advice, as first built: for a made-up
  type such as `ios`, it suggested `os` and dropped the advice that fit.
- For a limit setup can't read, leaving the skill where it already is, as for a file that can't
  be read at all: the edit that broke the limit may have been meant to take the skill out of
  somewhere, so leaving it there can keep it where it doesn't work.
- Warning about what every skill depends on, added or not: a skill the end user said no to would
  keep asking for its programs, every time `/dev-home skills` lists it. Once a skill is turned on,
  `/dev-home skills` shows what it lacks, and the skill checks for its programs itself.
- Ignoring a field setup doesn't know in an entry of `supportedOn`, as elsewhere: a newer field
  that narrows the limit, such as a minimum agent version, would be skipped by older copies, and
  the skill would go where it may not work.
- A minimum dev-home-toolkit version for skills: an end user's own skills are written against their
  own copy, and skills from elsewhere won't declare it. The `PROBLEM` line tells the end user to
  update instead.

**Look again if:** setup can check a requirement in the agent's own shell; and when the
opt-in for an end user's skills to be generated is built, since a `python` requirement gets a
reliable meaning for those skills then.
