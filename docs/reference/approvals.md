# Commands that run without asking

The skills run dev-home-toolkit's own scripts many times a day, such as a sync at the start of
each skill command and a commit after each change to your dev-home, so your agents run them
without a permission prompt each time. Filing a GitHub issue is the one exception: it asks
first, unless you allow it yourself. Claude Code and Codex get there in different ways,
described below.

"Without asking" here means no permission prompt from Claude Code or Codex. The skills still
ask for your yes wherever their own steps say to, such as before saving a draft.

## Which commands

| Command | Claude Code | Codex |
| --- | --- | --- |
| dev-home-toolkit's scripts, with any arguments: `setup.py`, `sync.py`, `prepare.py`, `facts.py`, and the handoff skill's `issue_status.py` | Without asking, while a skill that runs it is in use | Without asking, outside its sandbox, in every session |
| `gh label list` and `gh issue list`, which only read | Without asking, while the handoff skill is in use | Without asking, outside its sandbox, in every session |
| `gh issue create`, which files a public issue | Asks first | Asks first, to run it outside its sandbox |
| Any other command | As your own settings say | As your own settings and rules say |

## Why filing an issue asks first

It's the only command the skills run that publishes. An issue is public, the repo's watchers are
notified at once, and it can't really be taken back. It may also be drafted from your private
handoff. The handoff skill already shows you the draft and waits for your yes, but only the agent
enforces that. The approval prompt is a second check, made by Claude Code or Codex itself, which
holds even if the agent misreads your reply, or is steered by text it has read, such as other
people's comments on an issue.

To file issues without the prompt, allow the command yourself:

- **Claude Code:** add `Bash(gh issue create *)` and `PowerShell(gh issue create *)` to
  `permissions.allow` in the `settings.json` of each Claude Code folder you use, such as
  `~\.claude\settings.json`.
- **Codex:** add `prefix_rule(pattern = ["gh", "issue", "create"], decision = "allow")` to a rules
  file of your own in each Codex home's `rules\` folder, such as `rules\default.rules`, where
  Codex saves the rules you approve with "always allow". Not to `dev-home-toolkit.rules`, which
  setup rewrites. Then restart Codex.

## Claude Code

Each skill lists the commands it may run without asking in the `allowed-tools` line of its
`SKILL.md`: each script it runs, by name, alone and with any arguments. Claude Code applies that
list only while the skill is in use, so the same command at any other time asks, or not, as your
own settings say. Setup writes no permission into your settings for this.

## Codex

Codex can't take approvals from a skill, so setup writes them as Codex command rules, in
`rules\dev-home-toolkit.rules` in each Codex home you said yes to (see
[What setup changes](setup-changes.md)). An `allow` rule makes Codex run the command outside its
sandbox, as you, without asking. That matters because on Windows, a command inside Codex's
sandbox can't reach GitHub with your sign-in, so a sync, or the push after a commit, would fail
there.

Codex's rules differ from Claude Code's approvals in these ways:

- **They apply in every Codex session,** in every project, not only while a skill is in use.
- **Codex reads them only when it starts,** so restart Codex when setup says it wrote or changed
  the file.
- **They cost a little in every session.** In each session where Codex can ask you for approval,
  as it does by default, it lists every `allow` rule, yours included, in the instructions it gives
  the model. dev-home-toolkit's rules take about 200 to 250 tokens of each such session.
- **Codex matches a rule only when it can take the command apart into plain words.** A command it
  can't, such as one with a `$` in double quotes, runs inside its sandbox instead, where a sync
  fails. That's
  why your dev-home-toolkit and dev-home folder paths can hold only letters, digits, `.`, `_`,
  and `-`, and why the skills keep `$` and backticks out of commit messages.
- **Filing an issue takes your approval in Codex's own prompt.** The agent requests to run
  `gh issue create` outside the sandbox, and Codex asks you. If you set Codex never to ask for
  approval, it can't file issues at all, since the command fails inside the sandbox.

## Modes that skip every prompt

Claude Code's bypass permissions mode, and Codex with its sandbox off (full access), run every
command without asking, filing an issue included. That comes with the mode you choose, not with
dev-home-toolkit. The handoff skill still shows you an issue's draft and waits for your yes.
