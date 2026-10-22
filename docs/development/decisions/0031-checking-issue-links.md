# 0031: Checking issue links

**Built:** yes.

**Decision:** `/handoff update` finds out whether linked GitHub issues have closed with one
script in the handoff skill's folder, not a `gh issue view` for each link. The script finds the
handoff from the folder it runs in, as `facts.py` does, reads every issue link in it, checks
them all with one `gh` request, and a second when an issue closed as not planned
([0045: Closed issues](0045-closed-issues.md)), and prints a line for each: closed, with GitHub's
reason; open; or not checked, and why, such as `gh` missing or signed out. The agent runs it in
the same turn as its read of the handoff just before editing, so it costs no extra turn. It never
runs for a read, `next`, or `issue`. It adds one Python start, about 0.04 s, and replaces a `gh`
process for each link with one. Changed on 2026-10-09.

**Why:** reading a link and checking its state takes no judgment, so it belongs in a script (see
[skills.md](../skills.md)). One call covers any number of links. When issues on GitLab, Bitbucket,
or Azure DevOps come, it's the one place that learns each host's program, so the skill's steps don't
grow with each host. Its lines can be tested with a faked `gh`.

**Options set aside:**

- Keeping a `gh issue view` for each link: each new host would add steps to the skill.
- Checking issues in the update's start-up call: about 0.04 s faster, and never a call of its
  own, but the update would need a start-up command of its own, and `prepare.py`, which every
  skill shares, would take on a network job for one skill.
- Waiting for a second host before writing the script: one call, testable lines, and shorter
  steps help with GitHub alone.

**Look again if:** reads should show closed issues too, which would put a network call on every
read.
