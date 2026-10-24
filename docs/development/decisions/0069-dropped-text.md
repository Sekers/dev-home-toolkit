# 0069: Dropped text

**Built:** yes.

**Decision:** text an end user tells setup to drop goes to the Recycle Bin, as a file, before
setup removes or overwrites anything. Decided by the developer on 2026-10-18, and changed on
2026-10-23 (what a run that can ask does with a hand edit the bin can't take).

- **Where text gets dropped:** wherever setup asks where an agent's rules go, "drop them" is an
  answer
  ([0064: Each agent's rules file](0064-each-agents-rules-file.md)).
  At a console, dropped text never enters dev-home. Through `/dev-home configure`, dropping an
  `unanswered/` file deletes a file whose text is also in dev-home's git history.
- **On Windows,** setup sends a file holding the text to the Recycle Bin through `IFileOperation`,
  called with `ctypes`, which setup already uses, so nothing new gets installed
  (`internal/shared/recycle_bin.py`). macOS's Trash and Linux's trash folder come with those
  systems. A file in `unanswered/` that's dropped goes to the bin itself.
- **Setup overwrites the agent's file only once the text is safe.** It writes the text to a file
  of its own, named for what it holds, in a new folder of the system's temporary folder, and sends
  that file to the bin with a progress sink listening to `IFileOperation`. The sink's
  `PostDeleteItem` is given the item the file became in the bin, or none when Windows deleted it
  for good, which it does without a word on a drive with no Recycle Bin, such as some network
  drives, or with a bin set to remove files at once, or too small for the file. That file was
  setup's own copy, so a delete for good loses nothing. Tested on Windows 11 on 2026-10-22: a
  file reached the real bin, and a delete without the bin's flags, which deletes for good, was
  reported as not in the bin.
- **When the bin can't take it,** setup says so and asks: keep it as one of the end user's rules,
  in the `mine/` they pick, or delete it for good. Through `/dev-home configure`, the agent asks
  the same in chat, as [0026: setup.py --configure](0026-setup-py-configure.md) says. No backup
  file is left anywhere.
- **The same rule covers a hand edit** to any file dev-home-toolkit owns in dev-home, the per-PC
  `AGENTS.md` and `CLAUDE.md` and built-in rules' files included: the edited text goes to the bin
  before setup puts the file back
  ([0070: Who owns each file in dev-home](0070-who-owns-each-file-in-dev-home.md)).
  A quiet sync puts files back too, and can't ask. So when the bin can't take a hand edit on a
  quiet sync, setup leaves the file as edited, and prints a `PROBLEM` line naming it on each sync,
  until a run that can ask. When the bin can't take a hand edit on a run that can ask, at a
  console or through `/dev-home configure`, setup shows the edited lines, then asks whether to
  delete them for good or leave the file as edited. At a console, setup tries the bin, and asks
  when it can't take the edit, before the work, with its other questions
  ([0034: Runs of setup by hand](0034-runs-of-setup-by-hand.md)); the work acts on that only
  while the file is still as it was then. Leaving it takes the quiet sync's path: the
  `PROBLEM` line stays, and a later run whose bin takes the edit puts the file back. This question
  covers dev-home's `AGENTS.md` and `CLAUDE.md`, the only hand edits setup puts back so far; each
  other file dev-home-toolkit owns gets its choice when setup starts keeping it current.

**Why:**

- A wrong answer at a prompt shouldn't lose rules, and the Recycle Bin is where people look for
  something deleted (the developer, 2026-10-18: the bin when possible). Windows empties it by
  itself, so nothing piles up.
- An agent's rules are dropped only where setup can ask: at a console, or through
  `/dev-home configure`. A quiet sync never drops them; it sets them aside in `unanswered/`. So
  when the bin fails, which should be rare since the agents' folders are on the local drive, setup
  can ask instead of leaving a copy somewhere. The one case a quiet sync meets, a hand edit to put
  back, waits for a run that can ask, so nothing is lost there either (the developer, 2026-10-18).
  A plain sync never commits a changed file, so the edit can't spread meanwhile.
- A hand edit to dev-home's `AGENTS.md` or `CLAUDE.md` is guidance for sessions in dev-home, and
  every level of `rules/` loads in every session, so keeping it as one of the end user's rules
  would load it everywhere. Leaving the file loses nothing without an answer, and the lines shown
  can be copied anywhere first (the developer, 2026-10-23).
- `IFileOperation`: Microsoft's page for `SHFileOperation` says it "has been replaced in Windows
  Vista by IFileOperation" (read 2026-10-18). The page doesn't say "deprecated", but AGENTS.md's
  rule against building on deprecated features points to the replacement.

**Costs:** the most code of the options: the bin through `ctypes` on Windows, and later macOS's
and Linux's, with tests that fake the bin, since they can't touch the real one; and one more
question in the rare case the bin fails.

**Options set aside:**

- A dated copy as the fallback, beside the agent's file, such as
  `AGENTS.md.bak-YYYYMMDD-HHMMSS`: clutter in a folder end users rarely open, churn for anyone who
  keeps `~/.claude` or `~/.codex` in a dotfiles repo, and a name ending in `.md` would load in
  Claude Code, which loads every `.md` under `rules\`.
- A dated copy in dev-home-toolkit's own folder: out of sight, a place there that needs the
  developer's approval, and removing dev-home-toolkit would delete it.
- Always a dated copy, with no Recycle Bin: the least code, but copies pile up out of sight.
- No way back: dropped means gone.
- On a quiet sync whose bin fails, putting a hand-edited file back anyway: the edit would be lost.
- For a hand edit to dev-home's `AGENTS.md` or `CLAUDE.md` that the bin can't take: keeping it as
  one of the end user's rules, in the `mine/` they pick (it would load in every session, in every
  project); or offering that beside leaving the file and deleting the edit (one more choice, which
  puts the text where it doesn't belong, for a rare case).
- `SHFileOperation`, documented as replaced.
- To confirm the bin took the file, comparing its count of items before and after
  (`SHQueryRecycleBin`): another program's delete at the same moment would look like this one.

**Look again if:** end users report text lost on a drive with no Recycle Bin, or Python gains a
standard way to reach the system's trash.
