# Settings

The rules for adding or changing a setting: one of dev-home-tools' own, in `local-settings.json`
or `dev-home.json`, or a skill's preference.
[Settings record answers, not just values](decisions/settings-record-answers-not-just-values.md)
defines the forms a saved setting takes and the four kinds of setting, with the reasons.
AGENTS.md's rules apply too.

## Adding a setting

- Declare it in one place: one of dev-home-tools' own in `internal/shared/setting-definitions.json`,
  and a skill's preference under `preferences` in that skill's `dev-home-skill.json`. Give it a
  kind, a default or none, a label, and help. Setup, the menu, `--configure`, and `facts.py` all
  read the declaration, so never write a setting's default or label anywhere else.
- Pick its kind from the four in the decision. The help of a setting with no default says what
  happens until it's answered.
- Decide what Enter does at its question, apart from its default. For a setting with a default,
  Enter means default. A folder's question takes Enter as yes, though a folder nobody has
  answered for isn't set up. `multiMachine`'s question has no Enter answer, since either wrong
  answer costs something.
- A setting is per PC, in `local-settings.json`, unless it describes dev-home itself, which every
  copy shares in `dev-home.json`. A skill's preferences are always per PC.
- Test each form it accepts, one it doesn't, and a plain value of the wrong type.

## Reading and writing

- Read every setting through the reader in `internal/shared/settings.py`. `facts.py` can't load
  setup's code, so it keeps a small reader of its own for skill preferences, and a test checks
  that the two agree.
- Write a plain value only when the end user chose that value, and `{"$state": "default"}` only
  when they chose the default. Never write a default as a plain value: that pins it.
- Quiet runs never ask, and the only state they write is `unanswered`, for something they
  announce.
- Save `local-settings.json` only through setup's save, which holds the sync's lock while it
  reads the file again and applies only that run's changes.
- Make a backup only when a person changes a setting, or answers are deleted.

## Changing a setting later

- To rename one, add its old name to its `formerNames`. Setup moves each PC's answer, and
  `schemaVersion` stays as it is.
- To remove one, delete its declaration. Setup deletes each PC's answer on its next run.
- Never give a new setting a removed one's name: a PC that gets both changes in one update would
  apply the old answer to the new setting.
- To change its default, change the declaration. Each PC that follows the default gets the new
  one, and the update says so once (not built yet).
- To change what a setting holds, such as hours to minutes, or the structure of a file, raise the
  file's `schemaVersion`, and add a conversion step for that version, with a test (not built
  yet).
