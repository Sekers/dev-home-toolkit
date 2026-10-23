# Glossary

The words dev-home-toolkit uses, one for each idea, in every file: the docs, the skills, the
operating rules, the code and its comments, the tests, and commit messages. Each entry says what
the word means here, then lists the words to avoid for that idea. Check it when you write. When
two words compete for an idea it doesn't list yet, propose an entry to the developer.

The words for people, the developer and the end user, are in AGENTS.md's "Who's who" section, and
the names of the two repos, dev-home and dev-home-toolkit, in its "The two repos". A test in
`internal/development/tests/test_docs.py` catches the mix-ups that wording alone gives away, such
as "both tools" for Claude Code and Codex.

## Agents and programs

- **Agent**: Claude Code, Codex, or a product like them that reads skills and rules, as in "added
  to your agents"; and the AI working in a session, where the sentence leaves no doubt which is
  meant. Where a sentence must tell the two apart, the product is an **agent product**. Name
  Claude Code and Codex where a sentence is about just those two, since "both agents" can read as
  two sessions, and write "agents" where it holds for any. In the code it's the class `Agent`,
  and in a skill's `supportedOn` the requirement type `agent`.\
  _Avoid_: tool, AI tool, client, harness.
- **Program**: anything a shell runs by name, such as `git`, `gh`, or `jira`. Write
  **command-line program** where a sentence needs the precision. The requirement type is
  `program`.\
  _Avoid_: tool, CLI, binary, executable.
- **Software**: anything installed on a PC: a program, a Python version, an editor extension, or
  a package, as in AGENTS.md's "Installing software".\
  _Avoid_: tool.
- **Development tools**: the programs used to work on dev-home-toolkit itself: pytest, ruff, and
  mypy, pinned in `internal/development/`, and uv, which installs and runs them. Always written
  out in full.\
  _Avoid_: the tools, dev tools, test tools.
- **Tool**: not a word of its own here: write agent, program, or development tools. "Tool" stays
  only inside names: an agent's own tools, such as Claude Code's Bash tool; fields and sections,
  such as `allowed-tools` and `[tool.uv]`; file names, such as the planned
  `docs/development/tools.md`, which will list the development tools; other projects' names, and
  words quoted from them; made-up names in examples, such as `you/tool`; and dev-home-tools, this
  product's name until 2026-10-17, where its history needs it.

## Setting up

- **Set up**: what setup does to dev-home on a PC, and to each Claude Code folder or Codex home
  answered yes, which gets dev-home's skills and rules linked in, with the settings they need. A
  skill is never set up: it's added.\
  _Avoid_: installed, configured, enabled (for a folder).
- **Added to your agents**: a skill that setup has linked into this PC's skills folders, by the
  end user's answer, the skill's default, or its `supportedOn`; `skills.<name>.addedToAgents` holds
  the answer. It's "added to your agents" in text for the end user, "added to the user's agents"
  in the skills, and "added" or "added to the agents" elsewhere.\
  _Avoid_: set up, installed, enabled (for a skill).
- **Claude Code folder**: a folder where Claude Code keeps one account's settings: `~/.claude`, or
  another, such as `~/.claude-<name>`, that `CLAUDE_CONFIG_DIR` names.\
  _Avoid_: Claude home, config folder, profile.
- **Codex home**: a folder where Codex keeps its settings, `~/.codex` or another that `CODEX_HOME`
  names, in Codex's own word. Claude Code folders and Codex homes together are **an agent's
  folders**.\
  _Avoid_: Codex folder.
- **Skills folder**: a folder an agent loads skills from, such as a Claude Code folder's
  `skills/`, or `~/.agents/skills`, which every Codex home reads.
- **Single-PC mode** and **multi-PC mode**: dev-home's two modes, which `multiMachine` in
  `dev-home.json` sets: `false` while dev-home is in active use in one copy, and `true` while it's
  in several, such as on two PCs, or on a PC and in a cloud session. A **copy** is a clone of
  dev-home in active use on its own; two sessions sharing one clone are one copy. Name the mode
  where text gives the setting's value, as setup's menu does, and count copies where text explains
  what a mode means. With no answer, no mode is chosen, and syncs check GitHub as in multi-PC
  mode.\
  _Avoid_: one-copy mode, single-machine mode, multi-machine mode.

## Rules

- **Operating rules**: the always-on rules dev-home-toolkit ships, the same for every end user, in
  `templates/operating-rules/operating-rules.md`, written in the end user's own voice.\
  _Avoid_: global rules, base rules, system rules.
- **The end user's rules**: always-on rules an end user writes for themselves, kept in their
  dev-home: the files under `rules/`, by level, called "your rules" for the end user and "my
  rules" in their own voice.\
  _Avoid_: personal rules, custom rules, user rules.
- **Built-in rule**: a rule dev-home-toolkit ships for end users to add to their own rules, which
  applies only after a yes, from `templates/built-in-rules/<name>/` (not built yet).\
  _Avoid_: example rule, starter rule, default rule.

## Answers and fields

- **State**: an answer that isn't a plain value. In the settings files it's
  `{"$state": "<state>"}`, one of `unanswered`, `default`, or `remind`; in a copy of a built-in
  rule, its note's `state` is `added`, `not added`, `default`, or `unanswered` (not built yet).\
  _Avoid_: status, which is for the status words such as `OK` and `PROBLEM`; mode.
- **Unanswered**: seen or announced, but not answered yet, such as a skill new to a PC. It follows
  its default until it's answered. It isn't missing, which means nothing is recorded yet.\
  _Avoid_: new, pending, unset.
- **Summary** (`summary`): one sentence of plain text for people, shown in notices and menus, for
  a skill, a built-in rule, or a release (not built yet). It isn't a skill's `description`, which
  is for agents deciding when to load it.\
  _Avoid_: description, blurb, tagline.
- **Used for** (`usedFor`): what a skill uses a program for, in that program's `dependsOn` entry,
  worded to finish "the skill uses it for".\
  _Avoid_: description, purpose.
- **Urgency** (`urgency`): how much a release's update notice asks for the end user's attention:
  `low`, `normal`, or `critical` (not built yet).\
  _Avoid_: priority, severity, importance.
- **Layout version**: the number of one part of dev-home's layout, such as `rules` or
  `knowledge`, in `dev-home.json`'s `layoutVersions`. A part with no number is at layout 1 (not
  built yet).\
  _Avoid_: schema version, which is each settings file's own `schemaVersion`; format version.

## Docs

- **Decision**: one file in `docs/development/decisions/`, cited as "decision 0054", or by number
  and name, "0054: Removing what setup set up".\
  _Avoid_: ADR, decision record, record.
- **Not built yet**: decided, but not in the code yet, as a decision's Built line says.\
  _Avoid_: planned, pending.
