# Handoff further files

How handoffs are read, what a long one costs, and tests of five ways to split a handoff into
`HANDOFF.md` and further files, behind [0091: Further files](../decisions/0091-further-files.md).
Then tests of the skill text that came out of it. Run on 2026-11-06 and 2026-11-07, with Claude
Code's fresh agents on Opus 5.5.

## How handoffs are read

From Claude Code transcripts on one PC, 2026-10-02 to 2026-11-06:

| What | Measured |
| --- | --- |
| `/handoff` commands | 168 in 67 sessions: 99 updates, 64 reads (18 with a question), 3 audits, 1 `next`, 1 `issue` |
| Model calls after a plain `/handoff` | median 143 |
| Model calls after an update | median 15 |
| Reads of a `HANDOFF.md` | 386, of which 270 read only part of the file |
| Tokens a read added to the context | median about 5,100 (the next call's context minus the last one's, so approximate) |
| Later calls that carried that read | median 30, until the session ended or compacted |

Every call re-reads the whole conversation, so what a session loads early costs again on each
later call. In raw tokens, the reads were re-read about 319 million times over against 3.4 million
read once; at the API's price for cached tokens, a tenth of normal, carrying them cost about 9
times reading them.

Item lengths in the 20 handoffs with list items in one dev-home (top-level items, Next up left
out):

| Items over | Handoffs with any | In the other 17 | In the three largest (84 to 129 items) |
| --- | --- | --- | --- |
| 60 words | 20 | 1 to 17 | 65, 67, 100 |
| 100 words | 17 | 0 to 11 | 35, 45, 75 |
| 200 words | 11 | 0 to 6 | 13, 19, 42 |

## Five layouts tested

Two real handoffs were split five ways by a script, with item summaries written once by an agent
(at most 40 words each) for the layouts that need them:

1. Today: one file.
2. An index: every item a summary line and a file.
3. By section: To do in `to-do.md`, each environment in a file of its own.
4. By size: an item over 200 words moves whole, leaving its first sentence and a link.
5. By need: an item over 60 words keeps a summary, with the rest in a file; an environment over 150
   words moves to a file of its own.

Sizes of `HANDOFF.md` in characters, with the further files' count:

| Layout | Long handoff | Mid-size handoff |
| --- | --- | --- |
| 1. Today | 202,825 | 21,069 |
| 2. Index | 47,550 (129 files) | 11,407 (28 files) |
| 3. By section | 26,303 (3 files; `to-do.md` 163,662) | 9,011 (3 files) |
| 4. By size | 65,684 (42 files) | 13,362 (3 files) |
| 5. By need | 37,877 (89 files) | 6,103 (8 files) |

In layouts 2 and 5, the pointer `Details: [<name>](<name>)` named each file twice, about 9,000 of
layout 5's characters.

Fresh agents with no other context ran the same tasks on each layout, reading only the handoff's
folder. Answers were scored against keys written before any run. "Weighted" prices each run's
tokens as the API does: cached reads at 0.1, cache writes at 1.25, and output at 5, against
input at 1. "Loaded" is a run's largest context less the about 55,000 every run started with.

Long handoff:

| Task | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| Summary: score of 13 | 13 | 13 | 13 | 12.5 | 12.5 |
| Summary: loaded | about 56,000 | 18,000 | 16,000 | 32,000 | 14,000 |
| Summary: weighted | 230,000 | 99,000 | 125,000 | 149,000 | 85,000 |
| Question on one item: score of 12, weighted | 12, 158,000 | 12, 144,000 | 12, 95,000 | 12, 128,000 | 12, 114,000 |
| Start the next step, several items: score of 12, weighted | 11.5, 153,000 | 12, 161,000 | 12, 177,000 | 12, 137,000 | 11.5, 132,000 |
| Update from a session report: score of 8, weighted | 8, 253,000 | 8, 271,000 | 8, 280,000 | 8, 265,000 | 8 and 8, 258,000 and 235,000 |

Mid-size handoff: every layout scored 7 to 8 of 8 on a summary and on a question needing one
item's details, within about 10% of each other's cost. On that question, layout 2's agent opened 9
files in 10 tool calls, and layout 5's opened 3 in 4.

What the runs show:

- Every layout answered equally well. Agents opened a file when they needed its details, and in
  the update runs every summary line and its file still agreed afterwards.
- The layouts differ in what a session loads to get its bearings, and that difference grows in
  real sessions, which go on long after the read. Focused tasks narrow it, because agents already
  search and read parts of a long file.
- Layout 3's detail work cost the most: a to-do's details meant reading or searching a
  164,000-character file, and one agent ran a command it was told not to, to size it up.
- A 40-word cap made the summary agent drop some rules a session must always follow; the test
  agents found them only by opening the file.

Limits: one run per layout and task, fresh agents without the handoff skill's text, summaries
written in one pass, and tasks chosen by the developer.

## Tests of the skill text

The skill text for layout 5, as decided, went through four rounds of fresh agents, each following
the skill on copies of a handoff, with every command written out rather than run:

- An update on a real handoff never split, an update on a made-up handoff already split, and a
  walkthrough of an audit, an issue, a move, a read, and a decision draft. They found a half-done
  Next up step kept whole, a summary missing a rule, an issue drafted before its file was read,
  an audit example that Codex never meets, and unclear names.
- The same three on the fixed text, which held, and found a decision draft lost when its issue
  closed, and a built decision with nowhere to go on a no.
- Updates where a contributor's commit closed a decision draft's issue, answered no and then yes,
  with a new environment long enough for its own file; and a step finished by someone else left
  in Next up.
- Short walkthroughs of each remaining fix, word for word.

Each round's findings were fixed before the next; the decisions record what came of them.
