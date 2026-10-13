# A security bug is offered with a warning, and each PC can turn the offers off

**Decision:** the handoff skill offers a security bug as an issue candidate like any other bug,
with a warning first: a public issue tells everyone about the hole before it's fixed, and
GitHub's draft security advisories keep it private until a fix is out. Filing one by name with
`/handoff issue <item>` shows the same warning above the draft. A setting on each PC,
`offerSecurityBugs` in `local-settings.json`, `true` unless set, turns the offers off when
`false`; filing by name still works. Setup's `--configure` changes it, and `facts.py`'s new
`settings` topic reports it, in the handoff's start-up call.

**Why:**

- A security bug can be harmless, or already public, so the person decides; the warning makes
  sure they decide knowing what a public issue does.
- Some people never want them offered, so a setting, rather than an answer per item.
- In `local-settings.json` because the person chose it: it sits with dev-home-tools' other
  settings, and a change commits nothing.
- The skill learns the setting from a fact, since reading it takes no judgment (see AGENTS.md).
  The topic reads one small file: 0.08 ms at the median in 200 reads on one PC.

**Options set aside:**

- Never offering security bugs: the person couldn't choose.
- `dev-home.json`, shared by every copy: it would follow the person to every PC, at the cost of
  a commit for each change and making setup's `dev-home.json` code handle a second setting.
- A question in setup's first run: the default suits most people, and `--configure` and the
  settings list of every run by hand reach it.

**Look again if:** people set it the same way on every PC and find one they missed.
