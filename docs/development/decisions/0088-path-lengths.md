# 0088: Path lengths

**Built:** yes, except: the `LONG` line; shortening a handoff's folder; a line for a folder in
`rules/` that setup can't list; and counting a path's length in UTF-16 units, where setup's check
of dev-home's folder counts Python's characters. Setup skips that check in a test profile, whose
dev-home sits deep in the repo's folder, so the tests check it directly.

**Decision:** every path in dev-home stays within the path budget: 139 characters inside
dev-home's folder, the longest path in `rules/` that its caps on names allow
([0065: Where end users' rules live](0065-where-end-users-rules-live.md)). With dev-home's folder
at most 89 characters, that keeps every path under Windows' limit of 260 characters, with 30 to
spare for git, the same on every PC. dev-home-toolkit shortens the paths it names itself, and
reports any other path past the budget from the first point its code sees it, never blocking.
Decided by
the developer on 2026-10-17 and 2026-10-18, as part of 0065 (the budget and setup's check), and
changed on 2026-10-29 (git's long-path option from a clone's start, handoffs, knowledge notes, and
the `LONG` line), 2026-10-30 (the room beside a handoff), and 2026-10-31 (a decision of its own).

- **dev-home's folder.** Each run, setup checks that dev-home's folder path, plus the path budget,
  plus 30 characters, fits under 260 characters, so a folder of at most 89, and otherwise prints
  a `PROBLEM` line suggesting a shorter place for dev-home. A path's length counts as Windows
  counts it, in UTF-16 units, so a character such as an emoji counts 2.
- **git's long-path option.** Setup turns on `core.longpaths` in dev-home's git config with its
  other git settings there. A dev-home that setup clones has it on from the start: its
  `gh repo clone` passes `-c core.longpaths=true` on to git.
- **Knowledge notes.** The knowledge skill's filing rules cap each name at 60 characters, `.md`
  included, so a note, `knowledge/<subject>/<topic>.md`, is at most 131 characters.
- **Handoffs.** When `handoffs/<service>/<parts>/`, plus 60 characters of room, would pass the
  path budget, `facts.py` (`find_handoff_place`) makes the folders after the service folder one:
  the parts joined with hyphens, then a hyphen and the first 8 hexadecimal characters of the
  SHA-256 of the `name` fact, with the joined parts cut from the end so the folder, plus the room,
  fits. `name` stays whole, for commit messages and `gh`'s repository, and the issue draft's path
  under `.drafts/` uses the same folder. That shortens only past 61 characters of GitHub owner and
  repository together, or 54 of Azure DevOps organization, project, and repository. The room is
  for files beside a handoff, planned but not designed: any path inside a handoff's folder,
  subfolders and `.md` included, at most 60 characters. Their design confirms or changes that
  number before 1.0.0, while a change needs no conversion. `facts.py` imports only Python's
  standard library, as a skill's script, so it can't import `rules.py`: it has its own copies of
  the path budget and of the length count, and a test checks that they match `rules.py`.
- **`rules/`.** The end user's files in `mine/` get the `LONG` line below, like any other path,
  but setup itself checks no rules file's length. A file in `rules/` that setup can't read gets a
  line, and so does a folder there that setup can't list.
- **Every other path: the `LONG` line.** A path past the path budget, such as a file the end user
  names, gets a `LONG` line naming the file, its length, and the budget, saying what may fail (a
  PC whose dev-home is in a deeper folder, or whose Windows long-path setting is off) and how to
  fix it (shorten its name or a folder above it). Nothing is refused, and the line leaves the
  sync's exit code at 0. The sync checks:
  - its list of uncommitted files, from the `git status` call it already makes, beside its `LEFT`
    or `STALE` line, on every sync while the file stays uncommitted;
  - in `sync.py --message`, the staged files' names, from the `git diff --cached` call it already
    makes (`--name-only -z` in place of `--quiet`, reading "nothing staged" from empty output),
    and the commit goes through;
  - the commits a plain sync pushes, and the commits any sync brings in, with one
    `git diff --name-only -z`, only on those syncs. A file brought in that's too long for this PC
    fails git's checkout first, and git's own error shows: no check can come before it.

  The skills tell each `LONG` line once per session, in the bullet they share, which becomes
  "`UPDATE`, `NEW`, `LARGE`, and `LONG`" ([0036: New items](0036-new-items.md)).

**Why:**

- Windows refuses a path over 260 characters by default, counting dev-home's own folder; Git for
  Windows won't check out a longer one without `core.longpaths`; and macOS and Linux cap each name
  at 255. Windows' long-path setting needs an administrator, so setup leaves it alone. With it off,
  the toolkit's own scripts, Windows PowerShell 5.1, and `cmd.exe` can't read a longer path through
  its plain form, though both agents can
  ([Long paths on Windows](../research/long-paths-on-windows.md)).
- One budget, the same on every PC: dev-home syncs between PCs, so a path made on one has to fit
  on every other, whatever its folder. Setup's check of dev-home's folder protects only the paths
  that stay within the budget.
- Turning `core.longpaths` on after a clone comes too late for its checkout: tested on 2026-10-28,
  a clone whose checkout passed the limit failed without it, even with Windows' long-path setting
  on, and `gh` passes the option on to git.
- Knowledge notes: 60 is also the cap on a file setup moves into `rules/`, and two names of 60 fit
  the budget. A line in the filing rules has the agent pick a name that fits from the start, for
  13 more words in the filing rules, which an agent reads once a session before adding a note,
  and `LONG` catches the rest.
- Handoffs: a project's address can pass the budget. GitHub allows 39-character owners and
  100-character repository names, so a handoff's path could reach 167 characters inside dev-home,
  and on Azure DevOps 212. Shortening asks nothing of the end user, and every program can then
  open the file. The start keeps the folder recognizable, and the hash keeps apart two long names
  that start the same. It's rare: the developer's longest owner and repository together had 38
  characters on 2026-10-30.
- The room: 60 characters, the cap on a file setup moves into `rules/` and on a knowledge note's
  name, fits a folder per script with its plans, such as `report-builder/monthly-plan.md`. One
  limit on the whole path inside a handoff's folder, not one per name as `rules/` and knowledge
  notes have, because those files' layout isn't designed yet, and two levels of 60 would leave 18
  characters for `handoffs/github/<owner>/<repo>/`. Room now, not later: files beside a handoff
  after 1.0.0 would need every handoff folder between the two cutoffs cut again, a conversion.
- `LONG` is its own word, not `PROBLEM`, since a long path isn't a failure. A `PROBLEM` would fail
  setup's own commits whenever a file too long sits anywhere in dev-home, since they go through
  the sync (`commit_for_setup`), which lists uncommitted files on every run, and the skills stop on
  a commit's `PROBLEM`.
- Checking what changes, where git already reports it: two of the checks read git calls the sync
  already makes, and the third adds one git call, 18 ms for one commit and 21 ms for ten (medians
  on a fast PC, 2026-10-29), only on syncs that push or bring in commits, a cost the developer
  approved. Without `-z`, git escapes names with non-ASCII letters, so the lengths would be wrong.
- No length check of rules files in setup: it would come on every sync for a file kept on
  purpose, and a PC that can't read one already says so.

**Options set aside:**

- Relying on Windows' long-path setting: it needs an administrator, and Explorer and `cmd.exe`
  stay affected.
- For handoffs:
  - A warning before a handoff is created, suggesting a shorter dev-home folder, as 0065 planned:
    it checks only the PC that creates the handoff, while the handoff syncs to PCs whose dev-home
    may be deeper, and the end user would have to move dev-home.
  - Long-path-safe reads in the scripts (`\\?\`): only the scripts gain; agents, editors, and
    Explorer don't.
  - Numbering, as `rules/` does for moved files: two PCs that haven't synced take the same name.
  - Keeping the start and the end: it hides a difference in the middle, such as an Azure DevOps
    project per region, cuts words at both ends, and is a second way of cutting.
  - A cap per folder level: a handoff's depth varies by service, and it would cut names that fit.
  - Cutting each folder evenly: harder to predict.
- For the room: 40 characters for a file name (a script's name with a plan's often passes it); no
  room (files beside a handoff after 1.0.0 would need a conversion).
- For other paths:
  - Refusing the commit: the file then reaches no other PC and has no backup, and a `STALE` file
    would be offered again on every sync.
  - Checking every file on every run: about 8 ms for 161 files, and growing.
  - Checking the end user's skills on every run: 0.23 ms for 10 files, growing in the very case
    it's for, such as a skill that bundles a library.

**Look again if:** Windows turns on long paths by default, or the design of files beside a handoff
needs more than 60 characters.
