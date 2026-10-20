# How often the sync checks GitHub

**Decision:** two settings on each PC, in `local-settings.json`, each a whole number of hours,
where 0 means every time:

- `devHome.checkEveryHours`, 12 by default: how long a sync with one active copy goes without
  fetching dev-home, and, in both modes, how long plain `/knowledge` reads the local copy before
  syncing first.
- `updates.checkEveryHours`, 24 by default: how long the update check goes without fetching
  dev-home-toolkit. Between checks, it still reports, or installs when
  `updates.installAutomatically` is on, the
  commits an earlier fetch found. `update.py` run by hand always fetches, and a sync someone asks
  for, `/dev-home sync` included, keeps to this interval.

Each is timed by its repo's `.git/FETCH_HEAD`, and an empty one counts as no fetch: a fetch that
fails, such as offline, empties the file and still sets its time (tested with git 2.55.0). A
value that isn't a whole number of 0 or more means the default, and setup says so.

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

**Changed on 2026-10-18,** not built yet, with the reasons in
[dev-home records the newest version and each part's layout](dev-home-records-the-newest-version-and-each-parts-layout.md):
when `dev-home.json` records a newer dev-home-toolkit than this PC's, the sync checks GitHub for
updates right away, ignoring `updates.checkEveryHours`, once per newer version. And for both
intervals, a last fetch with no line for the upstream branch, only `not-for-merge` lines, no
longer counts.

**Changed on 2026-10-20,** with the reasons in
[A dev-home skill syncs and configures](a-dev-home-skill-syncs-and-configures.md): plain
`/knowledge` no longer has its own interval, so `devHome.checkEveryHours` applies only with one
active copy, and `--fetch when-due` is gone. Setup's menu names the two answers single-PC mode
and multi-PC mode, and in multi-PC mode shows this setting as
`every time (fixed in multi-PC mode)`.

**Look again if:** git changes what a failed fetch does to `FETCH_HEAD`.
