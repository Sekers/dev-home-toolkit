# dev-home-toolkit

**dev-home** is a home base for working with AI coding agents (Claude Code and Codex): a private
GitHub repo of your own, holding what your agents should have in every session. That's your own
rules, your own skills, and anything those skills keep for you. Use it on one PC, as a private
backup with full history, or on several, each with its own copy, so all of it travels with you
from PC to PC.

**dev-home-toolkit**, this repo, is the public tooling that makes dev-home work:

- **Setup.** Its `setup.py` creates your dev-home the first time you run it, and clones it on
  your other PCs. On each PC, it connects dev-home to Claude Code and Codex, so every session
  loads your rules and skills.
- **Sync.** It keeps dev-home in sync with its online copy, so your work is backed up with its
  full history, and, if you use more than one PC, a change made on one reaches the others.
  - Setup puts dev-home on GitHub for now (just dev-home: your project repos can be hosted
    anywhere). Automated setup for GitLab, Bitbucket, and Azure DevOps is coming.
- **Privacy.** It tells every session never to copy dev-home into your project repos, or even
  mention it there, so your projects can stay public.
- **Skills.** It comes with ready-made skills, listed below, and adds any you put in your own
  dev-home to your agents too.

This repo never holds anyone's own content: that stays in each person's private dev-home.

