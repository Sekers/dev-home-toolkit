# 0070: Who owns each file in dev-home

**Built:** yes, except: keeping `README.md`, `.gitignore`, and `.gitattributes` current, with hand
edits to them, which waits for the version check below, since without it two PCs on different
versions would undo each other's copies; built-in rules' files and the `unanswered/` folders,
which come with those parts; withdrawn files; and a release that changes line endings. Until then,
a new dev-home starts with the other files in `templates/dev-home/`, filled in, and nothing
updates them.

**Decision:** each file dev-home-toolkit puts in a dev-home has one owner. Either dev-home-toolkit
owns it, and setup writes it and keeps it current, or the end user does, and setup creates it only
when it's missing and never changes it. Decided by the developer on 2026-10-18, and changed on
2026-10-23 (how setup tells a dev-home, where the files live in this repo, a missing file git
still has, and no place for an end user's guidance for dev-home sessions alone).

| File | Owner | What setup does |
| --- | --- | --- |
| `AGENTS.md`, `CLAUDE.md` | dev-home-toolkit | writes them on each PC with that PC's commands, always overwriting them; `.gitignore` lists both |
| `README.md` | dev-home-toolkit | keeps it current |
| `.gitignore`, `.gitattributes` | dev-home-toolkit | writes them whole and commits them with the sync, only from a PC on the newest version |
| `dev-home.json` | dev-home-toolkit | its code creates the file, and tells a dev-home by it |
| Built-in rules' files in `built-in/`, and the `unanswered/` folders | dev-home-toolkit | writes, moves, and removes them ([0067: Built-in rules](0067-built-in-rules.md), [0064: Each agent's rules file](0064-each-agents-rules-file.md)) |
| `my-rules.md` in each `mine/` setup keeps | the end user | creates it, empty, whenever it's missing and the last commit doesn't have it either |
| `knowledge/README.md` | the end user, through the knowledge skill | when it's missing, puts it back as the last commit has it, or creates it with only its title when the last commit has none |

- **How setup tells a dev-home** from another folder, such as a project's repo named by mistake,
  before it sets that repo's git config: by its `dev-home.json` alone (the developer,
  2026-10-23).
- **Where the files live in this repo:** `templates/dev-home/`, which holds only the files
  dev-home-toolkit owns; setup's code makes `dev-home.json` and the end user's files.
- **The end user's own patterns:** ignore patterns go in a `.gitignore` inside a subfolder, such as
  `knowledge/.gitignore`, which every copy shares, or in `.git/info/exclude` for one copy;
  attributes go in a subfolder's `.gitattributes`, or in `.git/info/attributes`. Git reads all of
  them. Dev-home's README says so.
- **No mixed files:** a rule for developers. dev-home-toolkit's text and an end user's content
  never share a file.
- **Examples ship as built-in rules or skills,** never as files dropped into a dev-home, so they
  get the existing offers and answers.
- **A hand edit to a file dev-home-toolkit owns,** any of those above, `AGENTS.md`, `CLAUDE.md`,
  and built-in rules' files included, goes to the Recycle Bin
  ([0069: Dropped text](0069-dropped-text.md)), then setup puts
  the file back, with one line saying so and where the end user's own content goes. For dev-home's
  `AGENTS.md` and `CLAUDE.md`, that line says setup rewrites the file on every run, and that the
  end user's guidance for every session goes in their rules, in `rules/`; nothing holds guidance
  for dev-home sessions alone (the developer, 2026-10-23). When the bin can't take it on a quiet
  sync, which can't ask, setup leaves the file as edited and names it in a `PROBLEM` line on each
  sync until a run that can ask, which asks as 0069 says. Setup tells a hand edit to dev-home's
  `AGENTS.md` and `CLAUDE.md` by a copy of what it last wrote there, as for the agents' rules
  files ([0064](0064-each-agents-rules-file.md)). With no copy, such as after the copy is lost,
  any text but what setup writes now counts as one, so text that may be setup's own older
  version goes to the bin too, and nothing is lost.
- **A file dev-home-toolkit stops writing,** such as `CLAUDE.md` if Claude Code someday needs no
  pointer, is listed in that release's `withdrawn` list, with `kind: "file"` and its reason
  ([0060: The release data file](0060-the-release-data-file.md)),
  and setup removes it.
- **A release that changes `.gitattributes`'s line-ending rules** handles rewriting the files once,
  since they'd look changed until git rewrites them.
- **Only the newest version writes** a committed file dev-home-toolkit owns, going by the version
  recorded in `dev-home.json`
  ([0068: Versions and layouts in dev-home](0068-versions-and-layouts-in-dev-home.md)),
  so a PC that's behind never writes an older copy back.
