# 0076: A PC catching up

**Built:** yes.

**Decision:** nothing syncs dev-home on its own. In multi-PC mode, a PC gets the other copies'
changes, to the end user's rules, skills, and knowledge, at its next sync: a `/handoff` command, a
plain `/knowledge`, adding a note, or `/dev-home sync`. Rules a sync brings in reach the sessions
started after it. The docs tell end users to start with one of those commands after switching PCs
([How often a sync checks GitHub](../../reference/scripts.md#how-often-a-sync-checks-github)).
Decided by the developer on 2026-10-20.

**Why:**

- Most of the similar projects checked sync when a person runs a command, and dev-home already
  syncs at more commands than they do.
- A project that pulls on its own has to pull before the content loads, as a shell function
  around `claude` does before Claude Code starts. A sync from an agent's session-start hook
  can't: the session has already loaded its rules, as tested in Claude Code's `claude -p`
  ([Syncing at session start](../research/syncing-at-session-start.md)).

**Options set aside:**

- A sync from each agent's session-start hook (`SessionStart` in Claude Code and Codex). It can't
  give the first session after a switch its new rules; it runs in every session of every project;
  Claude Code kills a background hook still running when a `claude -p` run ends, which could stop
  a sync partway through a merge; and Codex runs a hook only after the end user approves it, and
  again after any change to it, says neither whether its IDE extension runs hooks nor whether they
  run outside its sandbox, and has an open report that its desktop app doesn't run them.
- A background sync the operating system runs, such as a Task Scheduler task at logon, at unlock,
  and every hour. Set aside by the developer.

**Look again if:** Claude Code or Codex gains a way to run a command before a session loads its
instructions, or end users report stale rules or knowledge on a second PC.
