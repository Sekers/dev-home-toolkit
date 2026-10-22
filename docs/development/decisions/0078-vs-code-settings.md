# 0078: VS Code settings

**Built:** yes.

**Decision:** a committed `.vscode/settings.json` holds two settings, so VS Code works the same on
every PC, with no step by hand:

- `python.defaultInterpreterPath` is
  `${workspaceFolder}/internal/development/.venv/Scripts/python.exe`, so VS Code uses the
  environment the development tools run in.
- `markdownlint.configFile` is `${workspaceFolder}/internal/development/.markdownlint.jsonc`, the
  markdownlint extension's rules for this repo: prose and headings wrap at 100 characters, and
  code blocks and tables have no limit (rule MD013).

The root gains a `.vscode/` folder for it. Other editor settings, such as the ruff extension's or
the test panel's, would join it once decided. Decided by the developer on 2026-10-22.

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
- markdownlint checks lines at 80 characters by default, and this repo wraps at 100, so about half
  its Markdown lines warned (4,262 of 8,422 on 2026-10-22), and Claude Code's VS Code extension
  hands an edited file's warnings to the agent after each edit: from a few KB to about 400 KB of
  text per edit (seen 2026-10-22). At 100, with code blocks and tables left out, 18 lines warned.
  Once 12 were rewrapped, and a sample output line moved into a code block, 5 did: commands in
  the skills, which stay on one line because agents copy them and the tests match them word for
  word.
- The extension's documentation (version 0.62.1, read 2026-10-22) calls the `markdownlint.config`
  setting deprecated and points to a config file instead. `markdownlint.configFile` takes a path
  in the project, for a project that keeps that file somewhere other than its root. Here it sits
  with the development tools' settings in `internal/development/`, so the root gains nothing, and
  every developer who uses VS Code gets it, where a developer's own config file, named in their
  user settings, covers only their PCs.

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
- Other markdownlint programs, such as markdownlint-cli2, don't read VS Code's settings, so they
  need the file named, such as with markdownlint-cli2's `--config`. The markdownlint extension
  isn't one of the development tools: a developer without it gets nothing from the file, and
  needs nothing from it.

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
- For markdownlint: `.markdownlint.jsonc` in the root, which every markdownlint program finds with
  no setting (a root file for an editor aid nothing else uses); `markdownlint.config` in this file
  (deprecated); only each developer's own config file; markdownlint's default of 80 characters
  (every file would need rewrapping); a comment turning MD013 off on each command line in the
  skills (agents read HTML comments in a skill's body, so each costs tokens on every skill
  command); and leaving the skills out of the check (their prose would go unchecked too).

**Not tested yet:** the setting with the Python Environments extension off, where the Python
extension reads it itself; and whether a developer's choice made by hand still wins over it at
the next start.

**Look again if:** development moves beyond Windows, which needs a path or a setting that works
there too; or the Python Environments extension becomes the default, whose search setting would
then work on every OS; or a markdownlint program other than VS Code's extension comes into use,
such as in the tests, which would want the file where every one of them finds it.
