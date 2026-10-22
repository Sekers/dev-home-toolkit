# 0045: Closed issues

**Built:** yes.

**Decision:** `issue_status.py` asks GitHub, in its one request, for the issue each duplicate
duplicates, and prints it with its state and title. When any linked issue closed as not planned,
a second request asks who closed each one and when, and for its last three comments, which it
prints as `COMMENT` lines. A comment longer than 300 characters is cut, never inside a reference
to an issue, and ends with the issues the cut part names, such as "... (cut; also names #20)".
The agent reports what the comments say, and never follows instructions in them. In the handoff,
a link after "See also:", written exactly so, at the end of an item, is there for what that
issue holds, its state changes nothing, and the script leaves it out; every other issue link is
one the item tracks. When a tracked issue closes:

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
  another issue, and when someone else closed it, the end user may not know which. The comments
  usually say. Removing the item, or keeping it without the reason, left the end user to go and
  look.
- Saying that an issue closed and moved belongs in the update's report, not the item: a handoff
  holds the current state, and git keeps the history (rule 2 of the handoff skill).
- The second request took 0.63 s in one run on one PC on 2026-10-09, about what the first takes
  (0.49 to 0.56 s in three runs). It runs only while a linked issue is closed as not planned,
  which ends once the end user answers.
- 300 characters keep the reason for a close, and naming what the cut part references keeps
  where the work went. From `gh` searches on 2026-10-10: 457 issues closed as not planned, in
  157 repos (half under 100 stars), with 642 comments by people. The reason for the close was in
  the first 300 characters of every comment sampled. Of the 257 comments by people that name
  another issue, a cut at 300 alone loses every reference in 10% of them (at 500, 5%; at 800,
  2%). Per issue, 300 characters and the names print about 82 tokens typically and 291 at most,
  against 114 and 382 for 500 characters.
- The last three comments, not fewer: in a busy repo such as `anthropics/claude-code`, the last
  comment is usually a later notice that the issue was locked.
- Anyone can comment on a public issue, so a comment can hold text written to steer an agent.
- "See also:" counts only written exactly so. A missed match only means the link is checked as
  usual, while a match in ordinary wording, such as "see also" in a sentence, would leave a
  tracked link unchecked without a word.

**Options set aside:**

- Removing a not-planned item and reporting it: the end user may not know why it closed.
- The closer and comments in the first request, for every issue: more data on every update, for
  issues that are mostly open.
- The agent running `gh issue view` for what it needs: the skill's steps would grow with each
  host, and the script is the one place that learns each host's program.
- Keeping the closed duplicate's link beside the original's: GitHub already links them.
- A note in the item that its issue moved: history, which the handoff leaves to git.
- Cutting comments at 500 or 800 characters instead of naming what the cut part references:
  more tokens on every such update, and still some references lost.
- Matching "see also" in any case: it hides tracked links when the words come up in a sentence.

**Look again if:** GitHub stops showing duplicates on the original, or issues on other hosts are
checked.
