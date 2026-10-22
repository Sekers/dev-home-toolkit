# 0035: Skills per PC

**Built:** yes, except: a no doesn't take a skill's always-on lines out of the rules, and a run of
setup by hand doesn't ask about skills.

**Decision:** setup decides which skills are added to the agents on each PC, meaning linked into
each Claude Code folder's `skills/` and into `~/.agents/skills` for Codex. Claude Code's and
Codex's own menus decide whether an added skill is shown in an account or a project. Changed on
2026-10-12, 2026-10-16, and 2026-10-17, before it was built.

- Each PC saves a yes or no for each skill in `local-settings.json`, as
  `skills.<name>.addedToAgents`. A no removes
  setup's links for it, and its lines leave the generated always-on rules
  ([0058: Skills' always-on lines](0058-skills-always-on-lines.md)).
  Nothing is deleted.
- `dev-home` is always added. `handoff` and `knowledge` are recommended because the starter
  dev-home makes their folders, so a change to the starter means looking at this set again.
- The person's own skills, from `skills/` in dev-home, work like recommended skills: added by
  default, in the same list and prompt, and asked about once on each PC.
- A skill can carry a `dev-home-skill.json` in its folder, with `recommended`,
  `alwaysAddedToAgents`, `supportedOn`, and `dependsOn`. Only dev-home-toolkit's own skills can declare
  `alwaysAddedToAgents`, so each PC asks about every skill of the person's own, as above. A skill
  isn't added to a skills folder whose agents, or whose PC's operating system, it doesn't work
  in, even with a yes;
  [0057: Requirements](0057-requirements.md)
  says how they're declared and checked, and what setup says. For the person's own skills the
  file is optional: without it, a skill is recommended and needs nothing.
- `/dev-home skills` shows each skill's state, from the result setup records. Codex records a
  skill turned off by its real path, inside `internal/.generated/skills/`, so that path stays
  fixed, and a test checks it.
- A renamed skill's answers move to its new name through `formerNames`.
- Until a run of setup by hand asks about skills, which comes with setup's question about skills
  and its preferences, a skill with no answer follows its default, the `NEW` line names it once
  ([0036: New items](0036-new-items.md)), and `/dev-home configure` changes it.

**Why:** checked on 2026-10-07 against Claude Code 2.1.293's docs and Codex's source at
rust-v0.161.0:

- Both agents have their own switch, saved on each PC and never synced. Claude Code's `/skills`
  menu writes `skillOverrides` to the current project's `.claude/settings.local.json`, and for a
  whole account `skillOverrides` goes in that account's `settings.json`. Codex's `/skills` writes
  `[[skills.config]]` entries to that Codex home's `config.toml`, and reads none from a project.
- So dev-home-toolkit adds what the agents lack, a choice of what a PC has at all, and leaves
  showing and hiding to them. The two answer different questions, so they can't disagree, and
  dev-home-toolkit never writes the agents' switches.
- Some planned skills suit only some setups, such as one for each work tracker, and some can't
  work everywhere: ones that use Claude Code-only features, need a program such as `gh`, or work
  on one OS. Only a step that adds skills per PC keeps those off a PC.
- Per PC, because the agents' own choices are per PC, and a skill for one setup belongs on that
  PC.
- Both agents list the name and description of every skill they have in every session, within 1%
  of the context window in Claude Code and 2% in Codex, so a skill a PC doesn't use costs tokens
  there.
- A file in the skill's folder rather than its frontmatter: dev-home-toolkit's skills and the
  person's own work the same way, setup reads JSON with Python's standard library, and a skill
  copied from elsewhere will need a file of its own anyway, to record where it came from.
- `addedToAgents` and `alwaysAddedToAgents`: "installed" already means installing
  dev-home-toolkit updates, and "added" alone could read as added to dev-home.

**Options set aside:**

- The agents' switches only: a skill dev-home-toolkit doesn't recommend would be linked and listed
  on every PC until turned off there.
- dev-home-toolkit's own on and off, ignoring the agents': two switches with the same meaning,
  which could disagree.
- Choices shared in `dev-home.json`, or per PC with shared defaults: a skill for one setup would
  follow to every PC, at the cost of commits and merge conflicts.
- `metadata` in the frontmatter: setup would need to read YAML without a library, and marking a
  skill copied from someone else would edit their `SKILL.md`.
- The person's own skills always added: one made for one PC could only be hidden per agent and
  per account.
- `skills.<name>.installed` and `alwaysInstalled` (see Why), and one `requires` list, or fields
  named `tools`, `programs`, and `os`, in place of `supportedOn` and `dependsOn`
  ([0062: Keeping a skill off](0062-keeping-a-skill-off.md) says why there are two lists).

**Look again if:** people find themselves making the same choices on every PC, when a one-time
copy of another PC's choices could help, or an agent starts syncing skill choices.
