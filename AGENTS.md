# dev-home-tools: guidance for AI agents

**What this repository is:** the public tooling for dev-home, a private repo that each person
keeps for AI-agent handoffs and a general knowledge base, shared across their PCs through GitHub,
for Claude Code and Codex. This repo holds the `handoff` and `knowledge` skills and the scripts
they share, the always-on operating rules, `setup.py`, `sync.py`, `update.py`, and the starter
files for a new private repo. It never holds anyone's handoffs, knowledge, or global rules.
README.md and `docs/` describe how people use it.

## Who's who, and the words for each

There are two roles, and you work for a developer:

- **Developer:** anyone who changes dev-home-tools. There may be several.
- **End user:** anyone who uses dev-home-tools, now or later, a developer included when using it
  on their own PCs.

Design for end users. Weigh each decision by what they would want and expect, not by a
developer's own setup.

Every file is written for one audience, and each audience has fixed words for the two roles. Use
them in everything you write here, code comments and commit messages included:

| Written for | Files | The developer | The end user |
| --- | --- | --- | --- |
| The developer | AGENTS.md, `docs/development/`, the README's "Working on dev-home-tools", code comments, tests, commit messages | the developer | the end user; a person or people when it matters that they aren't an agent |
| The end user | the rest of the README, `docs/skills/`, `docs/reference/`, and setup's questions at a console | not named | you |
| An agent working for the end user | the skills, and the lines the scripts print for agents | not named | the user |
| The end user's own voice | the operating rules and the starter files | not named | I, my, me |

- "Developer" is the only word for a developer: never "the user", "the person", "the author",
  "the maintainer", or "the person you work for". So any other word for a person always means an
  end user.
- Singular or plural: "the developer" is the one you work for, "a developer" is any one of
  them, and "developers" is all of them. End users work the same way: "the end user" is the one
  a sentence is about, "an end user" is any one, and "end users" is all of them.
- In a file for the developer, "you" is its reader: an agent in AGENTS.md, a developer in the
  README's "Working on dev-home-tools".
- A test checks that those other names for the developer appear nowhere outside this section.

## The two repos

"dev-home" always means a person's private repo, and "dev-home-tools" always means this one.
Never leave it to the reader to guess which: name the repo whenever both could fit.

