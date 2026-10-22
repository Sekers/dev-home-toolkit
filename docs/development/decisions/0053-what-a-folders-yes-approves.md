# 0053: What a folder's yes approves

**Built:** yes.

**Decision:** the yes to setting up a Claude Code folder, or Codex in every Codex home, also
approves the one change setup makes in that folder's settings file: dev-home and dev-home-toolkit
in `permissions.additionalDirectories` in Claude Code's `settings.json`, and dev-home in
`writable_roots`, with `project_doc_max_bytes`, in Codex's `config.toml`. The question says so
first, including the access it grants. Every run, quiet ones included, makes the change when it's
missing, with a dated backup and a `SET` line naming the file, so an entry that goes missing comes
back, as a deleted skill link does. Setup keeps no record of what it added. A no to the folder
approves taking the change back out, the same way
([0054: Removing what setup set up](0054-removing-what-setup-set-up.md)). A file setup can't
safely edit, such as one with comments, still gets a `PROBLEM` line, and a run by hand prints
what to add. Optional settings, such as recommended ones, keep a question of their own. Since
syncs write these files too, setup makes the changes while it holds the sync's lock.

In a Claude Code folder other than `~/.claude`, the yes also approves two patterns in
`claudeMdExcludes`, which keep `~/.claude`'s instructions out of that folder's sessions
([0074: Instructions in other Claude Code folders](0074-instructions-in-other-claude-code-folders.md)),
and the no approves taking them out. They grant no access, so the question's note about access
doesn't cover them; the question for the folder says what they do and why. Changed on 2026-10-16
and 2026-10-19.

**Why:** every way a folder got answered, except a yes at a terminal, left it half set up, with a
`PROBLEM` line on every sync. That covered a yes in chat through `/dev-home configure`, a new
Codex home that got the main home's answer, a home only a session's `CODEX_HOME` names, and a
moved dev-home. For a home only a session names, the line's advice to run setup in a terminal
couldn't work, since a terminal can't see that home. A folder set up without the change works
badly: Claude Code can't use dev-home's files from another project without asking, and Codex's
sandbox blocks writes there. Checked 2026-10-15 in Claude Code's docs: it shows no prompt when
user settings change on disk, and reloads them live; its sandbox doesn't run on native Windows.

**Options set aside:**

- Keeping a separate diff and a typed yes for each file: the cases above stay half set up.
- Setting up only the homes setup can name itself (the code review's fix), ignoring
  `CODEX_HOME`, or skipping homes inside a repo: each leaves some real home without dev-home, or
  set up only partway.
- A clearer `PROBLEM` line alone: the folder stays half set up.

**Look again if:** an agent needs a settings change whose access a person would want to weigh
apart from setting up the folder.
