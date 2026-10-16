# What the root holds

**Decision:** the root holds only what must be there, and the scripts a person runs by hand.
AGENTS.md lists them, with the rule to ask before adding anything there. The rest of what used to
be there lives under `internal/`: the generated files in `internal/.generated/`, the Python link
in `internal/.python/`, and everything for development in `internal/development/` (the tools'
settings, the tests, and what the tools write: `.venv`, caches, and the test sandboxes).

**Why each item stays:**

- `.gitattributes` and `.gitignore`: git applies them to the whole repo only from the root.
- `AGENTS.md` and `CLAUDE.md`: Codex and Claude Code read them from the root.
- `CHANGELOG.md`: Keep a Changelog names it so and puts it in the root, where people and tools
  look for one.
- `LICENSE`: GitHub's docs put it in the root.
- `README.md`: GitHub's front page, and where people look first. GitHub would also show one from
  `docs/` or `.github/`, so this one is convention.
- `setup.py`, `sync.py`, and `update.py`: people run them by hand. They're short entry points
  that load their code from `internal/shared/`. Python writes a `__pycache__` folder beside any
  file another script loads, and `prepare.py` loads the sync's code into its own process, so
  that code in the root would put that folder there. People run them as `py <path>\sync.py`,
  since the Python install manager's
  `py` is an app execution alias in `%LocalAppData%\Microsoft\WindowsApps`, which Windows puts
  on every Windows account's PATH by default (aliases arrived in Windows 10 version 1709), and
  as `python3` on macOS and Linux. An entry point checks the Python version before anything
  else, so an older Python gets a message instead of a syntax error.
- `templates/`: the repo's main content, what setup fills in and links into the tools.
- `internal/`: there to keep everything else out of the root.
- `docs/`: GitHub Pages, without a build workflow, publishes only from the root or `docs/`.
- `local-settings.json`: people edit it by hand to change a setting.

**Why `.generated/` moved, though every PC's links pointed into it:** that was only a reason
about the cost of moving, and on its merits the folder is machinery nobody runs or edits. It
moved in the same update as phase 1's other changes to it, so each PC goes through one
transition. On a PC set up before, the old folder is deleted by hand; setup then replaces the
links into it, as it does any link whose target is gone.

**Why `internal/development/`, with the tests in it:** ruff finds its settings by looking in a
file's folder and the ones above it, so tests under the settings get them with no flag, in the
editor too. "development" matches `docs/development/`; `dev/` or `dev-tools/` would read like
"dev-home" or "dev-home-tools".

**What it costs:** longer development commands (`uv run --directory internal/development ...`).
Ruff has to be given its settings for the skill scripts, which aren't under them, and an editor's
ruff extension and test panel won't find them for those files without settings of its own. The
usual fix for the editor, a `.vscode/settings.json`, would be a root folder, so it needs its own
decision.

**Options set aside:**

- `pyproject.toml` and `uv.lock` in the root, where Python projects usually keep them: the tools
  would find them without flags, but they and what the tools write would add seven entries to
  the root, and dev-home-tools isn't a package.
- The whole of sync's and update's code in the root, with `prepare.py` loading it without
  writing a cache: it would be compiled again on every skill command, and the code they share
  would still need a folder elsewhere.
- `prepare.py` starting `sync.py` as a process of its own: one more Python start, about 0.03 to
  0.1 s, on every skill command.
- The Python code in a folder of its own, such as `internal/lib/`, with `internal/shared/` left
  to setup's PowerShell files until phase 3: two folders doing one job until then.
- The whole of setup's code in the root: setup runs inside the sync's process too, so the same
  `__pycache__` reason applies.
- The tests staying in `internal/tests/`: ruff wouldn't find its settings for them.

**Look again if:** dev-home-tools becomes a Python package, an editor's settings become worth a
root folder, or a `--configure` switch means nobody edits `local-settings.json` by hand.
