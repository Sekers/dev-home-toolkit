# dev-home

These sync your dev-home with GitHub when you ask, list each skill and whether it's added to your
agents, and show and change dev-home-toolkit's settings. The exact steps agents follow are in the
skill itself: [`SKILL.md`](../../templates/skills/dev-home/SKILL.md).

| Command | What it does |
| --- | --- |
| `/dev-home` | Lists these commands. It runs nothing, so typing the name alone never reaches GitHub. |
| `/dev-home sync` | Syncs your dev-home with GitHub now, however many copies are in use: brings in commits from your other copies, pushes this PC's, and lists the files left uncommitted. Like every sync, it also checks for dev-home-toolkit updates and runs setup quietly. |
| `/dev-home configure` | First asks about anything setup is waiting on your answer for. Then shows every setting with its value, and changes one you choose. The agent shows you the exact change first, and makes it only after your yes. |
| `/dev-home configure <change>` | The same, starting from your change, such as `/dev-home configure check GitHub every 6 hours`. |
| `/dev-home skills` | Lists every skill, dev-home-toolkit's own and then yours, with what each is for, whether it's added to your agents on this PC, and if not, why, and any program or Python version it needs that's missing. It changes nothing, and works in Codex too. |

- **A sync commits nothing by itself.** For a file in your dev-home that nobody has touched for
  15 minutes, the agent asks whether to commit and push it. A file changed more recently may be
  another session's work in progress, so it's left alone unless you say it's yours. What the
  sync's status words mean is in [The scripts](../reference/scripts.md#what-they-report).
- **Settings change only through setup.** The agent runs `setup.py --configure` with the one
  setting you agreed on, such as `devHome.checkEveryHours=6`: first with `--what-if`, to show you the
  change, then for real after your yes. Setup checks the value, and keeps a dated backup of
  `local-settings.json`.
- **What setup is waiting on your answer for comes first:** rules it set aside from an agent's
  rules file (see [Your rules](../guide/your-rules.md#lines-in-those-files-that-setup-didnt-write)),
  an edit to your dev-home's `AGENTS.md` or `CLAUDE.md` that the Recycle Bin couldn't take, and
  the settings dev-home-toolkit recommends for a Claude Code folder that you haven't answered yet
  (see [What setup changes](../reference/setup-changes.md)). The agent asks about each one at a
  time: it shows it to you, says which of its lines your rules already have, for rules, and
  recommends an answer. For recommended settings, that's all recommended, none, each, or remind
  me in N days. Your answer is the go-ahead, so the agent runs it with no second question, and
  setup commits and pushes an answer about rules. Setup acts on it only while the file, or the
  setting, is still what you were shown.
- **A recommended setting you've answered** isn't asked about again. If you change one later in
  Claude Code's `/config`, setup leaves it as you set it, and `/dev-home configure` shows the
  value now beside your answer: ask it to set the setting again, or change your answer to no.
- **A Claude Code folder or Codex home setup has no answer for** is left as it is, and a `NEW`
  line names it on every sync until you answer: set it up, no, or remind me in N days, such as
  `/dev-home configure remind me about ~/.claude-second in a week`. Setup works out the date, and
  until then doesn't ask about the folder, and syncs don't name it. A reminder is only for a
  folder with no answer yet: one you've answered stays yes or no, and you change it the same way.
- **One setting is shared by every copy:** whether dev-home is in active use anywhere besides
  this PC. It's kept in your dev-home's `dev-home.json`, so a change to it is committed and
  pushed, and the agent's question says so. Before a switch to one copy, the agent asks whether
  your other copies are retired. After a switch to several, run `/dev-home sync` on each of the
  others.
- **The skills list reads this PC's copy,** with no sync, so a skill you added on another PC
  shows up after the next sync. One of yours with the same name as a dev-home-toolkit skill isn't
  added, and the list says so.
- **Each PC adds every skill to your agents unless you say no there,** or the skill says it
  isn't recommended; `dev-home` is always added. To change it, ask, such as
  `/dev-home configure don't add tidy on this PC`, which changes `skills.tidy.addedToAgents`. A
  skill that works only on another operating system isn't added, and one that works only in one
  agent goes only where that agent reads it. One that needs a program or a newer Python this PC
  lacks is still added, and the list says what's missing (see
  [A skill's dev-home-skill.json](../reference/dev-home-skill-json.md)). One of yours named
  `synced` is never added, since Claude Code keeps that name for the skills it downloads from
  claude.ai.
- **In Codex, `sync` and `configure` change nothing,** for the same reason as
  [handoff commands](handoff.md): on Windows, git and `gh` can't use your GitHub credentials
  there. The agent gives you the command to run in a terminal instead.
