# 0058: Skills' always-on lines

**Built:** not yet.

**Decision:** the operating rules, `templates/operating-rules/operating-rules.md`, stay one
complete file, in two parts. Not built yet.

- A general part, always loaded: what dev-home is, git there only through `sync.py`, privacy in
  project repos, where an end user's own skills go, their global rules winning, and every rule
  about something that must never happen, such as project status in auto memory, or a project's
  private details in its own files.
- One block per skill that has always-on lines, opened by a marker such as
  `<!-- skill: handoff -->`, holding only how to use that skill: for `handoff`, that project
  status and private details go in the handoff; for `knowledge`, the knowledge-candidate offer.

Setup writes each agent's rules with the general part and the block of each skill added for that
agent, and leaves the other blocks out. It turns each marker into the heading "When the
`<skill>` skill is available", worded in setup alone. Claude Code's folders still share one
generated file, and each Codex home still gets one `AGENTS.md`: skills are answered per PC, and an
agent requirement covers a whole agent
([0057: Requirements](0057-requirements.md)),
so there's one version per agent.

- A skill hidden with an agent's own switch, at any level, keeps its block, and the agent skips it
  because it can't see the skill. Setup never reads or writes the agents' switches.
- A skill an agent leaves out of its list, as Codex does when shortening descriptions isn't enough
  to fit its skills into 2% of the context window, at most 10,000 tokens, loses only its offers
  and its "use me" lines, since every protection is in the general part.
- A skill gets always-on lines only when agents must act without being asked, such as making an
  offer or keeping something out of auto memory. Everything else goes in its description or its
  steps. Only dev-home-toolkit's own skills have blocks: an end user's own rules go in their global
  rules. `docs/development/skills.md` says so.
- Tests check that each agent's rules hold the block of each skill added for it and no other,
  that every marker names a skill that exists, and that the heading "Private repo: dev-home
  (rules loaded)" stays first, since the handoff skill checks for it.

**Why:** the rules held lines about `handoff` and `knowledge` when every PC had every skill. Once
skills are a choice per PC
([0035: Skills per PC](0035-skills-per-pc.md)),
and the agents can hide a skill per account or project, those lines can send an agent toward a
skill it doesn't have. It may then improvise, such as writing a work project's status into
dev-home in an account where `handoff` is hidden, which is what hiding it was meant to prevent.
Leaving a block out where its skill isn't added saves its words, and the heading covers hiding by
any switch for about 6 words a block. One complete file keeps the rules easy to read whole after
a change, as AGENTS.md's "Clarity for agents" asks, and the marker is the kind the planned shared
skill text uses
([0012: Shared skill text](0012-shared-skill-text.md)).
Measured on 2026-10-16: the rules are 317 words, about 150 general, 50 for `handoff`, and 117 for
`knowledge`.

**Options set aside:**

- Leaving it as it is: lines about a hidden skill load in every session there, and can lead an
  agent to do that skill's job without its rules.
- Answering skills per account instead of per PC: the questions multiply, Codex can't do it,
  since every Codex home reads `~/.agents/skills`, and it reverses the split in which
  dev-home-toolkit decides what a PC has and the agents decide what each account shows.
- Setup reading the agents' switches and leaving a hidden skill's lines out: Claude Code's
  `/skills` menu writes its switch to the project's `.claude/settings.local.json` (its settings
  reference, read 2026-10-07), which setup can't see, so the most common way of hiding a skill
  would still leave its lines. It also needs a rules file per account, and the most code.
- One sentence in the general part, telling agents to skip the lines of any skill they don't
  have: about 25 more words in every session, and unused lines still load.
- Leaving blocks out where a skill isn't added, with no heading: a skill hidden with an agent's
  switch still has its lines applied.
- Moving the lines into each skill's description: both agents shorten or drop descriptions when
  they have many skills, so rules there aren't reliable.
- A file of lines in each skill's folder, which setup assembles: the rules stop being one file to
  read whole, and the file is linked into the agents with the skill.

**Changed on 2026-10-18,** not built yet, with the reasons in
[0064: Each agent's rules file](0064-each-agents-rules-file.md):
each Claude Code folder gets a file of its own, which setup writes in its `rules\` in place of the
links, so the one generated file every Claude Code folder shared goes. Each agent's file joins the
operating rules, with the blocks of the skills added for that agent, and the end user's rules for
that agent on that PC. The blocks, their heading, and the tests work as above.

**Look again if:** many skills need always-on lines, or an agent starts loading rules per skill.
