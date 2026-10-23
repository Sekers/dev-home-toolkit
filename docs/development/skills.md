# Skills and everything else under templates/

The rules for changing anything under `templates/`: the skills, the scripts they share, the
operating rules, and the files in `templates/dev-home/`, and for adding a script anywhere.
AGENTS.md points here; its rules apply too.

## Where things go

- Where a script goes depends on who runs it. The only scripts in the root are the ones a person
  may run by hand; agents run those too. A script that only agents run goes under
  `templates/`: in its skill's folder when one skill uses it, and in
  `templates/shared-skill-scripts/` when skills share it. The same goes for anything else a
  skill has: one skill's in its own folder, and what several skills share in a
  `templates/shared-skill-*` folder for its kind.
- `templates/dev-home/` holds only files dev-home-toolkit owns in a dev-home, which a new one
  starts with
  ([0070: Who owns each file in dev-home](decisions/0070-who-owns-each-file-in-dev-home.md)).
  An end user's own file, such as the knowledge index or a `my-rules.md`, never goes there:
  setup's code creates it when it's missing. Until the version check of decision 0070 is built, a
  change to a committed file there reaches only new dev-homes.

## Templates, generated files, and names

- Every file under `templates/` is a template: setup replaces these placeholders with
  forward-slash absolute paths.
  - `{{TOOLKIT_DIR}}`: this repo's folder on that PC.
  - `{{CONTENT_DIR}}`: that person's dev-home folder.
  - `{{SKILL_DIR}}`: the skill's own folder under `internal/.generated/skills/` (skills only).
  - `{{SHARED_SKILL_SCRIPTS_DIR}}`: the shared scripts' folder,
    `internal/.generated/shared-skill-scripts/`.
  - `{{PYTHON}}`: `internal/.python/python.exe` in this repo's folder, the Python the scripts
    run with. `internal/.python/` is a junction setup makes to a Python 3.12 or later, so the
    path is short, has no spaces, and is the same on every PC.
  - `{{SKILL_STAMP}}`: the skill's stamp, a fingerprint of its `SKILL.md` (skills only). See
    "Skills" below.
- `templates/skills/` and `templates/shared-skill-scripts/` are filled in on every setup run and
  written to `internal/.generated/`, at the same paths. The skills there are what gets linked into
  the agents, and the skills run the shared scripts from there. `templates/operating-rules/` is
  filled in on every setup run too, but goes straight into each agent's rules file (see
  "Operating rules", below). `templates/dev-home/` has no copy there either: setup fills it in
  only for a new dev-home. Python adds `__pycache__` folders there when the scripts
  run, and setup leaves those, and any link, alone.
- A file and its folder keep the same name at every stage: template, generated copy, and link,
  such as `skills/handoff/SKILL.md`.
- Pre-approvals in `allowed-tools` match the literal command text, so write every command with a
  placeholder where the path goes, never a variable or `~`. After setup fills it in, the command
  in the steps and the pre-approval match exactly.

## Skills (templates/skills/)

- Frontmatter uses only standard fields: `name`, `description`, and `allowed-tools`. The name
  matches the folder name, and follows the rule for names in
  [0072: Fields in skill and rule files](decisions/0072-fields-in-skill-and-rule-files.md)
  (a test checks).
