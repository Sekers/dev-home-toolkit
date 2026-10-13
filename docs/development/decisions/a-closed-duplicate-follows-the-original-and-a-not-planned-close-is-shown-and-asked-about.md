# A closed duplicate follows the original, and a not-planned close is shown and asked about

**Decision:** `issue_status.py` asks GitHub, in its one request, for the issue each duplicate
duplicates, and prints it with its state and title. When any linked issue closed as not planned,
a second request asks who closed each one and when, and for its last three comments, which it
prints as `COMMENT` lines. In the handoff, a link after "See also:" in an item is there for what
that issue holds, its state changes nothing, and the script leaves it out; every other issue link
is one the item tracks. When a tracked issue closes:

- as completed: as before, an item filed as it is removed, and any other is kept and reported;
- as a duplicate: the link moves to the original, and an item already tracking the original is
  merged with it;
- as not planned: the item stays, and after committing, the agent says who closed it and what the
  comments say, and asks whether to remove it, link it to where the work moved, or keep it with
  the closed issue under "See also:", where it stops coming up.

An item keeps a "See also:" link to another issue the work needs only when its own issue doesn't
link to it, and keeps it until the item is removed.

**Why:**

- GitHub shows a duplicate on the original's page: on 2026-10-09, each of five recent duplicates
  in `cli/cli` appeared on its original as "marked as duplicate" and as a cross-reference. So the
  original is where the work, and the duplicate's information, can be found, and the handoff
  needn't keep the old link. A related issue that GitHub doesn't link is a different matter, and
  only the handoff can keep the two together.
- A not-planned close can be a decision, a bot closing an inactive issue, or the work moving to
  another issue, and when someone else closed it, the person may not know which. The comments
  usually say. Removing the item, or keeping it without the reason, left the person to go and
  look.
- Saying that an issue closed and moved belongs in the update's report, not the item: a handoff
  holds the current state, and git keeps the history (rule 2 of the handoff skill).
- The second request took 0.63 s in one run on one PC on 2026-10-09, about what the first takes
  (0.49 to 0.56 s in three runs). It runs only while a linked issue is closed as not planned,
  which ends once the person answers.

This changes "The handoff update checks issue links with one script": one `gh` request becomes
two when an issue closed as not planned.

**Options set aside:**

- Removing a not-planned item and reporting it: the person may not know why it closed.
- The closer and comments in the first request, for every issue: more data on every update, for
  issues that are mostly open.
- The agent running `gh issue view` for what it needs: the skill's steps would grow with each
  host, and the script is the one place that learns each host's tool.
- Keeping the closed duplicate's link beside the original's: GitHub already links them.
- A note in the item that its issue moved: history, which the handoff leaves to git.

**Look again if:** GitHub stops showing duplicates on the original, or issues on other hosts are
checked.
