# 0088: Path lengths

**Built:** yes.

**Decision:** every path in dev-home stays within the path budget: 139 characters inside
dev-home's folder, the longest path in `rules/` that its caps on names allow
([0065: Where end users' rules live](0065-where-end-users-rules-live.md)). With dev-home's folder
at most 89 characters, that keeps every path under Windows' limit of 260 characters, with 30 to
spare for git, the same on every PC. dev-home-toolkit shortens the paths it names itself, and
reports any other path past the budget from the first point its code sees it, never blocking.
Decided by
the developer on 2026-10-17 and 2026-10-18, as part of 0065 (the budget and setup's check), and
changed on 2026-10-29 (git's long-path option from a clone's start, handoffs, knowledge notes, and
the `LONG` line), 2026-10-30 (the room beside a handoff), 2026-10-31 (a decision of its own,
a second read after a push GitHub rejects, and `LONG` out of `/dev-home sync`'s summary), and
2026-11-02 (cutting only a handoff's last folder, dropping what's left at the cut's end, the
length in the line for a path in `rules/` too long for Windows, and CRC-32 in place of SHA-256),
and 2026-11-07 (the room beside a handoff used by further files).

- **dev-home's folder.** Each run, setup checks that dev-home's folder path, plus the path budget,
  plus 30 characters, fits under 260 characters, so a folder of at most 89, and otherwise prints
  a `PROBLEM` line suggesting a shorter place for dev-home. A path's length counts as Windows
  counts it, in UTF-16 units, so a character such as an emoji counts 2. Setup skips the check in
  a test profile, whose dev-home sits deep in the repo's folder, so the tests check it directly.
- **git's long-path option.** Setup turns on `core.longpaths` in dev-home's git config with its
  other git settings there. A dev-home that setup clones has it on from the start: its
  `gh repo clone` passes `-c core.longpaths=true` on to git.
- **Knowledge notes.** The knowledge skill's filing rules cap each name at 60 characters, `.md`
  included, so a note, `knowledge/<subject>/<topic>.md`, is at most 131 characters.
- **Handoffs.** When `handoffs/<service>/<parts>/`, plus 60 characters of room, would pass the
  path budget, `facts.py` (`find_handoff_place`) keeps the folders above the last part whole, and
  cuts the last from its end so the folder, plus the room, fits, drops any hyphens, spaces, and
  dots left at the end of the cut, then adds a hyphen and the CRC-32 of the `name` fact, as 8
  hexadecimal characters, or those alone when nothing is left, so no folder starts with a hyphen
  ([0089: Where a handoff lives](0089-where-a-handoff-lives.md) says why CRC-32). A handoff's
  folder under `handoffs/pcs/<pc>/` already ends with its path's hash, so only the folder's name
  before it is cut. When the folders above leave the last no room for even its first character,
  it joins the one just above it, with a hyphen, and so on up, only as far as it must; no folder
  has a cap of its own. On GitHub that never happens: a 39-character owner, the longest GitHub allows,
  still leaves 13 characters for the repository, so an owner's folder always stays. `name` stays
  whole, for commit messages and `gh`'s repository, and the issue draft's path under `.drafts/`
  uses the same folders. That shortens only past 61 characters of GitHub owner and repository
  together, or 54 of Azure DevOps organization, project, and repository, and joins on Azure
  DevOps only past 44 of organization and project together. The room is for a handoff's further
  files ([0091: Further files](0091-further-files.md)), which sit flat in its folder, each name at
  most 60 characters with `.md`. `facts.py` imports only Python's standard library, as a
  skill's script, so it can't import `internal/shared/`: it has its own copies of the path budget
  and of the length count, and a test checks that they match `paths.py`'s.
- **`rules/`.** The end user's files in `mine/` get the `LONG` line below, like any other path,
  but setup itself checks no rules file's length. A file in `rules/` that setup can't read gets a
  `PROBLEM` line, and so does a folder there that setup can't list, though a missing `mine/` or
  `unanswered/` needs none. With Windows' long-path setting off, Windows says a path that long
  isn't there, so for a file of 260 characters or more, or a folder of 256 or more (Python adds 4
  to a folder's path to list it), the line gives the path's length and says to shorten it.
- **Every other path: the `LONG` line.** A path past the path budget, such as a file the end user
  names, gets a `LONG` line naming the file, its length, and the budget, saying what may fail (a
  PC whose dev-home is in a deeper folder, or whose Windows long-path setting is off) and how to
  fix it (shorten its name or a folder above it). Nothing is refused, and the line leaves the
  sync's exit code at 0. A file gets the line at most once per run, and only while it's on this
  PC, so a file deleted or renamed away gets none. Windows ignores letter case, so a file is there
  whatever the case of its name on this PC, and two names that differ only in case, as after a
  rename that changed only that, are one file, named in the line as it's spelled on this PC. The
  sync checks:
  - its list of uncommitted files, from the `git status` call it already makes, beside its `LEFT`
    or `STALE` line, on every sync while the file stays uncommitted;
  - in `sync.py --message`, the staged files' names, from the `git diff --cached` call it already
    makes (`--name-only -z --no-renames` in place of `--quiet`, reading "nothing staged" from
    empty output), and the commit goes through;
  - the commits a plain sync pushes, and the commits any sync brings in, with one
    `git diff --name-only -z --no-renames` between this PC's last commit and GitHub's, made before
    any merge, so one call covers the commits both ways; only on those syncs. A push GitHub
    rejects gets a second round, which reads it again for the commits that came in meanwhile (the
    developer, 2026-10-31). A sync that commits
    reads it only when commits come in, and then it covers that sync's other commits going out
    too, such as one made by hand. The files get the line only once commits came in or went out,
    so a merge that's undone, or a push that fails, gives none; commits that came in while the
    push failed give the files of those waiting here the line too, since the one diff can't tell
    the two apart. A file brought in that's too long for this PC fails git's checkout first, and
    git's own error shows: no check can come before it.

  The skills tell each `LONG` line once per session, in the bullet they share, which becomes
  "`UPDATE`, `NEW`, `LARGE`, and `LONG`" ([0036: New items](0036-new-items.md)).
  `/dev-home sync`'s summary, which names what each `UPDATE`, `NEW`, or `LARGE` line says is
  still waiting, leaves `LONG` out (the developer, 2026-10-31).

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
- Only the last folder cut: a shortened handoff stays in the folders above it, as other handoffs
  of the same owner, group, or project do, and the developer wants GitHub organizations and users
  to keep their folders (2026-11-02). Keeping a folder whole hides no more of the name than
  joining it would, since a slash and a hyphen each take one character, so folders join only
  when there's no room otherwise.
- Hyphens, spaces, and dots dropped at the cut's end: repository names are often hyphenated, so
  without it a double hyphen before the hash would be common, and dropping them only makes the
  folder shorter (the developer, 2026-11-02).
- The room: 60 characters, the cap on a file setup moves into `rules/` and on a knowledge note's
  name, fits a further file named for a script and its plan, such as
  `report-builder-monthly-plan.md`. Room from the start: files beside a handoff added after
  1.0.0 would have needed every handoff folder between the two cutoffs cut again, a conversion.
- `LONG` is its own word, not `PROBLEM`, since a long path isn't a failure. A `PROBLEM` would fail
  setup's own commits whenever a file too long sits anywhere in dev-home, since they go through
  the sync (`commit_for_setup`), which lists uncommitted files on every run, and the skills stop on
  a commit's `PROBLEM`.
- Checking what changes, where git already reports it: two of the checks read git calls the sync
  already makes, and the third adds one git call, 18 ms for one commit and 21 ms for ten (medians
  on a fast PC, 2026-10-29), only on syncs that push or bring in commits, a cost the developer
  approved. Without `-z`, git escapes names with non-ASCII letters, so the lengths would be wrong;
  with renames found, a diff names only one side of a rename, so a file renamed on the other side
  would go unchecked. The second round's read costs the same again, only when two PCs push
  within moments of each other; without it, the files in the commits that came in on that round
  would never get the line on this PC.
- `LONG` out of `/dev-home sync`'s summary: a committed long file gets the line only on the sync
  that commits, pushes, or brings it in, and is quiet after that, so it's rarely still waiting;
  only an uncommitted one repeats, and the shared bullet already passes each line on once a
  session. Naming it would add about 4 words to the dev-home skill, read on every `/dev-home sync`.
- No length check of rules files in setup: it would come on every sync for a file kept on
  purpose, and a PC that can't read one already says so.
- The length in the line for a path in `rules/` too long for Windows: Windows' own answer, that
  the path isn't there, sends the end user looking for a file or folder that is. The line gives
  the length only for a path that reaches Windows' limit, so one shorter that really is gone
  keeps Windows' words.

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
  - Joining every folder after the service's into one, as first written here: a shortened handoff
    leaves its owner's folder for a place among the owners' folders, and shows no more of the
    name.
  - A cap per folder level, or on the organization's folder alone: a handoff's depth varies by
    service, and it would cut names that fit. GitHub owners never need one; a cap on an Azure
    DevOps organization alone leaves no room under a long project, and one on the project cuts
    names whose paths fit; and a cut folder above the last needs a hash of its own, 9 more
    characters.
  - Cutting each folder evenly: harder to predict.
  - Keeping a hyphen, space, or dot left at the cut's end: it gives folders such as
    `name--<hash>`.
- For the room: 40 characters for a file name (a script's name with a plan's often passes it); no
  room (files beside a handoff after 1.0.0 would need a conversion).
- For other paths:
  - Refusing the commit: the file then reaches no other PC and has no backup, and a `STALE` file
    would be offered again on every sync.
  - Checking every file on every run: about 8 ms for 161 files, and growing.
  - Checking the end user's skills on every run: 0.23 ms for 10 files, growing in the very case
    it's for, such as a skill that bundles a library.

**Look again if:** Windows turns on long paths by default, or further files need longer names.
