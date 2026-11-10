# 0035: Skills per PC

**Built:** yes.

**Decision:** setup decides which skills are added to the agents on each PC, meaning linked into
each Claude Code folder's `skills/` and into `~/.agents/skills` for Codex. Claude Code's and
Codex's own menus decide whether an added skill is shown in an account or a project. Changed on
2026-10-12, 2026-10-16, and 2026-10-17, before it was built, and on 2026-11-09 (the question at
a run by hand) and 2026-11-10 (the answer's name).

- Each PC saves a yes or no for each skill in `local-settings.json`, as
  `skills.<name>.addToAgents`. A no removes
  setup's links for it, and its always-on lines leave each agent's rules file
  ([0058: Skills' always-on lines](0058-skills-always-on-lines.md)).
  Nothing is deleted.
- `dev-home` is always added. `handoff` and `knowledge` are recommended because every dev-home
  holds their files, and setup keeps the knowledge index there, so a change to what setup keeps
  in dev-home means looking at this set again.
- The person's own skills, from `skills/` in dev-home, work like recommended skills: added by
  default, in the same list and question, and asked about once on each PC.
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
- A skill with no answer follows its default. A quiet sync's `NEW` line names a new one once
  ([0036: New items](0036-new-items.md)), and `/dev-home configure` changes it.
- **A run of setup by hand asks about skills,** after the folders' questions, since a skill's
  state depends on them, while a skill or a preference has no answer. It shows "These have no
  answer yet, so each follows its default:", then each of them under the settings menu's Skills
  section's headings, with no numbers: its default, as "yes (the default)", its state where that
  differs, and a skill's `summary` set in under its name. Then it asks "Change any of these?
  [y/N]". Enter, or a no, saves `default` for each item listed, so the question comes back only
  for a new one; a yes opens the Skills section
  ([0026: setup.py --configure](0026-setup-py-configure.md)), and leaving it saves `default`
  for any item still unanswered. Input that ends without an answer saves nothing, and a quiet
  run never asks. A skill this PC's operating system can't run, or with a dot in its name, isn't
  listed, nor are its preferences, and never brings the question up: nothing answered here can
  change it, or setup can't save the answer. If an update makes such a skill work here, the next
  run by hand asks about it while it has no answer. This departs from the shared prompt for
  optional lists and the standard answers
  ([0033: Prompts for optional lists](0033-prompts-for-optional-lists.md),
  [0040: Answers to offers](0040-answers-to-offers.md)).

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
- The question at a run by hand: on a first run a person sees what each skill does, and whether
  it's added, before choosing; it shows the Skills section's rows, with one layout and one code
  path; and one plain question fits any mix of skills and preferences. Saving the defaults that
  Enter keeps stops the question coming back at every run by hand. The developer's choice,
  2026-11-09; the preferences of a skill this PC can't run, on 2026-11-10.
- `addToAgents` and `alwaysAddedToAgents`: "install" already means installing dev-home-toolkit
  updates, and "add" alone could read as adding to dev-home. `addToAgents` is the end user's
  answer, so it names what a yes does, as every other yes-or-no answer in `local-settings.json`
  does, such as `installAutomatically`, a folder's `setUp`, and the handoff skill's
  `includeSecurityBugsInIssueOffers`. The skill's state can differ from the answer, such as a
  skill added in Claude Code but not in Codex.
  `alwaysAddedToAgents` describes the skill, as the other fields of `dev-home-skill.json` do,
  such as `recommended` and `supportedOn`.

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
- For the question at a run by hand: the 2026-10-28 draft, a line naming the skills "each with
  its default preferences", then "Customize skills and their preferences? [y/N]" (names only, and
  it names both kinds when one waits); the rows with a question naming what waits, such as
  "Customize skills?" (three forms, and "customize" suits preferences more than adding a skill);
  asking only on a first setup, by a note or by "no dev-home folder saved yet" (it misses what an
  update brings, which [0025: Setup's questions](0025-setups-questions.md) already ruled out); a
  separate list of preferences seen (two records that can disagree, and a changed default would
  silently change PCs that answered).
- `addedToAgents` for the answer, its name until 2026-11-10: the only answer in
  `local-settings.json` named for a state, which the answer doesn't always give.
- `skills.<name>.installed` and `alwaysInstalled` (see Why), and one `requires` list, or fields
  named `tools`, `programs`, and `os`, in place of `supportedOn` and `dependsOn`
  ([0062: Keeping a skill off](0062-keeping-a-skill-off.md) says why there are two lists).

**Look again if:** people find themselves making the same choices on every PC, when a one-time
copy of another PC's choices could help, or an agent starts syncing skill choices.
