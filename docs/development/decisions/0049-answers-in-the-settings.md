# 0049: Answers in the settings

**Built:** yes.

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
| No default | `devHome.folder`, `multiMachine` | missing, plain | Whatever the setting says: with `multiMachine` unanswered every sync fetches, and without a dev-home folder setup stops |
| Offer | each folder's `setUp`, recommended settings, update notices | missing, `remind`, plain | Offered again, as [0040: Answers to offers](0040-answers-to-offers.md) says. An unanswered folder isn't set up |

A folder setup hasn't asked about is offered in a `NEW` line with the standard answers, "remind me
in N days" among them, which is why each folder's `setUp` is an offer. Until a reminder's date,
the folder isn't set up, its `NEW` line is quiet, and a run of setup by hand doesn't ask. Only a
person's answer saves a reminder, at a question in a terminal, in the settings menu, or through
`--configure`, and only for a folder with no yes or no, the developer's choice: a folder already
answered stays yes or no, since a reminder brings back a question nobody has answered, and a
folder answered yes that took one would keep its links but get no new skills until the date, with
nothing saying so. A shared agent's reminder goes in every folder's entry, as its answer does.
Changed on 2026-10-14, 2026-10-16, and 2026-10-17.

A form a setting doesn't accept, or a plain value of the wrong type, is a `PROBLEM`, and the
setting counts as missing.

- A question about a setting with a default takes yes, no, or default. Yes and no save plain
  values, and default saves `{"$state": "default"}`. `--configure '<name>=default'` does the same.
  At any question, Enter keeps the saved answer, a plain value or the default alike, and means
  default only when nothing is answered yet.
- A skill's preferences are saved as `skills.<name>.preferences.<preference>`, beside
  dev-home-toolkit's own settings for that skill, such as `skills.<name>.addedToAgents`.
- dev-home-toolkit's own settings are declared in `internal/shared/setting-definitions.json`, the way
  a skill declares its preferences in its `dev-home-skill.json`: each with its kind, its default,
  a label, help, and `formerNames`, the names it had before.
- A setting found under a name in `formerNames` has its answer moved to the new name, unless the
  new name already has an answer: a mark that it's unanswered isn't one. The move happens on the
  first setup run that sees it, quiet runs included, with one line. One that nothing declares any
  more, dev-home-toolkit's own or a skill's, is deleted on the first run that sees it, with one line
  and a backup, and nobody is asked. A whole skill that's gone has its answers deleted by the
  first run that holds the sync's lock from its start, a sync's setup, so a skill that a sync or
  an update is replacing at that moment never looks gone.
- Entries of an agent's folders that name the same folder, such as `~/.claude` and its full path,
  which only a hand edit makes, are merged into one on the first setup run that sees them, quiet
  runs included, with one line and a backup. The entry kept is the first answered yes, else no,
  else with a reminder, the answer setup already goes by for a Claude Code folder; Codex homes
  then share the main home's answer, as always. It's kept whole, its answers to recommended
  settings included, and written as setup writes a folder; the others' answers are deleted, and
  so is any problem found in them. A folder reached through a link under another name isn't
  merged.
- When an update changes a default, the PCs that follow it get the new value, and the update says
  so once. It reads the definitions, and each skill's `dev-home-skill.json`, before and after it
  pulls.
- A change to a file's structure raises its `schemaVersion`, and comes with a conversion step for
  that version, which setup runs, in order, on the first run that sees an older file, with one
  line and a backup.
- Setup saves `local-settings.json` while it holds the sync's lock, which it holds for all its
  work, after every question, so no sync waits while a question does
  ([0034: Runs of setup by hand](0034-runs-of-setup-by-hand.md)). It reads the file again, and
  applies only the answers that run changed, so whatever a sync wrote in the meantime is kept.
  Where both changed the same setting, the end user's answer wins. Reading the file never waits
  for the lock. Before there's a dev-home, there's no sync, and no lock to take.
- The answers a run changed are the end user's, given in that run: at a question, in the menu, or
  through `--configure`. What setup works out by itself isn't an answer: the mark for a skill new
  to the PC, an answer moved for a rename or a name's case, a setting nothing declares removed,
  entries for one folder merged, and the answer every Codex home shares. Setup works each of
  those out again at the save, from the file as it reads it then, after making the end user's
  changes there, and sets up from what it saved. It removes a setting nothing declares only when
  the file held it when the run first read it: anything newer came from another run, which may
  know a declaration this run doesn't, such as one an update brought.
  A sync's setup reads nothing again: it has held the lock since before it read the file.
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
- Nesting preferences means dev-home-toolkit's own settings for a skill can never collide with that
  skill's preferences, whatever either is named later. No PC had a preference saved yet, so it
  cost nothing.
