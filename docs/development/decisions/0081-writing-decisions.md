# 0081: Writing decisions

**Built:** yes.

**Decision:** each design decision has a file of its own in `docs/development/decisions/`,
numbered oldest first and named for its subject, such as `0054-removing-what-setup-set-up.md`,
titled `# 0054: Removing what setup set up`. It opens with a Built line, then the Decision, then
Why, Costs, Options set aside, and Look again if, each only when it adds something. A change edits
the file in place. The folder's [README](README.md) gives the format and lists every decision, and
research a decision rests on has a page of its own in [research/](../research/README.md). Decided
by the developer on 2026-10-12 (a file per decision, and the research folder), and changed on
2026-10-22 (numbers, names by subject, the Built line, and changes in place).

**Why:**

- A file per decision: `decisions.md` had reached 1,674 lines and 44 entries in 10 days. A file
  per decision is the practice known as architecture decision records, and a docs website needs
  pages anyway. Research waiting for a decision had no home, so it got a folder of its own.
- Named for the subject: a name that states the answer changes when the answer or its wording
  does. Five renames had already changed every link to the files they renamed, three of them for
  the glossary's words. A number gives a short reference, such as "decision 0054", and keeps the
  order. MADR, a common template for these files, names them `NNNN-title-with-dashes.md`.
- The Built line: 13 decisions said "not built yet" somewhere in their text, and several recorded
  a change decided but not built, so a reader had to read a whole file to know what the code does.
- Changes in place: notes added at the end, `Changed on <date>`, made a file read like a log, and
  an agent paid for that history every time it read the file. Git keeps the old text.

**Options set aside:**

- One file, `decisions.md`, or splitting it later; a research page with no folder of its own; and
  research data in `internal/development/`, since a link out of `docs/` breaks on a website.
- Files named for the answer, unnumbered, listed in order by an `index.md`, as until 2026-10-22.
- A Status line with MADR's statuses (proposed, accepted, superseded): the glossary keeps "status"
  for the scripts' status words, a proposal isn't written up as a decision until it's decided, and
  what matters here is whether a decision is built.
- No Built line: "not built yet" stays buried in the text.
- A new file for each change, marking the old one replaced: the folder becomes a log to read
  through.

**Look again if:** decisions still grow long through changes, or a docs website needs another
layout.
