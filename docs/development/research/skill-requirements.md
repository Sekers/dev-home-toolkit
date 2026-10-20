# Skill requirements: what keeps a skill off a PC

On 2026-10-16 and 2026-10-17, the developer and an agent reviewed how setup decides which skills a
PC's agents get, after a bug review found that a skill's links could flip in and out from one sync
to the next. This page sums up that discussion, what was checked, every option weighed, and a
recommended design. The developer decided most of it on 2026-10-17: "Decisions made, and waiting",
at the end, is the record of what's decided, and the sections before it show how the discussion
got there.

## Summary

- **The problem.** A skill can declare in its `dev-home-skill.json` that it needs a program, such
  as `{ "type": "program", "name": "jira" }`. As 6b was first built, setup added the skill to
  the agents only where it found that program. But "is `jira` here?" depends on which
  process asks: each shell has its own copy of `PATH`, and setup runs in whichever shell started
  it. The agent later runs the program in its own shell, which setup never sees. So setup's answer
  can be wrong, and since it decides the links, a skill can flip in and out.
- **The root cause.** Whether a program can run is a fact about the place an agent runs commands,
  not about the PC. No check at setup time can be right for every shell.
- **The recommended design.** Setup keeps a skill off only for what it knows exactly and nobody
  can change: the operating system, and which agent reads a skills folder. A missing program, or
  Python version, no longer keeps a skill off: setup adds the skill, tells the end user once what
  it needs, and the skill or the agent deals with the gap where it runs. The end user's answer
  for each PC stays the switch for everything else, and a skill for one setup ships not
  recommended.
- **Why it's better for end users.** Nothing flips. The agent can always see the skill, so it can
  say what's missing, use the parts that work, or work around the gap. A live test showed the
  difference (see "An agent with the skill, and without it").
- **The words.** "Tool" means at least four things in this repo, so the requirement type `tool`,
  which means Claude Code or Codex, is easy to misread. A glossary of fixed words, with a test, is
  recommended (see "Words: tool, agent, program").

## Where things stand

- **Part 6a, committed (`acdd061`):** the reader of the whole `dev-home-skill.json`
  (`internal/shared/settings.py`), and the checker with the types `os`, `tool`, `program`, and
  `python` (`internal/shared/requirements.py`).
