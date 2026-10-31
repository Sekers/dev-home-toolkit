# Long paths on Windows

On 2026-10-28, these checks looked at Windows' 260-character path limit across every path
dev-home-toolkit creates or relies on, to decide what to do about the handoff skill's own check of
a path's length, which
[0065: Where end users' rules live](../decisions/0065-where-end-users-rules-live.md) planned then
and which was never built. The design decided from them is
[0088: Path lengths](../decisions/0088-path-lengths.md).

## The limit

**From documentation** (read 2026-10-28):

- Windows limits a path to 260 characters, the terminating null included. A program can use a
  longer one only when Windows' long-path setting is on (`LongPathsEnabled` set to 1, which needs
  an administrator, or the Group Policy "Enable Win32 long paths") *and* the program declares
  itself long-path aware in its manifest, or when the program uses the `\\?\` form of a path
  itself ([Maximum Path Length Limitation](https://learn.microsoft.com/windows/win32/fileio/maximum-file-path-limitation)).
- Python: "paths longer than this would not resolve and errors would result", until an
  administrator turns the setting on; then `open()` and the `os` module accept them
  ([Using Python on Windows](https://docs.python.org/3/using/windows.html)).
- Git for Windows: "long paths support in Git for Windows is disabled by default", and
  `core.longpaths` turns it on for its C-based commands; scripted commands may still fail, and
  Windows Explorer, `cmd.exe`, many IDEs, and the bash, perl, and tcl bundled with Git for Windows
  are affected too
  ([Git for Windows vs long paths](https://gitforwindows.org/git-cannot-create-a-file-or-directory-with-a-long-path.html)).
- macOS and Linux limit each name to 255 characters
  ([Git cross-platform compatibility](https://learn.microsoft.com/azure/devops/repos/git/os-compatibility)).
- Both Claude and Codex have open GitHub issues titled as failures on Windows paths over 260
  characters, in specific parts of each product: for Claude, Cowork's session folders and desktop
  sessions ([#91935](https://github.com/anthropics/claude-code/issues/91935),
  [#98009](https://github.com/anthropics/claude-code/issues/98009)); for Codex, its code-mode host
  and marketplace checkouts ([#55349](https://github.com/openai/codex/issues/55349),
  [#48564](https://github.com/openai/codex/issues/48564)). Only the titles were read, and none is
  about the agents' file tools.

## Tests

**Measured** (2026-10-28, Windows 11 with Windows' long-path setting **on**, Git for Windows
2.55.0, `gh` 2.103.0, Python 3.15.1, PowerShell 7.6.9 and 5.1, Claude Code 2.1.312 in VS Code), in a
scratch folder:

- **git clone**, of a repo holding one file at a 191-character path, into a folder that made the
  file's full path 360 characters:
  - With no `core.longpaths` anywhere (the global config replaced with an empty file through
    `GIT_CONFIG_GLOBAL`): "Clone succeeded, but checkout failed", exit code 128, "Filename too
    long". Windows' setting being on didn't help.
  - With `git clone -c core.longpaths=true`: the checkout succeeded, and the clone's own config
    holds `core.longpaths = true`.
- **gh:** `gh repo clone <a small public repo> <folder> -- -c core.longpaths=true`, with the same
  empty global config: the clone's config holds `core.longpaths = true`, so `gh` passes the option
  on to git, as its help says.
- **Python 3.15.1**, the toolkit's: read the file at its plain 359-character path, and at its `\\?\`
  form.
- **PowerShell 7.6.9 and Windows PowerShell 5.1:** `Get-Content` read the plain path.
- **Claude Code 2.1.312:** its Read tool read the 359-character path, and its Write and Edit tools
  created and changed a new file at a 402-character path. VS Code's Markdown checker reported on
  that file, so VS Code opened it too.
- **cmd.exe:** `type` failed on the path, but the command passed through two shells, so the result
  is inconclusive.

**Measured with the setting off** (2026-10-30, Windows 11 26H2, build 26300, `LongPathsEnabled`
0; Git for Windows 2.54.0, `gh` 2.101.0, Python 3.14.8, PowerShell 7.6.9 and 5.1, Claude Code
2.1.314 in VS Code, the Codex CLI 0.166.0), in a scratch folder, with the test file made by Python
through the `\\?\` form:

- **git clone**, the same test, of a repo holding one file at a 193-character path, into a folder
  that made the file's full path 360 characters: the same results as with the setting on. With no
  `core.longpaths` anywhere, "Filename too long" and exit code 128; with
  `git clone -c core.longpaths=true`, the checkout succeeded. `gh` passed the option on to git, as
  before.
- **Python 3.14.8**, the toolkit's: `open()` on the plain 345-character path failed with
  `FileNotFoundError` (errno 2), and the `\\?\` form worked. So with the setting off, a path over
  the limit is one the toolkit's own scripts can't read through a plain path, though both agents
  can.
- **PowerShell 7.6.9:** `Get-Content` read the plain path. **Windows PowerShell 5.1:** it failed,
  "Cannot find path ... because it does not exist".
- **cmd.exe:** `type` failed, "The system cannot find the path specified", with the path passed in
  an environment variable, so no shell changed it.
- **Claude Code 2.1.314:** its Read tool read the 345-character path, and its Write and Edit tools
  created a new folder and file at a 409-character path, then changed the file.
- **Codex CLI 0.166.0**, through `codex exec`, told to use the plain paths with no workaround: it
  read the 345-character file with PowerShell 7's `Get-Content`, and its `apply_patch` created a
  new folder and file at a 383-character path, then changed the file. Python read both agents'
  files back afterwards.

- A pitfall for anyone repeating these: Git Bash's `cygpath -w` gives a path over 260 characters
  in its `\\?\` form already, so a test that builds its path with it tests the long-path form, not
  a plain path.
- **Not tested:** Windows Explorer; Codex on a PC without PowerShell 7, where its commands may run
  in Windows PowerShell 5.1, which failed above.

## Where dev-home-toolkit's paths come from

From the code at `bc46971`:

| Path | Named by | How long it can get | Guarded? |
| --- | --- | --- | --- |
| `rules/` in dev-home, apart from the end user's files in `mine/` | dev-home-toolkit | 139 characters inside dev-home, by the caps in decision 0065 | Yes: setup allows dev-home's folder up to 89 characters (260, less 30 of room for git, less 139, less 2; `path_problem` in `internal/shared/rules.py`) |
| `rules/<level>/mine/...`, the end user's own rules files | The end user | Any `.md` name, subfolders included | Only by setup's depth check |
| `handoffs/<service>/<parts>/HANDOFF.md`, and the issue draft at `.drafts/<service>/<parts>/issue.md` | `facts.py`, from the project's address | GitHub: 167 inside dev-home (39-character owners and 100-character repositories, from decision 0065). Azure DevOps: 212 (organization names under 50 characters, projects and repositories up to 64 each, by [Azure DevOps' naming rules](https://learn.microsoft.com/azure/devops/organizations/settings/naming-restrictions)). GitLab: nested groups, which copies of GitLab's docs say go up to 20 levels (not checked on gitlab.com). Other hosts and none: the project folder's name | No: decision 0065's check isn't built |
| `knowledge/<subject>/<topic>.md` | The agent, by the knowledge skill's filing rules | The filing rules set no length | Only by setup's depth check |
| `skills/<name>/...`, the end user's own skills | The end user | Names up to 64 characters (setup's check of the Agent Skills standard); the files inside, any length. Agents also reach them through each Claude Code folder's `skills/` link, so the path an agent uses is that folder's path plus the skill's | Only by setup's depth check, for dev-home's copy |
| `internal/.generated/...` in dev-home-toolkit's own folder | dev-home-toolkit | Fixed names | No: setup checks only the characters in the folder's path, not its length |
| Backups beside a file | dev-home-toolkit | The file's name plus `.bak-YYYYMMDD-HHMMSS` | No |

Put together:

- A GitHub handoff of the longest names, in a dev-home folder of the longest length setup allows,
  is 257 characters: under 260, but not with git's 30 characters of room.
- An Azure DevOps handoff of the longest names, in a short dev-home folder such as
  `C:\Programming\dev-home`, is 236 characters, which fails once git's room is counted.
- On 2026-10-28 the longest path in the developer's own dev-home was 90 characters.

## What relies on a handoff's path

- `facts.py` prints `handoff`, `draft`, and `link`, which the handoff skill uses. The skill's
  step 3, for a handoff that doesn't exist, lists every `HANDOFF.md` under `handoffs/`, to find one
  kept under an old name.
- `docs/skills/handoff.md` ("Where handoffs are kept"), and `templates/dev-home/README.md` and
  `AGENTS.md`, describe the layout. `test_facts.py` and the layout lists test it.
- The `name` fact, such as `you/tool`, is also the repository `gh` files issues in. So any change
  to a long handoff's folder may change only the folder, never `name`.

## Checking paths at a sync

**Measured** (2026-10-29, on a fast PC, medians), for where a sync could check the paths in
dev-home:

- One `git diff --name-only -z` over the commits a sync pushes or brings in: 18 ms for one commit,
  21 ms for ten.
- The length of every file's path in a dev-home of 161 files: about 8 ms, growing with dev-home.
- The end user's skills, 10 files: 0.23 ms.

Without `-z`, git escapes names with non-ASCII letters, so lengths counted from its output would be
wrong.

## Options

Weighed on 2026-10-28. [0088: Path lengths](../decisions/0088-path-lengths.md) took option 1; for
option 2, B, with room for files beside a handoff; and for option 3, a length rule in the
knowledge skill's filing rules, with a `LONG` line from the sync for any path past the budget.

1. **Clone with long paths on** (fits any of the options below): setup's `gh repo clone` adds
   `-- -c core.longpaths=true`, tested above. Setup turns `core.longpaths` on in dev-home only after
   the clone, so today a PC whose git doesn't have it on can't check out dev-home once any path in
   it is too long, and Git for Windows has it off by default.
2. **Handoff paths:**
   - **A. Warn**, decision 0065's plan: before a handoff is created, `facts.py` prints a `PROBLEM`
     line when its path, with git's room, would pass 260, suggesting a shorter dev-home folder.
     Pros: the path stays the project's address; a little code. Cons: the end user has to act,
     and for Azure DevOps a short dev-home folder isn't always enough.
   - **B. Cap**: `facts.py` shortens a folder name that's too long, keeping its start and adding a
     short code made from the whole name, so two long names can't collide, the way decision 0065
     caps names in `rules/`. Pros: the end user does nothing, and every program can open the file,
     whatever it does with long paths. Cons: a very long project's folder shows a shortened name;
     changes decision 0065; the agent's own design, not a practice found elsewhere.
   - **C. Long-path-safe reads** in the scripts (`\\?\`): only the toolkit's own scripts gain;
     agents, editors, and Explorer don't.
3. **Paths the end user names** (knowledge notes, their own skills' files): today only setup's depth
   check guards them. Options: leave it (they'd need about 140 characters inside dev-home to fail);
   a length rule in the knowledge skill's filing rules (words read on every add); or a check in
   setup (a scan of dev-home on every sync, which AGENTS.md's Speed rule says to measure and ask
   about first).
