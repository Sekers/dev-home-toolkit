# 0078: VS Code settings

**Built:** yes.

**Decision:** a committed `.vscode/settings.json` sets `python.defaultInterpreterPath` to
`${workspaceFolder}/internal/development/.venv/Scripts/python.exe`, so VS Code uses the
environment the development tools run in, on every PC, with no step by hand. The root gains a
`.vscode/` folder for it. It holds only that setting; other editor settings, such as the ruff
extension's or the test panel's, would join it once decided. markdownlint's rules aren't one of
them: they're in a file of their own in the root
([0082: markdownlint's rules](0082-markdownlints-rules.md)). Decided by the developer on
2026-10-22.

**Why:**

- VS Code doesn't find the environment by itself: the Python Environments extension looks for
  one only in the folder VS Code opens and one folder down (its default search paths, `.venv` and
  `*/.venv`, read in version 1.40.0), and this one is two folders down. VS Code then uses the
  global Python, which doesn't have the development tools, so the editor can't resolve the tests'
  imports.
- A choice made by hand in VS Code is kept per folder and per PC: every developer would repeat it
  on every PC, and it's lost when the folder moves, as it was when this repo's folder was renamed
  on 2026-10-17. Developers work on more than one PC, and there may be more of them later.
- `python.defaultInterpreterPath` is the Python extension's own setting, so it works whether or
  not the Python Environments extension is on. That extension is a preview turned on by
  experiment (`python.useEnvironmentsExtension` defaults to `false` in the Python extension
  2026.10.0). With it on, the setting comes before its own search. Checked on 2026-10-22 on
  Windows, with it on: once the file was added, the open window switched to the environment
  without a reload.
- VS Code reads a folder's workspace settings only from `.vscode/` in that folder. `.gitignore`
  already let `.vscode/settings.json` and `.vscode/extensions.json` be committed, and the
  decision "[0016: The root](0016-the-root.md)" left this to a decision of its own.

**What it costs:**

- A folder in the root, read only by VS Code and editors built on it, such as Cursor.
- The path names `Scripts`, Windows' folder for an environment's programs; macOS and Linux use
  `bin`. Where the path doesn't exist, as there or in a clone without the environment built, the
  Python Environments extension falls back to its own search, as its code shows.
- A developer who wants other workspace settings edits a tracked file. The Python Environments
  extension can also write its own settings here, such as `python-envs.defaultEnvManager`, when a
  developer picks an environment by hand (seen in its code, not tested), so read this file's diff
  before committing it.
- A clone where VS Code wrote workspace settings of its own, into an untracked
  `.vscode/settings.json` before this file arrived or into this file since, can't take an update
  that adds or changes this file: git refuses to overwrite the local copy, so that update and every
  later one wait until the copy is moved aside. The update's line quotes only git's first line,
  which doesn't name the file. Tested with git on 2026-10-22.

**Options set aside:**

- Each developer picking the environment by hand, as before: repeated on every PC, lost on a
  move, and a new developer meets the unresolved imports first.
- A committed template, such as `settings.template.json`, that each developer copies to
  `.vscode/settings.json`, as TypeScript and Prettier do: VS Code's own writes would stay out of
  a tracked file, but every clone needs a step by hand, which this decision set out to avoid.
- The Python Environments extension's `python-envs.workspaceSearchPaths`, which takes a relative
  path and so works on every OS: that extension is off by default.
- A `.code-workspace` file in `internal/development/`: no root folder, but everyone would have to
  open that file instead of the repo's folder.
- The environment back in the root: it goes against decision 0016, "The root", and
  needs either the development tools' settings in the root or a setting on every developer's PC,
  such as uv's `UV_PROJECT_ENVIRONMENT`.

**Not tested yet:** the setting with the Python Environments extension off, where the Python
extension reads it itself; and whether a developer's choice made by hand still wins over it at
the next start.

**Look again if:** development moves beyond Windows, which needs a path or a setting that works
there too; or the Python Environments extension becomes the default, whose search setting would
then work on every OS.
