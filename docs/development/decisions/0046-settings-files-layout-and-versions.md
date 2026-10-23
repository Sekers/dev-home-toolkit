# 0046: Settings files' layout and versions

**Built:** yes, except: the change of 2026-10-18: `dev-home.json` records no dev-home-toolkit
version or layout versions yet. Setup's code creates it, as that change says.

**Decision:** this PC's settings are grouped by what they're about, and each one's name is its
path, as in git config and Codex's `-c`:

```json
{
  "schemaVersion": 1,
  "devHome": { "folder": "C:/Programming/dev-home", "checkEveryHours": 12 },
  "updates": { "installAutomatically": false, "checkEveryHours": 24 },
  "claudeCode": { "folders": { "~/.claude-second": { "setUp": true } } },
  "codex": { "homes": { "~/.codex": { "setUp": true } } },
  "skills": { "handoff": { "preferences": { "includeSecurityBugsInIssueOffers": true } } }
}
```

- `--configure` takes the path, such as `--configure 'updates.checkEveryHours=6'`. A folder has
  a dot in its name, so folders keep `claudeCode.folders+=<folder>` and `-=<folder>`. Every Codex
  home has the same answer, the main home's, which setup keeps in every home's entry
  ([0052: Codex homes](0052-codex-homes.md)).
- A setting may be written before it's answered, such as a skill saved as `unanswered`
  ([0049: Answers in the settings](0049-answers-in-the-settings.md)). Once it's answered, it
  stays, so a later change of default never changes a PC that answered. `testHomeDir` stays at
  the top, as before.
- `schemaVersion` says which layout the file has. A change to the structure raises it, with a
  conversion step from 1.0.0 on (decision 0049, and
  [0080: Compatibility before 1.0.0](0080-compatibility-before-1-0-0.md)). A file without one,
  from before this layout, is set aside: a run by hand
  offers to rename it to a dated backup and ask its questions again, keeping only `testHomeDir`,
  and a quiet run says so and stops. A version higher than the code knows is a `PROBLEM`, and
  setup never saves over that file.
- Every value is checked on every run, against one list of the settings plus the preferences
  each skill declares. A value of the wrong kind is a `PROBLEM` that names it and says what it
  counts as instead. A key nothing declares is removed, with one line naming it and a backup, as
  decision 0049 says. Setup stops only when the file can't be read at all.
- `dev-home.json` gets `schemaVersion` too, and the same checks of its values, but setup keeps
  any key there it doesn't know (`dev_home_text` in `internal/shared/settings.py`), which
  [0068: Versions and layouts in dev-home](0068-versions-and-layouts-in-dev-home.md) relies on.
  Its setting keeps its name,
  `multiMachine`. Without a version, a run by hand asks its question again, with the old answer as
  the default, and rewrites the file in place: git keeps its history, and a backup file would show
  up in every sync as an uncommitted file. Until then, and while its version is higher than the
  code knows, the copies setting counts as unanswered, so each sync checks GitHub. It also records
  the newest dev-home-toolkit version that has set dev-home up, and `layoutVersions`, one number
  for each part of dev-home
  ([0068: Versions and layouts in dev-home](0068-versions-and-layouts-in-dev-home.md)), and
  setup's code creates it
  ([0070: Who owns each file in dev-home](0070-who-owns-each-file-in-dev-home.md)).
- `setUp` may go on any folder, the default ones (`~/.claude`, `~/.codex`) included. Missing
  means not answered yet, and a folder with no answer isn't set up, `~/.claude`, `~/.codex`, and
  the session's own included
  ([0034: Runs of setup by hand](0034-runs-of-setup-by-hand.md)). A `false` is kept wherever
  it's written. A folder answered yes that no longer exists is skipped without a word and keeps
  its answer, and the settings menu shows it as not found.
- A skill declares its preferences in a `dev-home-skill.json` in its folder:
  `{"preferences": {"<name>": {"default": true, "label": "...", "help": "..."}}}`. Setup reads
  these from dev-home-toolkit's skills and from the person's own, and a preference is saved, and
  set with `--configure`, as `skills.<skill>.preferences.<name>`
  ([0049: Answers in the settings](0049-answers-in-the-settings.md)).
  Only yes-or-no preferences for now.

Changed on 2026-10-13, 2026-10-14, 2026-10-15, and 2026-10-18.

**Why:**

- The groups match the settings menu, and a name says where the setting is. Settings planned for
  later, such as recommended settings per Claude folder and skills per PC, have an obvious place:
  a folder's answer and its recommended settings share one entry, in place of two lists and a
  map. Decision 0025, "Setup's questions", set aside one map only because it changed a format
  already in use, a cost the developer waived.
- A file newer than the code happens when a branch is checked out in the live folder and then
  `main` again, and with `dev-home.json` when the PCs update at different times. An older file
  happens when a backup is restored. Without a version, the code would read either as broken
  settings. "schemaVersion" follows Docker's image manifests: "version" alone would read as
  dev-home-toolkit's own version.
- Setting an old file aside, rather than moving it forward, keeps code for an old layout out of
  the scripts: each PC answers setup's questions again, once.
- A `PROBLEM` on every sync for a folder that's gone nags someone who removed an account on
  purpose, and a folder that's only gone for a while, such as one on a drive that's unplugged,
  gets set up again as soon as it's back.
- Reading skills' preferences from the start means the first skill that declares one only adds
  its file.

**Options set aside:**

- Flat keys with the skill's name in front of each (every name repeats it), and flat keys with
  dots in them, as VS Code's settings have (grouped by name only).
- Moving an old file to the new layout automatically: code that would stay in the scripts long
  after every PC had moved.
- For a folder that's gone: keeping the `PROBLEM` (it nags on every sync), and dropping its answer
  (a quiet run would have to write the file, and a folder missing only for a while would lose its
  answer).
- A dated backup of `dev-home.json` when it's rewritten: git already has every version.

**Look again if:** a setting needs more than two levels of grouping, or a file without a version
should be moved forward instead of set aside.
