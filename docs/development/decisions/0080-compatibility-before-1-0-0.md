# 0080: Compatibility before 1.0.0

**Built:** nothing to build.

**Decision:** until dev-home-toolkit's first release, 1.0.0, nothing keeps it compatible with its
own older versions. A change to a file's layout, a setting, or a name comes with no conversion
step, no fallback, and no code that still reads the old form, even where a decision describes such
handling. A layout change raises no layout version either: it updates the current layout's list
in place, in the same commit
([0068: Versions and layouts in dev-home](0068-versions-and-layouts-in-dev-home.md)). When a
change needs something done on a PC that's already set up, the agent tells the developer what to
do there by hand. The one exception is `formerNames`, which carries end users'
answers over a rename
([0049: Answers in the settings](0049-answers-in-the-settings.md)). Decided
by the developer, who on 2026-10-16 set 1.0.0 as the point where compatibility starts, and changed
on 2026-10-22 (layout versions).

**Why:**

- Semantic Versioning lets anything change before a first release.
- Layouts and settings are still settling, and conversion code written now would have to be kept,
  and tested, through every later change.
- No layout version raised: setup treats a `schemaVersion` other than its own as unknown, reports
  a `PROBLEM`, and never saves over the file, so each raise would mean editing the number by hand
  on every PC that's set up, and 1.0.0 would start at whatever number the changes had reached.
  Updating the list in place still makes every layout change show in the commit's diff.
- One rule in one place, AGENTS.md's "Layout and what to build on", is all that changes at 1.0.0.
  The decisions describe the handling that applies from then on.

**Options set aside:**

- Keeping the rule out of the public docs: developers and agents couldn't follow it, and
  [settings.md](../settings.md) would keep telling them to write conversion steps before 1.0.0.
- Stating it in each decision it touches: "before 1.0.0" clauses across many pages, each to clean
  up at 1.0.0.
- Raising a layout version for each layout change before 1.0.0, as from then on: each raise needs
  the number edited by hand on every PC that's set up.

**Look again if:** 1.0.0 is near. This then becomes the rule that backwards compatibility is
generally needed, unless the developers decide a case makes it too difficult.
