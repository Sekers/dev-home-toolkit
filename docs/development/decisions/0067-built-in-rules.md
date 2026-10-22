# 0067: Built-in rules

**Built:** not yet.

**Decision:** dev-home-toolkit ships built-in rules: rules an end user can add to their own. Each
is a file in dev-home that setup owns, and none applies without a yes. It comes after
version numbers
([0060: The release data file](0060-the-release-data-file.md)).
Decided by the developer on 2026-10-17 and 2026-10-18.

- **In dev-home-toolkit,** each rule is a folder, `templates/built-in-rules/<name>/`, holding
  `RULE.md`, its text, and `dev-home-rule.json`, mirroring a skill's folder. The folder's name is
  the rule's name: an ID the developer sets, fixed, unique, never reused, renamed through
  `formerNames`, following the naming rule in
  [0072: Fields in skill and rule files](0072-fields-in-skill-and-rule-files.md), and at
  most 40 characters. A rule's text holds no per-PC paths, since every PC shares the file setup
  writes. The JSON holds a `summary`, and may hold `recommended`, `supportedOn`, and
  `formerNames`:

  ```json
  {
    "summary": "Windows treats file names that differ only in case as one file.",
    "supportedOn": [
      { "type": "os", "anyOf": ["windows"] },
      { "type": "agent", "anyOf": ["claude-code", "codex"] }
    ]
  }
  ```

- **In dev-home,** a rule with no `agent` entry is one file in `rules/_all-agents/built-in/`, which
  holds only rules for every agent, agents added later included. A rule with an `agent` entry
  gets a copy in each listed agent's folder, `rules/<agent>/built-in/`, even one naming both of
  today's agents. Each copy sits in `built-in/on/` (`added`, or `default` while recommended) or
  `built-in/off/` (`not added`, `unanswered`, or `default` while not recommended), and is named
  `<rule>.<state>.md`, with the state appended (`.added`, `.not-added`, `.default`,
  `.unanswered`), so a rule's place in the join order never shifts.
- **A copy's note** holds only `built-in`, `state`, and `os` when the rule has an `os` entry, never
  `by`, `when`, or `pc`, so every PC writes the same bytes. Setup writes `os` from the JSON and
  never reads it back.

  ```markdown
  <!-- note
  built-in: windows-file-names
  state: added
  os: windows
  -->
  ```

- **`state` is the only control,** and each copy has its own. The end user or an agent edits that
  line, and setup moves and renames the file to match. A move or rename by hand is put back, with
  one line saying so; a typo in `state` is reported, and the file left where it is; a missing
  `state` is restored from the folder; setup always writes `state`. Setup replaces a built-in file
  whole whenever it differs from the rule and its `state`, first sending a hand edit to the
  Recycle Bin, as for every file dev-home-toolkit owns
  ([0069: Dropped text](0069-dropped-text.md)); it reports the
  edit it put back in one line, and commits.
- **A file that loses its note,** or the note's `built-in` field, becomes the end user's own rule.
  Setup moves it into the same level's `mine/`, named for the rule with the state dropped, such as
  `mine/windows-file-names.md` (a taken name gets `-2`, as moved files do), says so in one line,
  and offers the rule again as new. So `built-in/` holds only dev-home-toolkit's files, and the end
  user's copy keeps loading at the same level. To undo it, the end user deletes that file and
  answers the offered rule.
- **A new rule** gets a file in `built-in/off/` with `state: unanswered`, off until added, and one
  `NEW` line names the batch, once. A PC writes and announces only rules for its own operating
  system and for an agent set up there. A run of setup by hand asks about unanswered rules in a
  question of their own, once per rule, and writes the answer into every copy still `unanswered`,
  never into a copy already answered. The answers are `added`, `not added`, `default`, and
  `unanswered`, as for skills, with no reminders. All recommended saves `default`, which follows
  the recommendation, setup moving the file between `on/` and `off/`.
- **Changing one:** setup's menu shows each agent's value on the rule's row, and picking the rule
  asks which agents to change, all of its agents listed first, or one. A request through
  `/dev-home configure` changes the agents it names, or every copy when it names none. Editing a
  copy changes only that copy.
- **Shown to end users:** a count of recommended rules not yet answered, only in `/dev-home sync`
  and setup's menu; new rules named in the update notice, found by comparing the built-in rules
  before and after the pull, as for changed defaults (`changed_defaults_notice` in
  `internal/shared/update.py`), so each PC's update names them; each rule's `summary`, in the
  notices, the menu, and `/dev-home configure`; and, on a PC whose operating system a rule doesn't
  list, the rule marked as, say, "Windows only".
- **Operating systems:** a rule's `os` entry limits it as a skill's does. On a PC whose system it
  doesn't list, setup joins none of its copies, writes no `unanswered` file for it, and prints no
  `NEW` line.
- **Updates:** built-in rules update with dev-home-toolkit the way skills do. Every copy takes the
  new text with no new yes, and keeps its `state`. A copy left at `default` follows a changed
  recommendation, named in the update notice as a skill's changed default is. A rule whose text
  changes isn't named in the notice: the changelog says what changed.