- **Part 6b, committed (`408ae14`):** each PC's answer, `skills.<name>.addedToAgents`; the
  one-time `NEW` line for a new skill; links added and removed by each skill's plan, per skills
  folder; the recorded state in `internal/.generated/skill-states.json`, which `/dev-home skills`
  shows; `formerNames` for a renamed skill; `--configure` for the answer; and the reference page
  [A skill's dev-home-skill.json](../../reference/dev-home-skill-json.md). A bug review then found
  and fixed eight bugs (see the summary of the discussion). The four checks pass: 572 tests, 2
  skipped, after the rework below.
- **What this page questions:** 6b lets a missing `program` or `python` requirement keep a skill
  off. Everything else in 6b stands, whichever design is chosen. 6b has since been reworked to
  the decisions below (see "Decisions made, and waiting").

## The discussion, in order

1. **The bug review of 6b** found, among others, that a skills folder shared through a junction
   (such as `~\.claude\skills` made a junction to `~\.agents\skills`) made a skill limited to one
   agent flip, and that runs by hand and agent syncs could disagree about a program on the
   `PATH`. The first was fixed: setup treats such folders as one folder that both agents read. The
   second needed a decision, which opened this discussion.
2. **First options** (all about where setup looks for a program): each run's own `PATH`, as built;
   Windows' saved `PATH`, alone or with the run's own; remembering where a program was found. Each
   left a case broken (see "Options").
3. **The developer asked which `PATH` was meant.** Measuring showed three different ones on the
   same PC, and that the same name can lead to different files from different shells.
4. **A fixed path for each program**, the way skills already run Python through
   `internal\.python`, was proposed. It works only for skills setup generates, not the end user's
   own, which setup links as written.
5. **The developer asked to restart from the whole picture.** The inventory showed that
   dev-home-toolkit's own needs (Python, Git, `gh`) are never in doubt, because each script finds a
   program and runs it in the same process. The trouble is only with a program a skill needs and
   the agent runs.
6. **Per-OS alternatives**, such as `clip`, `pbcopy`, or `xclip`, are plausible once macOS and
   Linux are supported. The developer pointed out that an older copy that doesn't know a newer
   form should just be updated, so this can wait until a skill needs it.
7. **A minimum dev-home-toolkit version for skills** isn't worth asking skill writers for: their own
   skills are written against their own copy, and skills from elsewhere won't declare it. Instead,
   an older copy should report a requirement it doesn't know, so the end user knows to update.
8. **The Agent Skills standard** has a free-text `compatibility` field and a string-only
   `metadata` map, and nothing checkable, which is why `dev-home-skill.json` exists.
9. **Requirements no dev-home-toolkit ever learns,** such as a VPN or an environment variable, have
   no type. As built, an unknown type says "needs a newer dev-home-toolkit", which is wrong for a
   type the skill's writer invented.
10. **The developer asked why skills are kept off at all,** and proposed adding them anyway and
    warning, since parts of a skill may work without a requirement, and agents work around what
    isn't blocked. That's the design this page recommends, for everything but the operating
    system and the agent.
11. **The words.** The developer noted that "tool" is confusing for Claude Code and Codex, that
    this repo needs a rule for its words, as it has for people and for the two repos, and pointed
    to a skill that keeps a repo's words consistent.

## What was checked

### The copies of PATH

`PATH` is the list of folders a shell looks in for a program it's asked to run by name. Windows
stores a user `PATH` and a system `PATH` in the registry, and gives every program a copy of the
two joined when it starts. A running program never sees later changes to the stored lists, and a
shell can add folders of its own. Measured on a Windows 11 PC on 2026-10-17:

| `PATH` | Folders | How it differs |
| --- | --- | --- |
| Windows' saved `PATH` (user and system) | 23 | The baseline: what a program started now gets |
| Claude Code's PowerShell tool | 23 | The same as the saved one, since nothing changed after Claude Code started |
| Claude Code's Bash tool | 29 | The saved one, plus Git Bash's own folders, such as `C:\Program Files\Git\usr\bin`, and `~\bin` |

A program started before a `PATH` change keeps the old copy until it restarts.

### Which file each shell finds

The same PC, the same day, searching each shell's `PATH` the way a shell does on Windows:

| Name | Claude Code's Bash tool | Claude Code's PowerShell tool |
| --- | --- | --- |
| `gh`, `uv`, `node`, `python` | the same file as PowerShell | the same file as Bash |
| `git` | `C:\Program Files\Git\mingw64\bin\git.exe` | `C:\Program Files\Git\cmd\git.exe` |
| `ssh` | `C:\Program Files\Git\usr\bin\ssh.exe` | `C:\Windows\System32\OpenSSH\ssh.exe` |
| `grep` | `C:\Program Files\Git\usr\bin\grep.exe` | not found |
| `claude`, `codex` | not found | not found |

So a program can be found by one shell and not another (`grep`), found as different files
(`git`, `ssh`), or installed but on no `PATH` at all (`claude` and `codex`, bundled inside VS
Code's extension folders). A program on no `PATH` can only be run by its full path.

### What the standard and the agents offer

- **Agent Skills specification** (agentskills.io, read 2026-10-17): beyond `name` and
  `description`, it defines `license`; `compatibility`, free text up to 500 characters that
  "Can indicate intended product, required system packages, network access needs, etc."; and
  `metadata`, "A map from string keys to string values" that "Clients can use … to store
  additional properties". Nothing in it can be checked by a program.
- **Claude Code** (its skills documentation, read 2026-10-17) accepts `compatibility` and
  `metadata` "but doesn't act on" them. Its own fields control when a skill is used, not whether
  it's installed: `paths` limits automatic use to matching files, and
  `disable-model-invocation: true` takes the description out of the session's context while
  `/name` still runs it. It loads only each skill's description at startup, cut at 1,536
  characters.
- **Codex** (its skills documentation, read 2026-10-17) reads `name` and `description`, and an
  optional `agents/openai.yaml`, whose `dependencies.tools` lists MCP servers. It documents no way
  to declare a program, an operating system, or an environment variable, and doesn't say that it
  checks the dependencies it does list. Its skill list gets at most 2% of the model's context
  window, and "may omit some skills" when there are many.

### How package systems treat requirements

- **npm:** a package's `engines`, the Node.js version it runs on, "is advisory only and will only
  produce warnings", unless `engine-strict` is set; and an optional dependency that "cannot be
  installed on the current platform or engine" is left out (npm's documentation, read
  2026-10-17). So the platform decides what's installed, while a runtime version only warns.
- **pip:** never installs a release whose `Requires-Python` the running Python doesn't meet
  (long-standing behavior, not rechecked on 2026-10-17).
- **JetBrains plugins:** a plugin can declare a dependency as optional, so the features that use
  it load only when it's there, and the rest of the plugin works without it (not rechecked on
  2026-10-17).

