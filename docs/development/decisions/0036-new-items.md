# 0036: New items

**Built:** yes.

**Decision:** an update or a sync can bring new items: a dev-home-toolkit skill or recommended
setting, a personal skill made on another PC, or a Claude Code folder or Codex home setup hasn't
asked about. Changed on 2026-10-16, 2026-10-24 (`LARGE` lines share the skills' bullet, and a
recommended setting is asked in plain words), 2026-10-29 (`LONG` lines share it too),
2026-11-09 (a new skill's summary), and 2026-11-11 (the recommended settings' line names each
one).

- When `update.py` runs at a console, the setup it runs afterward does too, and asks about the new
  items right then.
- A quiet sync adds a new skill by its default, and nothing else. The first setup run that finds
  it saves it as `unanswered`, which
  [0049: Answers in the settings](0049-answers-in-the-settings.md) lets a quiet run write, and
  names it in one `NEW` line, once: its `summary`, if it has one, then whether it was added to the
  person's agents, such as `'tidy' (Tidy up downloaded files; added to your agents)`, and that
  `/dev-home configure` changes that. The line offers no answers, since the skill works at its
  default, as a new preference gets no line at all; that's a departure recorded in
  [0040: Answers to offers](0040-answers-to-offers.md). A skill the person made on another PC can
  arrive in the sync a handoff or knowledge commit makes, whose steps don't list `NEW`, so its
  line may go unsaid. `/dev-home skills` still lists it.
- A Claude Code folder or Codex home setup hasn't asked about gets a `NEW` line on every sync
  until it's answered, in place of a `PROBLEM` line. It offers the standard answers: set it up,
  no, or remind me in N days, answered with `/dev-home configure` or at a run of setup by hand.
  Saying nothing skips it for the session.
- A new recommended setting gets a `NEW` line on every sync until it's answered, where one answer
  covers a batch, with the shared prompt's choices, in chat or at the next run of setup by hand,
  whichever comes first. It's asked in plain words, and nothing is written without a yes
  ([0032: Recommended settings](0032-recommended-settings.md)). The one line covers every Claude
  Code folder set up. It names each setting waiting, by its id and summary, as the line for new
  skills names a skill, with the folders it waits in, and gives the answers, as the line for a
  folder does. Settings waiting in the same folders are named together: "Setup has no answer yet
  about a setting dev-home-toolkit recommends for Claude Code in ~/.claude and ~/.claude-second:
  'idle-compaction-off' (Stop Claude Code from compacting a long conversation while you're
  away). It leaves it as it is. Answer with /dev-home configure: all recommended, none, each, or
  remind me in N days. Or run setup.py in a terminal, and it asks." Settings waiting in
  different folders are named in groups, each after its folders, separated by semicolons, such as
  "in ~/.claude, 'attribution-off' (...); and in ~/.claude and ~/.claude-second,
  'idle-compaction-off' (...)". The answers are the developer's choice of 2026-10-28, and naming
  each setting the developer's choice of 2026-11-11.
- A `NEW` line never sets the exit code. The skills pass `NEW` and `UPDATE` lines on with one
  bullet, worded the same in every skill, which `LARGE` lines share
  ([0065: Where end users' rules live](0065-where-end-users-rules-live.md)), and `LONG` lines too
  ([0088: Path lengths](0088-path-lengths.md)): "`UPDATE`, `NEW`, `LARGE`, and `LONG`: tell the
  user each such line once per session, as its own line, and continue." "Each such line" keeps a
  different line from being dropped because another came earlier in the session.
  `/dev-home sync`'s summary still names what each `UPDATE`, `NEW`, or `LARGE` line says
  is waiting, under the name of what it's about, without asking again.

**Why:** a line printed once is easy to lose in an agent's reply, and the agent decides what to
pass on, so an item that waits on an answer repeats until it's answered, once per session, and one
answer, even no, ends it. A new skill is already at work at its default, so it needs telling, not
an answer, and saving it as `unanswered` is what lets its line be said once. `PROBLEM` would say
something is broken, and set the exit code. When the person is at a terminal, asking right then
is clearest. A new skill's summary says what it does when it arrives, for about 12 words, said
once per skill on each PC
([0072: Fields in skill and rule files](0072-fields-in-skill-and-rule-files.md)). A recommended
setting is named with its summary for the same reason: a count alone didn't say what was waiting,
so the person needed another round, through `/dev-home configure`, to find out. In the usual
case, one new setting, the name costs about 10 words more than the count did, and each further
setting about 10 more, such as about 43 for all four waiting in a folder just set up. The agent
reads those words on every skill command until the person answers.

The skills share one bullet for these lines: `UPDATE` already repeated on every sync while commits
waited, and the skills told the end user each time; once per session follows "nothing asked
twice in one session"; one text in every skill fits
[0012: Shared skill text](0012-shared-skill-text.md), and a later line joins by adding its name,
as `LARGE` and `LONG` did; and `/dev-home sync` still reports what's waiting, each part under its
own name.

**Options set aside:**

- One line, the first time only, for an item that waits on an answer: easily lost.
- A new skill's line repeating until answered: the skill already works at its default, so there's
  nothing it needs answered.
- Nothing in syncs, only at the next run by hand: weeks could pass.
- A line for each item: a batch, such as after months without updating or from a set of copied
  skills, would flood the reply.
- For recommended settings, only how many wait in each folder (the line until 2026-11-11): it
  didn't say what was waiting.
- That count, with a pointer saying `/dev-home configure` describes each one: about 6 words more
  whatever the batch, but the person still needs another round to find out what's new.
- Recommended settings named in a small batch, and counted above some size: two forms of one
  line, with a cutoff that would be arbitrary.
- A bullet for `NEW` alone: 15 words, and `UPDATE` would still repeat.
- No bullet: each skill's "pass on anything beyond `OK`" repeats the line on every command.
- The instruction inside the line: a person at a terminal reads it too.
- A `dev-home` bullet without "once per session": it breaks the one shared text.

**Look again if:** the reminders come to feel like noise, such as many new personal skills a week
across several PCs.
