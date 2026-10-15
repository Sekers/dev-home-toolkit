# A Codex home answered no gets dev-home's skills hidden

**Decision:** in a Codex home answered no, setup leaves out the always-on rules and the
`config.toml` lines. While any Codex home is set up, it also hides dev-home's skills there with
Codex's own switch for that home: a `[[skills.config]]` entry for each skill setup links, with
`path` (the `SKILL.md` the link leads to) and `enabled = false`, in that home's `config.toml`.

- A run of setup by hand shows the entries as a diff, together with any other change the file
  needs, and writes them after a yes, with a backup.
- Setup records the entries it wrote in the home's entry in `local-settings.json`, as
  `hiddenSkills`, a list of their `SKILL.md` paths, saved only once the entries are written. It
  writes each entry once, so a skill turned back on through Codex's `/skills` menu, which
  deletes its entry, stays on.
- It touches only entries in that record: one the person wrote, even for one of dev-home's
  skills, stays.
- It offers to remove an entry it wrote for a skill that's gone, or now at another path, such as
  after dev-home's folder moves; and every entry it wrote when the home changes to yes.
- Quiet runs never change Codex's settings. No sync mentions hiding a skill in a home answered
  no, so a new skill shows there until the next run of setup by hand. The `--configure` run that
  answers a home no says once that a run of setup in a terminal hides the skills. A home answered
  yes that still has setup's entries is reported on every sync, as its other missing lines are,
  since the yes isn't in effect until they go.
- With no Codex home answered yes, setup links no skills into `~/.agents/skills`, and leaves the
  entries in homes answered no as they are.

**Why:** every Codex home reads `~/.agents/skills` (Codex's source at rust-v0.161.0), so a home
answered no would otherwise list dev-home's skills, with neither the rules they depend on nor
write access to dev-home. Codex's switch is per home, in that home's `config.toml`.

- Codex matches an entry's `path` and each loaded skill's `SKILL.md` after resolving links on
  both sides, so a skill reached through a junction is matched by its real file (Codex's source
  at rust-v0.162.1, read 2026-10-14). OpenAI's config reference says the path is the skill's
  folder, which the source contradicts.
- Codex's menu turns a skill back on by deleting its entry, not by setting `enabled = true`
  (`set_skill_config` in `codex-rs/core/src/config/edit.rs`, rust-v0.162.1, read 2026-10-14). So
  the file alone can't tell a skill turned back on from one never hidden, and the record can.
- The record holds paths, not names, because Codex names an entry by its path, so the record
  compares with the entries directly. A move of dev-home's folder, which the settings menu
  supports, then shows up as entries to replace, where a name would still look hidden while its
  entry pointed at the old path.
- Saving the record only once the entries are written means one declined, or whose write fails,
  is never recorded, so the next run by hand offers it again.
- Hiding is cosmetic in a home answered no, and a line on every skill command, for each new
  skill, until a run by hand would cost every session tokens. A yes that isn't in effect is worth
  the line.

This is a narrow exception to
[Setup installs skills per PC, and the tools show or hide them](setup-installs-skills-per-pc-and-the-tools-show-or-hide-them.md),
where dev-home-tools never writes the tools' switches: setup writes only entries it records, only
in a home the person said no to, and only after a yes to the diff. It adds the record's save,
after the settings files, to the order in
[A run of setup by hand asks what's unanswered, then shows every setting](a-run-of-setup-by-hand-asks-whats-unanswered-then-shows-every-setting.md).

**Options set aside:**

- One question for all of Codex: no way to pick homes.
- A question per home, without hiding the skills: a home answered no would list skills with
  neither the rules nor write access to dev-home.
- Linking the skills into each home's `$CODEX_HOME/skills`: Codex calls that folder deprecated,
  and dev-home-tools builds on nothing deprecated.
- No record, deciding from the file alone: a skill turned back on would be hidden again at the
  next run by hand.
- A comment beside each entry in `config.toml` as the record: Codex's menu deletes it with the
  entry.
- Recording skill names: see Why.
- Saving the record with this PC's other answers, before the settings files: a declined or failed
  write would be recorded as hidden, and never offered again.
- A `PROBLEM` on every sync for a home answered no that needs an entry, as for other settings
  files: tokens in every session for something cosmetic. And no line at all for a home answered
  yes that still has entries: a yes in chat would leave the skills hidden, with no word why.

**Look again if:** Codex gets a folder of skills per home that isn't deprecated, or changes how
its menu turns a skill back on; or `--configure` can write a settings file after a yes in chat
([--configure applies a recommended setting after a yes in chat](configure-applies-a-recommended-setting-after-a-yes-in-chat.md)),
when a home answered no in chat could get its entries right away.
