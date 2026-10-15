# local-settings.json groups its settings, and both settings files carry a version

**Decision:** this PC's settings are grouped by what they're about, and each one's name is its
path, as in git config and Codex's `-c`:

```json
{
  "schemaVersion": 1,
  "devHome": { "folder": "C:/Programming/dev-home", "checkEveryHours": 12 },
  "updates": { "installAutomatically": false, "checkEveryHours": 24 },
  "claudeCode": { "folders": { "~/.claude-second": { "setUp": true } } },
  "codex": { "homes": { "~/.codex": { "setUp": true } } },
  "skills": { "handoff": { "includeSecurityBugsInIssueOffers": true } }
}
```

- `--configure` takes the path, such as `--configure 'updates.checkEveryHours=6'`. A folder has
  a dot in its name, so folders keep `claudeCode.folders+=<folder>` and `-=<folder>`. (Later
  changed by
  [Codex is set up in every Codex home, or in none](codex-is-set-up-in-every-codex-home-or-in-none.md):
  Codex has one answer for every home, `codex.setUp`, and an entry in `codex.homes` holds no
  answer of its own; it lists a home setup can't find by itself.)
- A setting is written only once it's answered, and then it stays, so a later change of default
  never changes a PC that answered. `testHomeDir` stays at the top, as before.
- `schemaVersion` says which layout the file has, and goes up only when a setting is renamed or
  moved. A file without one, such as one from before this change, is set aside: a run by hand
  offers to rename it to a dated backup and ask its questions again, keeping only `testHomeDir`,
  and a quiet run says so and stops. A version higher than the code knows is a `PROBLEM`, and
  setup never saves over that file.
- Every value is checked on every run, against one list of the settings plus the preferences
  each skill declares. A value of the wrong kind is a `PROBLEM` that names it and says what it
  counts as instead. A key setup doesn't know was kept, with a `PROBLEM` naming it, until
  [Settings record answers, not just values](settings-record-answers-not-just-values.md) had it
  removed, with one line naming it and a backup. Setup stops
  only when the file can't be read at all.
- `dev-home.json` gets `schemaVersion` too, and the same checks. Its setting keeps its name,
  `multiMachine`. Without a version, a run by hand asks its question again, with the old answer as
  the default, and rewrites the file in place: git keeps its history, and a backup file would show
  up in every sync as an uncommitted file. Until then, and while its version is higher than the
  code knows, the copies setting counts as unanswered, so each sync checks GitHub.
- `setUp` may go on any folder, the default ones (`~/.claude`, `~/.codex`) included. Missing
  means not answered yet: the default folders are set up, as the recommended pick, and extra
  folders aren't, except the one the session runs in. A `false` is kept wherever it's written.
  (Later changed by
  [A run of setup by hand asks what's unanswered, then shows every setting](a-run-of-setup-by-hand-asks-whats-unanswered-then-shows-every-setting.md):
  a Claude Code folder or Codex home with no answer isn't set up, `~/.claude`, `~/.codex`, and
  the session's own included.)
  A folder answered yes that no longer exists is skipped without a word and keeps its answer, and
  the settings menu shows it as not found.
- A skill declares its preferences in a `dev-home-skill.json` in its folder:
  `{"preferences": {"<name>": {"default": true, "label": "...", "help": "..."}}}`. Setup reads
  these from dev-home-tools' skills and from the person's own, and a preference is saved, and
  set with `--configure`, as `skills.<skill>.preferences.<name>`
  ([Settings record answers, not just values](settings-record-answers-not-just-values.md)).
  Only yes-or-no preferences for now.

**Why:**

- The groups match the settings menu, and a name says where the setting is. Settings planned for
  later, such as recommended settings per Claude folder and skills per PC, have an obvious place:
  a folder's answer and its recommended settings share one entry, in place of two lists and a
  map. "Setup asks each question whose answer isn't saved yet" set aside one map only because it
  changed a format already in use, a cost the developer waived.
- A file newer than the code happens when a branch is checked out in the live folder and then
  `main` again, and with `dev-home.json` when the PCs update at different times. An older file
  happens when a backup is restored. Without a version, the code would read either as broken
  settings. "schemaVersion" follows Docker's image manifests: "version" alone would read as
  dev-home-tools' own version.
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

This changes "Setup asks each question whose answer isn't saved yet", whose two lists become
`claudeCode.folders`; the names used in "How often the sync checks GitHub", "setup.py
--configure changes every setting", and "Setup finds extra Codex homes as it finds extra Claude
folders"; where "Setup offers recommended settings for Claude Code and Codex" and "Setup installs
skills per PC, and the tools show or hide them" save their answers; and the schema version that
"A dev-home has one active copy, or several" set aside until the format changed.

**Look again if:** a setting needs more than two levels of grouping, or a file without a version
should be moved forward instead of set aside.
