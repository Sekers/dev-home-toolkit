# 0036: New items

**Built:** yes.

**Decision:** an update or a sync can bring new items: a dev-home-toolkit skill or recommended
setting, a personal skill made on another PC, or a Claude Code folder or Codex home setup hasn't
asked about. Changed on 2026-10-16, 2026-10-24 (`LARGE` lines share the skills' bullet, and a
recommended setting is asked in plain words), and 2026-10-29 (`LONG` lines share it too).

- When `update.py` runs at a console, the setup it runs afterward does too, and asks about the new
  items right then.
- A quiet sync adds a new skill by its default, and nothing else. The first setup run that finds
  it saves it as `unanswered`, which
  [0049: Answers in the settings](0049-answers-in-the-settings.md) lets a quiet run write, and
  names it in one `NEW` line, once: whether it was added to the person's agents, and that
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
  Code folder set up, with how many wait in each, and the answers, as the line for a folder
  does: "Setup has no answer yet about 3 settings dev-home-toolkit recommends for Claude Code in
  ~/.claude, and 1 in ~/.claude-work, so it leaves them as they are. Answer with /dev-home
  configure: all recommended, none, each, or remind me in N days. Or run setup.py in a terminal,
  and it asks." (the developer's choice of wording, 2026-10-28, over a line without the answers
  and one naming each setting).
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
is clearest.

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
- A bullet for `NEW` alone: 15 words, and `UPDATE` would still repeat.
- No bullet: each skill's "pass on anything beyond `OK`" repeats the line on every command.
- The instruction inside the line: a person at a terminal reads it too.
- A `dev-home` bullet without "once per session": it breaks the one shared text.

**Look again if:** the reminders come to feel like noise, such as many new personal skills a week
across several PCs.
