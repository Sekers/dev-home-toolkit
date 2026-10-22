# 0048: Status words

**Built:** yes.

**Decision:** `sync.py`'s status words and lines stay as they are, including `LEFT`, `STALE`, and
the `OK` line "dev-home is up to date with GitHub". The "What they report" section of
`docs/reference/scripts.md` says where each change it reports is: in a file on this PC, in a
commit on this PC, or on GitHub.

**Why:** the lines don't say whether they mean this PC or GitHub, and in git, "stale" usually
means the remote side. A guide in the reference answers that without changing what agents read,
and agents put the words into plain language when they pass them on. The developer chose the
guide over changing the output, as simpler.

**Options set aside:**

- Renaming `LEFT` and `STALE` to `RECENT` and `IDLE`: it touches three skills, the reference, a
  decision, and the tests, and a changed skill makes every open session stop once with `RELOAD`.
- Adding "uncommitted, only on this PC" to each `LEFT` and `STALE` line: 5 more words for each
  file listed.
- Rewording the `OK` line to "dev-home and GitHub have the same commits".

**Look again if:** people still misread the lines, or the sync's lines change for another reason.