The common thread: what can't change, such as the platform, decides what's installed; what the
end user can fix, such as a version, warns, or turns off only the parts that need it.

### An agent with the skill, and without it

A test skill, `zork-tickets`, said to run `zorkcli ticket create --title "<title>"`, and named the
program in its `compatibility` text. `zorkcli` doesn't exist. Claude Code 2.1.301, on its smallest
model, in print mode, was asked to "File a Zork ticket titled 'Printer jam on floor 2'", allowed
to run only `zorkcli`:

- **With the skill,** it ran the command, got "command not found", tried to find the program
  another way, and said exactly what was wrong: `zorkcli` isn't on the Bash `PATH`, so give its
  full path or approve looking for it.
- **Without the skill,** it didn't know what Zork was. It searched other folders for it,
  considered another skill, and asked which GitHub repo to file in: it improvised in the wrong
  direction.

A skill kept off is invisible, so the agent can't tell the end user what's missing. A skill that's
there, even one whose program is missing, lets the agent explain the gap.

## Why keeping a skill off needs a reliable answer

Two lookups happen for the same program: setup's, to decide the links, and the agent's, when it
runs the skill. They use different copies of `PATH`, so they can disagree. dev-home-toolkit's own
scripts never have this problem, because each finds a program and runs it in the same process.
A warning can afford to be wrong now and then: a wrong hint costs a sentence. A decision about
links can't, because a wrong one flips the skill in and out, or leaves the agent blind to it.

## Options

| Option | How it works | Pros | Cons |
| --- | --- | --- | --- |
| A. Each run's own `PATH` (as built) | Setup checks the `PATH` of whatever started it | Simple | Flips between Bash and PowerShell syncs, and after an install until the agents restart; worse on macOS and Linux |
| B. Windows' saved `PATH` | Alone, or with the run's own | A new install counts at once | Alone, it misses Git Bash's programs; with the run's own, the Bash-versus-PowerShell flip stays; Windows only |
| C. Remember where it was found | Once found, it counts while that file exists | Never flips; any OS | New stored state; still a guess about the agent's shell, such as `grep` from PowerShell |
| D. Add, but never remove | A found program adds the skill; a lost one doesn't remove it | Three lines; never flips | Keeps a skill after its program is uninstalled; reverses the decided removal |
| E. Setup stops checking programs | `program` becomes a stated need | Simplest; never wrong | Tells the end user nothing up front |
| F. E, plus an offer | The skill offers to take itself off when its program is missing | Covers the listing cost after the first try | A few lines in each such skill |
| G. A hint, not a decision | Setup looks for the program only to word the `NEW` line | Keeps the decided notice; never flips | Adds the skill even when its program is missing |
| Fixed path | Setup links each program under `internal\.programs`, and skills run it through a placeholder, as with Python | Works from every shell, even ones started before an install | Only for skills setup generates; the end user's own skills are linked as written, so they'd still run programs by name |
| Add and warn (recommended) | Keep off only for the operating system and the agent; warn for the rest | Never flips; the agent always sees the skill; less code | A skill whose program is missing costs its listing until the end user says no for that PC |

