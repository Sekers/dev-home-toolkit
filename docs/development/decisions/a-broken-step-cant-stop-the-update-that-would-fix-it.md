# A broken step can't stop the update that would fix it

**Decision:**

- `sync.py` loads `internal/shared/update.py` only when it reaches the update check, and reports
  anything that stops it, even an error that keeps it from loading, as a `PROBLEM` line, then
  goes on to setup.
- Each of the sync's other steps (the commit, syncing with GitHub, listing the uncommitted
  files, and setup) runs in a guard: an error in one, such as a bug on a path no test covers,
  is a `PROBLEM` line, and the steps after it still run. A commit that stops still ends the
  sync, so nothing half done is pushed.
- When the code can't load or run at all, the entry points and `prepare.py` print a `PROBLEM`
  line with the commands that install a fix by hand (`git -C <toolkit> pull --ff-only`, then
  setup), and the README's troubleshooting says the same. `prepare.py` still prints the facts.

**Why:** an update is how fixes arrive, so a bug in the sync must not stop the check that would
install the fix, and a broken sync must never keep an agent from the facts it needs. A guard
costs about 36 ns per sync when nothing fails (measured), against a sync's 1.7 s. Tests break
each part on purpose.

**Options set aside:**

- Only documenting the way out: the likelier failure, an error partway through a sync, would
  still skip the update check every time it happened.
- update's code standing alone, with its own copy of a git runner, status lines, and the
  settings reader, so even a broken `git.py` couldn't stop it: about 40 copied lines, to guard
  against a module that won't load, which the tests catch before any commit.

**Look again if:** the update check moves out of the sync, or a broken shared module ever
reaches a user.
