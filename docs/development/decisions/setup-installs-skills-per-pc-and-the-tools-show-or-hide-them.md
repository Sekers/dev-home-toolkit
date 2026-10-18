# Setup installs skills per PC, and the tools show or hide them

**Decision:** setup decides which skills are installed on each PC, meaning linked into each Claude
folder's `skills/` and into `~/.agents/skills` for Codex. Claude Code's and Codex's own menus
decide whether an installed skill is shown in an account or a project.

- Each PC saves a yes or no for each skill in `local-settings.json`, as
  `skills.<name>.addedToAgents`. A no removes
  setup's links for it, and its lines leave the generated always-on rules
  ([A skill's always-on lines are blocks in the operating rules](a-skills-always-on-lines-are-blocks-in-the-operating-rules.md)).
  Nothing is deleted.
- `dev-home` is always installed. `handoff` and `knowledge` are recommended because the starter
  dev-home makes their folders, so a change to the starter means looking at this set again.
- The person's own skills, from `skills/` in dev-home, work like recommended skills: installed by
  default, in the same list and prompt, and asked about once on each PC.
- A skill can carry a `dev-home-skill.json` in its folder, with `recommended`,
  `alwaysAddedToAgents`, `supportedOn`, and `dependsOn`. Only dev-home-toolkit's own skills can declare
  `alwaysAddedToAgents`, so each PC asks about every skill of the person's own, as above. A skill
  isn't added to a skills folder whose agents, or whose PC's operating system, it doesn't work
  in, even with a yes;
  [Skills and releases declare their requirements as facts](skills-and-releases-declare-their-requirements-as-facts.md)
  says how they're declared and checked, and what setup says. For the person's own skills the
  file is optional: without it, a skill is recommended and needs nothing.
- `/dev-home skills` shows each skill's state, from the result setup records. Codex records a
  skill turned off by its real path, inside `internal/.generated/skills/`, so that path stays
  fixed, and a test checks it.

Changed on 2026-10-12 and 2026-10-16, before it was built: the answer was
`skills.<name>.installed` and the field `alwaysInstalled`. "Installed" already means installing
dev-home-toolkit updates, and "added" alone could read as added to dev-home, so both say
`addedToAgents`. `requires` became a list of typed entries, checked per skills folder, in place of
`tools`, `programs`, and `os`. On 2026-10-17, before any release, it was split into two lists,
`supportedOn` and `dependsOn`
([Setup keeps a skill off only for its operating system or agent](setup-keeps-a-skill-off-only-for-its-operating-system-or-agent.md)).

Built: each PC's answer, the links setup adds and removes by it and by `supportedOn`, a renamed
skill's answers moved through `formerNames`, and the state setup records. Not built yet: a
skill's always-on lines leaving the rules with a no, and asking at a run of setup by hand, which
comes with setup's question about skills and its preferences. Until then, a skill with no answer
follows its default, the `NEW` line names it once
([New items reach the person at a terminal, or in a NEW line](new-items-reach-the-person-at-a-terminal-or-in-a-new-line.md)),
and `/dev-home configure` changes it.

**Why:** checked on 2026-10-07 against Claude Code 2.1.293's docs and Codex's source at
rust-v0.161.0:

- Both tools have their own switch, saved on each PC and never synced. Claude Code's `/skills`
  menu writes `skillOverrides` to the current project's `.claude/settings.local.json`, and for a
  whole account `skillOverrides` goes in that account's `settings.json`. Codex's `/skills` writes
  `[[skills.config]]` entries to that Codex home's `config.toml`, and reads none from a project.
- So dev-home-toolkit adds what the tools lack, a choice of what a PC has at all, and leaves showing
  and hiding to them. The two answer different questions, so they can't disagree, and
  dev-home-toolkit never writes the tools' switches.
- Some planned skills suit only some setups, such as one for each work tracker, and some can't
  work everywhere: ones that use Claude Code-only features, need a program such as `gh`, or work
  on one OS. Only an install step keeps those off a PC.
- Per PC, because the tools' own choices are per PC, and a skill for one setup belongs on that PC.
- Both tools list every installed skill's name and description in every session, within 1% of the
  context window in Claude Code and 2% in Codex, so a skill a PC doesn't use costs tokens there.
- A file in the skill's folder rather than its frontmatter: dev-home-toolkit's skills and the
  person's own work the same way, setup reads JSON with Python's standard library, and a skill
  copied from elsewhere will need a file of its own anyway, to record where it came from.

This changes "/dev-home skills lists the skills dev-home sets up", whose list now shows each
skill's state.

**Options set aside:**

- The tools' switches only: a skill dev-home-toolkit doesn't recommend would be linked and listed on
  every PC until turned off there.
- dev-home-toolkit's own on and off, ignoring the tools': two switches with the same meaning, which
  could disagree.
- Choices shared in `dev-home.json`, or per PC with shared defaults: a skill for one setup would
  follow to every PC, at the cost of commits and merge conflicts.
- `metadata` in the frontmatter: setup would need to read YAML without a library, and marking a
  skill copied from someone else would edit their `SKILL.md`.
- The person's own skills always installed: one made for one PC could only be hidden per tool and
  per account.

**Look again if:** people find themselves making the same choices on every PC, when a one-time
copy of another PC's choices could help, or a tool starts syncing skill choices.
