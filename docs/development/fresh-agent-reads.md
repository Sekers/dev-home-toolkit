# A fresh agent's read

How to run a fresh agent's read of a change, which AGENTS.md's "Clarity for agents" says when to
offer; its rules apply too.

- A fresh agent is a second agent with no context from your session, walking through scenarios
  you give it. Include edge cases, a no to each question the text asks, and, for text that runs
  in both agents, how Claude Code and Codex would each handle it. For text an end user's agent
  reads, such as a skill, the operating rules, or the lines the scripts print, tell it to judge
  the text as that agent would, without AGENTS.md, which that agent never sees. Ask it what it
  would do at each step, what it could misread, and what conflicts with other rules, and to say
  "none" where nothing is wrong. Its findings aren't always right, and two reads can find
  different things, so check each one before changing anything.
- A fresh agent's tokens come on top of your own read, and depend on what it reads, so keep them
  down (see AGENTS.md's "AI usage"): give it only the changed text, the files that text refers to
  or works with, and the scenarios; ask it to read nothing else; and ask for a short report.
  Offer it once for a piece of work, when its text is ready to approve, saying what it will read
  and which model and effort you'd use (the decision
  [/handoff audit has a fresh agent check the handoff](decisions/handoff-audit-has-a-fresh-agent-check-the-handoff.md)
  has measurements of both). If your agent product can't start one, say so rather than offering
  it; if it can't set the model or effort, say which it will run on. A no covers that piece of work.
