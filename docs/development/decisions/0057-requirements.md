# 0057: Requirements

**Built:** yes, except: the release side, with the `devHomeToolkit` type, and built-in rules'
files.

**Decision:** a skill's `dev-home-skill.json`, and a release's data file
([0060: The release data file](0060-the-release-data-file.md)),
list what it needs to run, as facts, and one checker in `internal/shared/` decides what that
means. For skills, the types are `os`, `agent`, `program`, and `python`, with the reader in
`settings.py`, the checker in `requirements.py`, and what setup does with the result in
`setup.py`; a release adds the type `devHomeToolkit`. Which requirements keep
a skill off, and which only warn, is a decision of its own:
[0062: Keeping a skill off](0062-keeping-a-skill-off.md).

- The requirements are in two lists of typed entries: `supportedOn`, where the skill works, and
  `dependsOn`, what it uses. Each list takes its own types:

  ```json
  "supportedOn": [
    { "type": "os", "anyOf": ["windows", "macos"] },
    { "type": "agent", "anyOf": ["claude-code"] }
  ],
  "dependsOn": [
    { "type": "program", "name": "jira", "usedFor": "filing and reading Jira issues" },
    { "type": "python", "atLeast": "3.13" }
  ]
  ```

  `os` and `agent` take any one of their values, each entry applies, and `python` is a minimum. A
  release adds a `devHomeToolkit` minimum, which list it goes in to be settled with the release
  design. A skill without the file needs nothing. The names, settled when the first four types
  were built:
  - `os` takes `windows`, `macos`, and `linux`, and `agent` takes `claude-code` and `codex`.
  - A `program`'s `name` is the program's name alone, such as `gh`, never a path, and its
    optional `usedFor` says what the skill uses it for.
  - `python`'s `atLeast` is text, such as `"3.13"` or `"3.13.1"`, since a JSON number would read
    3.10 as 3.1.
- Anything in a list the reader can't use is reported as a `PROBLEM` line naming the file. Under
  `supportedOn` it counts as not met, so it keeps the skill off: an entry with a mistake, a type
  the list doesn't take, or a field the reader doesn't know. Under `dependsOn` it's left out. A
  type under the other list is one that list doesn't know; the reader has no check of its own for
  that. A name in `anyOf` that the reader doesn't know, such as `macOSX` for `macos`, is
  reported the same way and left out of the entry, so a misspelling never matches by chance; an
  entry left with no names counts as not met. A type, and a name in `anyOf`, match in any case,
  such as `Windows` for `windows`: no two known names differ only in case, so none can match the
  wrong one.
- One reader reads the whole file, for setup and for the update check. One checker holds a rule
  for each type: whether a skill that doesn't meet it is kept off (`os` and `agent`) or only
  warned about (the rest); whether it applies per skills folder (`agent`) or to the whole PC (the
  rest); whether an end user can act on it (not on the operating system; on a program, an agent,
  a newer Python, or a newer dev-home-toolkit, yes); and the message that says what's missing.
- A skill goes into a skills folder only when it meets its `supportedOn`: its `os` requirement,
  and its `agent` requirement for every agent setup sets up that reads the folder. An `os`
  requirement, which
  nobody can act on, leaves the skill out silently, and `/dev-home skills` lists it. An `agent`
  requirement is announced once, in the one-time `NEW` line for new skills, such as
  "'claude-only' (added to your agents in Claude Code, not in Codex: works only in Claude Code)".
  When one stops being met, the answer is kept, setup removes the skill's links with a line
  saying why, and adds them back once it's met again.
- Setup gathers this PC's facts once a run, without starting a process: the operating system,
  the agents it sets up and the folders they read, each named program on the `PATH`, and the
  Python and dev-home-toolkit versions. Anything that needs a process, such as whether `gh` is
  signed in, is the skill's to check when it runs.
  - A program counts when it's in a folder that `PATH` names by its full path, in setup's own
    `PATH` or, on Windows, the saved one, with any of the extensions in `PATHEXT` on Windows,
    such as `.cmd`, as a shell finds it. The current folder never counts: it may be a project's.
  - The Python version is that of the Python setup runs with. On every sync a skill starts, that's
    the skills' own, since the sync runs setup with the Python it runs with. Finding the version
    of the Python that `internal/.python` leads to would take a process.
- Setup records its result for each skill, as one state that says where it's added and why it
  isn't elsewhere, such as "added to your agents in Claude Code, not in Codex: works only in
  Claude Code", in `internal/.generated/skill-states.json`, which `/dev-home skills` reads, and
  later the settings menu. Beside the state go the programs and the Python minimum the skill
  only warns about, which `/dev-home skills` checks again where the agent runs.
- A skill whose `dev-home-skill.json` can't be read, such as one that isn't valid JSON, is left as
  it is, links and all, and setup reports the file as a `PROBLEM` on every run. What it requires
  isn't known, so it can't be added, but taking it out of every agent over a slip in a hand edit
  would cost more than leaving it, as its saved answers are kept too.
- For a release, the update check holds the update back when the PC can't meet a requirement,
  with a line saying what's missing.
- A skill copied from elsewhere keeps its own files. If its `SKILL.md` has the Agent Skills
  standard's `compatibility` text, `/dev-home skills` shows it.
- A test checks each of dev-home-toolkit's own skill files, setup reports a mistake in an end
  user's own as a `PROBLEM`, and a page in `docs/reference/` describes the file.
- A built-in rule's `dev-home-rule.json` takes the same `supportedOn`, with `os` and `agent`, and
  no `dependsOn`, since a rule loads whether or not a program is there
  ([0072: Fields in skill and rule files](0072-fields-in-skill-and-rule-files.md)). Neither file
  has a format version: a rule for developers, in [skills.md](../skills.md), says a field never
  changes meaning.