**What's a skill?** It's like a custom command for your agent: a folder of instructions that
teaches it one task. Type its name to run it, such as `/handoff` in Claude Code or `$handoff` in
Codex, or just ask in your own words, and the agent uses the matching skill on its own. Both
agents support skills in the shared [Agent Skills](https://agentskills.io) format. To learn more,
see skills in the [Claude Code docs](https://code.claude.com/docs/en/skills) and the
[Codex docs](https://learn.chatgpt.com/docs/build-skills).

**Skills included:**

| Skill | What it does |
| --- | --- |
| [`handoff`](docs/skills/handoff.md) | Keeps one private note per project in your dev-home: what's next, what's in progress, what's waiting on you or on others, and what's left to do. Start a session with `/handoff`, and the agent picks up where the last one stopped, on any of your PCs. |
| [`knowledge`](docs/skills/knowledge.md) | Keeps your own knowledge base in your dev-home: general things you've learned about languages, programs, extensions, and AI agents, so no session has to work them out twice. Agents check it before researching or testing a general question, even partway through other work. |
| [`dev-home`](docs/skills/dev-home.md) | Syncs your dev-home with GitHub when you ask, lists each skill and whether it's added to your agents, and shows and changes dev-home-toolkit's settings, such as how often syncs check GitHub. |

Works with Claude Code, Codex, or both. Windows only, for now. To start, see
[Set up a PC](#set-up-a-pc).

## Requirements

| What | Why | Install |
| --- | --- | --- |
| Python 3.12 or later | Runs setup, the sync, updates, and the scripts the skills use. Only Python itself: nothing else to install. | The Python install manager: `winget install 9NQ7512CXL7T -e --accept-package-agreements --disable-interactivity`, then `py install 3.14` (or the latest version). |
| Git 2.31 or later | Every sync with GitHub. | `winget install --id Git.Git --source winget` |
| GitHub CLI (`gh`) | Creates or clones your dev-home on GitHub, and files issues for `/handoff issue`. | `winget install --id GitHub.cli --source winget` |
| Claude Code, Codex, or both | The agents the skills and rules are for. | Each agent's own installer. |

Open a new terminal window after installing, so the programs are on the PATH. Nothing here needs
admin rights. You start setup with the install manager's `py`, and after that the skills find
Python on their own (see [What setup changes](docs/reference/setup-changes.md)).

## Set up a PC

You clone this repo yourself. Setup then creates your dev-home on your first PC, or clones it on
later ones. Use a normal terminal window, not an administrator one.

### 1. Before setup, once per PC

1. Sign in to GitHub: `gh auth login`. Choose HTTPS, and answer yes when it asks to authenticate
   Git with your GitHub credentials. Then git can pull and push without asking, even when an
   agent runs a sync. Signed in earlier without that? Run `gh auth setup-git`.
2. Make sure git knows who you are, because the scripts commit. If git already commits on this
   PC, keep what you have. Otherwise, set at least a name and email:

   ```powershell
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```

   - To keep your email address private, use your GitHub no-reply address instead, such as
     `12345678+you@users.noreply.github.com`. GitHub shows yours under Settings > Emails.
   - If you sign your commits, leave that on. Setup turns signing off only inside dev-home, so
     a commit there never stops in the middle of a sync to ask for your signing passphrase. Your
     project repos keep signing as usual.

3. Start Claude Code once, and Codex if you use it, so their folders (`~\.claude`, `~\.codex`)
   exist. Setup skips each one whose folder is missing.

### 2. Clone this repo

Clone it into a folder near the root of a drive, where you keep your programming work, such as
`C:\Programming`. Avoid your Documents folder, which is often synced by OneDrive, and OneDrive
can corrupt a git repo. The full path can't have spaces or other characters that need quoting
(letters, digits, `.`, `_`, `-`, and `@` are fine), because setup writes it into commands as it
is. If you use a [Dev Drive](https://learn.microsoft.com/windows/dev-drive/), it's an even
better place, such as `D:\Programming`.

```powershell
gh repo clone Sekers/dev-home-toolkit C:\Programming\dev-home-toolkit
```

Cloning your own fork instead? Updates then come from it. See
[Where updates come from](docs/reference/scripts.md#where-updates-come-from) to change that.

### 3. Run setup

```powershell
py C:\Programming\dev-home-toolkit\setup.py
```

To see what it would change first, add `--what-if`. It still asks its questions, but changes
nothing.

The first run asks these, and a later run asks any whose answer isn't saved yet. dev-home comes
first, and setup saves none of your answers until it's in place:

| Question | What to answer |
| --- | --- |
| Your dev-home folder | Where your dev-home is, or should go. Press Enter for the suggestion: a `dev-home` folder next to this one, such as `C:\Programming\dev-home`. The same rules for the path apply. A folder that already has files in it must be a dev-home: setup checks for `dev-home.json`, which every dev-home has, and asks again if it's missing, so it never changes a project's repo by mistake. |
| Clone your existing dev-home (c), create a new private one (n), or stop (s)? | Only when the dev-home folder doesn't exist yet. On your first PC, `n` creates a private repo on GitHub from the files in `templates/dev-home/`. On every later PC, `c` clones it. Either way, it then asks for the repo's name; Enter accepts `dev-home`. |
| Pull updates automatically? | Enter, or `d`, follows the default, yes: new versions of this repo install as soon as a sync finds them. `n` tells you about them instead, to install yourself, and `y` keeps yes even if a later version changes the default. See [Updates](docs/reference/scripts.md#updates). |
| Set up Claude Code in this folder? | Asked once for each Claude Code folder it finds: `~\.claude`, once Claude Code has made it, and each `~\.claude-<name>`, one per extra Claude account you run with `CLAUDE_CONFIG_DIR`, including one made after your first run. Several are asked about together: Enter sets them all up, `n` none, and `e` asks about each, where Enter means yes. Each of these questions also takes `s`, to skip for now, or a number of days, such as `7`, to have setup ask again then. A yes also approves the change the folder's `settings.json` needs, which the question says first: your dev-home and dev-home-toolkit folders in `permissions.additionalDirectories`, so Claude Code can use them from any project, and in a folder other than `~\.claude`, two patterns in `claudeMdExcludes` that keep `~\.claude`'s `CLAUDE.md` and rules out of that account's sessions ([why](docs/reference/setup-changes.md)). A no is kept, so it isn't asked again. Setup sets up no folder before you answer: until you do, it leaves the folder as it is, and every sync names it in a `NEW` line, which the agent passes on, so you can answer in chat with `/dev-home configure`: set it up, no, or remind me in N days. Until a reminder's date, setup doesn't ask, and syncs don't name the folder. |
| Set up Codex in every Codex home? | Asked once, for all the Codex homes it finds: `~\.codex`, once Codex has made it, and each `~\.codex-<name>` that Codex has used, one per extra home you run with `CODEX_HOME`. Every Codex home reads the same skills, so it's all of them or none: a home made later gets the same answer, and the sync that gives it says so. A yes also approves the change each home's `config.toml` needs, which the question says first: dev-home in `writable_roots`, so Codex can write there from any project, and `project_doc_max_bytes`. Enter means yes, `s` skips it for now, and a number of days has setup ask again then, for every home together. Until you answer, setup leaves Codex as it is, and every sync names it in a `NEW` line, as for a Claude Code folder. |
| Is dev-home in active use anywhere besides this PC? | Asked on each PC's first setup, since adding a PC is when the answer most often changes, with your dev-home's answer as the default; and whenever your dev-home has no answer yet, or you've just cloned one set to a single copy. Not asked when setup has just created your dev-home. Type `y` for multi-PC mode, if another PC, virtual machine, or cloud session uses it too, and each command that syncs then checks GitHub first; or `n` for single-PC mode, if this PC is the only one, such as one replacing a PC you've retired, and syncs then check GitHub only every few hours. With no answer yet, there's no default. Setup shows the change, and after a `y` to saving it, commits and pushes `dev-home.json`, so every copy agrees. |
| Make these changes in its settings.json? | Asked for each Claude Code folder you've set up, about the settings dev-home-toolkit recommends there that you haven't answered yet: leaving Claude Code's name out of your commits and pull requests (`"attribution": false`), turning off its session quality survey (`"feedbackSurveyRate": 0`), and connecting Remote Control when each session starts (`"remoteControlAtStartup": true`). Each shows its value now and what that means. Enter changes the ones marked recommended, and keeps a value you chose yourself, such as Remote Control switched off in `/config`. `e` asks about each, and `s` and a number of days work as for a folder. A yes is written in that folder's `settings.json`, with a backup. Once you've answered, setup never asks again, and never changes the setting back. Until you answer, every sync names them in a `NEW` line, so you can answer in chat with `/dev-home configure`. |

Then it shows every setting, as `--configure` does (see below): change any, or press Enter to go
on. Once you've answered everything, it does its work: it links the skills and rules, then makes
the change each folder you said yes to needs in Claude Code's or Codex's settings (see
[What setup changes](docs/reference/setup-changes.md) for what and why), saving a dated backup
of the file first, named `settings.json.bak-YYYYMMDD-HHMMSS`. Every sync puts the change back if
it goes missing, and says so. It never edits a file it can't fully read, such as a
`settings.json` that isn't valid JSON (Claude Code can't use one either), or a read-only one; it
prints what to add by hand instead.

Setup can create or clone dev-home only on GitHub for now; automated setup for GitLab,
Bitbucket, and Azure DevOps is coming. If your dev-home is already on one of those, or on your
own git server, clone it into your dev-home folder yourself before running setup. Setup then
uses it as it is, and syncing works the same as with GitHub.

This limit applies only to where dev-home itself is hosted. Your project repos can be anywhere,
or not hosted at all, and the skills work with them the same way. The one exception is filing a
handoff item as an issue, which needs the project on GitHub.

### 4. Restart, and check

Restart Claude Code and Codex, so they load the skills and rules. Run setup again, and repeat
until it ends with "All checks passed." Then you can delete the backups.

Syncs also run setup quietly, so changes to the skills, and skills you add on another PC, reach
this one. The one exception is a skill you've just created on this PC: it's linked at the next
`/handoff`, or right away when you run setup with `--quiet` (see
[Your own rules and skills](#your-own-rules-and-skills)).

Setup keeps your answers in two places. Most belong to this PC alone, in `local-settings.json` in
your dev-home-toolkit folder, next to `setup.py`. Whether dev-home is in active use anywhere besides
this PC is shared by every copy, so it goes in your dev-home's `dev-home.json`, and setup commits
and pushes any change to it.

To change a setting later, ask your agent with [`/dev-home configure`](docs/skills/dev-home.md):
it shows you the exact change, and makes it after your yes. Or run setup with `--configure` in a
terminal:

```powershell
py C:\Programming\dev-home-toolkit\setup.py --configure
```

It shows every setting with its value, as every run of setup in a terminal does once it has
asked its questions. Type a setting's number to change it, `a` to go through them all, or press
Enter to go on; each question has your current answer as its default. Setup keeps a dated backup
of `local-settings.json` before it saves a change.

You can also edit `local-settings.json` and run setup again. Its settings are grouped, and each
one's name is its path, which `--configure` takes too:

- `devHome.folder` is your dev-home folder. To use a different one, run setup with
  `--content-dir <folder>`.
- `updates.installAutomatically` is `true` or `false` (`true` unless set).
- `updates.checkEveryHours` and `devHome.checkEveryHours` say how often a sync checks GitHub for
  dev-home-toolkit updates (24 hours unless set) and, in single-PC mode, for dev-home's changes
  (12 hours unless set), where 0 means every time.
- `rules.warnAboveKiB` is the size, in KiB, past which a sync warns, in a `LARGE` line, that your
  rules for one agent on this PC have grown (32 unless set). 0 never warns.
- `codex.instructionsMaxKiB` is how much of `AGENTS.md`, from its home and a project's folders
  together, Codex reads, in KiB (128 unless set): setup raises each Codex home's
  `project_doc_max_bytes` to match, and never lowers it. With no value there, Codex reads 32 KiB.
- `skills.<name>.addedToAgents` is whether setup adds a skill to your agents on this PC: `true`
  or `false`. Until you choose, it follows the skill's default, and setup saves it as
  `{"$state": "unanswered"}`. `dev-home` is always added, so it has none.
- A skill's preferences go under `skills` too, such as
  `"skills": {"handoff": {"preferences": {"<name>": false}}}`.
- A setting with a default can also be `{"$state": "default"}`, which follows the default even if
  a later version of dev-home-toolkit changes it, where a value you write stays as you wrote it.
  `--configure '<name>=default'` writes it for you.
- `claudeCode.folders` holds each Claude Code folder with its answer, such as
  `"~/.claude": {"setUp": true}`. Taking a folder out makes setup ask about it again, and leave it
  as it is until you answer. A folder's answers to its recommended settings go in its entry too,
  by each one's id, such as `"recommendedSettings": {"attribution-off": true}`.
- `codex.homes` holds each Codex home the same way, but every Codex home reads the same skills,
  so they all share one answer, the main home's: `~/.codex` when it's there. A sync gives any
  other home that answer, and says so, such as a new home, or one whose answer you changed by
  hand. Setup keeps the homes in order, with the main one first.
- `schemaVersion` says which layout the file has. Leave it as it is: setup sets aside a file in
  an older layout and asks its questions again.

Setup checks every value on each run. It reports one of the wrong kind without changing it, and
removes a setting nothing declares any more, such as a name misspelled in a hand edit, saying
which, after a backup of the file.

## Day to day

Run the skills in any project, in as many sessions at once as you like. Type one of a skill's
commands, which its page lists (see [Documentation](#documentation)), or ask in plain words and
the agent uses the matching skill. In Codex, type `$` instead of `/`, such as `$handoff`.

A typical day with the included skills:

1. In a project, run `/handoff`. The agent syncs your dev-home with GitHub, reads the project's
   handoff, and tells you what's next. For a project with no handoff yet, it offers to create
   one.
2. Work as usual. When you learn something worth keeping for every project, the agent may offer
   to add it to your knowledge base.
3. Before you stop, run `/handoff update`. The agent writes down where things stand, and saves
   it to GitHub so your other PCs get it.
4. Next time, on this PC or another one, `/handoff` picks up from there.

## Your own rules and skills

- **Rules.** Every session, in both agents and on every PC, loads two sets of always-on rules:
  - **Your rules**, in `rules/` in your dev-home: your own preferences, for every agent or one,
    on every PC or one. [Your rules](docs/guide/your-rules.md) says where each goes.
  - **The operating rules**, which come with dev-home-toolkit, in
    [`templates/operating-rules/operating-rules.md`](templates/operating-rules/operating-rules.md):
    how every session works with your dev-home, which the skills and scripts depend on. They're
    the same for everyone, and updates to dev-home-toolkit change them.

  Keep yours short: every line costs tokens in every session.
  - **How they load.** Setup joins the two into one file in each agent's standard place for
    always-on instructions: Claude Code's
    [user-level rules](https://code.claude.com/docs/en/memory#user-level-rules) folder, as
    `dev-home-rules.md`, and Codex's
    [global `AGENTS.md`](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
  - **Already using `~\.claude\CLAUDE.md`?** It keeps loading in Claude Code, alongside these
    rules, and setup never touches it. But only Claude Code reads it, and only for that account
    on that PC. Move anything you want everywhere into your rules, and take it out of
    `CLAUDE.md` so Claude doesn't read it twice.
  - **Already have your own `~\.codex\AGENTS.md`, or one in another Codex home?** Setup needs
    that file for the joined rules, so it leaves yours alone and reports it. Move what you want to
    keep into your rules, delete the file, and run setup again.
- **Skills.** Create `skills/<name>/SKILL.md` in your dev-home, with standard frontmatter only:
  `name` (the same as the folder, following
  [the rule for names](docs/reference/dev-home-skill-json.md#the-skills-name)), `description`, and
  optionally `allowed-tools`. Run
  `py C:\Programming\dev-home-toolkit\setup.py --quiet` to link it, and commit it (ask an agent,
  or wait for the next `/handoff` to offer). Your other PCs link it at their next
  sync. A skill can't share a name with one in this repo. Every skill is added to your agents
  unless it's marked as not recommended, or you say no on that PC, with `/dev-home configure`; a
  skill can also say what it needs to run, in a
  [`dev-home-skill.json`](docs/reference/dev-home-skill-json.md).

## What's in your dev-home

| Path | What it is |
| --- | --- |
| `handoffs/` | One handoff per project, filed by where the project is hosted (see [Handoffs](docs/skills/handoff.md#where-handoffs-are-kept)). |
| `knowledge/` | Your knowledge base. `knowledge/README.md` is its index. |
| `rules/` | Your rules: your own preferences, loaded in every session, for every agent or one, on every PC or one (see [Your rules](docs/guide/your-rules.md)). |
| `skills/` | Skills of your own, if you add any. |
| `README.md` | Notes on working in dev-home itself. |
| `AGENTS.md`, `CLAUDE.md` | The same for agents, with this PC's commands. Setup writes them on each PC, so git ignores them. |
| `dev-home.json` | Settings every copy of your dev-home shares. Setup tells a dev-home from any other folder by this file, so keep it. |
| `.drafts/` | Scratch space for text that leaves dev-home, such as GitHub issue bodies. Git ignores it. |

Setup creates it from the files in this repo's `templates/dev-home/` folder, with `dev-home.json`
and a knowledge index that has only its title. Setup never changes your files there, but puts two
kinds back when they go missing:

- **The knowledge index:** as your last commit has it, rows and all, or, when your last commit has
  none, with only its title.
- **Each `my-rules.md` setup keeps:** empty. When you rename or delete one, setup waits until that
  change is committed, so your other PCs never get an empty file in the meantime.

`AGENTS.md` and `CLAUDE.md` are setup's own: it rewrites them on every run. An edit you make to
either goes to the Recycle Bin before setup puts the file back, so put your own guidance for
agents in `rules/`.

## Documentation

Everything beyond getting started is in the `docs/` folder:

| Section | Page | What's in it |
| --- | --- | --- |
| Skills | [Handoffs](docs/skills/handoff.md) | Every `/handoff` command, with examples: when a change is committed and pushed, how issues are filed, and where handoffs are kept. |
| Skills | [Knowledge base](docs/skills/knowledge.md) | Every `/knowledge` command, and when agents check the knowledge base or offer to add to it. |
| Skills | [dev-home](docs/skills/dev-home.md) | `/dev-home sync`, `configure`, and `skills`: syncing when you ask, changing a setting, and listing your skills. |
| Guide | [Your rules](docs/guide/your-rules.md) | Where each of your rules goes, for every agent or one, on every PC or one, and how your agents get them. |
| Reference | [The scripts](docs/reference/scripts.md) | `setup.py`, `sync.py`, and `update.py`: when each one runs, what their status words mean, how updates are installed, and where they come from. |
| Reference | [What setup changes on your PC](docs/reference/setup-changes.md) | Every link, file, and setting that setup adds, why, and how to remove it all. |
| Reference | [A skill's dev-home-skill.json](docs/reference/dev-home-skill-json.md) | The file that says whether a skill is added to your agents unless you say no, what it needs to run, its preferences, and its old names. |
| Reference | [Rule files](docs/reference/rule-files.md) | The files in your dev-home's `rules/`: which join for each agent, in what order, how each is read, and their notes. |
| Development | [Design decisions](docs/development/decisions/README.md) | For people changing dev-home-toolkit: decisions made and options set aside, with the reasons. |
| Development | [Skills and everything else under templates/](docs/development/skills.md) | The rules for changing the skills, the scripts they share, the operating rules, and the files in `templates/dev-home/`. |
| Development | [setup.py, sync.py, and update.py](docs/development/scripts.md) | The rules for changing the scripts and their code in `internal/shared/`. |
| Development | [Settings](docs/development/settings.md) | The rules for adding or changing a setting, or a skill's preference. |
| Development | [Testing](docs/development/testing.md) | How the tests work, and the rules for writing them. |
| Development | [Writing the docs](docs/development/writing-docs.md) | Where each page goes, and the rules for the README and `docs/`. |
| Development | [A fresh agent's read](docs/development/fresh-agent-reads.md) | How to have a second agent, with no context, check a change. |
| Development | [Glossary](docs/development/glossary.md) | The one word for each idea in dev-home-toolkit, and the words to avoid. |
| Development | [Research](docs/development/research/README.md) | Investigations that decisions rest on: what was tested, how, when, and the results. |

## Safety and privacy

- **Your project repos are treated as public.** The operating rules tell agents never to quote
  dev-home, paraphrase its notes, or mention that it exists in a project's files, commits, PRs,
  or issues. The one way handoff content reaches a project is an issue you approve word for word.
- **No secrets in dev-home:** no credentials, tenant or account IDs, or personal information
  about anyone else. Note where a secret is kept, never its value.
- **`sync.py` commits only what it's given.** Several sessions and PCs share dev-home, so any
  other changed file may be someone's work in progress. It never stages, commits, stashes,
  resets, or discards those. It runs one sync at a time, undoes a merge that conflicts, and never
  deletes a git lock file.
- **`setup.py` replaces only its own work:** its generated files, its rules file in each agent's
  folder while that still matches what it last wrote there, links whose target is gone, and links
  it made to skills that no longer exist. Anything else in its way is reported, not changed. It
  changes an agent's settings file only in a folder you said yes to, after saying what that yes
  changes, and keeps a backup.
- **Tooling updates install themselves,** as most apps' do, unless you turn off
  `updates.installAutomatically`. Whoever controls this repo on GitHub controls code that runs on
  your PC, so turn it off if you'd rather look at each update first and install it with
  `update.py`.
- **Never run `Remove-Item -Recurse`** on `~\.claude`, `~\.claude-*`, or `~\.agents`. It follows
  the links into your dev-home and deletes what's there. Remove a single link with
  `cmd /c rmdir <link>`.
- **Edit your rules in dev-home,** in `rules/`, never in the file setup writes for each agent,
  `dev-home-rules.md` in a Claude Code folder's `rules\` or a Codex home's `AGENTS.md`, which
  setup rewrites.

## Troubleshooting

- **Setup ends with "problem(s) to fix".** Each `PROBLEM` line says what to do. Fix those, then
  run setup again.
- **`/handoff` says the operating rules aren't loaded.** Restart the agent. If it still says so,
  run setup and read its output.
- **A skill seems to be missing.** Run setup with `--quiet`, then restart the agent.
- **A skill says dev-home-toolkit needs Python.** Install Python 3.12 or later (see
  [Requirements](#requirements)), then run setup again.
- **A sync says it stopped, with `git -C ... pull --ff-only` in the line.** dev-home-toolkit's
  own code couldn't load or run, so it can't check for updates, and a fix can't arrive by
  itself. Run the two commands the line gives: they install any update by hand, then run setup.
- **A skill says it has changed since the session loaded it.** An update changed the skill's
  steps. Type its command again, such as `/handoff`, to load the new ones; you don't need a new
  session.
- **Setup reports a dev-home repo with no commits.** A setup run stopped partway through
  creating it, for example because git didn't know your name yet. If that folder holds nothing
  you need, delete it, fix the cause, and run setup again.

## Working on dev-home-toolkit

| Path | What it is |
| --- | --- |
| `setup.py`, `sync.py`, `update.py` | The scripts (see [The scripts](docs/reference/scripts.md)): short entry points that load their code from `internal/shared/`. |
| `templates/` | Everything setup fills in with each PC's paths. |
| `templates/operating-rules/` | The operating rules every session loads, before the end user's rules. Filled in on every setup run, into each agent's rules file. |
| `templates/skills/` | The skills, one folder each. Filled in on every setup run, into `internal/.generated/`. |
| `templates/shared-skill-scripts/` | Python scripts that the skills share and only agents run. Filled in on every setup run, into `internal/.generated/`. |
| `templates/dev-home/` | The files dev-home-toolkit owns in each dev-home. A new dev-home starts with them, filled in, apart from `AGENTS.md` and `CLAUDE.md`, which every setup run fills in for that PC. |
| `internal/` | dev-home-toolkit's own machinery, which nobody runs directly. |
| `internal/shared/` | The code the scripts load, one file per job: `setup.py`, `sync.py`, and `update.py`, and the modules they share, such as `git.py` and `output.py`. The skills' `prepare.py` loads it too. |
| `internal/development/` | Only for changing dev-home-toolkit: the development tools' settings (`pyproject.toml`, `uv.lock`) and the tests (`tests/`, run with pytest). People who only use dev-home-toolkit never need it. |
| `docs/` | Everything this README leaves out (see [Documentation](#documentation)). |

[AGENTS.md](AGENTS.md) has the rules for changing this repo, for developers and agents alike, and
points to a page in `docs/development/` for each area's own rules.
[Design decisions](docs/development/decisions/README.md) says why it works the way it does.

Changing dev-home-toolkit takes [uv](https://docs.astral.sh/uv/), which installs the pinned
development tools (pytest, ruff, and mypy) the first time you run them. Before committing, run
these from this folder:

```powershell
uv run --directory internal/development pytest
uv run --directory internal/development ruff check --config pyproject.toml ../..
uv run --directory internal/development ruff format --check --config pyproject.toml ../..
uv run --directory internal/development mypy
```

The development tools run from `internal/development/`, so their environment and caches stay there.
The tests check the working tree in throwaway copies under `internal/development/.test-sandbox/`,
never your real profile or dev-home, and need no network. Never point this folder's scripts at a
test dev-home: they would rewrite the files your real links depend on.

## License

MIT. See [LICENSE](LICENSE).
