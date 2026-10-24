# 0065: Where end users' rules live

**Built:** yes, except: the handoff skill's own check of a path's length, and `built-in/`, which
comes with built-in rules. Setup skips its check of dev-home's path in a
test profile, whose dev-home sits deep in the repo's folder, so the tests check it directly.

**Decision:** dev-home's `global-rules/` becomes `rules/`, with four levels:

```text
rules/_all-agents/              every agent, every PC
rules/<agent>/                  one agent, every PC: claude-code/, codex/
rules/pcs/<pc>/_all-agents/     every agent, one PC
rules/pcs/<pc>/<agent>/         one agent, one PC
```

Each level holds `mine/`, the end user's rule files. `_all-agents/` and each `<agent>/` also hold
`built-in/`
([0067: Built-in rules](0067-built-in-rules.md)),
never the per-PC levels, and `pcs/<pc>/<agent>/` also holds `unanswered/`
([0064: Each agent's rules file](0064-each-agents-rules-file.md)).
Decided by the developer on 2026-10-17 and 2026-10-18, and changed on 2026-10-22 (a code block
left open, the order inside a merged section, `# My rules`, and the size settings' details) and
2026-10-23 (a missing `my-rules.md` git still has).

- **Names.** `<pc>` is the PC's name ([0083: The PC's name](0083-the-pcs-name.md)) in
  lowercase, any other character a hyphen.
  `claude-code/` and `codex/` exist only for agents set up on some PC.
  `claude-code` matches the agent's name in `dev-home-skill.json`.
- **`mine/`.** Setup makes sure every `mine/` exists and holds a `my-rules.md`, recreating an empty
  one whenever it's missing (deleted or renamed away, letter case ignored), for `_all-agents` and
  each agent set up on that PC, at both levels, and commits it. While git still has the missing
  file, a delete or rename the end user hasn't committed yet, setup waits for that commit, so its
  own commit never takes those rules from the other copies (the developer, 2026-10-23). It never
  touches any other file in `mine/`. The end user's files there take any `.md` name, subfolders
  included, joined alphabetically by path. A file directly in a level folder is reported on each
  sync and not joined. The end user's current `global-rules.md` moves to
  `rules/_all-agents/mine/my-rules.md`.
- **Operating systems.** A rule file's note may say `os: windows`, or several names separated by
  commas, the names `supportedOn` takes, in any case
  ([0066: Notes in rule files](0066-notes-in-rule-files.md)). Setup joins the file only on
  those systems. A misspelled name gets a `PROBLEM` line naming the file, with "Did you mean
  ...?", and the rule loads everywhere until it's fixed.
- **Joining.** Each agent's file holds the operating rules first, never merged, then
  `_all-agents`, `<agent>`, `pcs/<pc>/_all-agents`, and `pcs/<pc>/<agent>`, each with
  `built-in/on/` before `mine/`, and `pcs/<pc>/<agent>/unanswered/` after them, each file there
  only in the rules file it came from
  ([0064: Each agent's rules file](0064-each-agents-rules-file.md)), files alphabetically by
  path. No sentence says which rule wins. Matching headings combine: the same level and text
  (letter case and surrounding spaces ignored) under the same parent. A merged section sits where
  its heading first appears, and holds its own text first, from each file in join order, then its
  subsections, each where it first appears, but a deeper heading before a shallower one, so text
  keeps the heading it had. What a file has outside a top-level heading of its own, its text
  before any heading and any deeper heading before its first top-level one, goes under
  `# My rules`, merged with that heading in any file, and a heading with nothing under it is left
  out (the developer, 2026-10-22).
  Only Markdown headings count: a line starting with one to six `#` and then a space or nothing,
  outside fenced code. The operating rules never merge, and content is never deduplicated. So a
  built-in rule carrying `## Writing style` lands under the end user's own section of that name.
- **The operating rules' last line** becomes "My rules are in `<dev-home>/rules/`;
  `<dev-home>/README.md` explains its folders.", dropping "and win where the two conflict".
- **Comments and blank lines.** Setup removes every HTML comment that starts a line, with all its
  lines, outside fenced code, notes included; a comment in the middle of a line stays. A comment
  with no `-->` in its file is removed to that file's end, and reported on every sync. A code
  block a file leaves open is closed at that file's end, and reported on every sync, so it can't
  turn the files after it into code (the developer, 2026-10-22). Each file's
  leading and trailing blank lines are dropped, one blank line separates files, and the joined
  file ends with one line break; blank lines inside a file stay. An empty file, or one with only a
  note, adds nothing.
- **Encoding.** Setup names every encoding, never the operating system's default, and writes the
  joined file as UTF-8 with LF. A byte-order mark decides (UTF-8 or UTF-16); any other file is read
  as UTF-8, each bad byte shown as the replacement character, NUL bytes dropped. A file that isn't
  clean UTF-8, or is UTF-16, is reported on every sync until it's saved as UTF-8; setup never
  rewrites it.
- **Size.** Two settings per PC, in KiB, changeable through `/dev-home configure` or setup's
  menu. `codex.instructionsMaxKiB`, "Codex's instruction limit", 128 by default: setup makes sure
  Codex reads at least that much in each Codex home, raising `project_doc_max_bytes`, or adding
  it where Codex's own default of 32 KiB is less, and never lowering it. `rules.warnAboveKiB`,
  "Warn when your rules for one agent pass", 32 by default: while the end user's own rules for
  one agent on one PC are past it, every sync says so in a `LARGE` line, until they shrink or the
  end user raises the size; 0 never warns (the developer, 2026-10-22).
- **Path length.** Caps of 40 characters on built-in skill and rule names, 24 on agent folder
  names, and 32 on PC folder names, with moved-file names cut to 60. A longer PC name is cut to
  32 characters; two PCs whose names agree that far would share a folder, which is accepted as
  rare, since Windows' own generated names have at most 15 characters. Each run, setup checks that
  dev-home's folder path, plus the longest rules path it creates, plus 30 characters, fits under
  260 characters, and otherwise prints a `PROBLEM` line suggesting a shorter place for dev-home.
  The handoff skill checks the same way when it creates a handoff. Setup turns on `core.longpaths`
  in dev-home's git config with its other git settings there; if checking it adds a git call to
  each run, it's measured and the developer is asked first, as AGENTS.md's Speed rule says.
- **Docs.** `docs/guide/your-rules.md` explains the levels with an example of each, `mine/` and
  `my-rules.md`, `os:`, a takeover of an agent's file, and getting dropped text back;
  `docs/reference/rule-files.md` holds the facts to look up; the README's "Your own rules and
  skills" points to the guide; and dev-home's root README explains `rules/`.

**Why:**

- Really per PC: a file in a Codex home is per home, and several homes would make "this PC"
  unclear. Synced and backed up. A file per rule is easy to update and has its own history, the
  way Claude Code's and Cursor's rules folders work. `_all-agents` always sorts first, whatever the
  next agent is called (Aider would sort above `all-agents`), and `claude-code` doesn't suggest
  claude.ai's chats.
- `mine/` and `my-rules.md`: an agent asked to add a rule for, say, Codex on this PC always knows
  which file to open. There's no `rules/README.md`: dev-home's root README, which setup keeps
  current, explains the layout, and a README an end user adds is theirs.
- No sentence says which rule wins: programs and agents that combine rule files, such as Ruler
  and Cursor, add none; a conflict is better fixed than ranked; and a later, more specific rule
  is usually followed.
- `# My rules`: setup creates every `my-rules.md` empty, and an end user's own file may start
  with `# My rules` or with no heading at all, so a rule written with no heading would follow the
  operating rules' last line as if it were one of them, and a `## Writing style` there wouldn't
  combine with the one under `# My rules`. Putting such rules under that heading in the join
  works for every file, with no habit for the end user to keep. A fresh agent's read found the
  gap (2026-10-22).
- Comments: Claude Code's memory docs (read 2026-10-18) strip "Block-level HTML comments" and keep
  "Comments inside code blocks", so both agents see the same rules, and comments cost no tokens in
  Codex. An unclosed comment kept would likely hide every later file from Claude Code (inferred
  from Markdown, not tested).
- Encoding: such files are unlikely. Editors and the agents' file tools write UTF-8; tested
  2026-10-18, only Windows PowerShell 5.1 wrote others (`>` UTF-16, `>>` a UTF-16 tail on a UTF-8
  file, which strict UTF-8 accepts, and `Set-Content` and `Add-Content` the PC's code page). Rules
  never drop out, the result is the same on every system, and it's about 10 lines. UTF-16 is
  reported because git counts a file with NUL bytes as binary, and `git merge-file` refuses it.
- Size: Codex reads the global file first and silently drops what passes its budget, 32 KiB by
  default. Claude Code loads files up to 4 MiB and advises under 200 lines per file, about 12.6 KiB
  at 63 bytes a line, and its own length warning doesn't show in the desktop app's or VS Code's
  `/status` (the developer's screenshots, 2026-10-18). 32 KiB is Codex's whole default budget, and
  about twice Claude Code's advice. Measured 2026-10-18: the operating rules 2,439 bytes, one
  end user's global rules 13,832, and Codex's joined file 16,289. The warning is its own word,
  not `PROBLEM`, since rules kept large on purpose aren't a failure. Saying it on every sync, as
  `NEW` does for a folder with no answer, needs no saved state, and raising the size stops it.
  Setup only ever raises what Codex reads, so a small limit can't cut Codex below its default.
- Path length: Windows refuses a path over 260 characters by default, counting dev-home's own
  folder; Git for Windows won't check out a longer one without `core.longpaths`; and macOS and Linux
  cap each name at 255. Windows' own long-path switch needs admin rights, so setup leaves it alone.
  With these caps the longest rules path is about 140 characters, so dev-home's folder can be about
  90 characters long. A handoff's path, `handoffs/github/<owner>/<repo>/HANDOFF.md`, can reach about
  170, since GitHub allows 39-character owners and 100-character repository names.
- `os:` in a note: agents are limited by folder, operating systems by declaration, as built-in
  rules declare theirs, and one file covers every Windows PC. A misspelled name loads the rule,
  since dropping a needed rule costs more than loading an extra one.

**Options set aside:**

- One file per level with notes and end notes inside it (too complex); the end user's files
  directly in each level folder (the developer chose `mine/`); `global-rules/` ("global rules for
  one PC" contradicts itself), `always-on-rules/`, `my-rules/`; an `agents/` subfolder, dotted
  names, and prefixes; per-PC files in each agent's own folder; `all-agents` and `0-all-agents`;
  `claude`. Per-account rules end for Codex homes, while Claude Code's own files stay; a level for
  them can come later.
- A placeholder with a note in every folder; a README in `rules/`; leaving a renamed or deleted
  `my-rules.md` alone.
- A "later rule wins" sentence; headings per level (they'd stop headings combining, and cost
  tokens); keeping the last line with a new path; removing it.
- Setup writing `# My rules` into each `my-rules.md` it creates, with end users starting their
  other files with it (a file without it still lands among the operating rules); leaving the join
  as it was and only rewording the guide.
- Leaving a file that isn't clean UTF-8 out (one bad line drops every rule in it); reading the
  whole file as Windows-1252 (garbles a mixed file's UTF-8 part, tested); repairing it line by line
  (about 30 more lines of guessing for unlikely cases); converting the file.
- Removing only setup's notes; also removing comments in the middle of a line (needs inline-code
  parsing); keeping an unclosed comment's text; collapsing runs of blank lines.
- A fixed 64 KiB; growing the budget automatically; Codex's default; no warning; a warning at
  16 KiB.
- For the warning: `PROBLEM` (setup would count rules kept large on purpose as a failure, with
  exit code 1); a general `WARNING` word (unrelated lines would gather under it); once a day, or
  once when the size is first passed (both need saved state, and the second is easy to miss).
  The names `rules.largeAboveKiB` and `codex.projectDocMaxKiB` (Codex's jargon, which suggests
  only the project's file).
- Limits worked out per PC (rule files sync between PCs, so names would be renamed back and
  forth); relying on long-path support alone; no caps and no check.
- No OS limit for the end user's rules (a Windows rule loads on every Mac, or is copied into each
  Windows PC's folder); per-OS folders such as `rules/os/windows/` (more levels and folders, and
  built-in rules declare their systems instead).

**Look again if:** an agent gains a way to load several global rules files, end users ask for a
level per account, or Windows turns on long paths by default.
