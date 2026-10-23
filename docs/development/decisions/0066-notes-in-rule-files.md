# 0066: Notes in rule files

**Built:** yes, except: built-in rules' fields, and setup moving files, which comes with taking
over an agent's file. `internal/shared/rules.py` reads a note's fields, acts on `os`, and works
out a moved file's note and name, and whether a file already holds its text.

**Decision:** any rule file in dev-home's `rules/` may start with a note: an HTML comment whose
first line is only `note`, then fields, then a blank line and free text. Decided by the
developer on 2026-10-17 and 2026-10-18.

```markdown
<!-- note
by: setup
when: 2030-01-15 09:30:00+01:00
pc: office
from: C:\Users\you\.codex\AGENTS.md

Moved here when setup took over this PC's Codex home.
-->
```

- **Fields,** all optional. A missing one is unknown, and unknown ones are kept, except in built-in
  rules' files, which setup replaces whole.
  - `by`: `setup`, `user`, or an agent's name such as `codex`, naming whoever composed the words.
  - `when`: ISO 8601 with a space and the local offset, as above.
  - `pc`: the computer the file was written or moved on.
  - `from`: a moved file's source.
  - `built-in`: a built-in rule's name.
  - `state`: `added`, `not added`, `default`, or `unanswered`, the settings files' word for an
    answer, `$state`.
  - `os`: the operating systems the rule is for, as `supportedOn` names them, separated by commas.
- **Syntax:** each field is split at its first colon. Names are letters, digits, and hyphens, read
  in any case and written in lowercase, in any order. Fields end at the first line that isn't one.
  A field written twice counts its last value, and both are kept. A value is the rest of its line,
  needing no quotes, with one pair forgiven. It isn't YAML. The free text is never read by setup,
  and only `-->` can't appear in it. A note covers its whole file.
- **What setup reads:** only `built-in` and `state` in `built-in/`, and `os` in every rule file
  outside `built-in/`, since in a built-in rule's file setup writes `os` from the rule's JSON
  instead. It checks nothing else. End users and agents may write, change, or remove any note, and nothing
  tells agents to write one.
- **Moved files.** Each file setup moves into `mine/` or `unanswered/` gets a note with `by: setup`,
  `when`, `pc`, and `from`, and the move is named in its commit message. Each moved file stays a
  file of its own, even when one takeover moves several. It's named `moved-<pc>-<folder>-<path>.md`,
  where `<folder>` is the agent folder's name, such as `codex` for `~/.codex`, and `<path>` is the
  file's path inside it without `.md`, all in lowercase, any other character a hyphen, such as
  `moved-office-codex-agents.md`. The whole name, `.md` included, is cut to 60 characters. A taken
  name gets the first free `-2`, `-3`, ... before `.md`, names compared regardless of case, and a
  file already in `mine/` is never overwritten. The file setup creates in each `mine/` is always
  `my-rules.md`, never a `moved-` name.
- **Duplicates.** A file to be moved whose text, without its note and with line endings and edge
  blank lines evened out, exactly matches a file already in the `mine/` picked isn't added again:
  setup removes the original and names the file that holds the text, in one line.

**Why:**

- End users and agents, who can't read dev-home's git history, can tell where a rule came from.
- A note loads nowhere: Claude Code strips block-level HTML comments (its memory docs, read
  2026-10-18), and setup removes them when it joins files
  ([0065: Where end users' rules live](0065-where-end-users-rules-live.md)).
- `when` with a space and a numeric offset: Windows gives localized zone names that aren't
  standard. `by` names whoever composed the words, never `me`, which an agent could write about
  itself, nor the end user's name.
- Setup reads only what it acts on: no code or reports beyond what's decided. Replacing a built-in
  rule's file whole avoids merging fields, and a hand edit there is put back at once, rather than
  lost when the rule later changes.
- Moved files' names are never a name an agent loads by itself: a `CLAUDE.md` in a subfolder loads
  on demand in Claude Code sessions there (its memory docs, read 2026-10-18). The name says where
  the file came from, PCs never pick the same one, and moved files sort together. `my-rules.md` is
  a plain name, and end users don't expect file names to rank rules: order within a folder matters
  only to Codex, whose docs say later text overrides, while Claude Code's say it may pick either.
- Duplicates: one file copied to several PCs is common, and its rules would load twice. A move
  retried after a failed removal is caught too.

**Options set aside:**

- A separate metadata file, which would drift.
- A one-line free note, or a list of fields; the markers `dev-home-note` and `rules-note`; `when`
  with a `T`, or with a zone name; `by: me`, or the end user's name; `answer` (chosen at first on
  an agent's unchecked claim that it was the project's term), `choice`, `status`, and `added`, for
  `state`; an `end` field and end notes, made needless by one file per rule.
- Checking every note's fields and format; rewriting only setup's own fields.
- Original names with a number; asking for a name at each takeover; `_my-rules.md` (an underscore
  reads as internal, and the top spot gains little).
- No duplicate check; matching near-duplicates.

**Look again if:** setup needs to act on a field it doesn't read yet.
