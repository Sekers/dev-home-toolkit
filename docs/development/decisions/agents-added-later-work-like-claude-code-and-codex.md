# Agents added later work like Claude Code and Codex

**Decision:** any agent dev-home-toolkit adds support for later, such as Gemini CLI, works the way
Claude Code and Codex do. Not built yet: no agent is planned. Decided by the developer on
2026-10-18.

- Setup asks before setting up its folders, and saves the answers per PC.
- Skills are linked into the folders it reads skills from.
- Its rules go into one file setup writes in its own folder, joined from the end user's rules in
  dev-home
  ([Each agent gets its rules as one file setup writes in its own folder](each-agent-gets-its-rules-as-one-file-setup-writes-in-its-own-folder.md)).
- It gets a `rules/<agent>/` folder in dev-home, named as in `supportedOn` and following the naming
  rule in [Skill and rule files share their fields](skill-and-rule-files-share-their-fields.md).
- A no for one of its folders removes what setup owns there.
- Everything not limited to an agent reaches it once the end user says yes: rules in
  `_all-agents/`, and skills with no `agent` entry, built-in ones included.
- An agent that can't take part of this, such as one whose global rules aren't kept in a file, is
  supported for what it can take, and the docs say what's missing.
- A page in `docs/development/` lists the developer's steps:
  - check every built-in skill and rule in the new agent, and give an `agent` limit to any that
    won't work there
  - add the settings lines it needs to pre-approve commands
  - update AGENTS.md's list of supported agents,
    [Only the latest versions of Claude Code and Codex](only-the-latest-versions-of-claude-code-and-codex.md),
    the docs, and the tests

**Why:** every agent works the same way, so end users learn it once, and adding one is mostly
following steps. Since setup asks before setting up a new agent's folders, nothing reaches it
without the end user's yes.

**Options set aside:** designing each agent's setup when it's added: each would fit its agent
exactly, but agents would end up working differently, and every addition would need its own round
of decisions.

**Look again if:** an agent is added whose way of loading skills or rules fits none of this.
