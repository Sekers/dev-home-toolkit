# Skills and releases declare their requirements as facts

**Decision:** a skill's `dev-home-skill.json`, and a release's data file
([A release data file holds the version and what end users need to know](a-release-data-file-holds-the-version-and-what-end-users-need-to-know.md)),
list what it needs to run, as facts, and one checker in `internal/shared/` decides what that
means. Built for skills, with the types `os`, `tool`, `program`, and `python`: the reader in
`settings.py`, and the checker in `requirements.py`. Setup doesn't act on a skill's requirements
yet, and the release side, with the `devHomeTools` type, isn't built.

- The list is `requires`, a list of typed entries, such as:

  ```json
  "requires": [
    { "type": "os", "anyOf": ["windows", "macos"] },
    { "type": "tool", "anyOf": ["claude-code"] },
    { "type": "program", "name": "jira", "description": "Atlassian's jira command-line tool" },
    { "type": "python", "atLeast": "3.13" },
    { "type": "devHomeTools", "atLeast": "1.2.0" }
  ]
  ```

  `os` and `tool` take any one of their values, each `program` entry is needed, and `python` and
  `devHomeTools` are minimums. A skill without the file needs nothing. The names, settled when
  the first four types were built:
  - `os` takes `windows`, `macos`, and `linux`, and `tool` takes `claude-code` and `codex`.
  - A `program`'s `name` is the program's name alone, such as `gh`, never a path, and its
    `description` is optional.
  - `python`'s `atLeast` is text, such as `"3.13"` or `"3.13.1"`, since a JSON number would read
    3.10 as 3.1.
- An entry the reader can't use, such as a program with no name, counts as not met, and setup
  reports it as a `PROBLEM` line naming the file. A name in `anyOf` that the reader doesn't know,
  such as `Windows` for `windows`, is reported the same way and left out of the entry, so a
  misspelling never matches by chance; an entry left with no names counts as not met.
- One reader reads the whole file, for setup and for the update check. One checker holds a rule
  for each type: whether it applies per skills folder (`tool`) or to the whole PC (the rest);
  whether an end user can act on it (not on the operating system; on a program, a tool, a newer
  Python, or a newer dev-home-tools, yes); and the message that says what's missing.
- A skill goes into a skills folder only when every tool setup sets up that reads the folder
  meets its requirements. A requirement nobody can act on leaves the skill out silently, and
  `/dev-home skills` lists it. One an end user can act on is announced once, in the one-time
  `NEW` line for new skills, such as "'jira' (not added: needs the jira program)". When a
  requirement stops being met, the answer is kept, setup removes the skill's links with a line
  saying why, and adds them back once it's met again.
- Setup gathers this PC's facts once a run, without starting a process: the operating system,
  the tools it sets up and the folders they read, each named program on the `PATH`, and the
  Python and dev-home-tools versions. Anything that needs a process, such as whether `gh` is
  signed in, is the skill's to check when it runs.
  - A program counts when it's in a folder that `PATH` names by its full path, with any of the
    extensions in `PATHEXT` on Windows, such as `.cmd`, as a shell finds it. The current folder
    never counts: it may be a project's.
  - The Python version is that of the Python setup runs with. On every sync a skill starts, that's
    the skills' own, since the sync runs setup with the Python it runs with. Finding the version
    of the Python that `internal/.python` leads to would take a process.
- Setup records its result for each skill and skills folder, added or not and why, in a file in
  `internal/.generated/`, which `/dev-home skills` and the settings menu read.
- For a release, the update check holds the update back when the PC can't meet a requirement,
  with a line saying what's missing.
- A skill copied from elsewhere keeps its own files. If its `SKILL.md` has the Agent Skills
  standard's `compatibility` text, `/dev-home skills` shows it.
- A test checks each of dev-home-tools' own skill files, setup reports a mistake in an end
  user's own as a `PROBLEM`, and a page in `docs/reference/` describes the file.

**How it grows:**

- A type a copy of dev-home-tools doesn't know counts as not met for a skill, reported as
  needing a newer dev-home-tools. The update check never holds a release back only because it
  can't read a requirement, so a new type ships in one release before any release requires it
  ([A broken step can't stop the update that would fix it](a-broken-step-cant-stop-the-update-that-would-fix-it.md)).
- A field a copy doesn't know is ignored, so a new field must be safe to ignore. A need of one
  command only, such as `/handoff issue` needing `gh`, would need a list of its own: as a field,
  an older copy would ignore it and leave out the whole skill.
- A skill that relies on a newer format declares a `devHomeTools` minimum, so the file needs no
  format version.

**Why:**

- Skills and releases need the same answer to "can this PC run it?", so they share one format
  and one checker, and a new type is one check and one rule.
- Files hold facts and the code decides, so the same missing thing behaves the same way in every
  skill, and nobody writing a skill decides what end users see.
- Codex's `agents/openai.yaml` lists a skill's MCP dependencies as typed entries (`type`,
  `value`, `description`), the same shape, which lets each entry grow. The Agent Skills
  standard's `compatibility` field is free text, so nothing can check it (both read
  2026-10-16).
- Per skills folder, not per tool: `~/.agents/skills` is read by Codex and, per their docs, by
  GitHub Copilot, Gemini CLI, and Cursor, so that folder can't hold a choice for one tool alone.
- Recording setup's result means only setup decides, and `/dev-home skills` shows exactly what it
  did, with no second checker in `facts.py`.
- An end user can't change the operating system, so a notice would only add noise. They can
  install a program, so knowing what's missing helps.

Established practice: typed entries, shipping a new type before requiring it, and treating what
can't be checked as not met. The rule per type, the check per skills folder, the recorded
result, and the `devHomeTools` minimum as the format gate are dev-home-tools' own design.

**Options set aside:**

- The standard's `compatibility` text alone: nothing can check it.
- An object with one key per type, such as `"programs": ["gh"]`: an entry can't grow.
- Each skill choosing its own action, such as `"ifMissing": "hide"`: the same missing thing would
  behave differently from skill to skill.
- Actions coded for three kinds, for skills only: releases would need a second set of checks.
- `facts.py` checking requirements on its own: a second checker that could disagree with setup.
- Moving the file to `agents/dev-home.json`, as Codex's reference suggests for a product's own
  configuration: that's Codex's convention, not the shared standard, and the file is built.

**Look again if:** a requirement needs a process to check, or the Agent Skills standard adds a
requirements format that can be checked.
