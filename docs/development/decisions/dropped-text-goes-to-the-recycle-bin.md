# Dropped text goes to the Recycle Bin

**Decision:** text an end user tells setup to drop goes to the Recycle Bin, as a file, before
setup removes or overwrites anything. Not built yet. Decided by the developer on 2026-10-18.

- **Where text gets dropped:** wherever setup asks where an agent's rules go, "drop them" is an
  answer
  ([Each agent gets its rules as one file setup writes in its own folder](each-agent-gets-its-rules-as-one-file-setup-writes-in-its-own-folder.md)).
  At a console, dropped text never enters dev-home. Through `/dev-home configure`, dropping an
  `unanswered/` file deletes a file whose text is also in dev-home's git history.
- **On Windows,** setup sends a file holding the text to the Recycle Bin through `IFileOperation`,
  called with `ctypes`, which setup already uses, so nothing new gets installed. macOS's Trash and
  Linux's trash folder come with those systems. A file in `unanswered/` that's dropped goes to the
  bin itself.
- **Setup overwrites the agent's file only once the text is safe.** How it confirms that the bin
  took it is settled and tested when building, since Windows can delete a file for good on a drive
  with no Recycle Bin, such as some network drives.
- **When the bin can't take it,** setup says so and asks: keep it as one of the end user's rules,
  in the `mine/` they pick, or delete it for good. Through `/dev-home configure`, the agent asks
  the same in chat. No backup file is left anywhere.
- **The same rule covers a hand edit** to any file dev-home-toolkit owns in dev-home, the per-PC
  `AGENTS.md` and `CLAUDE.md` and built-in rules' files included: the edited text goes to the bin
  before setup puts the file back
  ([Every file in dev-home belongs to dev-home-toolkit or to the end user](every-file-in-dev-home-belongs-to-dev-home-toolkit-or-to-the-end-user.md)).
  A quiet sync puts files back too, and can't ask. So when the bin can't take a hand edit on a
  quiet sync, setup leaves the file as edited, and prints a `PROBLEM` line naming it on each sync,
  until a run that can ask.

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
- `SHFileOperation`, documented as replaced.

**Look again if:** end users report text lost on a drive with no Recycle Bin, or Python gains a
standard way to reach the system's trash.
