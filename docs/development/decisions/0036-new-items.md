# 0036: New items

**Built:** yes, except: recommended settings, which aren't built, and the one bullet the skills
share for passing `NEW` on.

**Decision:** an update or a sync can bring new items: a dev-home-toolkit skill or recommended
setting, or a personal skill made on another PC.

- When `update.py` runs at a console, the setup it runs afterward does too, and asks about the new
  items right then.
- A quiet sync installs a new recommended skill or personal skill, and nothing else. From then on,
  every sync prints one line with the status word `NEW`, summing up what's new and what's waiting,
  until the person answers, None included. The exit code stays 0. Skills pass the line on once
  per session, as a line of its own.
- One answer covers a batch, with the shared prompt's four choices, in chat or at the next run of
  setup by hand, whichever comes first. A recommended setting still shows its diff and needs a
  yes.
- Quiet runs write nothing for this.

**Why:** a line printed once is easy to lose in an agent's reply, and the agent decides what to
pass on, while a new skill is already at work in every session. Repeating it until answered, once
per session, means nothing is missed, and one answer, even no, ends it. `PROBLEM` would say
something is broken, and set the exit code. When the person is at a terminal, asking right then
is clearest.

**Options set aside:**

- One line, the first time only: easily lost, and a new skill would be at work before the person
  heard of it.
- Saving that the line was shown: quiet runs would start writing `local-settings.json`.
- Nothing in syncs, only at the next run by hand: weeks could pass.
- A line for each item: a batch, such as after months without updating or from a set of copied
  skills, would flood the reply.

**Later changed,** on 2026-10-16. The first two changes below are built, the second on
2026-10-20, and the third isn't yet:

- A new skill gets its `NEW` line once, not on every sync. The first setup run that finds it
  saves it as `unanswered`, which
  [0049: Answers in the settings](0049-answers-in-the-settings.md) lets a
  quiet run write, and names it in one line: whether it was added to the person's agents, and that
  `/dev-home configure` changes that. The line offers no answers, since the skill works at its
  default, as a new preference gets no line at all; that's a departure recorded in
  [0040: Answers to offers](0040-answers-to-offers.md). A skill the person made on
  another PC can arrive in the sync a handoff or knowledge commit makes, whose steps don't list
  `NEW`, so its line may go unsaid. `/dev-home skills` still lists it.
- A Claude Code folder or Codex home setup hasn't asked about gets the repeating `NEW` line, in
  place of a `PROBLEM` line, so it no longer sets the exit code. It offers the standard answers:
  set it up, no, or remind me in N days, answered with `/dev-home configure` or at a run of setup
  by hand. Saying nothing skips it for the session.
- The skills pass `NEW` and `UPDATE` lines on with one bullet, worded the same in every skill:
  "`UPDATE` and `NEW`: tell the user each such line once per session, as its own line, and
  continue." "Each such line" keeps a different line from being dropped because another came
  earlier in the session. `/dev-home sync`'s summary still names what each `UPDATE` or `NEW` line
  says is waiting, under the name of what it's about, without asking again.

**Look again if:** the reminders come to feel like noise, such as many new personal skills a week
across several PCs.
