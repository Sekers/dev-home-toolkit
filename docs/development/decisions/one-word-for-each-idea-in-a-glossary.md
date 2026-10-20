# One word for each idea, in a glossary

**Decision:** dev-home-toolkit uses one word for each idea, listed in the
[glossary](../glossary.md) with the words to avoid, in the format of the `domain-modeling` skill in
[mattpocock/skills](https://github.com/mattpocock/skills): each word, what it means here, and an
"Avoid" line. It covers every file, and existing text was brought in line in one sweep when it
landed. AGENTS.md's "Who's who" keeps the words for people, links to the glossary, and repeats
only the rule agents break most: "tool" never stands alone. A test in `test_docs.py` catches the
mix-ups that wording alone gives away, such as "both tools" for Claude Code and Codex. Decided by
the developer on 2026-10-17, with the words below on 2026-10-17 and 2026-10-19.

- **Agent** is the word for Claude Code, Codex, and products like them, and for the AI working in
  a session. "Agent product" is used only where a sentence must tell the two apart. The
  requirement type `tool` became `agent`, and the code's `Tool` class became `Agent`.
- **Program** is anything a shell runs by name, such as `git`, `gh`, or `jira`. The requirement
  type stays `program`. The knowledge base's test of a general finding replaced "tool" with
  "program, extension": "the same language, platform, program, extension, library, or service"
  (the developer, 2026-10-19).
- **Development tools**, written out, are what's used to work on dev-home-toolkit: pytest, ruff,
  mypy, and uv. "Tool" stays only inside names, as the glossary lists them, such as an agent's own
  tools, like Claude Code's Bash tool, and fields such as `allowed-tools`.
- **Software** is anything installed on a PC, the word for AGENTS.md's rule on installing, whose
  heading became "Installing software" (the developer, 2026-10-19).
- **Added to your agents** is a skill's state, and **set up** is a folder's, so neither "installed"
  nor "set up" is used for a skill (the developer, 2026-10-10 and 2026-10-19). The decisions
  "Setup installs skills per PC, and the tools show or hide them" and "/dev-home skills lists the
  skills dev-home sets up" were renamed
  [Setup adds skills per PC, and the agents show or hide them](setup-adds-skills-per-pc-and-the-agents-show-or-hide-them.md)
  and
  [/dev-home skills lists every skill and whether it's added](dev-home-skills-lists-every-skill-and-whether-its-added.md),
  and a skill of the end user's with a dev-home-toolkit skill's name shows as "not added".
- The glossary also holds the rules design's words, such as "built-in rule", `state`,
  `unanswered`, `summary`, `usedFor`, `urgency`, and "layout version", as the decisions that use
  them define them.

**Why:**

- "Tool" meant at least four things here: Claude Code and Codex ("both tools"), installed programs
  ("the tools are on the PATH"), the development tools, and part of the product's old name
  ([Skill requirements](../research/skill-requirements.md), "Words: tool, agent, program"). A
  misread costs an agent a wrong action or extra turns, which AGENTS.md's "Clarity for agents"
  weighs above a shorter text.
- "Agent" is the most common word for the products: AGENTS.md itself, the Agent Skills site's
  "skills-compatible agent", and most of the products' own descriptions.
- "Program" frees "tool". Most docs say "command-line tool" or "CLI", so it's a deliberate choice.
- In the knowledge base's test, the subjects such notes cover are mostly programs, beside the
  languages, platforms, libraries, and services the test already named. An editor's or a
  browser's extension isn't something a shell runs, and an end user's agent reads the test in the
  operating rules and the knowledge skill without the glossary, so "program" alone could make it
  pass over a general finding about one. "Extension" costs one word in each of those two
  always-loaded texts, and AGENTS.md's "Clarity for agents" weighs a misread above that.
- One wording for a skill's state everywhere, as the 2026-10-10 decision asked. The Skills
  summary had already changed from "3 installed" to "3 added" on 2026-10-12.
- The `domain-modeling` format is opinionated on purpose: one word for each idea, with the others
  listed to avoid. This repo already fixed two sets of words that way: the names for the developer
  and the end user, with a test, and dev-home versus dev-home-toolkit.

**Options set aside:**

- **Keeping "tool" for Claude Code and Codex:** it meant four things here.
- **"CLI" or "command-line tool" for programs:** the most common words elsewhere, but they keep
  "tool".
- **"Program" alone in the knowledge base's test:** no added words, but an end user's agent could
  read it as leaving out extensions.
- **"Software" in the knowledge base's test, in place of "tool":** no added words and broader,
  but a library is software too, so the list overlaps.
- **Keeping "tool" for software in general in that test:** the test can't tell that use from the
  ones it rules out, and "the same tool" can still be read as an agent.
- **"Installed" beside "added" for skills:** two words for one idea, though "install" is the word
  in Claude Code's and Codex's own docs.
- **"Not set up" or "not linked" for a skill of the end user's with a dev-home-toolkit skill's
  name:** "set up" belongs to folders, and "linked" names how setup works, a third word for the
  same idea.
- **A glossary with no test:** nothing would catch the words that drift back.

**Look again if:** agents keep reaching for a word the glossary avoids, which may mean it picked
the wrong one, or the agent products start calling themselves something else.
