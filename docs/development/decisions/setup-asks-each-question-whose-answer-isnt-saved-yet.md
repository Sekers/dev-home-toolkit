# Setup asks each question whose answer isn't saved yet

**Decision:** setup asks each of its questions whenever the answer isn't saved, not only on a
PC's first run, and only when a person can answer (see "Setup never waits for input nobody can
give" in
[dev-home-tools moves from PowerShell to Python, in phases](dev-home-tools-moves-from-powershell-to-python-in-phases.md)).

- Whether to pull updates automatically: asked until answered. A quiet run leaves
  `updates.installAutomatically` out of `local-settings.json`, and a sync treats a missing answer
  as no. (Later changed by
  [dev-home-tools updates install themselves unless you say no](dev-home-tools-updates-install-themselves-unless-you-say-no.md):
  a missing answer follows the default, yes.)
- Each `~/.claude-*` folder: asked once. A yes or a no is saved in `claudeCode.folders`, so it
  isn't asked again.
- A quiet run never asks, so it names each `~/.claude-*` folder with no answer, in a line the
  agent passes on. A folder with no answer that the session runs in (`CLAUDE_CONFIG_DIR`) is
  still set up, so that account keeps working, and its settings line says that setup without
  `--quiet` asks about it. A folder with a no is left alone, even from a session there.
- A save keeps every key in `local-settings.json` that setup doesn't know. (Later changed by
  [Settings record answers, not just values](settings-record-answers-not-just-values.md): one
  nothing declares is removed.)

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
  [setup.py --configure changes every setting](setup-py-configure-changes-every-setting.md)), and
  asking only on the first run.
- For quiet runs: naming only the session's own folder (a new account has no skills linked yet,
  so it would almost never come up), and naming none.
- One map of every folder to its answer, in place of a second list: it would change a format
  already in use, by hand on each PC. That cost was later waived, and the map came with
  "local-settings.json groups its settings, and both settings files carry a version".

**Look again if:** setup gains a question that shouldn't wait for an answer.
