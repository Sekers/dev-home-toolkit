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
  one.
- Run the skills' commands word for word from the sandbox's generated skills, as `helpers.py`
  does. It starts each with the test environment's Python, by its real path, in place of
  `internal/.python/python.exe`, because a virtual environment's `python.exe` can't run through
  a junction; that also lets coverage measure the scripts. One test runs a command unchanged.
  Adding `--cov` to the pytest command reports coverage, on demand and with no minimum.
- A script that should only report, `facts.py` or the handoff skill's `issue_status.py`, runs
  through `tests/read_only_launcher.py` whenever `run_command` runs it, and the test fails at
  anything the script changes, or at a kind of audit event the launcher hasn't sorted yet, such
  as one a new Python version raises; the failure says how to sort it
  ([why](decisions/the-tests-check-the-scripts-that-only-report-in-two-ways.md)).
- Fake only what needs a person or an outside service, such as a console answer, `gh`,
  Developer Mode, or another platform; git and the file system stay real. Use `monkeypatch` and
  small typed fakes first, and `unittest.mock` only with `autospec`, where recording calls saves
  real work.
- What needs a person is tested with a fake for them: setup's questions, a yes or no to a
  settings change, and creating dev-home with a faked gh (`test_setup_questions.py`, which runs
  setup's code in the test process from the sandbox's copy). What the tests can't reach, so it
  gets checked by hand: a real console's prompts, a real clone or repo creation on GitHub, and
  finding a Python through the registry, which a test profile skips. Say which of those a change
  affects.
