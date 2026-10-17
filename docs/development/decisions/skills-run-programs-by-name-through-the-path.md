# Skills run programs by name, through the PATH

**Decision:** a skill runs each program it needs by name, as its steps write it, such as
`zorkcli ticket create`, and the shell the agent uses finds the program through its own `PATH`.
dev-home-tools doesn't give programs fixed paths, as it does for Python. Decided by the developer
on 2026-10-17.

- A program a skill needs must be on the `PATH` of the shell the agent runs it in. One installed
  elsewhere needs its folder added to the `PATH`, and on Windows, agents started before an install
  see the program only after a restart.
- Python is the exception, for its own reasons: dev-home-tools' skills, and skills that setup
  generates, run `{{PYTHON}}`, the one Python 3.12 or later that setup links as
  `internal/.python`, because their scripts must run on a known Python with pre-approved
  commands, and on Windows Python is often reached only through the Store's placeholder.
- A missing program doesn't keep a skill off a PC; setup warns about it instead
  ([Setup keeps a skill off only for its operating system or agent](setup-keeps-a-skill-off-only-for-its-operating-system-or-agent.md)).

**Why:**

- It's how every skill works, including skills made elsewhere, which never use dev-home-tools'
  placeholders. So programs run one way for every skill.
- Programs installed the usual way are on the `PATH` of every shell: on 2026-10-17, `gh`, `uv`,
  `node`, and `python` were found as the same file from Claude Code's Bash and PowerShell tools
  ([Skill requirements](../research/skill-requirements.md)).
- The cases it leaves have fixes end users already know: a program on no `PATH`, a tool only Git
  Bash provides, and a session not restarted after an install. The warning says which applies.
- Fixed paths would cost about a whole part of setup's work, for skills nothing has yet.

**Options set aside:**

- **Fixed paths, as for Python:** setup finds each program a skill declares, links its folder as
  `internal/.programs/<name>`, and fills a `{{PROGRAM:<name>}}` placeholder in the skill. A test
  on 2026-10-17 showed that such a path runs `.exe` and `.cmd` files from both of Claude Code's
  shells, when it names the file with its extension. Set aside because:
  - it reaches only skills setup generates, so skills made elsewhere still run programs by name;
  - it needs finding programs on each OS, a per-PC setting for a program pointed at by hand, and
    links re-pointed when a program moves, which some do on every update;
  - it doesn't fix a program that itself needs the `PATH`, such as a tool installed with npm that
    runs `node`;
  - its placeholder would be public, and frozen from 1.0.0;
  - nothing uses it yet.
- **A folder of launchers on the end user's `PATH`:** it changes their `PATH` outside
  dev-home-tools, still needs restarts, and Git Bash can't run a `.cmd` launcher by its bare name
  (tested 2026-10-17).

**Look again if:** programs off the `PATH` turn out to be common for the skills people use, a
skill needs its program run exactly, such as a work-tracker skill, or sessions not restarted after
an install cause real trouble. Fixed paths can then be added for skills setup generates,
dev-home-tools' own and those that opt in, without changing anything else.