- **A change to the layout of the end user's own files,** such as the knowledge index or `rules/`,
  goes through layout versions and conversion steps, not through these files.

So the planned offer of starter updates is dropped. Starter files were copied once, so a later
change never reached an existing dev-home, and the plan was to record the last starter commit an
end user answered, and offer each later change to merge into their copies. With every file now
either kept current or the end user's own, there's nothing left to offer. It also means the
starter's macOS and Linux section in `.gitignore` reaches existing dev-homes by itself.

**Why:**

- Each PC writes its own commands into `AGENTS.md` and `CLAUDE.md`, since paths differ per PC. If
  they were committed, every PC's sync would commit its own version, and the PCs would keep undoing
  each other. Listing them in `.gitignore` is visible where git users look, covers a copy from the
  moment it's cloned, and is the standard way.
- `.gitignore` and `.gitattributes` hold what dev-home-toolkit's own machinery relies on: the
  sync's merges, LF line endings, and `merge=union` for the knowledge index. So they change with
  the code that relies on them, and leftovers, such as a `*.ps1` line from when the scripts were
  PowerShell, can be tidied for everyone.
- One place defines `dev-home.json`, the code that already reads, asks about, and writes it. Each
  new field is added only there, never also in a starter copy that has to match.
- One clear owner per file, now and as files are added, with no record of starter commits and no
  three-way merges to build. It reuses what's already decided: the Recycle Bin, the `withdrawn`
  list, and layout versions.
- `dev-home.json`: only dev-home-toolkit writes it, every dev-home has it from its start, and a
  project's repo won't. An end user's file, such as the knowledge index, would stop every sync
  when it's missing, before the run that puts it back. Setup can't rebuild a missing
  `dev-home.json` itself, since it holds an answer, so its `PROBLEM` line says to restore it from
  git.
- `templates/dev-home/`: nothing there is copied once any more, so "starter" would mislead.
- A missing file git still has is the end user's delete or rename, not committed yet. A commit of
  the recreated file then would carry the loss to every copy: an empty `my-rules.md` while the
  renamed file isn't committed, or a title-only index in place of all its rows. Renaming
  `my-rules.md` to move its rules is normal, so setup waits for that commit; nothing renames the
  index, so a missing one is a mistake, and setup puts back its rows. Checking costs one git
  call, only on a run that finds a file missing (the developer, 2026-10-23).
- No place for an end user's guidance for dev-home sessions alone: dev-home's `AGENTS.md` and
  `CLAUDE.md` hold what agents need to work with dev-home-toolkit's machinery there, and an end
  user's own preferences have their place in `rules/`. A file of their own for dev-home sessions
  would add to dev-home's layout and to setup, for a need nobody has shown (the developer,
  2026-10-23).

**Costs:** an end user can't keep their own wording in a file dev-home-toolkit owns, such as a
personal note in dev-home's `README.md`; dev-home is private, so that README is mostly for the end
user and their agents anyway. Guidance an end user wants only in dev-home sessions has no place of
its own: in `rules/`, it loads in every session. A copied skill still needs its own record of
where it came from.

**Options set aside:**

- `.git/info/exclude` for `AGENTS.md` and `CLAUDE.md`, kept by setup on every run: invisible, and
  the developer wants `.gitignore` owned.
- The end user owning `.gitattributes`: a change the sync or the knowledge index depends on might
  never reach them.
- The starter seeding `dev-home.json`: two places define its first contents.
- Keeping the planned starter updates: it still needs each file's owner decided, doesn't cover a
  mixed file, an example, or a withdrawn file any better, and is the most to build.
- Telling a dev-home by any one of several files, such as `dev-home.json`, the knowledge index,
  or `rules/` (a docs project with a knowledge index would pass); checking only when a folder is
  chosen (a hand-edited setting that points elsewhere would go unnoticed, and it needs a record of
  which folder was checked).
- Keeping the folder's name, `templates/dev-home-starter/`; `templates/dev-home-files/` (longer,
  and says no more).
- For a missing file git still has: waiting on the index too (lookups find no index until it's
  restored by hand); committing the recreated file at once (it spreads the loss).
- For an end user's guidance for dev-home sessions alone: a file of theirs that setup joins onto
  the end of dev-home's `AGENTS.md` (a new file in dev-home's layout, and more code, for a need
  nobody has shown); a `.claude/rules/` folder committed in dev-home, which Claude Code loads only
  there (Codex ignores it).

**Look again if:** a file needs content from both dev-home-toolkit and the end user.
