# Knowledge base

These read and update the knowledge base in your dev-home. The exact steps agents follow are in
the skill itself: [`SKILL.md`](../../templates/skills/knowledge/SKILL.md).

| Command | What it does |
| --- | --- |
| `/knowledge` | Syncs your dev-home, then lists the subjects and asks what to look up or add. |
| `/knowledge <question>` | Looks it up in this PC's copy, without syncing. |
| `/knowledge add <what you learned>` | Checks that it's general, files it by the skill's rules, then commits and pushes only the files it changed: typing the command is your go-ahead. A request in plain words works the same when it's a direct instruction, such as "add this to the knowledge base: ..."; anything else gets a draft first. |

- Agents check the knowledge base before researching or testing a general question, or asking
  you to test one, even partway through other work.
- They offer a "Knowledge candidate", with its evidence, only for a finding checked in that
  session, or a pitfall agents keep hitting. Most sessions have none. The offer ends "Add it,
  commit, and push?", and nothing is added without your yes.
- A note has to help any project that uses the same program, extension, library, or service, whoever
  makes it, your own projects included. What only helps work on one project's own code stays in that
  project. When a finding is a normal docs item for a project whose docs you can change, the offer
  asks whether it goes there instead.
- Plain `/knowledge` and adding a note sync first. In multi-PC mode, when dev-home is in active
  use on several copies, such as two PCs, that sync checks GitHub every time, so the subjects
  listed and the note you add are up to date; in single-PC mode, only once 12 hours have passed,
  since nothing else changes it. See
  [How often a sync checks GitHub](../reference/scripts.md#how-often-a-sync-checks-github).
- Commits cover only the knowledge base. If the agent offers to fix a skill or an instructions
  file instead, it shows you the text first and never commits that file: the rules that cover
  that file decide that, meaning the skill that looks after it, if there is one, that repo's own
  rules, and your global rules.
- In Codex, knowledge commands edit but don't commit, for the same reason as
  [handoff commands](handoff.md). The next sync in Claude Code, such as
  [`/dev-home sync`](dev-home.md), lists the files, and offers to commit and push them once
  nobody has touched them for 15 minutes.
