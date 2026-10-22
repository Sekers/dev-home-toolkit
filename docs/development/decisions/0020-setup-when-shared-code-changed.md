# 0020: Setup when shared code changed

**Built:** yes.

**Decision:** the sync normally runs setup's code with `--quiet` inside the sync's process, as
it does update's. When `programs.py` loads, it records every Python file's name and modification
time in `internal/shared/`, then checks them again before setup. Setup runs as a Python process
of its own when the sync has just installed an update, or when that check finds a change (tests
check both cases).

The second case covers two overlapping syncs. One can load its modules and wait for the other
to release dev-home's sync lock. If the first sync installs a dev-home-toolkit update, the waiting
one otherwise has old modules loaded when it reaches the new setup file. The fresh process
loads one consistent version. An unreadable check also counts as a change, since isolation is
the safe choice then. The same rule holds for setup's code as for the rest of
`internal/shared/`: it changes nothing the whole process shares (a test checks), its `main`
never raises, and its step in the sync runs in a guard.

**Why:** each sync used to start a PowerShell process for setup, about 0.6 s of every skill
command that syncs. Starting a Python process instead would still cost about 0.05 s each time.
On this PC, the two small folder scans together took about 0.08 ms.

**Options set aside:**

- Run setup in a Python process of its own every time: simpler isolation, but every skill
  command that syncs pays the process start.
- Accept a rare, recoverable import error and let the next sync repair the generated files: the
  failed run leaves the current setup incomplete and tells the end user there is a problem when the
  code can prevent it at negligible cost.

**Look again if:** setup needs something the whole process shares, such as its own current
folder.
