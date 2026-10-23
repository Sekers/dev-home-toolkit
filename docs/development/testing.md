# Testing

How the tests work, and the rules for writing them. AGENTS.md has the four checks to run before
proposing a commit, and points here; its rules apply too.

- uv installs the development tools pinned in `internal/development/pyproject.toml` and
  `uv.lock`, for development only: people who use dev-home-toolkit never need them. They run from
  that folder, so their settings, `.venv`, and caches stay out of the root. Ruff looks for settings
  only in each file's own folder and the ones above it, so the ruff commands name them, and
  check the whole repo from its root, skipping what git ignores. The tests check the working
  tree, uncommitted changes included, and need no network or GitHub.
- pytest is the one entry point. It runs the tests in `internal/development/tests/`, which
  share `helpers.py`. `conftest.py` gives every test process the environment the scripts get
  in the sandbox, for the tests that run the scripts' code in that process, and checks after
  each worker's tests that nothing in the real profile points into a sandbox.
- The tests never run the scripts in this folder. They copy the repo into
  `internal/development/.test-sandbox/` (git ignores it), leaving out `internal/development/`
  and what's set up for this PC, and run the copy, whose `local-settings.json` sets
  `testHomeDir`, so every setup run from the copy uses a scratch profile instead of the real
  one. A module's sandbox is deleted when its tests pass, and kept for a look when one fails;
  the next run that passes removes the kept ones that haven't changed for an hour
  ([why](decisions/0079-old-test-sandboxes.md)).
- Run the skills' commands word for word from the sandbox's generated skills, as `helpers.py`
  does. It starts each with the test environment's Python, by its real path, in place of
  `internal/.python/python.exe`, because a virtual environment's `python.exe` can't run through
  a junction; that also lets coverage measure the scripts. One test runs a command unchanged.
  Adding `--cov` to the pytest command reports coverage, on demand and with no minimum.
- A script that should only report, `facts.py` or the handoff skill's `issue_status.py`, runs
  through `tests/read_only_launcher.py` whenever `run_command` runs it, and the test fails at
  anything the script changes, or at a kind of audit event the launcher hasn't sorted yet, such
  as one a new Python version raises; the failure says how to sort it
  ([why](decisions/0050-testing-scripts-that-only-report.md)).
- Fake only what needs a person or an outside service, such as a console answer, `gh`,
  Developer Mode, or another platform; git and the file system stay real. Use `monkeypatch` and
  small typed fakes first, and `unittest.mock` only with `autospec`, where recording calls saves
  real work.
- The layout tests keep a list of what the code writes into each file another version of
  dev-home-toolkit may read: so far `local-settings.json` and `dev-home.json`, by their
  `schemaVersion`. The lists are in `tests/layout-lists/`, and `tests/layouts.py` says how
  they're written. Every script a test runs is checked afterwards: each key path it added to one
  of those files has to be on that file's list, and `layouts_checked` in `helpers.py` does the
  same for code a test runs in its own process. A test that writes one of those files during such
  a run, standing in for another run, does it inside `writing_meanwhile`, so what it writes isn't
  counted as the run's. `test_layouts.py` checks that the code still writes everything on each
  list, and that the check works. A change in what a key means, or in which files the code reads,
  is a layout change too, though the lists can't see it. Before 1.0.0, a layout change updates
  the current layout's list in place, in the same commit; from 1.0.0 it raises the file's
  `schemaVersion`, saves a list for the new layout, and adds a conversion step
  ([0068](decisions/0068-versions-and-layouts-in-dev-home.md),
  [0080](decisions/0080-compatibility-before-1-0-0.md)).
- What needs a person is tested with a fake for them: setup's questions, a yes or no to a
  settings change, and creating dev-home with a faked gh (`test_setup_questions.py`, which runs
  setup's code in the test process from the sandbox's copy). What the tests can't reach, so it
  gets checked by hand: a real console's prompts, a real clone or repo creation on GitHub,
  finding a Python through the registry, which a test profile skips, and sending a file to the
  real Recycle Bin, which the tests leave alone. Say which of those a change affects.
