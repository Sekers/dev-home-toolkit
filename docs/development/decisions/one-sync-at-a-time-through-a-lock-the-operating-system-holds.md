# One sync at a time, through a lock the operating system holds

**Decision:** `sync.py` locks the file `dev-home-sync.lock` in dev-home's `.git` folder through
the operating system (`msvcrt.locking` on Windows, `fcntl.flock` elsewhere), and waits up to 2
minutes for another run on the same dev-home to let go. `update.py`, run by a person, holds the
same lock for its pull, so a sync in another session can't run setup while git replaces the
skills' files. It never holds it while its question waits, or while the setup after the pull
runs, since that setup may ask questions too. Setup holds it for its own work, which comes after
all its questions
([A run of setup by hand asks what's unanswered, then shows every setting](a-run-of-setup-by-hand-asks-whats-unanswered-then-shows-every-setting.md)).

**Why:** the operating system lets go of the lock when the process ends, even one that stops
partway, so no lock is ever left behind for someone to delete. It's in Python's standard
library on every platform, and the file sits inside `.git`, where git ignores it.

**Options set aside:**

- A named mutex, as `sync.ps1` used: Windows only, and Python would need `ctypes` calls to
  reach it.
- A file that exists only while a run holds it: one left by a run that stopped partway would
  stop every sync until someone deleted it.

**Look again if:** dev-home moves somewhere a file lock doesn't hold, such as a network drive.
