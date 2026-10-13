# New items reach the person at a terminal, or in a NEW line

**Decision:** an update or a sync can bring new items: a dev-home-tools skill or recommended
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

**Look again if:** the reminders come to feel like noise, such as many new personal skills a week
across several PCs.
