# Decisions

One file per design decision, numbered oldest first and named for its subject, such as
`0054-removing-what-setup-set-up.md`, titled `# 0054: Removing what setup set up`
([why](0081-writing-decisions.md)). Read a decision before reopening a question. Research a
decision rests on has a page of its own in [research/](../research/README.md).

## The format

- **Built:** first: `yes`, `not yet`, `nothing to build` (a decision not to do something), or
  `yes, except: <what isn't built yet>`. A replaced decision has **Replaced by:** and a link in
  its place.
- **Decision:** the current rule, ending with who decided it and when, and `changed on <date>`
  for each change.
- Then, each only when it adds something: **Why**, **Costs**, **Options set aside** (each with
  why it wasn't taken), and **Look again if**.

To change a decision, edit its file: the Decision says the current rule, Why gives the current
reasons, Options set aside gains anything newly set aside, with why, and the Built line says what
the code does. The commit message says what changed and why, and git keeps the old text. A new
file is only for a new subject. When part of a decision moves to another, remove it from the old
file and link to the new one.

## All decisions

- [0001: Plugins](0001-plugins.md)
- [0002: Hand edits to generated files](0002-hand-edits-to-generated-files.md)
- [0003: Scripts the skills share](0003-scripts-the-skills-share.md)
- [0004: Commands per call](0004-commands-per-call.md)
- [0005: Starting a skill command](0005-starting-a-skill-command.md)
- [0006: Commands as a skill loads](0006-commands-as-a-skill-loads.md)
- [0007: The State line's commit](0007-the-state-lines-commit.md)
- [0008: Environment notes](0008-environment-notes.md)
- [0009: Moving from PowerShell to Python](0009-moving-from-powershell-to-python.md)
- [0010: Python for the skills](0010-python-for-the-skills.md)
- [0011: Folders for shared skill files](0011-folders-for-shared-skill-files.md)
- [0012: Shared skill text](0012-shared-skill-text.md)
- [0013: Telling a session its skill changed](0013-telling-a-session-its-skill-changed.md)
- [0014: Supported versions of Claude Code and Codex](0014-supported-versions-of-claude-code-and-codex.md)
- [0015: Test framework](0015-test-framework.md)
- [0016: The root](0016-the-root.md)
- [0017: Command-line options](0017-command-line-options.md)
- [0018: One sync at a time](0018-one-sync-at-a-time.md)
- [0019: Updates that fix a broken step](0019-updates-that-fix-a-broken-step.md)
- [0020: Setup when shared code changed](0020-setup-when-shared-code-changed.md)
- [0021: Folder links](0021-folder-links.md)
- [0022: Active copies](0022-active-copies.md)
- [0023: The order of a sync's push](0023-the-order-of-a-syncs-push.md)
- [0024: Checking GitHub](0024-checking-github.md)
- [0025: Setup's questions](0025-setups-questions.md)
- [0026: setup.py --configure](0026-setup-py-configure.md)
- [0027: Saving settings files](0027-saving-settings-files.md)
- [0028: Reading Claude Code's settings](0028-reading-claude-codes-settings.md)
- [0029: The dev-home skill](0029-the-dev-home-skill.md)
- [0030: /dev-home skills](0030-dev-home-skills.md)
- [0031: Checking issue links](0031-checking-issue-links.md)
- [0032: Recommended settings](0032-recommended-settings.md)
- [0033: Prompts for optional lists](0033-prompts-for-optional-lists.md)
- [0034: Runs of setup by hand](0034-runs-of-setup-by-hand.md)
- [0035: Skills per PC](0035-skills-per-pc.md)
- [0036: New items](0036-new-items.md)
- [0037: Extra Codex homes](0037-extra-codex-homes.md)
- [0038: Recommended settings from chat](0038-recommended-settings-from-chat.md)
- [0039: What the knowledge base takes](0039-what-the-knowledge-base-takes.md)
- [0040: Answers to offers](0040-answers-to-offers.md)
- [0041: What a handoff update reviews](0041-what-a-handoff-update-reviews.md)
- [0042: /handoff audit](0042-handoff-audit.md)
- [0043: Issue candidates](0043-issue-candidates.md)
- [0044: Security bugs in issue offers](0044-security-bugs-in-issue-offers.md)
- [0045: Closed issues](0045-closed-issues.md)
- [0046: Settings files' layout and versions](0046-settings-files-layout-and-versions.md)
- [0047: What AGENTS.md holds](0047-what-agents-md-holds.md)
- [0048: Status words](0048-status-words.md)
- [0049: Answers in the settings](0049-answers-in-the-settings.md)
- [0050: Testing scripts that only report](0050-testing-scripts-that-only-report.md)
- [0051: Automatic updates](0051-automatic-updates.md)
- [0052: Codex homes](0052-codex-homes.md)
- [0053: What a folder's yes approves](0053-what-a-folders-yes-approves.md)
- [0054: Removing what setup set up](0054-removing-what-setup-set-up.md)
- [0055: Keys and answers in prompts](0055-keys-and-answers-in-prompts.md)
- [0056: Checking the knowledge index](0056-checking-the-knowledge-index.md)
- [0057: Requirements](0057-requirements.md)
- [0058: Skills' always-on lines](0058-skills-always-on-lines.md)
- [0059: Release branches](0059-release-branches.md)
- [0060: The release data file](0060-the-release-data-file.md)
- [0061: How skills run programs](0061-how-skills-run-programs.md)
- [0062: Keeping a skill off](0062-keeping-a-skill-off.md)
- [0063: The product's name](0063-the-products-name.md)
- [0064: Each agent's rules file](0064-each-agents-rules-file.md)
- [0065: Where end users' rules live](0065-where-end-users-rules-live.md)
- [0066: Notes in rule files](0066-notes-in-rule-files.md)
- [0067: Built-in rules](0067-built-in-rules.md)
- [0068: Versions and layouts in dev-home](0068-versions-and-layouts-in-dev-home.md)
- [0069: Dropped text](0069-dropped-text.md)
- [0070: Who owns each file in dev-home](0070-who-owns-each-file-in-dev-home.md)
- [0071: The knowledge index](0071-the-knowledge-index.md)
- [0072: Fields in skill and rule files](0072-fields-in-skill-and-rule-files.md)
- [0073: Agents added later](0073-agents-added-later.md)
- [0074: Instructions in other Claude Code folders](0074-instructions-in-other-claude-code-folders.md)
- [0075: Glossary](0075-glossary.md)
- [0076: A PC catching up](0076-a-pc-catching-up.md)
- [0077: Which Python setup uses](0077-which-python-setup-uses.md)
- [0078: VS Code settings](0078-vs-code-settings.md)
- [0079: Old test sandboxes](0079-old-test-sandboxes.md)
- [0080: Compatibility before 1.0.0](0080-compatibility-before-1-0-0.md)
- [0081: Writing decisions](0081-writing-decisions.md)
- [0082: markdownlint's rules](0082-markdownlints-rules.md)
- [0083: The PC's name](0083-the-pcs-name.md)
- [0084: dev-home's commit history](0084-dev-homes-commit-history.md)