## Recommended design

### What setup keeps off

| Requirement | Keeps the skill off? | Why |
| --- | --- | --- |
| Operating system (`os`) | Yes, silently | It can't work on this PC, and nothing the end user does changes that. `/dev-home skills` still lists it, with why |
| Agent (`tool` today) | Yes, per skills folder | Its writer says it works only there, and setup knows exactly which agent reads each folder |
| Program (`program`) | No: add it, and warn | Parts may work, the agent can work around it, and only the agent's own shell knows |
| Python version (`python`) | No: add it, and warn | The same: setup checks only the Python it runs on, which only dev-home-toolkit's own skills run (decided 2026-10-17) |
| Anything else | No: described in `compatibility` | Setup can't check it |

### How the end user hears about a missing need

- **Once, when the skill is new:** the `NEW` line, such as "'zork-tickets' (added to your
  agents; it uses the zorkcli program, which setup didn't find)". The hint comes from setup's own
  `PATH` together with Windows' saved `PATH`, so a program installed after the agents started
  still counts; it's wrong only for a program that only one shell adds, such as Git Bash's programs.
  A wrong hint never changes a link.
- **When they ask:** `/dev-home skills` lists each skill's needs, and checks each program in the
  shell the agent runs it from, which is the one that matters at that moment. Today it shows only
  what setup recorded; the live check would be `facts.py` looking for the program in its own
  `PATH`, read-only, as setup does.
- **When the skill runs:** the skill's first step checks for its program, as `/handoff issue`
  already does for `gh`, says what's missing and how to install it, and goes on with what works.
  A skill made elsewhere doesn't do this, but as the live test showed, the agent explains a
  "command not found" well on its own.

### Requirements dev-home-toolkit doesn't know

A type, or a field in an entry, that this copy doesn't know is reported as a `PROBLEM` naming the
file and the type or field: "If the skill came from a newer dev-home-toolkit, update this one;
otherwise, describe the need in the skill's `compatibility` text instead." It doesn't keep the
skill off: under this design, only the operating system and the agent do. No skill writer has to
declare a minimum dev-home-toolkit version.

### The end user's answer, and what ships not recommended

The per-PC answer, `skills.<name>.addedToAgents`, stays the switch for whether a PC wants a skill.
A skill that suits only some setups, such as one for a single work tracker, ships with
`recommended: false`, so a PC gets it only after the end user says yes there. That serves "suits
only some setups" better than guessing from installed programs.

### For whoever writes a skill

- Declare only what setup checks: the operating system, the agent, a program, a Python version.
- Describe anything else in `compatibility`.
- Check for a program in the skill's first step that uses it, say how to get it, and keep working
  without it where the skill can.

### What changes in 6b, and what stays

- **Stays:** the per-PC answer and its states, the `NEW` line's one-time naming, the per-folder
  links and their removal, the junction fix, `formerNames`, `--configure`, the recorded state,
  and the other bug fixes.
- **Changes:** each rule in `requirements.py` says whether it keeps a skill off (`os` and the
  agent) or warns (`program` and `python`); `plan_skill` keeps a skill off only for the first kind,
  and words the rest into its state; the `NEW` text and the states gain "uses …"; unknown types
  and fields become `PROBLEM` lines; `facts.py` shows each skill's needs, checks programs in its
  own shell, and shows the `compatibility` text; the tests, the two decisions, and the reference
  page follow.

### Walking it through for end users

| Case | What happens |
| --- | --- |
| A new PC without `zorkcli` | The skill is added; the `NEW` line says it uses `zorkcli`, which setup didn't find; asked to file a ticket, the agent explains what's missing |
| Installing `zorkcli` while agents are running | Nothing changes in the links; a session started before the install still can't run it until it restarts, and says so when asked |
| A skill that uses `grep` | Added everywhere; it works from the Bash tool, and from PowerShell the agent reports that `grep` isn't there, or uses something else |
| A skill only for macOS, on Windows | Not added, and not named in the `NEW` line; `/dev-home skills` says why |
| A skill only for Claude Code, with Codex set up too | Added to Claude Code's folders only; the `NEW` line and `/dev-home skills` say so |
| Uninstalling `zorkcli` | The skill stays; the agent explains the gap if asked; the end user can say no for that PC |
| A skill for one work tracker, not recommended | Not added until the end user says yes on that PC |

