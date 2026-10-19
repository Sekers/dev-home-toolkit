# A release data file holds the version and what end users need to know

**Decision:** dev-home-toolkit's version lives in a small data file in `internal/shared/`, such as
`release.json`, beside the code that reads it, with the facts about the release that end users
and the update check need. Not built yet. Its exact name and fields are decided with the
changelog's format.

- It holds the version, such as `1.2.0`, and facts such as whether the release fixes a security
  problem, whether it needs the end user to do something, how urgent it is, a one-line summary,
  and what a PC needs to run it (`supportedOn` and `dependsOn`, as
  [Skills and releases declare their requirements as facts](skills-and-releases-declare-their-requirements-as-facts.md)
  describes).
- It keeps every release, newest first, so a PC several versions behind sees each one's facts. On
  `develop`, its newest entry stays the last release's until the next release adds one.
- The update check reads the waiting release's file from the fetched commit with one git command,
  only when an update is waiting. From it, the update lines show versions, not commits, such as
  "dev-home-toolkit 1.1.0 is available; you have 1.0.0", and the check holds the update back when
  the PC can't meet a requirement. The lines' exact wording, and their link to the changelog, are
  decided when it's built.
- Each release's tag matches the file
  ([Releases go to main, and work happens on develop](releases-go-to-main-and-work-happens-on-develop.md)).
  A test checks the version against the changelog's newest version, and the security fact against
  a Security section.
- `CHANGELOG.md`, in the root ([What the root holds](what-the-root-holds.md)), holds the release
  notes for people. It gets its format and its first entries before the first public release.

**Added on 2026-10-18,** not built yet, decided by the developer:

```json
{
  "releases": [
    { "version": "1.3.0", "summary": "...", "urgency": "low" },
    { "version": "1.2.0", "summary": "...", "needsAction": "...",
      "withdrawn": [{ "kind": "rule", "name": "...", "reason": "..." }] },
    { "version": "1.1.0", "summary": "...", "security": true }
  ]
}
```

- **`urgency`:** `"low"`, `"normal"`, or `"critical"`, and `"normal"` when left out. A security fix
  counts as critical. On a PC with automatic updates off, a low release gets no line of its own,
  and is named when a bigger update also waits, such as a release that changes only docs. A normal
  one gets the `UPDATE` line, which the end user's "no" or "remind me" can silence once the update
  notice takes those answers. A critical one can't be silenced.
- **Waiting releases combine:** the update a PC installs contains every release in between, so it
  takes the highest `urgency` among them, counts as a security fix if any is one, and shows every
  `needsAction`, oldest first.
- **Majors get no rule of their own:** each release's `urgency` is the developer's call, and the
  update notice always marks a major, such as "2.0.0 is a major update: see what changed".
- **The security fact is written twice,** as a `### Security` section in `CHANGELOG.md` and as
  `"security": true`, and a test checks that they match, naming the version. With the list of
  releases, tests also check that every version in `CHANGELOG.md` has an entry, in order.
- **`withdrawn`:** each release's entry may list what that release takes away, each item with
  `kind` (`skill`, `rule`, or `file`), `name`, and `reason`. The update notice names each one with
  its reason. The release step checks that every built-in skill gone since the last release's tag
  is listed.
- **`CHANGELOG.md` is written for end users, never developers.** The baseline is the last release,
  so a bug made and fixed between releases is no entry. An entry says what an end user saw, what
  happens now, and what they have to do, and leaves out root cause, internal names, and how it was
  found. Keep a Changelog 1.1.0, with its sections in order, `Minor:` and `BREAKING CHANGE:`
  prefixes, and one entry per audience. Changes that touch only developers stay out. Security lists
  only fixes for a hole in what runs on end users' PCs, using the handoff skill's definition of a
  security bug, and a new security feature goes under Added. These rules go on the release-steps
  page in `docs/development/`.
- **The release step refuses** while an `[Unreleased]` section exists, and when the release file's
  newest version already has a tag.

**Why:** the code reads the version from a file, so a tag that's missing, never pushed, or wrong
never changes what end users see, and a copy without tags, such as a fork that didn't copy them,
still knows its version. A tag that never reaches GitHub is a common slip, since a plain
`git push` sends no tags. The facts beside the version are what the update check needs before it
decides what to say, or whether to install at all, so they're data, not prose. Picked out of the
changelog's text, they'd break when its wording changed, take a second git command, and leave
nowhere for requirements. A security fix matters most to end users who turned automatic updates
off, and an update that needs them to act should say so, not only through a new first number.

**Options set aside:**

- The tags alone: finding the version takes a git command each time, and a copy without tags has
  none.
- A one-line version file, with the other facts read from the changelog's prose: fragile, two
  git commands, and no place for requirements.
- Two files, one for the version and one for the facts: one more file, for nothing.
- A `VERSION` file in the root: the root holds only what must be there, and end users see the
  version in what the scripts print, not in a file.
- A line of Python, such as `VERSION = "1.0.0"`: reading a waiting release's version would mean
  picking it out of code.
- Keeping only the last release, or the latest few with an older PC treating the update as
  recommended: a PC that skipped versions would miss a security fix, a step it had to take, or a
  withdrawn item's reason.
- Using only the newest release's facts when several wait: the same loss.
- `recommended`, matching skill and rule files: a release's field grades how much it matters, so
  the match was cosmetic, and "not recommended" reads as "don't install". `"optional": true`, with
  only two levels: no way to mark a critical fix that isn't a security fix, and adding one later
  wouldn't reach the PCs that are behind, which are the ones that need it. `level`, which doesn't
  say level of what. Debian's changelogs use `urgency` for the same idea.
- A test requiring every major to be recommended: with releases combined, it would only nudge a
  PC with automatic updates off sooner, and it takes away the developer's judgment. A warning in
  the release step, asking the developer to confirm.
- The release step filling `security` from `CHANGELOG.md`'s heading: it would make the release
  step edit the JSON, to save one line that the test already catches.

Why three levels now: a fix for a bug that can lose an end user's files is as urgent as a security
fix but isn't one, and an older copy can only act on levels it already knows, so every level has to
exist before 1.0.0.

**Look again if:** releases need facts that change after they ship, such as a release withdrawn,
which a file inside the release can't say.
