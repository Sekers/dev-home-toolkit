# Codex is set up in every Codex home, or in none

**Decision:** Codex has one answer for every Codex home on a PC, `codex.setUp` in
`local-settings.json`, asked once, recommended, in place of a question for each home. A yes sets
up every home setup finds, and each one found later: the always-on rules in its `AGENTS.md`,
dev-home in its `config.toml` after a diff and a yes, and dev-home's skills, linked into
`~/.agents/skills`. A no sets up none. Until it's answered, setup adds no links and removes none,
and a quiet run names the homes. Claude Code keeps an answer for each folder.

Both tools' folders keep one shape in `local-settings.json`, an entry for each folder by its
path, as written:

```json
"claudeCode": { "folders": { "~/.claude": { "setUp": true } } },
"codex": { "setUp": true, "homes": { "~/codex-work": {} } }
```

A Claude Code folder's entry holds its own answer. A Codex home's entry holds none: it only lists
a home setup can't find by itself, such as one outside the profile folder that a session's
`CODEX_HOME` names.

**Why:**

- Codex has no skills of a home's own: every home reads `~/.agents/skills` (Codex's source at
  rust-v0.161.0), and Codex calls the folder of a home's own, `$CODEX_HOME/skills`, deprecated.
  So an answer for each home could only imitate one. A home answered no got dev-home's skills
  hidden with `[[skills.config]]` entries in its `config.toml`, offered as a diff at a run by
  hand, and setup kept a record of the entries, so a skill turned back on through Codex's
  `/skills` menu stayed on. A new skill showed in every home until the next run by hand.
- That imitation spread. With every home answered no, the shared links stayed, listed in every
  home, with no hiding to offer, since hiding needs a home answered yes. Skills per PC,
  recommended settings for each home, and `--uninstall` would each have had to handle the
  entries and their record.
- The rules and the settings are per home in Codex, but setting those up per home while the
  skills are shared would leave a home answered no listing skills that work without the rules or
  write access to dev-home.
- Decided on 2026-10-14, the day the answers for each home were built, so nothing is converted.
  A PC that saved some gets them deleted from the homes' entries, with a backup, as values
  nothing declares, and is asked the one question.
- The same shape for both tools' folders means a Codex home's entry can later take an answer of
  its own, exactly as a Claude Code folder's does, with nothing renamed or converted.

**Built so that each home can get its own answer later:** once Codex reads skills per home, a
home's entry in `codex.homes` takes `setUp`, as a Claude Code folder's does (`answered_each` in
`internal/shared/settings.py`), and `codex.setUp` stays the answer for every home without one.
Nothing saved now needs converting, and no setting is renamed. In setup, one place,
`tool_folders`, decides which homes are set up, and everything after it takes that list.

**Costs, accepted:**

- With two Codex accounts, such as a work one, dev-home can't be kept out of just one: a yes puts
  the always-on rules, the person's global rules included, write access to dev-home, and the
  skills in every home.
- A folder that only looks like a home, such as a backup copy with a `config.toml`, is set up
  too.

**Options set aside:**

- An answer for each home, with dev-home's skills hidden in each home answered no: see Why. It
  was built in `7928593` and `769bbfc`, and taken out by this decision.
- A plain list of the homes setup can't find by itself, beside `codex.setUp`: an answer for each
  home would then need a second structure, unlike Claude Code's, or a conversion of the list.
- An answer for each home for the rules and the settings, with the skills shared: a home
  answered no would list skills with neither the rules nor write access to dev-home.
- Asking again about a home found later: the skills reach it anyway, through
  `~/.agents/skills`, so a question could only hold back the rules and the write access they
  need.

**Look again if:** Codex gets a folder of skills for each home that isn't deprecated: each home
can then have its own answer, as each Claude Code folder has.