- One way to declare every setting makes renames and changed defaults work the same for
  dev-home-toolkit's settings as for a skill's, and gives the menu every label and help from data.
  An update can compare a default before and after only when it's in a file; in Python code, it
  would have to load the new code.
- Deleting what nothing declares keeps the file to what setup knows. Setup can't tell a removed
  setting from a typo in a hand edit, or from a setting a newer version or branch wrote, so the
  line and the backup show what went.
- Converting the file keeps the end user's answers through a change to its structure, with
  nothing asked again.
- A renamed skill's answers move with it, so an end user's no stays a no, with their preferences.
  Nothing keeps the old name working: no link, alias, or stub, so a rename that leaves out
  `formerNames` works as a removal and a new skill. A skill that's gone has its answers deleted,
  since one removed and added back may not come back the same way, and its old answers could be
  wrong for it. Nothing stops a new skill from reusing a removed name, the developer's choice: a
  PC that installs the removal and the reuse in one update gives the new skill the old answers.
- Syncs write the file too, for an announced skill, a rename, or a removal, while a run of setup
  by hand can spend minutes on its questions. Holding the lock for the work, which comes after
  every question, and reading the file again before saving, loses neither write, and never holds
  up a sync while a question waits. It reuses
  the sync's lock ([0018: One sync at a time](0018-one-sync-at-a-time.md)),
  which the operating system lets go of when a process ends, however it ends.
- What setup works out by itself depends on what the file holds, so a change worked out from an
  earlier read can undo another run's answer: a rename's old no, moved to the new name, replaced
  a yes given meanwhile through `--configure`, without a word, and a Codex home found during the
  run kept a yes that another run had just turned to no for every home, so the homes disagreed.
  Working those changes out again at the save leaves the end user's answers as the only changes
  carried over, and gives each later change setup makes by itself one place to go.
- A write that only records something can come on any sync, so a backup of each would pile up
  beside the file.
- Two entries for one folder, with different answers, left setup's parts disagreeing (found
  2026-10-28): setup set up a folder that the menu said was answered no, a no in the menu or
  through `--configure` changed nothing, and a yes to a recommended setting was saved where its
  offer didn't read it. Merging them where the file is read gives every part one answer, as a
  rename's move does. For a Claude Code folder, keeping the answer setup already goes by changes
  nothing setup does, and the backup keeps what was deleted.

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
- Reserving dev-home-toolkit's names among a skill's settings, instead of nesting preferences: a
  later name could hit a preference already in use.
- Keeping dev-home-toolkit's settings declared in Python: no notice of a changed default, and two
  ways to declare a setting.
- Naming the file `settings-schema.json` (it suggests a JSON Schema), `dev-home-toolkit-settings.json`
  (it reads like values), or `settings-catalog.json`.
- Keeping a key setup doesn't know, with a `PROBLEM` on every sync: it nags about a setting that's
  gone.
- A separate script for conversions (another process on a path every sync takes), or a data file
  of changes (it would repeat `formerNames`, and a change to the structure needs code anyway).
- Holding the lock for setup's whole run: every sync would wait while a question does.
- For what setup works out by itself, at the save: checks that only keep a mark from replacing an
  answer, or a skill from being named twice (the rename and Codex cases stay open, and each later
  change setup makes by itself would need a check of its own); having only a sync's setup make
  those changes (it changes decided behavior to make the code easier: runs by hand would stop
  naming new skills, and would still have to work the changes out to show them); working out only
  the marks again (the rename and Codex cases stay open); removing whatever the run's own
  declarations don't know, newer settings included (one a sync or an update brought meanwhile
  would lose its answer).
- For a renamed skill: treating it as new (an end user's no would become a yes, and their
  preferences would be lost); deciding at the first rename, with a tripwire; the update comparing
  skill folders (it misses a `git pull`, a skill of the end user's own, and a failed setup).
- For a skill that's gone: a list of removed skills (the developer turned it down); keeping its
  answers quietly, with a `PROBLEM` on every sync, or deleting them only at a run of setup by
  hand; a test against reusing a removed name.
- For a folder: `setUp` as a setting with no default, as until 2026-10-16 (it can't hold a
  reminder); and a reminder replacing a yes or a no (see above).
- For a folder listed twice: fixing each part that reads the entries to prefer the yes (several
  places, and the next part to read them can bring the problem back); a `PROBLEM` on every sync
  until it's fixed by hand (until then the menu shows the wrong answer, and a no does nothing);
  fixing only where a yes to a recommended setting is saved (the menu and the no stay wrong).
- Carrying the changes setup works out over from the run's first read, as until 2026-10-17: a
  newer run may have written the file since, with a declaration this run doesn't know.

**Look again if:** settings often need a value and a state at once, so that pairs of settings get
in the way, or the forms grow past what a person reading the file can follow.
