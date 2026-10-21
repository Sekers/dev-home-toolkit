# A skill's dev-home-skill.json

A skill can carry a file named `dev-home-skill.json` in its folder, beside its `SKILL.md`, to
tell dev-home-toolkit what the Agent Skills standard has no place for: whether to add the skill to
your agents unless you say otherwise, where it works and what it depends on, its preferences, and
the names it had before. Your own skills, in `skills\` in your dev-home, can have one too. The
file is optional, and so is each field: a skill without one is added to your agents, and needs
nothing.

```json
{
  "recommended": true,
  "supportedOn": [
    { "type": "agent", "anyOf": ["claude-code"] }
  ],
  "dependsOn": [
    { "type": "program", "name": "jira", "usedFor": "filing and reading Jira issues" }
  ],
  "preferences": {
    "includeClosedIssues": {
      "default": false,
      "label": "Include closed issues",
      "help": "Whether the skill lists issues that are closed."
    }
  },
  "formerNames": ["tracker"]
}
```

Setup reads the file on every run, and reports each mistake in it as a `PROBLEM` line that names
the file and says what setup did about it. That includes a field it doesn't know, such as a
misspelled one, which it otherwise ignores:

```text
C:\Programming\dev-home\skills\tracker\dev-home-skill.json: "descripton" is a field this dev-home-toolkit doesn't know, so setup ignores it. Check the spelling of "descripton", or update dev-home-toolkit to a newer version.
```

When the word is close to one setup knows in that place, such as `usedfor` in an entry of
`dependsOn`, the line asks `Did you mean "usedFor"?` before its other advice.

While setup can't read the file at all, such as when it isn't valid JSON, it leaves the skill as
it is: it adds no links to it, and removes none.

## recommended

`true` or `false`, and `true` when it's missing: whether a PC adds the skill to your agents until
you choose. Each PC saves your choice in its `local-settings.json`, as
`skills.<name>.addedToAgents`, and `/dev-home configure` changes it. The first time a PC's setup
finds a skill you haven't chosen for, it names the skill once, in a `NEW` line, with whether it
was added.

## supportedOn and dependsOn

What the skill needs to run, in two lists of entries, each entry with a `type`. Every entry in
both lists applies.

- **`supportedOn`** says where the skill works: the operating system and the agent. Nobody can
  work around those, so setup adds the skill only where every entry is met.
- **`dependsOn`** says what the skill uses: a program or a Python version. Setup adds the skill
  anyway when one is missing, and says what's missing: once in the `NEW` line when the skill is
  new, and in `/dev-home skills` whenever you ask. The agent can still use the parts that work,
  and tell you what's missing when you ask for the rest. A skill that isn't added anywhere on
  this PC, such as one you said no to, gets no such warning, since no agent uses it.

A skill that works on every operating system has no `os` entry. Listing all three leaves out any
other, such as Android. Likewise, a skill that works in every agent has no `agent` entry, and so
works in agents dev-home-toolkit sets up later too.

| List | `type` | Takes | What setup does |
| --- | --- | --- | --- |
| `supportedOn` | `os` | `anyOf`: a list of one or more of `windows`, `macos`, and `linux` | Adds the skill only on a PC that runs one of them. On any other, it's left out with no `NEW` line, and `/dev-home skills` still lists it, with why. |
| `supportedOn` | `agent` | `anyOf`: a list of one or more of `claude-code` and `codex` | Adds the skill only to the skills folders these agents read: each Claude Code folder's `skills\` for `claude-code`, and `~\.agents\skills\` for `codex`. |
| `dependsOn` | `program` | `name`: the program's name alone, such as `gh`; and, if you like, `usedFor`: what the skill uses it for, worded to finish "the skill uses it for", such as "filing and reading Jira issues" | Adds the skill either way. When a newly started shell wouldn't find the program on your `PATH`, the `NEW` line says so, and `/dev-home skills` checks again in the agent's own shell. |
| `dependsOn` | `python` | `atLeast`: the lowest Python version, in quotes, such as `"3.13"` | Adds the skill either way. When the installed Python that dev-home-toolkit uses, which runs its own skills, is older, the `NEW` line and `/dev-home skills` say so, with its version. A skill of yours that runs another Python, such as `python` from your `PATH`, may get a warning that doesn't apply to it, so describe its Python version in `compatibility` instead. |

A `type`, and a name in `anyOf`, can be written in any case, such as `Windows` for `windows`.

When a `supportedOn` entry stops being met, setup takes the skill's links out, with a line saying
why, and puts them back once it's met again.

### Mistakes, and what setup doesn't know

Each list has its own types: a type under the other list is one that list doesn't know. Setup
can't tell a misspelled type from one a newer dev-home-toolkit knows, or one you made up, so its
line gives every fix that may apply, and asks `Did you mean ...?` when a type the list takes is
close.

- **In `supportedOn`, anything setup can't use keeps the skill off until it's fixed:** a type it
  doesn't know, a field it doesn't know, such as a limit a newer dev-home-toolkit adds, or an entry
  with a mistake, such as an `anyOf` that isn't a list. A name in `anyOf` that setup doesn't know
  is only reported, since it can only add a place, never rule out one that's listed.
- **In `dependsOn`, anything setup can't use is ignored,** and the skill is added.

```text
C:\Programming\dev-home\skills\tracker\dev-home-skill.json: "agents" in supportedOn is a requirement this dev-home-toolkit doesn't know, so setup keeps the skill off until it's fixed. Did you mean "agent"? If not, update dev-home-toolkit to a newer version, or remove "agents" from supportedOn and describe it in the compatibility: line at the top of the skill's SKILL.md.
C:\Programming\dev-home\skills\tracker\dev-home-skill.json: "vpn" in dependsOn is a requirement this dev-home-toolkit doesn't know, so setup ignores it. Update dev-home-toolkit to a newer version, or remove "vpn" from dependsOn and describe it in the compatibility: line at the top of the skill's SKILL.md.
```

### A program that isn't on the PATH

A skill runs each program by name, so the program must be on the `PATH` of the shell the agent
runs it in. To add a program's folder to your `PATH`:

- **Windows:** open Start, search for "environment variables", and choose "Edit environment
  variables for your account". Select `Path` under your user variables, choose Edit, then New,
  and add the folder.
- **macOS:** add a line such as `export PATH="$HOME/tools/bin:$PATH"` to `~/.zprofile`.
- **Linux:** add the same line to your shell's startup file, such as `~/.bashrc` or
  `~/.profile`.

Then restart your agents, and the editor they run in: a program that's already running keeps the
`PATH` it started with.

### When you write a skill

Declare only what the table above says setup checks, each type in its list, and describe anything
else in `compatibility` (below). In the skill's first step that uses a program, check for it by
running its version command, such as `gh --version`, say how to get it when it's missing, and
keep working without it where the skill can.

## compatibility, in SKILL.md

The Agent Skills standard gives a skill's `SKILL.md` a `compatibility` field, free text of up to
500 characters, for what it needs that setup can't check, such as a VPN or an environment
variable. Setup doesn't act on it, and `/dev-home skills` shows it after the skill's description.

```yaml
---
name: tracker
description: Files and reads issues in the team's tracker.
compatibility: Needs the office VPN to reach the tracker.
---
```

## preferences

Settings of the skill's own, each `true` or `false`, which `/dev-home configure` changes on each
PC. Each has a name with no dots, and these fields:

- `default`: `true` or `false`.
- `label`: a short name, which `/dev-home configure` shows.
- `help`, optional: what it does.
- `formerNames`, optional: the names it had before, as a list, so each PC's answer moves to the
  new name.

## The skill's name

A skill's name is its folder's name, and its `SKILL.md` repeats it on its `name:` line. Name it
as the Agent Skills standard says: lowercase letters, digits, and hyphens, at most 64 characters,
with no hyphen at the start or the end, and no two in a row. Leave out `claude` and `anthropic`,
which claude.ai and Anthropic's API don't allow in a skill's name.

When a skill of yours breaks this rule, or its `name:` line doesn't match its folder, setup says
what to fix in a `PROBLEM` line on every sync, and still adds the skill to your agents:

```text
PROBLEM   The skill My_Notes has a name the Agent Skills standard doesn't allow: use lowercase letters, digits, and hyphens, such as "my-notes". Rename its folder and the name: line in its SKILL.md, and add "My_Notes" to formerNames in its dev-home-skill.json so your answers move with it.
```

- **A dot in the name** also stops setup saving your answers for the skill, so it follows its
  default until it's renamed.
- **A skill named `synced`,** in any case, is never added: Claude Code keeps that name for the
  folder where it saves the skills it downloads from claude.ai.

## formerNames

The names the skill had before, as a list. When you rename a skill's folder, add its old name
here, and each PC moves its answers, whether to add the skill and its preferences, to the new
name on its next sync. Nothing keeps the old name working.

## alwaysAddedToAgents

For dev-home-toolkit's own skills only: `true` adds the skill to your agents on every PC, with no
answer to change, as for `dev-home`. In one of your own skills, setup reports it as a mistake,
and treats the skill like any other.
