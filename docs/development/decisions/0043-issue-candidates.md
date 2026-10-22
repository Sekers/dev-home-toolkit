# 0043: Issue candidates

**Built:** yes.

**Decision:** an update offers an item from To do or Bugs as a GitHub issue only when it's a bug,
a feature, or an improvement to the project's own files, such as tests, docs, refactoring,
performance, or upgrading what it depends on, and someone outside the project would understand
it. Chores, checks, research, reviews, the end user's own workflow steps, and work outside the
project, such as a release or an account to set up, never qualify, and neither does a decision
still to make, such as a "Decide whether" item or a proposal not decided yet. A decision made but
not built can qualify. The other tests stay as they were.

An update offers at most one: a bug first, otherwise the item likely to stay open longest. When
others qualify too, a line before the offer says how many and points to `/handoff issue`, which
lists them all. The offer ends with its question, and everything else, such as that line and a
security bug's warning, comes before it. `/handoff issue <item>` still files any item the end
user names, decided or not.

**Why:**

- It matches what the platforms say issues are for, checked on 2026-10-09: GitHub's docs name
  "ideas, feedback, tasks, or bugs", and its default issue types are task, bug, and feature;
  GitLab's name "feature proposals, tasks, support requests, and bug reports", and
  "decision-making"; Bitbucket's issue kinds are bug, enhancement, proposal, and task (from
  third-party references to its API). Ideas and proposals are the exception, below.
- "Task" was too broad. On GitHub it's the catch-all for whatever isn't a bug or a feature,
  such as releases and routine maintenance, which make poor candidates from a handoff. What's
  worth offering from that bucket is work on the project's own files, which "improvement" names.
- The old wording, "a bug, a feature request, or a concrete task someone could pick up and do",
  filtered nothing by kind: candidates come only from To do and Bugs, which hold bugs, planned
  work, and decisions, and decisions were excluded by name. Its only effect was "pick up and
  do", which an agent read as "doable today", turning away items with a part still waiting on
  other work, though issues track blocked work all the time.
- "Feature request" fits only what someone asked for; "feature" also covers what the end user
  planned themselves.
- A decision still to make stays out. A project that uses the handoff skill researches a
  decision in its handoff and records it in its own files, so an issue would be a third place
  for the same decision. When the end user wants outside input first, filing the item by name
  does that.
- One offer per update: each offer is a question, so several would mean several questions in a
  row. The line that counts the others says what else qualifies without asking anything.
- The question comes last, so the part to answer is the last thing read, and the count and a
  security bug's warning are read before answering it.

This keeps the handoff skill's earlier rule that a decision still to make is never offered. That
rule wasn't recorded here before.

**Options set aside:**

- Keeping "task": see above.
- Bugs only, or bugs and features only: docs and test work, which issues suit, would never be
  offered.
- Offering decisions still to make, as the platforms use issues for proposals and ideas: while
  one person works on a project, an issue mostly repeats the handoff, and a handoff can hold many
  undecided items, so offers would come far more often.
- A test of whether a pull request could close the item: that's how bugs, features, and
  improvements end, not what "task" means, so it named the wrong thing.
- A test of whether an issue would help anyone besides the end user: more judgment, so less
  consistent from session to session, and "no (never ask again)" already turns down one item
  for good.
- Up to three offers per update: up to three questions in a row.
- Notes after the offer's question: what comes after a question is easily missed.

**Look again if:** offers miss items worth filing, or other people start working on a project
and want to weigh in on its decisions before they're made.
