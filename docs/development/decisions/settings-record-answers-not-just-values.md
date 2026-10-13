# Settings record answers, not just values

**Decision:** every saved setting, in `local-settings.json` on each PC and in `dev-home.json` in
dev-home, is in one of these forms:

- missing: nothing is recorded for it yet;
- `{"$state": "unanswered"}`: seen or announced, but not answered;
- `{"$state": "default"}`: answered, to follow the default, whatever it becomes;
- `{"$state": "remind"}`, with an optional `"on": "YYYY-MM-DD"`: answered, to be asked again on
  that date, or with no date, the next time it would be asked;
- a plain value of any type: the end user's own answer, which never changes on its own.

`$state` is reserved: no setting's own value is an object with that key. A state never carries a
value, so something that needs both, such as the last starter commit approved and when to offer
the next one, is two settings.

Each setting is one of four kinds, and accepts only the forms that fit it:

| Kind | Examples | Forms | Until it's answered |
| --- | --- | --- | --- |
| Has a default, and setup asks about it | `updates.installAutomatically`, skill preferences, `skills.<name>.addedToAgents` | missing, `unanswered`, `default`, plain | Follows the default, and a run of setup by hand asks |
| Has a default, and nobody asks about it | `updates.checkEveryHours`, `devHome.checkEveryHours` | missing, `default`, plain | Follows the default |
| No default | `devHome.folder`, `multiMachine`, each folder's `setUp` | missing, plain | Whatever the setting says: with `multiMachine` unanswered every sync fetches, an unanswered folder isn't set up, and without a dev-home folder setup stops |
| Offer | recommended settings, update notices | missing, `remind`, plain | Offered again, as [Offers use the same answers](offers-use-the-same-answers.md) says |

A form a setting doesn't accept, or a plain value of the wrong type, is a `PROBLEM`, and the
setting counts as missing.

- A question about a setting with a default takes yes, no, or default. Yes and no save plain
  values, and default saves `{"$state": "default"}`. `--configure '<name>=default'` does the same.
  At any question, Enter keeps the saved answer, a plain value or the default alike, and means
  default only when nothing is answered yet.
- A skill's preferences are saved as `skills.<name>.preferences.<preference>`, beside
  dev-home-tools' own settings for that skill, such as `skills.<name>.addedToAgents`.
- dev-home-tools' own settings are declared in `internal/shared/setting-definitions.json`, the way
  a skill declares its preferences in its `dev-home-skill.json`: each with its kind, its default,
  a label, help, and `formerNames`, the names it had before.
- A setting found under a name in `formerNames` has its answer moved to the new name on the first
  setup run that sees it, quiet runs included, with one line. One that nothing declares any more,
  dev-home-tools' own or a skill's, is deleted on the first run that sees it, with one line and a
  backup, and nobody is asked.
- When an update changes a default, the PCs that follow it get the new value, and the update says
  so once. It reads the definitions, and each skill's `dev-home-skill.json`, before and after it
  pulls.
- A change to a file's structure raises its `schemaVersion`, and comes with a conversion step for
  that version, which setup runs, in order, on the first run that sees an older file, with one
  line and a backup.
- Setup saves `local-settings.json` only while it holds the sync's lock, and only for the moment
  of saving: it reads the file again, and applies only the answers that run changed, so whatever
  a sync wrote in the meantime is kept. Where both changed the same setting, the end user's answer
  wins. Reading the file never waits for the lock. Before there's a dev-home, there's no sync,
  and no lock to take.
- A backup is made only when a person changes a setting, or answers are deleted, never for a
  write that only records something, such as `unanswered`.

**Why:**

- The file says what the end user meant, not just a value: a choice never changes on its own,
  and a changed default still reaches the PCs that follow it, with a line.
- Setup knows what it has announced without a second record that could disagree with the first.
- Only settings setup asks about need `unanswered`, and only offers need `remind`. Accepting only
  the forms that fit catches a mistake in a hand edit.
- Default is an answer of its own because, if Enter saved `default` while a typed yes saved a
  plain yes, two answers that look the same at the console would behave differently later. Enter
  keeps a saved answer because a question asked again, as the settings menu does, would otherwise
  turn a yes the end user chose into following the default without their noticing.
- Nesting preferences means dev-home-tools' own settings for a skill can never collide with that
  skill's preferences, whatever either is named later. No PC had a preference saved yet, so it
  cost nothing.
- One way to declare every setting makes renames and changed defaults work the same for
  dev-home-tools' settings as for a skill's, and gives the menu every label and help from data.
  An update can compare a default before and after only when it's in a file; in Python code, it
  would have to load the new code.
- Deleting what nothing declares keeps the file to what setup knows. Setup can't tell a removed
  setting from a typo in a hand edit, or from a setting a newer version or branch wrote, so the
  line and the backup show what went.
- Converting the file keeps the end user's answers through a change to its structure, with
  nothing asked again.
- Syncs write the file too, for an announced skill, a rename, or a removal, while a run of setup
  by hand can spend minutes on its questions. Holding the lock only to save, after reading the
  file again, loses neither write, and never holds up a sync while a question waits. It reuses
  the sync's lock ([One sync at a time, through a lock the operating system holds](one-sync-at-a-time-through-a-lock-the-operating-system-holds.md)),
  which the operating system lets go of when a process ends, however it ends.
- A write that only records something can come on any sync, so a backup of each would pile up
  beside the file.

**Options set aside:**

- Writing values only once answered: nothing records what was announced, and a changed default
  adds or removes skills without a word.
- Writing the default as a plain value when a setting is first seen: a changed default reaches no
  one.
- A separate "seen" mark or `announcedDefault` key, or a separate field or section for the state:
  two records that can disagree.
- Setup's links as the record of what's announced: a skill that's off by default would be
  announced on every sync.
- Every value as an object: wordier, for no planned need.
- Reserving dev-home-tools' names among a skill's settings, instead of nesting preferences: a
  later name could hit a preference already in use.
- Keeping dev-home-tools' settings declared in Python: no notice of a changed default, and two
  ways to declare a setting.
- Naming the file `settings-schema.json` (it suggests a JSON Schema), `dev-home-tools-settings.json`
  (it reads like values), or `settings-catalog.json`.
- Keeping a key setup doesn't know, with a `PROBLEM` on every sync: it nags about a setting that's
  gone.
- A separate script for conversions (another process on a path every sync takes), or a data file
  of changes (it would repeat `formerNames`, and a change to the structure needs code anyway).
- Holding the lock for setup's whole run: every sync would wait while a question does.

This changes
[local-settings.json groups its settings, and both settings files carry a version](local-settings-json-groups-its-settings-and-both-settings-files-carry-a-version.md):
a setting may be written before it's answered, a key setup doesn't know is deleted instead of
kept, preferences are nested under `preferences`, and a change to the structure converts the file
instead of setting it aside.

**Look again if:** settings often need a value and a state at once, so that pairs of settings get
in the way, or the forms grow past what a person reading the file can follow.
