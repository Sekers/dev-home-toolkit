# 0091: Further files

**Built:** yes.

**Decision:** a handoff keeps a long item's details in a further file beside `HANDOFF.md`, so a
session reads them only when its work needs them. The rules are in the handoff skill's
`further-files.md`, which `update`, `audit`, and `issue` read; a plain `/handoff` doesn't. They hold
for every handoff. Decided by the developer on 2026-10-30 (further files, from their idea of
2026-10-16) and 2026-11-07 (what moves, the summary, the pointer, and the layout).

- **What moves.** An item in any section but Next up and the State line moves once it passes about
  100 words. It leaves a summary of at most about 40 words: what it is, where it stands, and
  what's next. The summary keeps the item's opening words (other items refer to it by them), its
  label, prefix, issue link, and issue mark, and every rule a session must always follow, in the
  item's own words with enough around it to make sense, on top of the 40. An item stays moved
  until it's finished or filed as a GitHub issue. An environment's subsection moves the same way,
  as a whole.
- **The pointer.** The summary ends with `([details](<file>))`, before any "See also:" link or
  issue mark.
- **The files.** Flat in the handoff's folder, never in a subfolder. An item's file is named from
  its title or opening words, in lowercase letters, digits, and hyphens, at most 60 characters
  with `.md`, starting with the part of the repo the item is about when it names one, such as one
  script in a repo of several. An environment's file is `environment-<name>.md`, with the name as
  its heading writes it. A name never changes once made. A file starts with the item's title as a
  heading.
- **Keeping them right.** An update reads an item's file before changing the item, checks the
  summary when the file changes and the other way round, searches the files it didn't read for
  what the session changed, deletes a finished item's file, and commits every file it added,
  changed, or deleted. Moving a handoff moves every file in its folder. Filing an item as an issue
  drafts from its file too, then keeps in it only the notes the issue couldn't hold, or deletes
  it. The audit's second agent reads every file an item links to, and reports a summary that
  contradicts its file or leaves out one of its rules.

**Why:**

- **What costs most is what a session loads to get its bearings.** In Claude Code transcripts on
  one PC (2026-10-02 to 2026-11-06), a handoff read stayed in context for a median of 30 later
  calls, and a plain `/handoff` was followed by a median of 143, each re-reading it
  ([research](../research/handoff-further-files.md)).
- **By need, not by size, section, or a file per item.** Fresh agents ran the same tasks on five
  layouts of two real handoffs (2026-11-06 and 2026-11-07): every layout answered equally well,
  and this one loaded the least to get a session's bearings, about 14,000 tokens of a 203,000-character
  handoff, against about 56,000 for the single file.
- **About 100 and about 40:** the gap means every move takes at least about 60 words out of
  `HANDOFF.md`. One number would move an item just over it for nearly nothing. At 100, small
  handoffs barely change: most move 0 to 6 items.
- **Rules in full:** a 40-word cap squeezed always-follow rules out of summaries in the test, and
  a session has to see them even when it never opens the file.
- **One rule for every handoff:** nothing restructures at a size threshold, and items move one at
  a time, in the session that made them long.
- **The pointer's shape** works for every kind of item, keeps the opening words first, and names
  the file once.
- **Flat, with the part's name first:** one rule. A file per part of a repo moves with it, such as
  a script that gets a repo of its own, by its name's start, as a folder would, without a second
  depth or a judgment of whether a repo is several projects. Filed by section, a file would move
  each time its item changes section.
- **A file of rules apart from the skill:** updates, audits, and issues need the rules; plain
  reads, 64 of 168 commands in the transcripts, don't.
- 60 characters confirms the room [0088: Path lengths](0088-path-lengths.md) reserved beside a
  handoff.

**Costs:** an item with a file is kept in two places. Fresh agents kept summaries and files in step
in every update tested, and the audit checks it.

**Options set aside:**

- A file for every item, as an index: about 40 more files here that only repeat their line, a
  larger `HANDOFF.md`, more reads, and two-place edits for one-line items.
- Whole sections in files of their own, such as `to-do.md`: a session needing one to-do still
  reads the whole section.
- Whole items over a size, moved with a pointer: an item just under the line keeps all its detail,
  and the pointer alone drops the item's status from the overview.
- A size budget for `HANDOFF.md`, moving the longest first: restructuring starts only past a
  threshold, and what stays depends on history.
- Further files only for handoffs over a size, with a `facts.py` line to say so: a big move at the
  threshold, and a size that doesn't predict long items.
- One number, 60 or 40, for both moving and the summary.
- The title as the link, or the file named twice in the pointer.
- A folder per part of a repo, or per section.
- Set aside on 2026-10-30: a script printing an outline, the project's decision files alone,
  trimming or a size warning alone, and a flat file per project.

**Look again if:** summaries drift from their files in practice, agents miss details they needed,
or `HANDOFF.md` grows long again from summaries alone.
