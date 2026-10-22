# 0042: /handoff audit

**Built:** yes.

**Decision:** `/handoff audit` starts a second agent, with no context from the session, which reads
the whole handoff and the project files its items point to. It reports each item a new session
couldn't act on: out of date, contradicting another item or the project's files, pointing to
something that doesn't exist, unfinished work without its next step, or a decision without its
reasons. The session checks each finding, fixes what the handoff or the project's files settle,
commits, and asks about the rest. It never changes Next up or rewords text the person approved
word for word. It runs only when asked, after a message saying it takes minutes and costs more
than most commands. In Claude Code it runs in the background; in Codex the chat waits, as
OpenAI's docs describe. It runs on the session's model and effort, unless the command names a
model or effort, such as `/handoff audit sonnet xhigh`; a model named without an effort runs at
xhigh. There is no setting for either.

**Why:**

- An update fixes what its session did, so items that earlier sessions left out of date pile up.
  On a 900-line handoff, on 2026-10-08, a second agent found four such problems that every update
  had kept.
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

**Look again if:** people type the same options on most audits, Codex runs second agents in the
background, or new models or prices change which model and effort suit an audit.
