# One sync at a time, through a lock the operating system holds

**Decision:** `sync.py` locks the file `dev-home-sync.lock` in dev-home's `.git` folder through
the operating system (`msvcrt.locking` on Windows, `fcntl.flock` elsewhere), and waits up to 2
minutes for another run on the same dev-home to let go.

**Why:** the operating system lets go of the lock when the process ends, even one that stops
partway, so no lock is ever left behind for someone to delete. It's in Python's standard
library on every platform, and the file sits inside `.git`, where git ignores it.

**Options set aside:**

- A named mutex, as `sync.ps1` used: Windows only, and Python would need `ctypes` calls to
  reach it.
- A file that exists only while a run holds it: one left by a run that stopped partway would
  stop every sync until someone deleted it.

**Look again if:** dev-home moves somewhere a file lock doesn't hold, such as a network drive.
