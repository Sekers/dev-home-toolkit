# 0007: The State line's commit

**Built:** yes.

**Decision:** the `newer-commits` topic of `facts.py` finds the commit hashes in the handoff's
State line that the project has, takes the one with the fewest commits after it, which is the
latest the update knew of, and counts both ways: `newer`, the commits this checkout has that it
doesn't, and `behind`, the ones it has that this checkout doesn't. The handoff skill's read
mentions newer commits, and says to pull when the checkout is behind. That's the common case
across PCs: work pushed from one, and not pulled yet on the other. A backticked hash this
checkout doesn't have at all gives `checked: missing`, with the same advice, since a commit the
update knew of is absent. Only a hash with letters and digits counts there, so a plain number or
a word such as `deadbee` doesn't raise it. One `git cat-file --batch-check` looks up every hash
at once. When the line names more than one commit, one `git merge-base --independent` drops each
that's an ancestor of another one named, and one `git rev-list --left-right --count` for each
left, usually only one, gives both counts. Of those left, the first named wins a tie. If
`merge-base` fails, every commit named is counted.

Changed on 2026-10-26 (`merge-base --independent`).

It looks for hashes only: a tag or branch name, such as `main`, would be too easy to match by
accident. A count it can't tell is `unknown`, never `none` or `0`, which would read as "nothing
changed". A git failure never stops the script, because the topics that say where the handoff
is matter more.

**The problem:** agents checked this on their own, with a `git log` from the State line's
commit: one more turn, and only in some sessions.

**Why in the script:** the same answer in every session, with no extra turn, from a command the
skill runs anyway.

**Why `merge-base` first:** each git call costs about 27 ms on Windows, mostly starting git, and
every `/handoff` command pays for these. Counting every commit named made the cost grow with the
State line: on one PC on 2026-10-26, with 12 named, the handoff skill's `facts.py` command took
0.57 s, and 0.30 s with `merge-base` first, for the same output. An ancestor never has fewer
commits after it than its descendant, so dropping ancestors never drops the latest, and one count
runs however many are named, unless some sit on branches apart. One difference from counting
them all: when a commit and a later one that this checkout lacks tie, the later one is taken, so
the checkout reads as behind it, where counting them all took whichever was named first. That
catches a checkout that has fetched a later commit but not merged it, as `update.py` leaves one
when updates wait, while the State line names both that commit and the checkout's current one;
counting them all missed it when the current one came first. Where the later one is on a branch the
checkout never had, the advice to pull doesn't fit, but the count is still true.

**Options set aside:**

- A topic printing only the project's current commit, for the agent to compare: a `git log`
  turn would still follow whenever the project had moved on.
- Leaving it to agents, as before.
- Counting every commit named (until 2026-10-26): one more git call for each.
- Counting only the first commit named: an earlier commit named first, in passing, would be taken
  for the one checked.
- A rule in the handoff skill that the State line name one commit: longer steps on every
  `/handoff`, no help for handoffs already written, and agents don't always follow such a rule.

**Look again if:** the State line gets a fixed form for the commit, or the handoff template
stops starting with it.
