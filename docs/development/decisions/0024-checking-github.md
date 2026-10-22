# 0024: Checking GitHub

**Built:** yes, except: the change of 2026-10-18: a sync doesn't check GitHub right away when
`dev-home.json` records a newer dev-home-toolkit, and a fetch with only `not-for-merge` lines still
counts.

**Decision:** two settings on each PC, in `local-settings.json`, each a whole number of hours,
where 0 means every time:

- `devHome.checkEveryHours`, 12 by default: how long a sync goes without fetching dev-home in
  single-PC mode. In multi-PC mode every sync fetches, and setup's menu shows this setting as
  `every time (fixed in multi-PC mode)`. Plain `/knowledge` syncs as adding a note does
  ([0029: The dev-home skill](0029-the-dev-home-skill.md)).
- `updates.checkEveryHours`, 24 by default: how long the update check goes without fetching
  dev-home-toolkit. Between checks, it still reports, or installs when
  `updates.installAutomatically` is on, the commits an earlier fetch found. `update.py` run by
  hand always fetches, and a sync someone asks for, `/dev-home sync` included, keeps to this
  interval. When `dev-home.json` records a newer dev-home-toolkit than this PC's, the update
  check fetches right away, once per newer version
  ([0068: Versions and layouts in dev-home](0068-versions-and-layouts-in-dev-home.md)).

Each is timed by its repo's `.git/FETCH_HEAD`. Two kinds count as no fetch: an empty one, since a
fetch that fails, such as offline, empties the file and still sets its time (tested with git
2.55.0); and one with no line for the upstream branch, only `not-for-merge` lines. A value that
isn't a whole number of 0 or more means the default, and setup says so. Changed on 2026-10-18 and
2026-10-20.

**Why:**

- On each PC, because how often a PC reaches GitHub is that PC's choice, such as a laptop on a
  metered connection. Nothing needs the copies to agree, and a change commits nothing.
- With one copy, `devHome.checkEveryHours` limits how long a wrong setting, or an edit made on
  GitHub's website, goes unseen. Its default is 12 hours, chosen over the 24 first planned.
- `updates.checkEveryHours` is apart from `updates.installAutomatically`: one says when to check
  GitHub, the other
  whether to install what a check found. A check on every command found nothing almost every
  time, and fewer checks bring updates in fewer batches, so a session is stopped to reload a
  changed skill less often.
- `FETCH_HEAD` already holds the time, so there's no state file to add.

**Options set aside:**

- Fixed intervals in the code: nobody could change them.
- `devHome.checkEveryHours` in `dev-home.json`, shared by every copy: each change would be a
  commit to
  all of them, with no reason for them to agree.
- A yes or no for the update check: one number covers the default, every time, and anything
  between.
- An interval of its own for plain `/knowledge` (decision 0029 has why).

**Look again if:** git changes what a failed fetch does to `FETCH_HEAD`.