Changed on 2026-10-17 and 2026-10-18, before any release.

**How it grows:**

- A new type goes in the list of its kind. A copy of dev-home-toolkit that doesn't know it reports
  it in a `PROBLEM` line for a skill, which tells the end user to update, and handles it as its
  list says: under `supportedOn` it keeps the skill off, and under `dependsOn` it's ignored. The
  update check never holds a release back only because it can't read a requirement, so a new
  type ships in one release before any release requires it
  ([0019: Updates that fix a broken step](0019-updates-that-fix-a-broken-step.md)).
- A type that later gains a use in the other list, such as `python` becoming a limit for skills
  that run dev-home-toolkit's Python, is one older copies don't know there: they keep the skill off
  or ignore the entry, as that list says. Plan for those copies when making such a change.
- A field a copy doesn't know is reported the same way. In an entry of `supportedOn` it keeps the
  skill off, since it may narrow the limit, such as a minimum agent version; anywhere else it's
  ignored, so a new field there must be safe to ignore. A need of one command only, such as
  `/handoff issue` needing `gh`, would need a list of its own.
- A skill declares no minimum dev-home-toolkit version: an older copy reports what it doesn't
  know. So the file needs no format version.

**Why:**

- Skills and releases need the same answer to "can this PC run it?", so they share one format
  and one checker, and a new type is one check and one rule.
- Files hold facts and the code decides, so the same missing thing behaves the same way in every
  skill, and nobody writing a skill decides what end users see.
- Codex's `agents/openai.yaml` lists a skill's MCP dependencies as typed entries (`type`,
  `value`, `description`), the same shape, which lets each entry grow. The Agent Skills
  standard's `compatibility` field is free text, so nothing can check it (both read
  2026-10-16).
- Per skills folder, not per agent: `~/.agents/skills` is read by Codex and, per their docs, by
  GitHub Copilot, Gemini CLI, and Cursor, so that folder can't hold a choice for one agent alone.
- Recording setup's result means only setup decides, and `/dev-home skills` shows exactly what it
  did. `facts.py` checks again only what setup warns about, a program or a Python version, where
  the agent runs, and decides nothing
  ([0062: Keeping a skill off](0062-keeping-a-skill-off.md)).
- An end user can't change the operating system, so a notice would only add noise. They can
  install a program, so knowing what's missing helps.
- Two lists, so the file says which kind each entry is. With one list, the reader knew an entry's
  kind only from its type's name, so a type it didn't know, whether misspelled, newer, or made
  up, couldn't be handled by the rule for its kind: a misspelled `agent` was ignored, and the
  skill went into agents its writer excluded. With two lists, each kind keeps its own rule even
  for what the reader doesn't know, and either kind can gain types later. Both names state facts
  about the skill, not what setup should do, so they hold for releases too.
- Types and names match in any case: the case carries no meaning, and the people writing these
  files write names the way they know them.

Established practice: typed entries, and shipping a new type before requiring it. The rule per
type, the check per skills folder, and the recorded result are dev-home-toolkit's own design.

**Options set aside:**

- One list, `requires`, with each entry's kind known from its type's name: see Why.
- A missing program or an older Python keeping a skill off, an unknown type counting as not met
  with no `PROBLEM` line, an unknown field going unsaid, and a `devHomeToolkit` minimum in a skill's file as the format's
  gate, as until 2026-10-17 ([0062: Keeping a skill off](0062-keeping-a-skill-off.md) says why
  not).
- The type name `tool`: "tool" means several things in this repo.
- A program's `description`: in a skill's folder, "description" means `SKILL.md`'s text for
  agents ([0072: Fields in skill and rule files](0072-fields-in-skill-and-rule-files.md)).
- Telling a misspelled limit from other unknown types by its spelling: the closest-word check
  matches made-up types such as `ios` and `dos` to `os`, which would keep such a skill off for
  good. By its shape, an `anyOf`: it would also catch made-up types written that way, and block a
  later need written with `anyOf`, such as alternatives for a program (`clip`, `pbcopy`, or
  `xclip`).
- A check for a known type under the other list, with a line saying where it belongs: once a
  type gains a use in the other list, an older copy would call a correct file wrong.
- Other names: `limits` (reads as usage or rate limits in agents), `onlyOn` (reads as the
  events that start something, as `on:` does in GitHub Actions), `platforms` (around Claude it
  means Anthropic's API platform), `runsOn` (picks a machine, rather than ruling others out),
  `compatibleWith` (too close to the standard's `compatibility`, which nothing checks); `needs`
  (too vague, and in GitHub Actions it means waiting for another job), `uses` (reads oddly for a
  Python version), `requires` (sounds enforced, for the list that only warns), and
  `prerequisites` (long, and strict-sounding).
- The standard's `compatibility` text alone: nothing can check it.
- An object with one key per type, such as `"programs": ["gh"]`: an entry can't grow.
- Each skill choosing its own action, such as `"ifMissing": "hide"`: the same missing thing would
  behave differently from skill to skill.
- Actions coded for three kinds, for skills only: releases would need a second set of checks.
- `facts.py` checking requirements on its own: a second checker that could disagree with setup.
  (It now checks again what setup only warns about, where the agent runs, and decides nothing.)
- Moving the file to `agents/dev-home.json`, as Codex's reference suggests for a product's own
  configuration: that's Codex's convention, not the shared standard, and the file is built.

**Look again if:** a requirement needs a process to check, or the Agent Skills standard adds a
requirements format that can be checked.
