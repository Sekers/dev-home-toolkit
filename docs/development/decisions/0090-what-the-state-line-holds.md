# 0090: What the State line holds

**Built:** yes.

**Decision:** a handoff's State line holds the date of the last `/handoff update` and the commit it
brought the handoff up to date with, then the latest result of each kind of check, such as the
tests or an in-game run, each with its date and the commit it ran at, and nothing else. Each
update sets that date and commit, replaces the result of each kind of check its session ran, keeps
the other checks' results, and drops anything else. The handoff skill's rule 2 names a replaced
result and a list of commits as running logs, and Work in progress says what's done in a few
words rather than commit by commit. Decided by the developer on 2026-11-04.

**Why:**

- The skill said to set the line "to what you actually checked this session; if you checked
  nothing, leave it", and to keep what's still true word for word. A session that runs only some
  checks can't follow the first without losing the other checks' latest results, and an earlier
  result stays a true sentence, so updates kept each earlier result and added their own, along
  with what each session did. In one handoff on 2026-11-04, the State line had grown to 1,345
  words, and a Work in progress item listing every commit to 931, of the handoff's 26,509, all
  read on every handoff command.
- The commit an update brought the handoff up to date with is the one `facts.py` needs
  ([0007: The State line's commit](0007-the-state-lines-commit.md)). With only the last check's
  commit, a session that commits without running a check leaves the next read warning that the
  handoff may not reflect a commit that it does.
- Each result has its own date because the line's date moves past the results it keeps.

**Tested** on 2026-11-04 with fresh agents on Sonnet 5.5, at Claude Code's default effort. Each
read only the skill's passages about the handoff's content, a made-up handoff whose State line had
grown into a log, and four sessions in a row (the tests pass, a docs-only commit, a run on a
staging server, a failing test), and gave the State line and the changed items after each update:

- The old wording: the agent replaced the whole line each session, losing the staging run's
  result and a release zip's SHA-256 that nothing else held, and added each commit to Work in
  progress.
- A draft without the update's commit: the line stayed short, but after the docs-only session
  `facts.py` would have reported a newer commit that the handoff reflected. A later draft without
  the change to Work in progress: its commit list grew again.
- The final wording: the line held the update's commit and three results throughout, `facts.py`
  would have reported no newer commit after each session, and Work in progress kept a one-line
  summary of what's done.

**Costs:** 76 more words in the handoff skill's steps, read on every handoff command. A result
whose kind of check doesn't run again, such as a released zip's, stays in the line until an
update removes it as finished; its date and commit show its age.

**Options set aside:**

- Replacing the whole line with each session's checks, as the old wording read literally: it
  loses the latest results of the checks that didn't run.
- Leaving the line alone when a session runs no check: the next read warns about commits the
  handoff reflects.
- Dropping a result once the code has changed after it: most results would go at the next commit,
  and a result's commit already shows how old it is.

**Look again if:** State lines still grow, or updates drop a result a later session needed.
