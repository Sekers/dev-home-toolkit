# Pylance comparison

On 2026-10-12, Pylance's standard and strict type checking were run on dev-home-tools' code, so
a later decision about strict mode doesn't need the comparison run again. Nothing is decided yet:
whether to adopt strict mode, and clean up what it reports, is still open. mypy stays one of the
four required checks in AGENTS.md's "Testing".

## Results

- **Standard:** no errors or warnings, 41 hints.
- **Strict:** 121 errors, no warnings, 39 hints. 119 of the errors report types Pylance can't
  work out (52 variables, 34 arguments, 30 members, and 3 lambdas), at parsed-data boundaries,
  in containers, and in test callbacks. The other 2 are deprecated `Iterator` return annotations
  on context managers. Most are in `internal/shared/settings.py` (57),
  `templates/skills/handoff/issue_status.py` (16), and `internal/shared/claude_settings.py`
  (11).
- **mypy in strict mode,** with its Python 3.12 target, passed all 33 files.

The errors show places to look, not defects found at run time.

[pylance-comparison.json](pylance-comparison.json) has the full results, including each
diagnostic by file and line. Read its summaries first, and then only the diagnostics for the
file you're looking into.

## How it was run

- VS Code 1.141.0 with Pylance 2026.4.1 (its Pyright 1.1.414), on Windows, with Python 3.14.7
  from the development environment, at commit `40be650`.
- Pylance ran in VS Code's extension test host, with its own profile and extensions folder, so
  nothing in the regular editor changed. The test opened all 33 files mypy checks, with the
  tests' import path set, and read VS Code's diagnostics. The
  [extension testing guide](https://code.visualstudio.com/api/working-with-extensions/testing-extension#advanced-setup-your-own-runner)
  describes the test host's options.
- The data keeps paths relative to the repo and the diagnostics' main fields. It leaves out
  paths on the PC, the editor's internal addresses, and the temporary test file's details. The
  runner and the raw editor output stay on the PC that ran the comparison: they hold that PC's
  paths, and add nothing a decision needs. The data is kept in the repo so another PC or
  developer can use it without running the comparison again.

## Limits

- The tested files had uncommitted changes, and no copy or fingerprint of them was kept, so
  today's files may give different counts.
- Each run counted as finished after a minimum wait and a quiet period with no new
  diagnostics. Pylance has no signal that it has finished a file.

## When to redo it

Redo it when the code it covers, the checker's settings, the dependencies, the Python version,
or the checkers' versions change, and a new baseline is needed. A change to the docs alone
doesn't need one. To check a cleanup, run strict mode on the files it touched.
