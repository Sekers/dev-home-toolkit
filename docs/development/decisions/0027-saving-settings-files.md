# 0027: Saving settings files

**Built:** yes.

**Decision:** every settings file setup writes goes through one function, `write_settings_file`
in `internal/shared/settings_files.py`: Claude Code's and Codex's settings, `local-settings.json`,
and dev-home's `dev-home.json`. It writes the new text to a file beside the original, reads it
back, and moves it over the original in one step, so a save that's interrupted leaves the old
file whole. Each caller states whether to keep a dated backup first: the changes to Claude Code's
and Codex's settings and `--configure`'s changes to `local-settings.json` do, and setup's other
saves of `local-settings.json` and `dev-home.json` don't, as before. Git's history is
`dev-home.json`'s backup.

When Windows refuses the move because another program has one of the files open, such as
antivirus scanning it, the move is tried again, waiting 0.05 s at first and doubling up to 0.5 s,
for up to 3 s (`REPLACE_WAIT_SECONDS`). Only access denied (WinError 5) and a sharing violation
(WinError 32) are tried again.

**Why:**

- A file written in place is emptied first, so a save that's cut off leaves a broken file. Setup
  refuses a `local-settings.json` it can't read, on every run, and a broken `dev-home.json` makes
  every sync check GitHub, with setup reporting it, until someone fixes it by hand.
- One function, because its steps (the new copy, the read-back, the read-only check, the backup,
  the move, and the cleanup when one fails) would otherwise be copied into each caller.
- The retry, because a save failed once in the tests with `[WinError 5] Access is denied`, and
  passed on a rerun. Tested on 2026-10-08, on Windows 11 with Python 3.14: `os.replace` fails
  with WinError 5 while any other handle has the file being replaced open, even one shared for
  deleting, and with WinError 32 while the new copy is open without being shared for deleting.
  3,600 swaps in a row, with and without pauses of up to 0.3 s, never failed with Microsoft
  Defender's real-time protection on, so how long such a lock lasts wasn't measured. Go's
  toolchain tries the same errors again for up to 2 s (`src/cmd/internal/robustio`), and npm's
  graceful-fs for up to 60 s, naming antivirus as the cause. 3 s is a little over Go's, and short
  enough for a command an agent runs.
- The retry adds no time to a save that works the first time, and setup's quiet runs, which
  every sync starts, save a settings file only when an answer changed.
- Setup's other files (the generated skills and rules, Codex's `AGENTS.md`, and the notes) stay
  written in place: every setup run compares each with what it should be and rewrites it, so a
  broken one is fixed at the next sync.

**Options set aside:**

- A rename with POSIX semantics (`SetFileInformationByHandle` with
  `FILE_RENAME_FLAG_POSIX_SEMANTICS`, through `ctypes`): tested, it replaces a file another
  handle holds only when that handle shares deleting, and it's NTFS only, so it would still need
  the retry.
- `ReplaceFileW`: Go's maintainers found lower error rates with the `MoveFileExW` call that
  `os.replace` uses.
- Writing in place when the move fails: a write that's cut off leaves a broken file.
- Fixing only the test, such as a pause before the save: a person's real save can fail the same
  way.
- A second copy of the safe save in `settings.py`, for `local-settings.json`.

**Look again if:** a save still fails after the 3 s retry, which would show how long such locks
really last.
