# 0023: The order of a sync's push

**Built:** yes.

**Decision:** after a commit, the sync pushes without fetching first. When GitHub rejects the
push because it has commits this copy lacks, the sync fetches, merges, and pushes again, once.
When the push fails for any other reason, such as being offline or signed out, the commit waits,
with no second network call, and the line reads "1 commit saved on this PC, not synced to GitHub
yet. The next sync sends it." A later sync pushes waiting commits even when it skips the fetch.
As before, the sync commits only the files it's given, and never rebases, stashes, resets,
checks out, or discards.

**Why:** a rejected push is git's own sign that a fetch and a merge are needed, so a fetch before
every push found nothing on the usual path. With several copies, a command that edits still
fetches at its start, before the agent changes anything. The line says "synced", the word the
project uses, because it's right in both modes: "backed up" fits only one copy, and "pushed" is
git's word.

**Option set aside:** fetching before every push, as before.

**Look again if:** pushes are rejected often enough that the retries cost more than fetching
first.
