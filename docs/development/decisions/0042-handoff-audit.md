# 0042: /handoff audit

**Built:** yes.

**Decision:** `/handoff audit` first does a full update, as `/handoff update` does, and commits it,
then starts a second agent, with no context from the session, which reads the whole handoff, the
further files its items link to ([0091: Further files](0091-further-files.md)), and the project
files its items point to. It reports each item a new session couldn't act on: out of date,
contradicting another item, its own further file, or the project's files, leaving out a rule its
further file says always to follow, pointing to something that doesn't exist, unfinished work
without its next step, or a decision without its reasons. The session checks each finding, fixes
what the handoff or the project's files settle, commits, and asks about the rest. It never changes
Next up or rewords text the person approved word for word. The update's own questions, such as
whether to move an item into the project's own files, wait until the second agent is running, and
are then asked one at a time, each answer's change committed on its own; in Codex, whose chat
waits for the second agent, they come after the audit. The audit's report ends with the next held
question still waiting, and only once none is waiting with "Answer any of these and I'll add it,
commit, and push." It runs only when asked, after a message saying it takes minutes and costs more
than most commands. In Claude Code it runs in the background; in Codex the chat waits, as OpenAI's
docs describe. It runs on the session's model and effort, unless the command names a model or
effort, such as `/handoff audit sonnet xhigh`; a model named without an effort runs at xhigh.
There is no setting for either. Changed by the developer on 2026-10-23 (the update first, and when
its questions are asked) and 2026-11-07 (the example of a held question, the report's ending, and
further files).

**Why:**

- An update fixes what its session did, so items that earlier sessions left out of date pile up.
  On a 900-line handoff, on 2026-10-08, a second agent found four such problems that every update
  had kept.
- The update first: a second agent reading an out-of-date handoff spends its time on what an
  update fixes more cheaply, such as items that commits since the State line's check have
  overtaken. It can't catch closed GitHub issues, which only the update checks, or anything only
  the session knows. Even a session that did nothing may find commits and closed issues that came
  in since the last update. The update reads the whole handoff, a good share of the audit's cost
  on a long one (a 2,000-line handoff is about 62,000 tokens), but an audit of an out-of-date
  handoff wastes more.
- The questions while the second agent runs: the person has just typed the command and is likely
  there, and the minutes of waiting aren't wasted. The second agent only reads, and a finding
  whose text changed after it read it is dropped, so an answer given meanwhile can't clash with
  the audit. Codex's chat waits for the second agent, so there the questions come after it.
- The example of a held question is one an update asks before committing, which an audit's update
  holds back, and one Codex asks too; an issue candidate, which Codex skips, comes after the
  commit anyway.
- One thing to answer per message: with a held question waiting, the invitation to answer the
  listed items would make a short reply such as "yes" ambiguous.
- It fixes rather than only proposing, because a handoff is a status note kept in git, and
  `update` already edits on a typed command. Claude Code's `/doctor prompt-audit` only proposes,
  because the instruction files it edits change every later session.
- The session reads only the parts of the handoff that the findings point to, not the whole file
  again. In the first real audit, on 2026-10-08, re-reading all 900 lines was three-quarters of
  what the session itself read, and its share came to about half of what the second agent cost.
  An edit that replaces only its target keeps what other sessions changed elsewhere, and Claude
  Code 2.1.295 lets a file be edited after reading only part of it (checked on 2026-10-09).
- On request, because of the cost: on that handoff, on 2026-10-08 with Claude Code 2.1.295, one
  audit took 0.6 to 15 minutes, and $0.03 to $1.12 at that day's API prices, by model and effort.
- The first real audit, later the same day on the same handoff, ran on Opus 5.5 at xhigh: 3.6
  minutes and about $1.44 at the same prices. It found 7 of the 9 known problems still there,
  plus 3 no test run had reported, and nothing it reported was wrong.
- Model and effort, from 11 runs on the same handoff on 2026-10-08, with Opus 5.5, Sonnet 5.5,
  and Haiku 5.5, scored against 12 known problems:
  - Effort mattered more than the model: Sonnet found 2 at medium and 8 at xhigh, and Haiku found
    4 and 6. Opus found 6 at both medium and xhigh, at medium in under half the time.
  - Max was slower and found no more.
  - No run found everything, and two identical runs found different problems.
  - Naming the kinds of problems in the prompt didn't raise the scores, but it made the runs cover
    every section, and gives the skill one list of what counts.
- A model named without an effort runs at xhigh, because Claude Code would otherwise run it at the
  level saved for that model, or its default, which is medium for the 5.5 models (Claude Code
  2.1.295, 2026-10-08). The session's own effort can't be read by a script, so the skill can't
  carry it over to another model.
- The name: Claude Code uses "audit" for the same kind of check; "check" is used loosely across
  the skill; and "review" is both agents' command for reviewing code.

**Options set aside:**

- An audit on every update: minutes and cost every time.
- Reporting without fixing: a second round for every audit.
- Two second agents at once, with their findings merged: about a third more found in the same
  time, at twice the cost. Running the audit again does the same when wanted.
- A setting for the audit's model and effort: the command's options cover the occasional change,
  and each agent product has a default for every second agent (Claude Code's
  `CLAUDE_CODE_SUBAGENT_MODEL`; Codex's `agents.default_subagent_model` and
  `agents.default_subagent_reasoning_effort`).
- A fixed model for each agent product: names go stale, and none was tested in Codex.
- Asking before starting: the typed command is the go-ahead, and the message says the cost.
- The names `check`, `review`, and `fresh-read`.
- A separate `/handoff update audit` command, also typed as `/handoff audit update` (decided on
  2026-10-09, never built): one more command to learn and to tell apart from an update's own text,
  while a plain audit would still read a handoff that may be out of date.
- An update only when something changed: the issue check is needed on every audit anyway, and a
  wrong guess about the session's work audits an out-of-date handoff.
- Typing `/handoff update`, then `/handoff audit`: two commands, and nothing makes the update come
  first.
- The update's questions before the audit: it waits until they're answered, so someone who walked
  away comes back to nothing done. After it: minutes of waiting for questions that were ready at
  the start.
- One commit when the audit finishes, for the update, the answers, and the fixes (2026-11-07): it
  saves one sync, about 1.7 seconds, on a rare command, while the update's work would wait
  uncommitted for the audit's minutes. It was weighed while an update still asked before clearing
  Next up, which a single commit would have let share the update's commit
  ([0093](0093-what-an-update-removes-from-next-up.md)).
- The invitation and a held question in one message, as approved on 2026-10-23; or no invitation
  at all, which leaves the person unsure that answering a listed item gets it added.

**Look again if:** people type the same options on most audits, Codex runs second agents in the
background, or new models or prices change which model and effort suit an audit.
