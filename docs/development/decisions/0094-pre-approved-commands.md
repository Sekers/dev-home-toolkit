# 0094: Pre-approved commands

**Built:** yes, except: Claude Code's pre-approvals by each script's name, since the skills still
pre-approve each command word for word; and the skills' steps for Codex, which still skip every
sync, commit, and `gh` command.

**Decision:** an agent runs each of dev-home-toolkit's scripts without asking, by the script's
name, with any arguments, in Claude Code and in Codex, with no exceptions.

- Claude Code: each skill's `allowed-tools`, which applies while that skill runs.
- Codex: it reads only `name`, `description`, and `metadata.short-description` from a skill, so a
  skill can't carry its pre-approvals there. Its command rules can. Setup writes
  `rules/dev-home-toolkit.rules` in each Codex home answered yes, from
  `templates/per-agent/codex/rules/dev-home-toolkit.rules`, with one `allow` rule for each script,
  as `{{PYTHON}} -I <script>`, and one for each other command the skills pre-approve, by the
  words before its wildcard: `gh label list` and `gh issue list`. An `allow` rule runs the command
  outside Codex's sandbox, as the end user, so git and `gh` can use their GitHub sign-in.
  `gh issue create` gets no rule, so Codex asks first, as Claude Code does. A test checks that the
  rules and the skills' pre-approvals cover the same commands.
- A Codex rule applies in every Codex session, not only while a skill runs: Codex has no way to
  tie one to a skill.
- The yes to Codex approves the file, as it approves the change in each home's `config.toml`
  ([0053: What a folder's yes approves](0053-what-a-folders-yes-approves.md)), and the
  explanation before the question says so: "It also writes rules/dev-home-toolkit.rules in each
  Codex home, so Codex runs dev-home-toolkit's own commands, such as its syncs, outside its
  sandbox, where your GitHub sign-in works." A no removes it
  ([0054: Removing what setup set up](0054-removing-what-setup-set-up.md)).
- Every run of setup, quiet ones included, writes the file when it's missing or differs, and says
  so, adding "Restart Codex to load the change.", since Codex reads rules only when it starts. An
  update that changes the template reaches Codex that way, with no question, just as an update
  brings Claude Code a skill's new pre-approvals.
- A hand edit goes to the Recycle Bin, then setup writes its own file again. While the bin can't
  take it, the file stays as edited, named in a `PROBLEM` line on every run. In a home answered
  no, setup removes the file once the bin has any hand edit to it. A file of that name with other
  text, which setup has no copy of, isn't setup's, and stays.
- `templates/per-agent/<agent>/` holds the files setup writes into only that agent's folders, the
  agent named as `supportedOn` names it, each at the path it lands at in each of those folders.
  What every agent gets, such as the skills and the operating rules, stays where it is.

Decided by the developer on 2026-11-18.

**Why:**

- On Windows, Codex's default sandbox runs commands as a separate account, `CodexSandboxOffline`
  or `CodexSandboxOnline`, which can't use the end user's Git Credential Manager or `gh` sign-in.
  So the skills skipped every sync, commit, push, and `gh` step in Codex, and a PC with only Codex
  never synced. Measured on 2026-11-18: an `allow` rule ran `sync.py` outside the sandbox, and its
  fetch of a private repo worked, in the Codex CLI 0.170.0, through `codex exec` with the VS Code
  extension's bundled 0.169.0-alpha.11.1, and in a chat in the desktop app 26.1111.9265.0, while
  `whoami` in the same sessions ran in the sandbox. `codex execpolicy check` matched the filled-in
  template's rules to the skills' commands, and matched nothing for `gh issue create`.
- From Codex's docs and source: its
  [rules page](https://learn.chatgpt.com/docs/agent-configuration/rules.md) says `allow` means
  "Run the command outside the sandbox without prompting", and that Codex reads `rules/` beside
  each config layer when it starts. Its source at `rust-v0.170.0` (`core/src/exec_policy.rs`)
  splits a `powershell -Command` script into its commands before matching them, and its skill
  parser (`skills/src/parser.rs`) reads only the three fields above.
- By name, with any arguments: a change to a script's options then needs no change to any agent's
  pre-approvals. Codex's rules couldn't hold the skills' stamps anyway: each skill update changes
  them, while Codex reads rules only when it starts. The scripts refuse options they don't have
  ([0017: Command-line options](0017-command-line-options.md)), so a rule reaches only what a
  script already does.
- One file in each Codex home, rewritten by setup like the rules file there: updates reach it the
  way they reach Claude Code's pre-approvals.
- `templates/per-agent/<agent>/`: [0073: Agents added later](0073-agents-added-later.md) expects
  each agent added later to need its own way to pre-approve commands, and a folder per agent keeps
  each agent's files together. Matching the agent's folder keeps each file's name the same at
  every stage.

**Costs:**

- Codex calls its rules experimental.
- Codex needs a restart after setup writes or changes the file. Codex's
  [skills page](https://learn.chatgpt.com/docs/build-skills.md) says it notices changed skills
  while it runs, so after an update that adds a script, a session can see the new skill before its
  rule, and asks to run that command outside the sandbox until Codex restarts.
- Pre-approvals arrive with updates, with no question, so they're only as trustworthy as the
  update that brings them.

**Options set aside:**

- The skills telling Codex to ask before running each command outside the sandbox: an approval
  on nearly every skill command; Codex's "Always allow" then saves a rule of its own choosing in
  `default.rules`; and approving a `prompt` rule still runs the command in the sandbox, as Codex's
  source shows.
- Changing Codex's sandbox mode: `unelevated` still has no network, full access drops the sandbox
  for every command, and each changes far more than dev-home-toolkit needs.
- Keeping Codex to editing files, with Claude Code committing: a PC with only Codex never syncs,
  and `/handoff issue` doesn't work in Codex.
- A question of its own for the file: a no would leave Codex unable to sync or commit, and the
  skills would have to keep their steps for Codex for that case.
- Pre-approving each command word for word, as the skills did: each change to a script's options
  meant changing each skill's Bash and PowerShell lines, and Codex's rules can't hold the stamps.
- Leaving out of the pre-approvals what can't be undone, such as the planned uninstall, by
  requiring a console for it or putting it in a script of its own: the developer chose no
  exceptions, so such an option gets its yes through the skill's steps in chat, as a settings
  change does.
- `templates/codex-rules/`: one folder per agent and kind, so `templates/` grows sideways with
  every agent. `templates/agent-folders/`: the skills and the operating rules reach the agents'
  folders too, so the name fits them as well. `templates/agents/`: easy to confuse with
  `~/.agents/skills`.
- Building each agent's pre-approvals from the commands in the skills: more code in setup, for a
  change that, by name, comes only with a new script.

**Look again if:** Codex lets a skill carry pre-approvals, or ties rules to skills; or its rules
change in a way that stops an `allow` rule from running a command outside the sandbox.