## Words: tool, agent, program

### What the words mean today

In this repo, "tool" means at least four things: Claude Code and Codex ("both tools"), installed
programs ("the tools are on the PATH"), the development tools ("The tools run from
`internal/development/`"), and part of the name dev-home-tools itself. AGENTS.md's "Tools"
section is about installing software. "Agent" means the AI working in a session ("an agent
working for the end user"), a second agent started by a skill, and, in "added to your agents",
Claude Code and Codex as set up on a PC.

Elsewhere, "agent" is the common word for the products. The Agent Skills site calls them
"skills-compatible agent[s]", "agent products", and "AI tools and agentic clients", and its list of
products describes most of them as an agent: Codex is one of ChatGPT's "agents", and Gemini CLI is
"an open-source AI agent". Claude Code calls itself "an agentic coding tool".

### How another project fixes its words

The `domain-modeling` skill in [mattpocock/skills](https://github.com/mattpocock/skills) keeps a
`GLOSSARY.md`: one bold term per entry, a definition of a sentence or two, and an "_Avoid_:" line
naming the words not to use for it. Its advice is to "Be opinionated": one word per idea, with the
others listed to avoid. It enforces the words by having agents challenge a word that conflicts
with the glossary while they work. This repo already enforces two sets of words more firmly: the
names for the developer and the end user ("Who's who" in AGENTS.md, with a test), and dev-home
versus dev-home-toolkit ("The two repos"). Another of the developer's projects has a rule for the
very same word: its agent guidance says to call products like it by their kind, not "tools",
because there "tools" means development tools.

### Recommendation

- **A glossary page,** `docs/development/glossary.md`, in the `domain-modeling` format: each word,
  its meaning here, and the words to avoid. AGENTS.md links to it from "Who's who", which keeps
  the people words, and repeats only the words agents mix up most.
- **A test** for the words that can be caught by their wording, as the people words are: such as
  "both tools", "each tool's", or "the tools'" for Claude Code and Codex.
- **The words, to confirm with the developer:** "agent" for Claude Code, Codex, and any later
  product that reads skills, as in "added to your agents"; "the agent" for the AI in a session,
  where context leaves no doubt; "program" for anything installed that a shell runs; and
  "tools" only for development tools, such as what's pinned in `internal/development/`, as in the
  developer's other project. The requirement type `tool` becomes `agent`, which costs nothing
  before the first release.

## Decisions made, and waiting

**Decided by the developer on 2026-10-17:**

- Setup keeps a skill off only for its operating system or the agent it works in; a skill whose
  program is missing, or whose Python version is too old, is added, with a warning.
- For Python, decided separately: setup checks the Python it runs on, which only dev-home-toolkit's
  own skills run (and later, skills that opt in to being generated); for any other skill, the
  check is a guess, as for a program, so keeping the skill off could hide one that works. Set
  aside: keeping the skill off (reliable only for skills that run dev-home-toolkit's Python, and it
  would treat two needs the end user can fix differently); keeping off only the skills that run
  dev-home-toolkit's Python (the rule would depend on the opt-in's flag, is harder to explain to
  skill writers, and applies to no skill today). Look again when the opt-in is built, since a
  `python` requirement gets a reliable meaning for the end user's skills then. An update that
  needs a newer Python is still held back, since it would break the sync itself.
- A skill lists its programs for the skill as a whole, with no map of which feature needs which.
- Setup generates only dev-home-toolkit's own skills, plus any skill of the end user's that opts in
  through a flag in its `dev-home-skill.json`; every other skill is linked as written. No new
  format is asked of skills made elsewhere. When built, as its own part (see the order below),
  settle the flag's name, a small public set of placeholders
  (such as `{{PYTHON}}`, `{{SKILL_DIR}}`, and `{{CONTENT_DIR}}`, keeping those that name
  dev-home-toolkit's internals private, since public names freeze at 1.0.0), and where generated
  copies go. Consequences found while deciding: a `python` requirement only means something for
  a skill that runs dev-home-toolkit's Python, so its meaning follows the opt-in; and an older
  dev-home-toolkit that doesn't know the flag links the skill with raw placeholders, which argues
  for reporting an unknown field.

- Skills run programs by name, through the `PATH`, with no fixed paths; fixed paths are recorded
  as the option to revisit if a need appears
  ([Skills run programs by name, through the PATH](../decisions/skills-run-programs-by-name-through-the-path.md)).

- The warning about a missing program: a one-time hint in the `NEW` line worded "isn't on the
  PATH", with what the skill uses the program for (its entry's `description`), looking where a
  newly started shell would on each OS (setup's own `PATH`, plus Windows' saved one on Windows); a
  live check in `/dev-home skills`, in the agent's shell; and the skill's own check when it runs,
  by running the program's version command. The reference page says how to add a folder to the
  `PATH` on each OS, and to restart the agents afterward.

- The file's format: the requirements are in two lists, `supportedOn` (`os` and `agent`) and
  `dependsOn` (`program` and `python`), so the file says which kind each entry is, and either
  kind can gain types later. Anything in `supportedOn` this copy can't use keeps the skill off:
  an entry with a mistake, a type the list doesn't take, or a field it doesn't know, which may
  narrow the limit. Anything in `dependsOn` it can't use is ignored, and so is a field it doesn't
  know anywhere else. Each is a `PROBLEM` naming the file and the word, said once however often
  the word appears, saying what setup did and every fix that may apply, since setup can't tell a
  typo from a newer or made-up word. When a word known in that place is close, the line first
  asks "Did you mean ...?", offering only types the same list takes, and keeps the rest of its
  advice. There's no check for a known type under the other list: that list doesn't know it. No
  skill declares a minimum dev-home-toolkit version; releases decide that separately. A skill
  without the file gets no such lines. The reference page explains `compatibility`, with an
  example. How this was reached, from one list called `requires`, with the options and names set
  aside, is in the decisions
  [Skills and releases declare their requirements as facts](../decisions/skills-and-releases-declare-their-requirements-as-facts.md)
  and
  [Setup keeps a skill off only for its operating system or agent](../decisions/setup-keeps-a-skill-off-only-for-its-operating-system-or-agent.md).

- A glossary for this repo's words: `docs/development/glossary.md`, in the `domain-modeling`
  format (the word, its meaning here, and an "Avoid:" line), linked from AGENTS.md's "Who's who",
  which repeats only the words agents mix up most. It covers every file, and existing text is
  brought in line in one sweep when it lands. Agents check it when writing, and a test catches the
  mix-ups that wording alone gives away, extending the test for the developer's names.

- "Agent" is the glossary's word for Claude Code, Codex, and products like them (the most common
  word: AGENTS.md says "coding agents", Agent Skills "skills-compatible agent"), with "agent
  product" only where a sentence must tell the product from the AI working in a session. With it,
  the requirement type `tool` becomes `agent`, as in `{ "type": "agent", "anyOf": ["claude-code"] }`,
  and the code's `Tool` class becomes `Agent`. A minimum agent version would later be a field on
  the same entry, and something an agent offers, such as an MCP server, its own type, such as
  `mcpServer`.
- "Program" is the glossary's word for anything a shell runs by name, such as `git`, `gh`, or
  `jira`, with "command-line program" where a sentence needs precision; "Avoid:" lists "tool",
  "CLI", "binary", and "executable". The type stays `program`. Most docs say "command-line tool"
  or "CLI", so this is a deliberate choice, to free "tool".

- "Development tools", written out, means what's used to work on dev-home-toolkit (pytest, ruff,
  mypy, uv). "Tool" and "tools" are never used for programs or agents, and stay only inside names:
  dev-home-tools, an agent's own named tools such as Claude Code's Bash tool, and fields such as
  `allowed-tools`. AGENTS.md's "Tools" section gets a heading that says it covers installing
  anything, such as "Installing software".
- The product is renamed **dev-home-toolkit**, from dev-home-tools; the private repo stays
  "dev-home". Set aside: "dev-home-kit" ("kit" is unclear to many people), keeping
  "dev-home-tools" (an awkward possessive, and the one name containing "tools" outside development
  tools), "dev-home-manager" (suggests an app with a window), "dev-home-keeper", and names for one
  job only, such as "dev-home-setup". The rename is its own piece of work (see the order below):
  the GitHub repo (its redirect keeps old clone and update addresses working), the folder on each
  PC with a setup run after, the handoff's path in dev-home, and every file that names it.
  Renaming the GitHub repo needs the developer's go-ahead at the time. Checked on 2026-10-17,
  when building it: no GitHub repo and no PyPI project had the name.
- The order, once 6b is committed: the rename, then the glossary with its sweep, both before 6c;
  then 6c to 6e, steps 7 to 9, `/handoff update audit`, and shared skill text; then the opt-in;
  then the release work and 1.0.0. Why: the text 6c to step 9 add, such as the always-on lines,
  setup's questions and menu, and the docs, is approved word for word, so it's written once, in
  its final words and name. The rename comes before the glossary because a word search for
  "tool" also matches inside "dev-home-tools" (338 times in 73 files), so afterwards the
  glossary's test needs no exception for the product's name; and it settles the name of the
  `{{TOOLS_DIR}}` placeholder. The opt-in comes after both, since its flag and placeholders
  become public names that freeze at 1.0.0. Set aside: both after step 9 (approved text would
  change and need approving again, and every new page adds to the sweep); both before 6b's commit
  (6b, uncommitted and live on the developer's PC, would wait longer).

**Still waiting:** the decision about generating the end user's own skills gets its decision file
when it's built. The rename's is
[The product is named dev-home-toolkit](../decisions/the-product-is-named-dev-home-toolkit.md),
and the words' is
[One word for each idea, in a glossary](../decisions/one-word-for-each-idea-in-a-glossary.md).
6b, reworked to these decisions, is committed
(`408ae14`), with the decision
[Setup keeps a skill off only for its operating system or agent](../decisions/setup-keeps-a-skill-off-only-for-its-operating-system-or-agent.md)
and changes to the decisions it touches.

**The earlier list, kept for its notes:**

1. Keep a skill off only for its operating system or the agent it works in, and add it with a
   warning when a program or Python version is missing. Recommended. **Decided by the developer
   on 2026-10-17 for programs:** yes, and for Python too (question 5). Also decided that day: a
   skill lists its programs for the skill as a whole, with no map of which feature needs which
   program.
2. The warning: a hint in the `NEW` line from setup's `PATH` and Windows' saved `PATH`, a live
   check in `/dev-home skills`, and each skill's own check when it runs. Recommended over a plain
   "uses …" with no checking.
3. Report an unknown type or field as a `PROBLEM` pointing to `compatibility`, and ask skill
   writers for no minimum dev-home-toolkit version. Recommended.
4. The glossary page, its test, and the words, including renaming the type `tool` to `agent`.
   Recommended.
5. Python: warn, like a program (recommended), or keep the skill off, since setup can check it.
   **Decided by the developer on 2026-10-17:** warn.
6. Then the commit of 6b, reworked to match.

Later, and separate: whether setup should generate the end user's own skills as it does
dev-home-toolkit's, which would give them `{{PYTHON}}`, pre-approved commands that work on every
PC, and fixed paths to programs.

## Limits, and when to look again

- The `PATH` measurements come from one Windows 11 PC on 2026-10-17. macOS and Linux weren't
  tried; there, the gap between an app started from the desktop and an agent's shell is expected
  to be wider.
- The live test used Claude Code 2.1.301 on its smallest model, in print mode, allowed to run only
  the missing program. Codex wasn't tried.
- The documentation was read on 2026-10-17. Look again if the Agent Skills specification gains a
  checkable requirements field, or Claude Code or Codex start hiding a skill whose needs aren't
  met.
