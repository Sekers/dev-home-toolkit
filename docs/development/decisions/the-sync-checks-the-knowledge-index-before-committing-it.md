# The sync checks the knowledge index before committing it

**Decision:** when a sync commits `knowledge/README.md`, dev-home's knowledge index, it first
checks two things, and commits nothing if either fails: every note the index lists is committed
already, or among the files given and still there; and no note is listed twice. After it brings
in commits from GitHub, by a fast-forward or a merge, it reports a note the index lists twice.
Each failure is a `PROBLEM` line, and nothing is printed when all is well.

**Why:** git commits a whole file, so a sync that commits the index also takes in a row that
another session on the same PC has added for a note it hasn't committed yet. Until that session
commits, the index on GitHub lists a note that isn't there, and if it never does, the row stays.
dev-home's `.gitattributes` merges the index line by line (`merge=union`), so rows added on two
PCs combine, but when both change the same row, both versions stay, and nothing flags it. The
check costs one git call, `git ls-tree` of `knowledge/` at `HEAD`, a median of 30 ms on a
Windows 11 PC (2026-10-16), and only in a sync that commits the index; the check after commits
come in only reads the file. The developer approved the call, as AGENTS.md's "Speed" asks.

**Options set aside:**

- `git ls-files` in place of `git ls-tree`: about as fast, but it also counts a note that's
  staged and not committed.
- Running the `git status` the sync makes at its end before the commit instead, and reusing it,
  to save the call: the closing list of uncommitted files would show the state from before the
  commit, and the commit step would grow more complex, to save about 30 ms in a sync that runs
  when a note is added.
- Checking only that each listed note is on disk: it misses the usual case, since the knowledge
  skill writes a note before its row.
- Generating the index from each note's **Covers:** line, so no agent edits it: it changes the
  index's format, the filing rules, and the knowledge skill, too much for problems this rare.

**Look again if:** the index stops being one row per line, or notes reach dev-home other than
through the sync.
