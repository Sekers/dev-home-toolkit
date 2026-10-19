# dev-home records the newest version and each part's layout

**Decision:** `dev-home.json` records the newest dev-home-toolkit version that has set dev-home
up, and a layout version for each part of dev-home, and tests catch a layout change made without
one. Not built yet: it needs version numbers
([A release data file holds the version and what end users need to know](a-release-data-file-holds-the-version-and-what-end-users-need-to-know.md)).
Decided by the developer on 2026-10-18.

- **The newest version** is a new field in `dev-home.json`, its name settled when building.
  `schemaVersion` doesn't change, since setup keeps keys it doesn't know there (`dev_home_text` in
  `internal/shared/settings.py`). A PC on an older version leaves `built-in/` alone, and the other
  files dev-home-toolkit owns in dev-home, with one line saying to update. A PC on the newest
  deletes any built-in rule it doesn't know, as withdrawn. Unreleased code needs a version that
  counts as newer than the last release, such as `1.5.0-dev` for work after 1.4.0: SemVer ranks a
  pre-release above the release before it and below its own, while build metadata such as `+dev`
  doesn't count in the order. The exact form is settled when building. Rolling every PC back
  freezes those files until
  the field is reset, such as through `/dev-home configure`.
- **An early update check.** When `dev-home.json` records a newer version than this PC's own, the
  sync checks GitHub right away, ignoring `updates.checkEveryHours`, and installs the update if
  automatic updates are on. With them off, the update's line, whenever the waiting releases'
  `urgency` gives one, also names the version another PC runs. Once per newer version: after a check that reaches GitHub, the sync writes that version as
  `alreadyCheckedFor` in `internal/.generated/update-check.json`, and a missing or unreadable file
  counts as no record. Both interval checks, for updates and for dev-home, keep using
  `.git/FETCH_HEAD`'s time, but a last fetch with no line for the upstream branch, only
  `not-for-merge` lines, doesn't count.
- **Layout versions:** a `layoutVersions` field, such as `{ "rules": 1 }`, with a part added when
  its layout first needs one: `knowledge` with its subject lists
  ([The knowledge index lists subjects, and each subject lists its notes](the-knowledge-index-lists-subjects-and-each-subject-lists-its-notes.md)),
  and `handoffs` when its layout first changes. A part with no number yet counts as layout 1, and
  its test's list is layout 1's. `schemaVersion` keeps meaning `dev-home.json`'s own
  layout. The code that writes a part checks only that part's number. A PC that finds a higher
  number than it knows leaves that part alone and says to update; for `rules/`, it also keeps its
  agents' files as they are. The newest version tells newer code which layout to convert from.
- **Layout tests,** for every part another version may read: `dev-home.json` and
  `local-settings.json`, by their `schemaVersion`, and `rules/`, `handoffs/`, and `knowledge/`, by
  `layoutVersions`. For each part, a test lists what its code produces: the files, with made-up
  names replaced by placeholders, each note's field names, JSON keys, and template sections. The
  list is saved in dev-home-toolkit's repo for each version. A difference fails the test until the
  version is raised and the new list saved, and from 1.0.0 on, until a conversion step exists.
  Every test counts: a file that matches nothing on its part's list fails the test that wrote it.
  Released lists are locked: the release step refuses if a released version's list changed, or if
  any check fails. Not caught: a change in what a file means, or in which files the code reads; a
  rule in `docs/development/` says those count as layout changes too. `rules/` and the two
  settings files get their tests with the rules work, and `handoffs/` and `knowledge/` before
  1.0.0. Layout changes before 1.0.0 need no conversion steps.

**Why:**

- Files dev-home-toolkit owns in dev-home are shared between PCs, so a PC that's behind must not
  write back older text, delete a newer built-in rule, or bring back a withdrawn one. One field,
  written once per release, keeps the files themselves free of versions.
- The early check: PCs differ in version only until the next sync. Nothing is added to ordinary
  syncs: it's one GitHub check, about 0.4 s for dev-home-toolkit (measured 2026-10-06), on the sync
  that first sees a newer version, approved by the developer under AGENTS.md's Speed rule. Git's
  record counts every tool's fetch.
- Layout versions: a PC that's behind can't tell whether a newer release changed a layout. One
  number per part stops it only where the layout changed, and different code writes different
  parts: setup writes `rules/`, and the skills write `handoffs/` and `knowledge/`.
- Layout tests (the developer): a layout change must never reach a release without its version.

**Costs:** on a PC that's behind, a `state` change to a built-in rule waits until it updates, and
version numbers are needed before built-in rules ship.

**Options set aside:**

- The version that last wrote each rule file (every release would rewrite every file, and a PC
  that's behind would still bring back withdrawn rules); a list of withdrawn names plus a
  `revision` per rule, a number the developer raises with each change to the rule's text (the same
  churn, and developers must remember to raise it); comparing rules at
  update time (it misses a `git pull` by hand).
- For the early check: `dev-home.json`'s file time (other changes to it would trigger checks); a
  `lastChecked` of its own (it ignores other tools' fetches, and repeats git's record); a time
  limit (a PC that stays behind would check every hour); keeping the record in
  `local-settings.json`, or in git's config; the names `checkedEarlyFor` and `checkedForVersion`.
- Every release counting as a layout change (a PC with automatic updates off would stop applying
  rule changes after every release); carrying on regardless (it would write into an old layout);
  widening `schemaVersion` to all of dev-home (a change in one part would freeze every part); a
  single `layoutVersion`.
- A registry of path templates with a gateway every write goes through (too complicated for
  developers); a fingerprint of names kept in one module (it misses paths built elsewhere, and
  rearrangements); review and a checklist alone; raising the version automatically (a layout
  change also needs a conversion step, which only a developer can write).

**This changes:**
[local-settings.json groups its settings, and both settings files carry a version](local-settings-json-groups-its-settings-and-both-settings-files-carry-a-version.md),
for `dev-home.json`'s new fields; and
[How often the sync checks GitHub](how-often-the-sync-checks-github.md), whose interval the early
check skips once per newer version, and whose last-fetch time no longer counts a fetch with only
`not-for-merge` lines.

**Look again if:** a part's layout needs more than one number, or PCs on different versions stay
apart for long.
