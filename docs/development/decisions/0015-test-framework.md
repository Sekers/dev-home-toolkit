# 0015: Test framework

**Built:** yes.

**Decision:** pytest is the one entry point for the tests. `internal/development/pyproject.toml`
holds the 3.12 floor, a development group (`pytest`, `pytest-xdist`, `pytest-cov`, `ruff`, `mypy`),
and each development tool's settings, and `uv.lock` beside it pins them (see decision 0016, "The
root", for why there). `mypy` runs in strict mode and `ruff` checks and formats from the first
Python file. The tests in `internal/development/tests/` share `helpers.py`, and `conftest.py`,
which gives a test that runs a script's code in its own process the script's environment, and
checks the real profile once a worker's tests are done. Fakes only stand in for what needs a
person or an outside service; git and the file system stay real. A test that needs a fake runs
the script's code in the test process, loaded from the sandbox's copy, with pytest's
`monkeypatch`. Coverage is a report run on demand, with no minimum. A test checks that the scripts
use only the standard library, since the development tools are importable when the tests run them.

**Why:** fixtures share one sandbox among a module's tests, `pytest-xdist` runs the groups in
parallel (the whole suite in about 30 s), and the "needs a person" paths get tests, with small
fakes for the person.

**Options set aside:**

- A plain script, as the PowerShell `Invoke-Tests.ps1` was: every runner feature would be
  written by hand.
- Pester: the scripts are moving to Python. An earlier version of this entry counted Pester's
  install against it, but an install isn't a reason against a development tool.
- `unittest`: no fixtures to share a sandbox, and no parallel runs.
- `pyright`: its PyPI package needs Node.
- `ty`: still in beta (0.0.84 when looked at). Look again once it's stable.
- A coverage minimum: the number would steer what gets tested.

**Look again if:** CI is added, or the suite gets slow.
