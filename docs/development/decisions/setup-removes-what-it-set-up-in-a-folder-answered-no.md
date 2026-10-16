# Setup removes what it set up in a folder answered no

**Decision:** once a Claude Code folder, or Codex, is answered no, every run of setup, quiet ones
included, removes what setup set up there, and lists each removal as it goes:

- In a Claude Code folder: the links setup made in its `skills\` and `rules\`, and dev-home and
  dev-home-tools in `permissions.additionalDirectories` in its `settings.json`.
- For Codex, in every Codex home: the `AGENTS.md` setup wrote, which starts with setup's note,
  and dev-home in `writable_roots` in its `config.toml`. And the links setup made in
  `~/.agents/skills`, the one skills folder every home reads.

```text
REMOVED   Link in a folder you said no to: C:\Users\you\.claude-second\skills\handoff
REMOVED   Rules file in a Codex home you said no to: C:\Users\you\.codex\AGENTS.md
REMOVED   Link for Codex, which you said no to: C:\Users\you\.agents\skills\handoff
SET       Claude Code settings in .claude-second: removed dev-home and dev-home-tools from permissions.additionalDirectories in C:\Users\you\.claude-second\settings.json. Backup of the old file: C:\Users\you\.claude-second\settings.json.bak-YYYYMMDD-HHMMSS
SET       Codex config in .codex: removed dev-home from writable_roots in C:\Users\you\.codex\config.toml. Backup of the old file: C:\Users\you\.codex\config.toml.bak-YYYYMMDD-HHMMSS
```

- A link counts as setup's when it points where setup's links point: in `skills\` and
  `~/.agents/skills`, to a skill in `internal/.generated/skills/` or in dev-home's `skills/`; in
  `rules\`, to the generated operating rules or dev-home's `global-rules/`. Anything else there
  stays: a link of the person's own, a file, a folder, and an `AGENTS.md` setup didn't write.
- Each link is removed by itself, never with a recursive delete, and never anything it points to.
- The question about a folder, or Codex, says what a no does, after what a yes does: "A 'no'
  removes all of that, if it's there.", and for Codex "A 'no' removes all of that but
  project_doc_max_bytes, if it's there." (the developer's wording, 2026-10-16). So the no
  approves the removal as the yes approves the setup.
- A folder nobody has answered for still gets nothing added and nothing removed.
- A folder answered no that is really one setup sets up, reached through a junction, keeps what
  that one uses: such as `~/.claude-alias` made a junction to `~/.claude`, or an account's
  `skills\` made a junction to another's, or to `~/.agents/skills`, to share skills. Setup
  compares real paths for this, only on a run with a folder answered no.
- The settings files: the no approves taking the access back out, as the yes approved adding it
  ([A yes to set up a folder approves the settings change it needs](a-yes-to-set-up-a-folder-approves-the-settings-change-it-needs.md)),
  so every run makes the change when it's needed, with a dated backup and a `SET` line. Setup
  takes out each entry naming those folders, written with `~` in Claude Code's file, or with
  either kind of slash, single or doubled, in Codex's. Every other entry and setting stays, and
  so does the layout of a `config.toml`, every comment included: a comment on a line setup takes
  out keeps a line of its own. Once nothing is left, the list goes, and with it `permissions` or
  `[sandbox_workspace_write]` when nothing else is in it, on it, or right above it, not even a
  comment, so a file setup changed reads as it did before. `project_doc_max_bytes` stays: it
  grants no access, and lets Codex read long `AGENTS.md` files in any project.
- A file setup can't safely edit gets a `PROBLEM` line on every run, and a run by hand shows what
  to take out by hand: one with comments, a form of `writable_roots` setup doesn't edit, such as
  a dotted key, and a `settings.json` that isn't JSON at all but names either folder.

**Why:**

- A no should mean dev-home is gone from that folder. Until this, a no only stopped setup from
  touching it, so a folder set up earlier and answered no later kept dev-home's skills and rules,
  loading in every session there, with nothing saying so (decided with the developer,
  2026-10-12).
- Setup links Codex's skills into `~/.agents/skills`, outside every home, since Codex calls the
  folder in each home, `$CODEX_HOME/skills`, deprecated (see
  [Codex is set up in every Codex home, or in none](codex-is-set-up-in-every-codex-home-or-in-none.md)).
  Removing only what's inside the homes would leave Codex listing dev-home's skills after a no
  (decided with the developer, 2026-10-16).
- The settings files' entries are what give an account access to dev-home: without them, Claude
  Code asks before using dev-home and dev-home-tools from another project, and Codex's sandbox
  blocks writes to dev-home. The usual reason for a no is keeping an account apart, such as a
  work one, so the access goes with the skills and rules (decided with the developer,
  2026-10-16).
- Only links that point where setup's do, so a person's own links stay. The cost: a link the
  person made by hand to one of those places looks like setup's, and goes too. Setup keeps no
  record of what it added, so an entry the person wrote by hand for the same folder goes too;
  the backup keeps it.
- What it costs: nothing on a PC with no folder answered no. Otherwise every sync's setup lists
  each such folder's `skills\` and `rules\`, or `~/.agents/skills`, follows a few links, and
  reads a small settings file: about 0.9 ms for each Claude Code folder answered no, at the
  median, measured on 2026-10-16 on folders made for the measurement, against about 500 ms for a
  quiet setup. That was a fast PC, so most take longer. Keeping a record of what's already
  removed would skip the work, at the cost of a record that can disagree with the folders;
  checking on every sync also catches anything setup removed that comes back (accepted by the
  developer, 2026-10-16).

**Other tools read the same folders,** checked in each tool's docs on 2026-10-16:

- `~/.agents/skills`: Codex; GitHub Copilot, beside `~/.copilot/skills`; Gemini CLI, beside
  `~/.gemini/skills`, where the copy in `~/.agents/skills` wins for a name in both; and Cursor,
  beside `~/.cursor/skills`. Claude Code doesn't read it.
- Cursor also reads `~/.claude/skills` and `~/.codex/skills`, for compatibility.

So on a PC with those tools, a no to Codex takes dev-home's skills from Copilot, Gemini CLI, and
Cursor too, and a no to `~/.claude` takes them from Cursor. dev-home-tools doesn't set those tools
up, so they had the skills only because those folders were set up for Claude Code or Codex.

**Adding an AI agent tool:** a folder that several tools read can't hold a different answer for
each. If setup ever sets up another tool that reads `~/.agents/skills`:

- Setup links the skills there while any tool that reads it is answered yes, and removes its links
  only once every one of them is answered no.
- A no to one of them can't hide the skills from it while another is answered yes. Only that
  tool's own switch for skills could, if it has one: a decision to make then.
- Its question says that it shares the folder, as Codex's says that every Codex home shares one
  answer.

The code that has to change then carries a comment starting "Adding an AI agent tool": search for
it, starting at `TOOLS` in `internal/shared/settings.py`.

**Options set aside:**

- Leaving a folder answered no as it is, with setup printing what to remove: the links would keep
  working, and most people would never remove them.
- Removing only what's inside each Codex home: Codex would still list dev-home's skills, through
  `~/.agents/skills`.
- Removing every link in those folders: links of the person's own would go too.
- Leaving the settings files' entries: an account answered no would keep access to dev-home, and
  nothing would say so.
- Showing each settings file's diff and waiting for a typed yes, at a run by hand (the plan
  before
  [A yes to set up a folder approves the settings change it needs](a-yes-to-set-up-a-folder-approves-the-settings-change-it-needs.md)):
  a no given in chat would leave the access until the next run by hand, a no to the removal would
  be asked again on every run unless it was saved, and it would bring back the prompt that
  decision took away for these same entries.
- Code for several tools sharing a folder, written now: of the tools setup sets up, only Codex
  reads `~/.agents/skills`, so the rule is the same today, and the comments mark where it changes.

This changes [Codex is set up in every Codex home, or in none](codex-is-set-up-in-every-codex-home-or-in-none.md),
where a no set up nothing and removed nothing;
[Setup asks each question whose answer isn't saved yet](setup-asks-each-question-whose-answer-isnt-saved-yet.md),
where a folder with a no was left alone; and
[A yes to set up a folder approves the settings change it needs](a-yes-to-set-up-a-folder-approves-the-settings-change-it-needs.md),
whose change a no now takes back out.

**Look again if:** setup sets up another tool that reads `~/.agents/skills`, Claude Code starts
reading it, or Codex gets a skills folder for each home that isn't deprecated.
