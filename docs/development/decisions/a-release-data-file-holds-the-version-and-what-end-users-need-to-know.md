# A release data file holds the version and what end users need to know

**Decision:** dev-home-toolkit's version lives in a small data file in `internal/shared/`, such as
`release.json`, beside the code that reads it, with the facts about the release that end users
and the update check need. Not built yet. Its exact name and fields are decided with the
changelog's format.

- It holds the version, such as `1.2.0`, and facts such as whether the release fixes a security
  problem, whether it needs the end user to do something, whether it's recommended or optional,
  a one-line summary, and what a PC needs to run it (`supportedOn` and `dependsOn`, as
  [Skills and releases declare their requirements as facts](skills-and-releases-declare-their-requirements-as-facts.md)
  describes).
- On `develop`, it keeps the last release's version and facts until the next release changes
  them.
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

**Look again if:** releases need facts that change after they ship, such as a release withdrawn,
which a file inside the release can't say.