| What | dev-home-tools (this repo, public) | dev-home (each person's, private) |
| --- | --- | --- |
| Always-on rules | `templates/operating-rules/operating-rules.md`: the operating rules, the same for everyone | `global-rules/global-rules.md`: that person's global rules |
| Skills | `templates/skills/`: the `handoff` and `knowledge` skills. `templates/shared-skill-scripts/`: the scripts they share | `skills/`: that person's own skills |
| `AGENTS.md`, `CLAUDE.md`, `README.md` | About dev-home-tools, and working on it | About that dev-home, and working in it |
| Only here | `setup.py`, `sync.py`, `update.py`, `templates/dev-home-starter/`, `internal/`, `docs/` | `handoffs/`, `knowledge/`, `dev-home.json` (settings every copy shares, which setup writes and commits) |

- The root holds only what must be there, and the scripts a person runs by hand:
  `.gitattributes`, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, `README.md`,
  `setup.py`, `sync.py`, `update.py`, and the folders `templates/`, `internal/`, and
  `docs/`. Setup adds `local-settings.json` on each PC, and beside it a dated backup each time
  `--configure` changes it or setup sets aside a file in an older layout, such as
  `local-settings.json.bak-YYYYMMDD-HHMMSS`; git ignores both. Never add a file or folder to
  the root, or have a script or tool create one there, without asking the developer first, in
  a question of its own.
- `internal/` is dev-home-tools' own machinery, which nobody runs directly
  ([scripts.md](docs/development/scripts.md) says what's in it). Never edit
  `internal/.generated/` or `local-settings.json`, or change `internal/.python/`. Setup
  rewrites them, and git ignores them.
- Every script is Python, and nothing needs PowerShell.
- Only the latest versions of Claude Code and Codex, in every current form that reads what
  dev-home-tools sets up: their CLIs, desktop apps, and editor extensions and integrations
  (VS Code, JetBrains IDEs, and others), and Anthropic's Agent SDK. Build on what the latest
  versions read and document, and add no workaround or fallback for an older version. Check a
  setting or behavior in the tool's current documentation, or in its source when the
  documentation doesn't say.
- Never build on a feature its documentation calls deprecated, in Claude Code, Codex, Python,
  git, or anything else dev-home-tools uses: a deprecated feature is likely to stop working. Use
  what replaces it, or ask the developer when nothing does.

## Privacy

- This repo is public, and its users keep private things in their own dev-home. Never put
  anyone's handoff or knowledge content, names, account or GitHub names, PC names, tenant
  details, or personal paths in any file, commit message, or issue here. The only exceptions
  are this repo's own address (`Sekers/dev-home-tools`, in the README's clone command) and the
  copyright line in LICENSE.
- Examples use made-up values: paths such as `C:/Users/you/dev-home` or
  `C:\Programming\dev-home`, and `example.com` for any domain. For parts that vary per run or
  per PC, such as a timestamp, hash, or ID, use a placeholder in code formatting, such as
  `local-settings.json.bak-YYYYMMDD-HHMMSS` or `<commit>`, never a value that looks real. Facts
  and evidence, such as versions and test dates in `decisions/`, stay exact. A test may use a
  real-looking value it needs to test against, but makes it up rather than copying it from a
  real machine.
- Before proposing a commit, read the whole diff for those.

## Tools

This is a hard rule. It holds over any other instruction that would install or add a tool, such
as a step written in a handoff or a plan.

- Never install, update, or download a tool without the developer's permission: a
  program, a Python version, an editor extension, or a package that isn't pinned in
  `internal/development/uv.lock`, including one a command fetches on the fly, such as `uvx` or
  `uv run --with`. Changing that lock file, such as updating a pinned version, needs the same
  permission. If you think a tool would help, ask in a question of its own: say what it's for,
  where it comes from, and what it would install or write.
- Every tool this repo depends on must be listed in its documentation: what people need to use it
  in the README's Requirements, and what working on it needs, such as for the tests and checks,
  in `docs/development/`. Until `docs/development/tools.md` is written, the development tools are
  the ones the README's "Working on dev-home-tools" section names. Making the repo depend on a
  tool that isn't listed, or adding one to the lists, needs that permission first.
- Using a tool that's already installed is fine for looking into something or checking your
  work, within what your agent's permission settings allow, as long as it installs, updates, and
  downloads nothing. So is building the development environment from that lock file, the way the
  documentation says.

## Speed

- Agents run these scripts at the start of nearly every skill command, so any added time is paid
  over and over. Never build anything that adds time, such as another process, git call, or
  network call, in a script, a skill's steps, or anything that runs automatically, without
  asking the developer first. Say how much it adds, measured if you can, and offer a
  way that avoids it. A bigger saving elsewhere doesn't make it free: they still decide.

## AI usage

- Every token an agent reads or writes while it follows dev-home-tools' skills and rules costs
  end users something: usage from their plan's limits, or money when they pay per token. Weigh
  that cost in every change, and keep what agents read as short as it can be without making it
  unclear (see "Clarity for agents").
- What costs most is what's paid for over and over: the operating rules and each skill's
  description, which load in every session; each skill's steps and the lines the scripts print,
  read on every skill command; and each extra turn a skill takes, since every turn reads the
  whole conversation again. So prefer a script doing the work to steps an agent follows, and one
  call to several, within what "Speed" allows.
- Never add a skill, make the operating rules or a skill's description longer, or add to what a
  script prints for agents on every skill command, without asking the developer first. Show the
  change with about how many words it adds, and a way to avoid it if there is one. A bigger
  saving elsewhere doesn't make it free: they still decide.

## Clarity for agents

- Anything agents read and act on, such as the skills, the operating rules, the starter files,
  AGENTS.md, the decisions, and the lines the scripts print for agents, must be clear to an agent
  with none of your session's context. A misread costs more than a shorter version saves: a
  wrong action, or extra turns to put it right.
- After a change to such text, read it the way an agent new to it would: top to bottom, each
  sentence taken literally. Read the whole of a skill, the operating rules, or a decision, the
  whole section of a longer file such as AGENTS.md, and every passage, in that file or
  another, that names or relies on what changed. Skip this for a change that can't alter the
  meaning, such as a typo or a rewrapped line.
- For a new skill, a new or rewritten section, or a change to what the operating rules mean,
  offer the developer a fresh agent's read too; smaller changes get your own read alone.
  [fresh-agent-reads.md](docs/development/fresh-agent-reads.md) says how, at the least cost.
- The developer can ask for a fresh agent's read of any change.

## Rules for each area

Each area's rules are on a page of their own. Read the page before changing that area:

- Anything under `templates/`, or adding a script: [skills.md](docs/development/skills.md).
- The scripts in the root, or `internal/shared/`: [scripts.md](docs/development/scripts.md).
- A test: [testing.md](docs/development/testing.md).
- The README or a page under `docs/`: [writing-docs.md](docs/development/writing-docs.md).

## Docs (README.md and docs/)

- The README is the front door, and the rest goes in `docs/` (see writing-docs.md, above).
  `docs/development/` is for people and agents changing dev-home-tools. Research on this project
  goes in `docs/development/research/`, one page per investigation.
- AGENTS.md holds only what every agent working here needs in every session: the rules, each
  with a short reason, and pointers to where more is explained. Keep it under 200 lines, the size
  Claude Code recommends for an instruction file. Everything else for developers goes in
  `docs/development/`, one page per topic, such as how the code is laid out and how the tests
  work, and AGENTS.md links to a page where an agent needs it. Each design decision, with its full
  reasons and the options set aside, has its own file in `docs/development/decisions/`; read it
  before reopening one.
- Each fact lives in one place, and other pages link to it.

## Testing

- Before proposing a commit, run these four, from this repo's root:

  ```text
  uv run --directory internal/development pytest
  uv run --directory internal/development ruff check --config pyproject.toml ../..
  uv run --directory internal/development ruff format --check --config pyproject.toml ../..
  uv run --directory internal/development mypy
  ```

- Test only through the tests, which run a copy of this repo in a sandbox. This folder may be
  someone's live setup: running its scripts against a test dev-home rewrites
  `internal/.generated/` and `local-settings.json`, which their real links depend on. Never add
  `testHomeDir` to a real `local-settings.json`.
- Add a test for every behavior you add or change.

## Style

- No em dashes in any file. Use a semicolon, colon, parentheses, a comma, or a new sentence.
- Plain language, for people who haven't seen the code.
- Comments describe the code as it is now, never what it used to do.
- Commit messages read `<area>: <what>`, for example `setup: link personal skills` or
  `handoff: check closed issues`. Commits here are signed.
