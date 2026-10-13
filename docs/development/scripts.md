# setup.py, sync.py, and update.py

The rules for changing the scripts in the root and their code in `internal/shared/`. AGENTS.md
points here; its rules apply too.

## The internal/ folder

`internal/` is dev-home-tools' own machinery, which nobody runs directly:

- `internal/shared/`: the code the scripts in the root load. `setup.py`, `sync.py`, and
  `update.py` in the root are short entry points that load the module of the same name from
  here, and `prepare.py` loads the sync's from here too.
- `internal/.generated/` and `internal/.python/`: what setup makes on each PC (see
  [skills.md](skills.md)). Git ignores both.
- `internal/development/`: everything only people changing dev-home-tools use: the development
  tools' settings (`pyproject.toml`, `uv.lock`), the tests, and what the tools write there, such
  as `.venv/`, their caches, and the tests' `.test-sandbox/`.

## Rules for the scripts

- Python 3.12 or later, the standard library only, and ASCII only (tests check). Windows only
  for now.
- `internal/shared/` holds their code, one file per job, named for it: `setup.py`, `sync.py`,
  and `update.py`, the code of the entry points of the same name; `git.py` (`run_git`, which
  retries while another git process holds a lock); `output.py` (`status_line`, which prints
  every status line in one format, and small text helpers); `programs.py` (finding a program,
  and running setup); `settings.py` (this PC's `local-settings.json`, dev-home's
  `dev-home.json`, the list of settings and their checks, and the preferences skills declare);
  and setup's own parts: `paths.py`, `links.py`, `generated.py`, `python_link.py`, `console.py`,
  `settings_files.py`, `claude_settings.py`, `codex_config.py`, and `configure.py`
  (`--configure`'s menu and assignments). They write UTF-8, read git's output as UTF-8, and find
  a program such as git by its full path in `PATH`, never in the current folder. Put anything
  the scripts would otherwise each copy there.
- Adding or changing a setting, or a skill's preference, follows [settings.md](settings.md).
- The entry points in the root stay short: they check the Python version, load
  `internal/shared/` by its path, and run the module of their own name (a test checks).
  [What the root holds](decisions/what-the-root-holds.md) says why the code isn't in the root.
- Safe to re-run. setup.py never overwrites or deletes anything except its own generated files,
  links whose target is gone, links it made to skills that no longer exist, the
  `internal/.python/` junction once the `python.exe` it leads to is gone, and settings files the
  person said yes to changing. A settings change is shown as a diff first, waits for a typed
  yes, saves a dated backup, and is never offered for a file the script can't fully parse, or
  for a read-only one. The exception to the backup is dev-home's `dev-home.json`, whose history
  is in git: setup commits and pushes it through the sync's `commit_for_setup`, which skips the
  update check and setup, since setup is already running. sync.py never stages, commits, or
  discards a file it wasn't given, and runs no destructive git command: no `add -A`, stash,
  `reset`, `checkout`, `clean`, or rebase.
- Never remove a link, or a folder that may hold one, with a recursive delete such as
  `Remove-Item -Recurse` or `shutil.rmtree`: whether it stops at a junction depends on the tool
  and its version, and one that doesn't deletes what the link points to. Remove each link by
  itself first (`links.py` does, and so does the tests' `remove_sandbox`), or use
  `cmd /c rmdir`.
- Agents run setup.py only with `--quiet`, which never prompts: no settings changes, and no
  creating repos. sync.py runs it that way after every sync that doesn't commit, and after one
  that commits when it brought in commits from GitHub. The one other way an agent runs it is
  `--configure '<name>=<value>'`, which changes that one setting with no prompt, after the end
  user approves the exact change in chat (`--what-if` shows it first): that chat approval stands
  in for a typed yes. Only a person runs it otherwise, and even then it asks only when its input
  comes from a real console and its output goes to one (`console.py`), so it never waits for an
  answer nobody can see or give.
- A question of setup's that offers something a person can take or turn down uses the standard
  answers, as [skills.md](skills.md) says for every such question.
- update.py pulls exactly the commit it showed the end user, so nothing new can slip in between
  their yes and the pull.
- Everything about dev-home-tools updates happens in update's code, so what the end user is told
  and what gets installed come from the same code. Every sync that doesn't commit runs it with
  `--quiet`, which checks GitHub only once `updates.checkEveryHours` have passed since its last
  fetch (and otherwise uses what that fetch found), never asks, and installs waiting commits only
  when `updates.installAutomatically` is on. Run by hand, it always checks GitHub. Keep it small
  and apart from setup: it's how fixes arrive, so even a broken setup can be fixed by an update.
  For the same reason, the sync loads it only when it reaches the check, and an update.py that
  can't load or stops is a `PROBLEM` line, after which the sync still runs setup; each of the
  sync's other steps runs in a guard too, so an error in one is a `PROBLEM` line and the update
  check and setup still run; and when the code can't load at all, the entry points and
  `prepare.py` print a `PROBLEM` line with the commands that install a fix by hand (tests check
  all three).
- `prepare.py` runs the sync inside its own process, and the sync runs update's and setup's
  code there too. Setup runs as a process of its own right after an update installs, or when
  the shared modules changed while this sync waited for another one, so it gets one consistent
  version of the code throughout. So nothing in `internal/shared/` changes what the whole
  process shares, such as environment variables, the current folder, the import path, or sys's
  streams, outside an `if __name__ == "__main__":` block (a test checks). Their `main`
  functions return a number, and never raise or call `sys.exit`. Ctrl+C (`KeyboardInterrupt`)
  passes through them on purpose: the entry points catch it, so it stops a whole sync. And keep
  the name and arguments of what `prepare.py` calls, `main(argv)` in `sync.py`: the
  `prepare.py` running may be a generated copy older than the code on disk.