- **Not recommended:** a built-in rule can ship as not recommended, listed but never added by All
  recommended. No two built-in rules may contradict each other, so All never adds a contradiction;
  a choice such as a spelling convention ships as one rule that isn't recommended.
- **Withdrawn:** a built-in rule dev-home-toolkit withdraws is deleted from dev-home, whatever its
  answer, and the update notice names it with its reason, kept in the release data file's
  `withdrawn` list. A renamed or merged rule uses `formerNames` instead.
- **Versions:** a PC on an older dev-home-toolkit than the newest recorded in `dev-home.json`
  leaves `built-in/` alone, with one line saying to update
  ([0068: Versions and layouts in dev-home](0068-versions-and-layouts-in-dev-home.md)).
- **Docs:** `docs/guide/built-in-rules.md`: how they're offered, adding one or turning it off for
  one agent, All recommended, and what updates and withdrawals do.

**Why:**

- A rule loads in every session and steers every agent, so it never applies without a yes, unlike
  a skill, which follows its default (the developer: riskier than a skill added by default). A
  rule is optional, so a line in every session would cost attention for nothing needed. The rest
  matches skills.
- Its text is in a file: easy for end users, and for agents who edit rules. On and off folders:
  the developer finds them the easiest for a person to read.
- "Built-in": some aren't recommended, so "suggested but not recommended" would contradict
  itself; the folders split rules by who wrote them; and the word is familiar and survives a
  product rename. The docs always call the always-on ones "the operating rules".
- `_all-agents` holds only rules for every agent, so end users can trust what the folder means
  (the developer). A `state` per copy is the only per-agent choice rules can have: Claude Code
  (`skillOverrides`) and Codex (`[[skills.config]]`) can turn a skill off for one agent, but
  nothing can turn off one rule inside a joined file. Copies sharing one answer would change one
  file from another, and lose a change when two PCs change different copies before syncing.
- No `by`, `when`, or `pc`: setup rewrites a file that differs from what it would write, so a
  field that differed by PC would have each PC rewriting the others' copies.
- `os` in the note: every rule file in dev-home shows its limit the same way, the end user's own
  included ([0066: Notes in rule files](0066-notes-in-rule-files.md)).
- Updates like skills (the developer's choice): the cost, that `default` and an update change
  what agents load without a new yes, is accepted, as it is for skills. With that, `revision`
  has nothing to do: a PC that's behind is guarded by the newest version in `dev-home.json`.
- Not recommended: a library of rules that suit some end users, as skills can ship off.
- Withdrawn (the developer): it's no longer an available built-in rule, usually because
  something replaces it or it was a bad rule, and its text stays in both repos' history.
- Folders mirroring skills: setup reads both kinds the same way, and tests check both the same
  way. JSON, as skills use, needs no package to read; YAML frontmatter would.

The folders, the `state` line, and the copies per agent are dev-home-toolkit's own design.

**Options set aside:**

- Answers in `dev-home.json`, or split between it and files; regions inside the end user's own
  files; a note-only include with the text added at join time (agents would search for text that
  isn't there); a folder per answer; the folder as the control, a `later/` folder, git detecting
  moves, a per-PC record, or an extra `folder:` field (too complex, or a field that goes stale);
  one built-in folder, with the state only in names.
- Following the default until answered; an offer (a line every session, and reminders); not
  raising them at all; the notice once on each PC; a monthly reminder; the agent asking "Add it?".
- The names `suggested`, `library`, and `optional`; earlier, `dev-home-toolkit`, `toolkit`,
  `managed`, `toolkit-suggested`, `dh-toolkit-suggested` ("dh" needs decoding),
  `dev-home-toolkit-suggested` (long, and it ties every dev-home's layout to the product's name),
  and `dev-home` (that word means the end user's repo).
- Shipping only recommended rules.
- For a withdrawn rule: keeping it as the end user's own when they'd added it; asking; a list of
  withdrawn names (the newest version in `dev-home.json` tells a withdrawn rule from a newer one).
- Every built-in rule in `_all-agents`, joined only for its agents; one shared answer for every
  copy; agent folders only for one-agent rules, with `_all-agents` for several.
- For operating systems: the wording alone (on mixed PCs, a rule costs tokens on the other
  systems, or isn't added anywhere); a per-OS folder; leaving `os` out of the note (first chosen,
  as a repeat of the JSON, then reversed so every rule file shows its limit the same way).
- A `revision` field, a number per rule the developer raises with each change to its text
  (nothing would use it); keeping the first PC's
  `when` and `pc` (more code, and git already records it).
- One Markdown file with its data in a note; one JSON file for every rule; `templates/rules/`,
  which reads like the operating rules' home.
- For a file that loses its note: leaving it in `built-in/on/` as the end user's (the folder would
  hold a file that isn't built-in); putting it back as a hand edit (it would reverse the end user's
  choice to make the rule their own).

**Look again if:** end users ask for reminders about unanswered rules, or a rule needs text that
differs by PC.
