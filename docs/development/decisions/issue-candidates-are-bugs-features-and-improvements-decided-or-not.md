# Issue candidates are bugs, features, and improvements, decided or not

**Decision:** an item can be offered as a GitHub issue when it's a bug, a feature, or an
improvement to the project itself, such as tests, docs, refactoring, performance, or upgrading
what it depends on, whether or not the person has decided on it, and someone outside the project
would understand it. Work done outside the project, such as a release, an account to set up, or
a step of the person's own workflow, isn't offered. The other tests stay as they were.

**Why:**

- It matches what the platforms say issues are for, checked on 2026-10-09: GitHub's docs name
  "ideas, feedback, tasks, or bugs", and its default issue types are task, bug, and feature;
  GitLab's name "feature proposals, tasks, support requests, and bug reports", and
  "decision-making"; Bitbucket's issue kinds are bug, enhancement, proposal, and task (from
  third-party references to its API).
- "Task" was too broad. On GitHub it's the catch-all for whatever isn't a bug or a feature,
  such as releases and routine maintenance, which make poor candidates from a handoff. What's
  worth offering from that bucket is work on the project itself, which "improvement" names.
- The old wording, "a bug, a feature request, or a concrete task someone could pick up and do",
  filtered nothing by kind: candidates come only from To do and Bugs, which hold bugs, planned
  work, and decisions, and decisions were excluded by name. Its only effect was "pick up and
  do", which an agent read as "doable today", turning away items with a part still waiting on
  other work, though issues track blocked work all the time.
- "Feature request" fits only what someone asked for; "feature" also covers what the person
  planned themselves.
- An undecided request or proposal is what issues are most often for: deciding is what triage
  does. The worry that an issue would split one decision across two places holds less than it
  seemed, since filing replaces the item with a link to the issue.

This reverses the handoff skill's earlier rule that a decision still to make is never offered.
That rule wasn't recorded here.

**Options set aside:**

- Keeping "task": see above.
- Keeping decisions out: an undecided request could never be offered.
- A test of whether a pull request could close the item: that's how bugs, features, and
  improvements end, not what "task" means, so it named the wrong thing.
- A test of whether an issue would help anyone besides the person: more judgment, so less
  consistent from session to session, and "no (never ask again)" already turns down one item
  for good.

**Look again if:** offers of undecided items come to feel like noise.
