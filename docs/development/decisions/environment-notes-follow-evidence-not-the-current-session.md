# Environment notes follow evidence, not the current session

**Decision:** an environment subsection says where a fact applies, not which session owns the
text. A session may edit any environment's subsection only when it has reliable evidence about
that environment: direct inspection, a fact from the end user, output from there, or a project-wide
change that makes an item plainly obsolete. Facts learned locally belong to the current
environment by default, and a session never infers one environment's state from another.

**Why:** limiting a session to its current environment prevents guesses about another one, but
it also blocks corrections the end user supplies, facts checked through a remote tool, retiring or
renaming an environment, and removal of notes that a project-wide change made obsolete. The
source of the evidence is the useful safety boundary; the session's location is not.

**Options set aside:**

- Let a session edit only its current environment: safe against cross-environment guesses, but
  leaves known errors and stale notes in every other subsection.
- Let a session edit any environment on judgment alone: easier cleanup, but no boundary keeps a
  fact observed in one environment from being copied to another.

**Look again if:** the evidence rule proves too broad or too narrow in real handoff updates.
