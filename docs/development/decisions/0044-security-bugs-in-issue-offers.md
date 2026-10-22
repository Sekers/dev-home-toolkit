# 0044: Security bugs in issue offers

**Built:** yes.

**Decision:** the handoff skill offers a security bug as an issue candidate like any other bug,
with a warning first: a public issue tells everyone about the hole before it's fixed, and
GitHub's draft security advisories keep it private until a fix is out. Filing one by name with
`/handoff issue <item>` shows the same warning above the draft.

- A security bug is one that could let someone else read, change, or do what they shouldn't, or
  stop it working with crafted input: such as a leak of private data or secrets, an injection
  (including text that steers an AI agent), or a way around a sign-in or a permission check.
  When the agent is unsure whether an item is one, it offers the item with the warning, and says
  it may be a security bug, even while security bugs are left out of offers.
- Each PC has a preference, declared in the handoff skill's `dev-home-skill.json` and saved as
  `skills.handoff.preferences.includeSecurityBugsInIssueOffers`, `true` unless set. Its label is
  "Include security bugs in GitHub issue offers", and its help "Whether the handoff skill
  includes security bugs in its GitHub issue offers, with a warning first. Other items are
  offered either way, and nothing is filed without your yes." Turned off, it leaves security
  bugs out of offers; filing by name still works. `--configure` changes it, as
  [0049: Answers in the settings](0049-answers-in-the-settings.md) says.
- The skill learns it from `facts.py`'s `preferences` topic, in its start-up call. The topic
  prints only the running skill's preferences, by name, with this PC's values.
- After a security bug's warning, and before the offer's question, the agent says: "Don't want
  security bugs offered? Turn off "Include security bugs in GitHub issue offers" with
  `/dev-home configure`. Other offers continue." That's how the preference reaches end users who
  never run setup by hand, and a new preference gets no `NEW` line.

**Why:**

- A security bug can be harmless, or already public, so the end user decides; the warning makes
  sure they decide knowing what a public issue does.
- Some people never want them offered, so a preference, rather than an answer per item.
- "Someone" alone let an agent flag a bug that only hurts the end user's own work as a security
  bug. Crafted input and text that steers an agent were missing, and both are common ways in.
- Treating an item the agent is unsure about as a security bug would hide it while the
  preference is off. Offering it with the warning, saying it may be one, leaves the end user to
  judge, and the offer is already the question, so there's no separate one.
- A preference that's fine at its default would make a `NEW` line on every sync for nothing. The
  line beside each offer reaches end users exactly when it matters.
- The label names one part of the offers, so a no leaves the other offers alone. It follows
  Microsoft's guidelines for on/off labels on Windows: say what "on" does, in positive words.
- In `local-settings.json`, per PC, because the end user chose it: it sits with dev-home-toolkit's
  other settings, and a change commits nothing.
- The skill learns the preference from a fact, since reading it takes no judgment
  ([skills.md](../skills.md)). The topic reads two small files: 0.14 ms at the median in 200
  runs on one PC.

**Options set aside:**

- Never offering security bugs: the end user couldn't choose.
- `dev-home.json`, shared by every copy: it would follow the end user to every PC, at the cost of
  a commit for each change, and setup's `dev-home.json` code handling a second setting.
- A question in setup's first run: the default suits most people, and the menu and the line
  beside each offer reach it.
- A `NEW` line for the new preference: it would come on every sync.
- The setting as a key of its own at the top of `local-settings.json`: a skill's preferences
  belong to the skill, declared beside it, and every skill's go through the same reader.
- A topic named `settings`: it suggested settings in general, such as the check intervals, which
  the topic doesn't print.

**Look again if:** people set it the same way on every PC and find one they missed.
