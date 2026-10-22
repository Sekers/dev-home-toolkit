# A passing test run removes the sandboxes earlier runs kept

**Decision:** a test module's sandbox is still deleted when its tests pass and kept for a look
when one fails. When a whole run passes, pytest's main process then removes each kept sandbox
that hasn't changed for an hour, through `remove_sandbox`, and the run's summary says how many
went (`pytest_sessionfinish` and `pytest_terminal_summary` in `conftest.py`, and
`remove_kept_sandboxes` in `helpers.py`). Any run that passes counts, a run of one test file
included. Decided by the developer on 2026-10-22.

**Why:**

- Nothing removed kept sandboxes before, so they piled up unnoticed: 23 on one development PC and
  30 on another by October 2026. Each is a copy of the repo with a junction to a real Python
  install, which a delete that follows junctions would wipe out, so removing them by hand was
  risky too.
- A failing run keeps everything, so a developer looking into a failure finds every sandbox it
  kept, and the first run to pass afterwards clears them.
- The hour: a whole run takes minutes, so a sandbox unchanged that long is never one a run going
  on at the same time is using. A sandbox's folder changes whenever an entry directly in it is
  added or removed.
- Only the main process: with xdist, each worker's session ends too, before the run's result is
  known.
- A sandbox that can't be removed, such as one a terminal has open, gets a line, and the next
  passing run tries again. The run's result stays as it was.

**Options set aside:**

- Removing kept sandboxes at the start of every run: it deletes one a developer is still looking
  at, an hour after the failure.
- Keeping only the newest few: a burst of failures pushes out the one wanted.
- Leaving them to be removed by hand, as before: they piled up unnoticed.

**Look again if:** a whole run comes to take close to an hour, or a test starts keeping a sandbox
on purpose.
