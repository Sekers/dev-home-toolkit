# 0036: New items

**Built:** yes, except: recommended settings, which aren't built, and the one bullet the skills
share for passing `NEW` on.

**Decision:** an update or a sync can bring new items: a dev-home-toolkit skill or recommended
setting, a personal skill made on another PC, or a Claude Code folder or Codex home setup hasn't
asked about. Changed on 2026-10-16.

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
  whichever comes first. It still shows its diff and needs a yes.
- A `NEW` line never sets the exit code. The skills pass `NEW` and `UPDATE` lines on with one
  bullet, worded the same in every skill: "`UPDATE` and `NEW`: tell the user each such line once
  per session, as its own line, and continue." "Each such line" keeps a different line from being
  dropped because another came earlier in the session. `/dev-home sync`'s summary still names what
  each `UPDATE` or `NEW` line says is waiting, under the name of what it's about, without asking
  again.

**Why:** a line printed once is easy to lose in an agent's reply, and the agent decides what to
pass on, so an item that waits on an answer repeats until it's answered, once per session, and one
answer, even no, ends it. A new skill is already at work at its default, so it needs telling, not
an answer, and saving it as `unanswered` is what lets its line be said once. `PROBLEM` would say
something is broken, and set the exit code. When the person is at a terminal, asking right then
is clearest.

**Options set aside:**

- One line, the first time only, for an item that waits on an answer: easily lost.
- A new skill's line repeating until answered: the skill already works at its default, so there's
  nothing it needs answered.
- Nothing in syncs, only at the next run by hand: weeks could pass.
- A line for each item: a batch, such as after months without updating or from a set of copied
  skills, would flood the reply.

**Look again if:** the reminders come to feel like noise, such as many new personal skills a week
across several PCs.
