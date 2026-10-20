# Setup follows the newest suitable Python on every run

**Decision:** on every run, quiet ones included, setup works out which Python a first run would
pick, and points `internal/.python` there when it doesn't already: the Python install manager's
folder for its commands, `%LocalAppData%\Python\bin`, or else the newest stable Python 3.12 or
later in the registry. A test release is left out: one the install manager installs has a
`Version` value such as `3.16.0a1` there. Setup starts a Python only to check it before pointing
the link at it, with the check's 60-second limit kept. A switch prints one `LINKED` line naming
both versions, such as `now 3.15.0, was 3.14.8`. Setup only uses Pythons already installed, and
never installs one. Decided by the developer on 2026-10-17.

**Why:**

- Setup's warning about a skill's Python minimum names the version dev-home-toolkit uses, so
  installing a newer Python should move dev-home-toolkit to it. The traditional installer puts a
  new version beside the old one, and the link used to stay on the old one until it was
  uninstalled. The install manager's commands already follow a new Python, so with them a run
  still costs one file check.
- It mostly closes a gap in checking a skill's Python minimum: setup checks it against the
  Python setup runs on, which on a sync is dev-home-toolkit's, but on a run by hand is whatever
  `py` starts. `py` usually starts the newest Python, and now dev-home-toolkit uses the newest
  too.
- The 60-second limit: antivirus software can take many seconds to scan a Python new to the PC,
  more on a slow PC, so a short limit would turn away a good Python.
- A Python that fails the check is noted in `internal/.generated/failed-pythons.json`, with its
  `python.exe`'s size and the time it last changed. A quiet run with a working link skips it
  until those change, so a broken install holds up at most one sync. A run by hand, or one
  without a working link, checks it again, since the end user may have fixed it, or the first
  check may have run out of time during an antivirus scan.
- The `LINKED` line: setup reports every change it makes, and if a script later fails on the new
  Python, the line is the clue. Nothing needs a restart, since each skill command starts
  `internal/.python/python.exe` anew.
- Setup never installs a Python itself. The install manager's commands are its documented way
  to run the Pythons it installed, and their installing one when none is installed at all is
  the install manager's own design, as its docs describe.
- Cost, measured on a developer PC faster than most: reading the registry takes about 0.3 ms
  and starts no process; checking a new Python is one process, about 20 ms, only on a switch.

**Options set aside:**

- A short limit for the check: it turns away a good Python on a slow PC.
- A silent switch, or an `OK` line, which quiet runs hide.
- Building it right after skills per PC: its text would then have been reworded again by the
  product's rename and the glossary.
- Pointing the link at the Python's own folder, picked from the registry, so dev-home-toolkit
  never starts the install manager's commands; or checking first that the Python such a command
  runs is still there, from the undocumented `.__target__` file beside it. Both were proposed
  on 2026-10-20 against the install manager installing a Python on its own, and set aside by the
  developer: the commands folder is the install manager's documented way to run its Pythons, and
  what it does there is its own design.
- For a PC with only the traditional installer, following the PATH, or the `py` launcher's own
  settings (`PY_PYTHON`, `py.ini`). That launcher is deprecated since Python 3.14, and the PATH
  differs with whatever started setup, so the link could flip between syncs. The newest
  registered Python is also what that launcher picks by default.

**Not tested yet:** how the traditional installer marks a test release in the registry's
`Version`; whether a missing-DLL error box holds up a Python started for the check, until the
time limit ends it; and whether the install manager's `python.exe` prompts or downloads when no
runtime is left.

**Look again if:** setup goes beyond Windows, where the newest Python is often not the one
`python3` runs, such as beside a Linux distribution's own.
