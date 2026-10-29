# 0085: Files dev-home ignores

**Built:** yes, except: existing dev-homes get these lines only once setup keeps dev-home's
`.gitignore` current, which
[0070: Who owns each file in dev-home](0070-who-owns-each-file-in-dev-home.md) hasn't built yet.

**Decision:** besides `.drafts/`, `AGENTS.md` and `CLAUDE.md`, and the files operating systems and
VS Code leave, dev-home's `.gitignore` (`templates/dev-home/.gitignore`) ignores what programs
make on each PC that can't work on another:

- `__pycache__/`: the caches Python writes beside a module another script imports.
- `.venv/`: a Python environment.
- `node_modules/`: JavaScript packages. A skill that ships its own brings them back with
  `!node_modules/` in a `.gitignore` in its folder.
- From a JetBrains IDE's `.idea` folder, at any depth, only `workspace.xml`,
  `usage.statistics.xml`, and `shelf/`.

It has no line for `.claude` and none for the caches of test and lint programs. Decided by the
developer on 2026-10-29.

**Why:**

- The sync lists every file git doesn't ignore, one per line, on every skill command, and the
  skills offer to commit each once nobody has touched it for 15 minutes. A Python environment with
  no ignore file of its own put 897 files in that list (tested on 2026-10-29).
- What to leave out: a wrong ignore line fails without a word, keeping a file meant for the end
  user's other PCs on one PC, while a missing one only shows a file in the sync's list.
- `__pycache__/`: a cache for one Python version, written whenever one script imports another.
  dev-home-toolkit's own `.gitignore` already has it, and one line in the root covers every depth
  (tested with git 2.55.0).
- `.venv/`: Python's `venv` docs say an environment is "not considered as movable or copyable"
  and "not checked into source control systems such as Git". Python 3.13 and later, and uv
  0.11.32, write a `.gitignore` holding `*` into each environment they make (tested on
  2026-10-29), but dev-home-toolkit supports Python 3.12, whose environments have none.
- `node_modules/`: Node looks for a module's packages in `node_modules` beside it, then in each
  folder above, after resolving links (Node's modules docs), and npm's docs say "If you wish to
  `require()` a package, then install it locally". So each PC installs a JavaScript skill's
  packages inside dev-home. GitHub's ignore file for Node lists `node_modules/`, Anthropic's
  published skills ship no packages (`anthropics/skills`, 2026-10-29), and a skill such as
  `civitai/civitai`'s `.claude/skills/browser-automation` keeps its `package.json` and
  `package-lock.json` without `node_modules`. A `!node_modules/` line in a skill's own folder
  overrides the root's line (tested with git 2.55.0).
- JetBrains: its article "How to manage projects under Version Control Systems" (updated
  2026-06-25) says to share "All files under the .idea directory in the project root except the
  items that store user-specific settings: workspace.xml, usage.statistics.xml, shelf directory".
  Its other files then reach the end user's other PCs, as `.vscode/settings.json` does. `**/`
  covers a project opened at any folder in dev-home. In Stack Overflow's 2026 survey, 24.3% of
  respondents used IntelliJ IDEA regularly and 13.5% PyCharm.

**Costs:** six lines and their comments in every dev-home's `.gitignore`, with no time added to
any run and nothing agents read.

**Options set aside:**

- `.claude/settings.local.json`: Claude Code adds `**/.claude/settings.local.json` to each PC's
  global git ignore file the first time it writes the file (its settings docs), so a line here
  would only cover a file made by hand, whose maker may mean to share it.
- All of `.claude/`: Claude Code's docs mark everything else there, such as `settings.json`,
  `skills/`, and `agent-memory/`, as files to commit, so in dev-home they're meant for the end
  user's other PCs. dev-home-toolkit never writes one.
- `.pytest_cache/`, `.mypy_cache/`, and `.ruff_cache/`: pytest 9.1.1, mypy 2.4.0, and ruff 0.16.10
  each write a `.gitignore` holding `*` into their cache (tested on 2026-10-29).
- GitHub's whole JetBrains file: written for teams, it also ignores the dictionaries folder,
  which JetBrains suggests excluding only "to avoid conflicts if other developer has the same name",
  while every PC sharing a dev-home is one person's, and it has lines for Gradle and Maven, which
  build Java projects.
- All of `.idea/`: against JetBrains' advice, and the end user's IDE settings would never reach
  their other PCs.
- No `.idea` lines: `workspace.xml` would be offered for commit after each use of the IDE, and
  the PCs would overwrite each other's.

**Look again if:** JetBrains changes its list, or JavaScript skills turn out to need their
packages committed.
