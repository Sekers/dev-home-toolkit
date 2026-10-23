# 0070: Who owns each file in dev-home

**Built:** yes, except: everything but `my-rules.md`, which setup creates, empty, wherever one is
missing ([0065: Where end users' rules live](0065-where-end-users-rules-live.md)).

**Decision:** each file dev-home-toolkit puts in a dev-home has one owner. Either dev-home-toolkit
owns it, and setup writes it and keeps it current, or the end user does, and setup creates it only
when it's missing and never changes it. Decided by the developer on 2026-10-18.

| File | Owner | What setup does |
| --- | --- | --- |
| `AGENTS.md`, `CLAUDE.md` | dev-home-toolkit | writes them on each PC with that PC's commands, always overwriting them; `.gitignore` lists both |
| `README.md` | dev-home-toolkit | keeps it current |
| `.gitignore`, `.gitattributes` | dev-home-toolkit | writes them whole and commits them with the sync, only from a PC on the newest version |
| `dev-home.json` | dev-home-toolkit | its code creates the file, and the starter drops its copy |
| Built-in rules' files in `built-in/`, and the `unanswered/` folders | dev-home-toolkit | writes, moves, and removes them ([0067: Built-in rules](0067-built-in-rules.md), [0064: Each agent's rules file](0064-each-agents-rules-file.md)) |
| `my-rules.md` in each `mine/` setup keeps | the end user | creates it, empty, whenever it's missing |
| `knowledge/README.md` | the end user, through the knowledge skill | creates it, with only its title, whenever it's missing |

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
  the file back, with one line saying so and where the end user's own content goes. When the bin
  can't take it on a quiet sync, which can't ask, setup leaves the file as edited and names it in a
  `PROBLEM` line on each sync until a run that can ask.
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

**Costs:** an end user can't keep their own wording in a file dev-home-toolkit owns, such as a
personal note in dev-home's `README.md`; dev-home is private, so that README is mostly for the end
user and their agents anyway. A copied skill still needs its own record of where it came from.

**Options set aside:**

- `.git/info/exclude` for `AGENTS.md` and `CLAUDE.md`, kept by setup on every run: invisible, and
  the developer wants `.gitignore` owned.
- The end user owning `.gitattributes`: a change the sync or the knowledge index depends on might
  never reach them.
- The starter seeding `dev-home.json`: two places define its first contents.
- Keeping the planned starter updates: it still needs each file's owner decided, doesn't cover a
  mixed file, an example, or a withdrawn file any better, and is the most to build.

**Look again if:** a file needs content from both dev-home-toolkit and the end user, or end users
ask to keep their own wording in a file dev-home-toolkit owns.