- A skill's preferences, declared in a `dev-home-skill.json` in its folder, follow
  [settings.md](settings.md). What it needs to run goes in the same file, as `supportedOn` and
  `dependsOn`
  ([0057: Requirements](decisions/0057-requirements.md)).
  A test reads each skill's file, and fails at anything the reader can't use, or doesn't know.
  [A skill's dev-home-skill.json](../reference/dev-home-skill-json.md) describes every field.
  Only `dev-home` declares `alwaysAddedToAgents`, since every PC needs it to change its answers
  in chat.
- A field in `dev-home-skill.json` never changes meaning: a new meaning gets a new name, so the
  file needs no version number.
- To rename a skill, rename its folder and its `name`, and add the old name to `formerNames` in
  its `dev-home-skill.json`: each PC's setup moves the old name's answers to the new one, and
  removes the old name's links. Codex records a skill turned off by its path,
  `internal/.generated/skills/<name>`, so a skill keeps that path while its name stays the same,
  added to the agents or not (a test checks). To remove a skill, delete its folder: each PC's
  setup removes its links, and its next sync deletes its answers. Never give a new skill a
  removed one's name: a PC that gets both changes in one update would give the new skill the old
  one's answers.
- Refer to a skill's own files through `{{SKILL_DIR}}`, to a shared script through
  `{{SHARED_SKILL_SCRIPTS_DIR}}`, and to anything else through `{{TOOLKIT_DIR}}` or
  `{{CONTENT_DIR}}`.
- Run a shared script as `{{PYTHON}} -I {{SHARED_SKILL_SCRIPTS_DIR}}/<script>.py`, followed by
  `--skill <the skill's name> --stamp {{SKILL_STAMP}}` and its own arguments. Setup stamps each
  skill with a fingerprint of its `SKILL.md`, and the script compares the stamp it's given with
  the one on disk, so a session following steps that have changed since it loaded them is told
  to stop. Every skill command that syncs starts with `prepare.py`. Tests check all of this.
- Run a script in the skill's own folder as `{{PYTHON}} -I {{SKILL_DIR}}/<script>.py`. It takes
  no stamp when it runs only after the skill's start-up command, which has just checked it.
  The shared scripts' rules for code apply to it too: Python 3.12 or later, the standard library
  only, and ASCII only (tests check both).
- Write steps in plain language, and write commands exactly as they will be run, with
  forward-slash paths, so they work in Git Bash, PowerShell, and Codex.
- Leave commands that publish outside dev-home, such as `gh issue create`, out of
  `allowed-tools`. Whether they ask first is each person's choice, in their own settings.
- Give each command both a `Bash(...)` and a `PowerShell(...)` pre-approval, as the Python
  commands and `gh issue list` have (a test checks the Python ones). Add no command that starts
  PowerShell (`pwsh`): dev-home-toolkit doesn't need it, and Claude Code's PowerShell tool asks
  before running any command that starts another PowerShell, even one a `PowerShell(...)` rule
  matches exactly (a test checks the generated skills).
- Each skill stands on its own. Mention another skill only where that's part of how this one
  works.
- A skill's rules for when it may change, commit, and push live in that skill, not in the
  operating rules or an end user's own rules.
- Some skills have similar rules. When you change a rule in one skill, check whether another skill
  has a similar rule that might need the same change. That it does is never a given: decide from
  how each skill works.
- After changing a skill, read it as AGENTS.md's "Clarity for agents" says, looking for anything
  an agent could misread or slip through: two rules that disagree, a question whose answer is
  unclear, a step the scripts can't do, or wording that only fits Claude Code.
- Every question that offers something a person can take or turn down uses the answers in
  [0040: Answers to offers](decisions/0040-answers-to-offers.md). To depart from them,
  ask the developer first, then add the departure and its reason to that decision.
- When you propose a commit that changes a skill's `SKILL.md`, say in chat about how many words
  it gained or lost.
- A skill that starts a second agent, as `/handoff audit` does, tells the end user before it
  starts, since that agent's tokens come on top of the session's.
- The handoff template has no line pointing agents to the handoff skill; the operating rules do
  that, in every session.

## Scripts the skills share (templates/shared-skill-scripts/)

- These are scripts that only agents run, and that more than one skill may run. Skills point to
  the one generated copy; never copy a script into each skill's folder.
  [0003: Scripts the skills share](decisions/0003-scripts-the-skills-share.md)
  says why, and why they aren't at the root or in `internal/`.
- One job per script, named for the job. `facts.py` reports facts about where a session is
  running, one topic at a time. `prepare.py` prepares dev-home for a skill command: it runs the
  sync inside its own process, checks the skill's stamp, then prints the facts for the topics
  it's given.
- Every skill command that syncs starts with `prepare.py`, so the agent gets everything it needs
  before its own work in one call. Anything a skill needs at that point that takes no judgment
  goes in the scripts, not in steps for the agent. `prepare.py` always exits 0 and says
  everything in its lines, and it never commits: skills commit through `sync.py --message`.
- `facts.py` only reports, and only from this PC: it changes nothing and never uses the network.
  That's what makes it safe to pre-approve. The tests read its code, and watch it as it runs (see
  [0050: Testing scripts that only report](decisions/0050-testing-scripts-that-only-report.md)).
  Adding a name to what it may use (`REPORTING_NAMES`, `REPORTING_METHODS`, or
  `REPORTING_ATTRIBUTES` in `internal/development/tests/helpers.py`) is a safety change: say so
  in the commit. Anything a skill needs done, rather than told, goes
  in a script of its own.
- `prepare.py` loads `facts.py` into its own process, after a sync that may have brought in a
  newer `facts.py` than the `prepare.py` already running. So keep the names and arguments of
  what `prepare.py` calls there, and `facts.py` changes nothing the whole process shares, such as
  environment variables or the current folder, outside its `__main__` block (a test checks).
- Python 3.12 or later, the standard library only, and ASCII only (tests check both). Both
  scripts write UTF-8, and read git's output as UTF-8, so an accented letter reaches the agent as
  it is. They find a program such as git by its full path in `PATH`, never in the current folder,
  which is a project's.
- A topic's lines are what skills build on. Add a topic freely: it costs nothing until a skill's
  command asks for it, and that's the change to ask the developer about (AGENTS.md's "AI
  usage"). Change or remove a line only after reading every skill that asks for its topic.
- Each script's description has a "Called by:" line naming the skills that run it. Read those
  skills before changing what the script takes or prints, and update the line when a skill starts
  or stops running it. A test compares the line with the skills.
- A skill writes each command in full, with fixed arguments, and pre-approves that exact text,
  never a wildcard. A test checks that the two match.

## Operating rules (templates/operating-rules/operating-rules.md)

- These are the rules every session follows so that a person's dev-home and this tooling work
  together: the same for everyone, and not theirs to edit.
- Keep the first heading, "Private repo: dev-home (rules loaded)". The handoff skill checks for
  it.
- Only rules the skills and scripts depend on belong here. Personal preferences go in each end
  user's own rules, in `rules/` in their dev-home, which load after these.
- Setup joins the two into one file for each agent: `dev-home-rules.md` in each Claude Code
  folder's `rules/`, and `AGENTS.md` in each Codex home
  ([0064: Each agent's rules file](decisions/0064-each-agents-rules-file.md)). Keep the operating
  rules short: they load in every session.
- Codex's own `~/.codex/rules/` holds command policies, not these, and setup never touches it.
