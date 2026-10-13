# The handoff update goes through what the session did

**Decision:** before editing, `/handoff update` lists what the session decided, built, changed,
and learned, and what it left unfinished, from the conversation and the commits since the State
line's. For each, it checks that a new session would find it: a built decision's reasons in the
project's files (offering the text when they're missing), an unbuilt one's in its To do item, a
finding where the project keeps research, and unfinished work with its next step. It fixes every
item the session's work made wrong, and after committing lists each entry with where it went.
Preferences the person shows about how they work are left out until the planned skill for their
global rules exists.

**Why:** the update's steps went through the handoff's own sections, so something a session did
that no item mentioned had no step looking for it. Two updates in one session missed the same
three things: a built decision with no entry here, a to-do still describing what that session
had changed, and preferences the person showed. The person found them only by asking. An agent
reading the handoff cold can't find these, since it never saw the session (see
[/handoff audit has a fresh agent check the handoff](handoff-audit-has-a-fresh-agent-check-the-handoff.md)).
Across 13 updates measured on one PC from 2026-10-03 to 2026-10-08, an update averaged 7.6 model
calls; the review adds a few thousand tokens and at most one more call, about a tenth.

**Options set aside:**

- An audit by a second agent on every update: it misses what only the session knows, and adds
  minutes and cost to every update.
- Showing the list for a yes before committing: a second round on every update, though the typed
  command is already the go-ahead.
- No change: the person had to ask what was missing.

**Look again if:** updates still miss what a session did, such as after a long conversation is
summarized.
