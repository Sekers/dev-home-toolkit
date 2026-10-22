# 0025: Setup's questions

**Built:** yes.

**Decision:** setup asks each of its questions whenever the answer isn't saved, not only on a
PC's first run, and only when a person can answer (see "Setup never waits for input nobody can
give" in
[0009: Moving from PowerShell to Python](0009-moving-from-powershell-to-python.md)).

- Whether to pull updates automatically: asked until answered. A quiet run leaves
  `updates.installAutomatically` out of `local-settings.json`, and a sync treats a missing answer
  as the default, yes ([0051: Automatic updates](0051-automatic-updates.md)).
- Each Claude Code folder setup finds, `~/.claude` included: asked once. Codex gets one question
  for every Codex home, `~/.codex` included
  ([0052: Codex homes](0052-codex-homes.md)). A yes or a no is saved in `claudeCode.folders` or
  `codex.homes`, so it isn't asked again
  ([0034: Runs of setup by hand](0034-runs-of-setup-by-hand.md)).
- A quiet run never asks, so it names each folder with no answer, in a line the agent passes on.
  A folder with no answer isn't set up, the session's own included, and setup removes the links
  it made in a folder with a no
  ([0054: Removing what setup set up](0054-removing-what-setup-set-up.md)).
- A save removes a key in `local-settings.json` that nothing declares
  ([0049: Answers in the settings](0049-answers-in-the-settings.md)).

Changed on 2026-10-13, 2026-10-14, 2026-10-15, and 2026-10-16.

**Why:** questions asked only on a first run missed what came later. A Claude folder made after a
PC's first run was never offered, and a first run with `--quiet --content-dir` saved the file
without asking anything, so it looked answered. Naming the folders on every quiet run means an
agent in any account passes the question on: listing them took 0.38 ms at the median, and 5.6 ms
at worst, in 50 runs on one PC, against about 500 ms for a quiet setup.

**Options set aside:**

- For Claude folders: offering every unlisted folder on every run (a no would be asked again
  each time), and asking only on the first run.
- For automatic updates: asking on every run, with the current answer as the default (changing
  an answer later is `--configure`'s job, in
  [0026: setup.py --configure](0026-setup-py-configure.md)), and
  asking only on the first run.
- For quiet runs: naming only the session's own folder (a new account has no skills linked yet,
  so it would almost never come up), and naming none.
- For a folder with no answer: still setting up the one the session runs in, so that account
  keeps working, as until 2026-10-15 (decision 0034 says why not).
- One map of every folder to its answer, in place of a second list: it would change a format
  already in use, by hand on each PC. That cost was later waived, and the map came with
  decision 0046, "Settings files' layout and versions".

**Look again if:** setup gains a question that shouldn't wait for an answer.
