"""Sets up dev-home-toolkit on this PC: finds or creates your dev-home, fills in the skills with
this PC's paths and links them into Claude Code and Codex, writes each agent's always-on rules,
and checks the settings they need.

Safe to run any number of times. It rewrites only its own generated files and rules files, and
dev-home's AGENTS.md and CLAUDE.md, sending a hand edit to either to the Recycle Bin first, and
moving the lines it didn't write in a rules file into dev-home first. It creates missing links,
replaces links whose target is gone, removes links it made to skills that no longer exist, removes
what it set up in a folder answered no, and reports anything else without changing it.

A run goes in this order, so the questions come first and the work after:

1. dev-home first. On the first run it asks where your dev-home is (the private repo that holds
   your handoffs and knowledge base). If that folder doesn't exist yet, it offers to clone your
   dev-home from GitHub, or to create a new private one from the files in templates/dev-home/.
   A folder that exists must look like a dev-home: it has dev-home.json, which only
   dev-home-toolkit writes. Setup sets that repo's own git config, so it never works on a folder
   without it, such as a project's repo named by mistake. When dev-home can't be put in place,
   setup stops, and saves nothing.
2. The questions not answered yet: whether to pull updates automatically, whether to set up each
   Claude Code folder it finds, whether to set up Codex, in every Codex home, and how many copies
   of dev-home are in active use. Each is asked whenever its answer isn't saved yet, not only on
   the first run. A no is saved too, so it's asked about once. Every run, quiet ones included,
   also gives each Codex home the main home's answer, saying so.
3. At a console, the settings menu that --configure shows, so any setting can be changed.
4. The change to confirm to dev-home.json. Then each hand edit to dev-home's AGENTS.md or
   CLAUDE.md that the Recycle Bin can't take, shown, with whether to delete it for good. Then the
   lines setup didn't write in each agent's rules file, and each file waiting in this PC's
   unanswered/ folders, shown, with where they go.
5. The work, which asks nothing, and holds the sync's lock, so a sync in another session waits
   for it, while no sync ever waits for a person's answer. It reads local-settings.json, in
   dev-home-toolkit's folder, again, since another run may have saved it meanwhile, makes there only
   the changes a person made in this run, works out its own changes again from what that gives,
   and saves it. Then it commits dev-home.json, sets up everything else from the settings it
   saved, and last makes the change each folder it sets up needs in Claude Code's or Codex's
   settings file.

local-settings.json groups the settings, and each one's name is its path, such as
devHome.folder. Its schemaVersion says which layout it has. A file without one, from before the
settings were grouped, is set aside: a run by hand offers to rename it to a dated backup and ask
its questions again, and a quiet run says so and stops. Every value is checked on every run, and
a setting nothing declares is removed, with one line and a backup: the answers of a skill that's
gone only by a sync's run, which holds the sync's lock from its start.

dev-home.json, in dev-home, says whether dev-home is in active use on one PC or on several, and
each sync acts on it. A new dev-home starts with one. Setup asks on a PC's first setup, with the
file's answer as the default, when the file has no answer, and after cloning one set to one. It
shows the change, and after a yes writes that file alone, then commits and pushes it, so every
copy agrees.

The templates in this repo hold placeholders where paths go. Setup writes copies of the skills
and the scripts they share, with this PC's paths filled in, to internal/.generated/, at the same
paths they have under templates/, and links the skills into the agents. Pre-approved commands must
match the command text exactly, so the paths can't be variables.

Each agent gets its always-on rules as one file setup writes in its folder: dev-home-rules.md in
each Claude Code folder's rules/, which Claude Code loads with every other .md file there, and
AGENTS.md in each Codex home. It holds the operating rules, from their template with this PC's
paths filled in and only the blocks of the skills added for that agent, then the end user's rules
from dev-home's rules/, joined for that agent on this PC (rules.py). Setup keeps a copy of what it
last wrote there, in internal/.generated/last-written/, by which it tells the lines it didn't
write: ones someone added, or a whole file that was there
before setup wrote its own. Before it rewrites or removes the file, those lines move into a file of
their own in dev-home's rules/, with the headings they were under: at a console, into the mine/
the person picks, or to the Recycle Bin; otherwise, set aside in this PC's unanswered/ for that
agent, named in a NEW line on every run until a person answers, at a console or through an agent
with --configure. A file there joins after mine/,
only in the rules file it came from, as its note's from field names it, so one Claude Code
account's lines never load in another's. Setup commits and pushes them before it touches the file,
and leaves the file as it is while they aren't committed, or once it changes after setup read it.
It never changes a Codex home's AGENTS.override.md, and reports one with text,
which Codex reads in place of AGENTS.md. The design is in docs/development/decisions/, in
decisions 0058, "Skills' always-on lines", 0064, "Each agent's rules file", 0065, "Where end users'
rules live", and 0066, "Notes in rule files".

In dev-home, setup creates the end user's files it keeps there wherever they're missing, and
commits them: the knowledge index, with only its title, and a my-rules.md, empty, at each level of
rules/ for every agent set up here. One that git still has, the end user's change not committed
yet, isn't committed over: the index is put back as git has it, and a my-rules.md waits. A new
dev-home starts with the files in templates/dev-home/, which dev-home-toolkit owns, and
dev-home.json (decision 0070, "Who owns each file in dev-home"). Two of those, AGENTS.md and
CLAUDE.md, hold this PC's commands, so they're never committed: dev-home's .gitignore lists them,
and setup writes them on every run, keeping a copy of what it wrote in last-written/, as for the
agents' rules files. Any other text there is a hand edit, which goes to the Recycle Bin before
setup puts the file back (decision 0069, "Dropped text"). When the bin can't take it, the file
stays as edited, named in a PROBLEM line on each run, until a run whose bin takes it, or a
person's answer, at a console or through an agent with --configure.

Each Claude Code folder and Codex home setup sets up needs a change in its settings file, so the
agent can reach dev-home from any project, and in a Claude Code folder other than ~/.claude, so its
sessions skip ~/.claude's instructions (see home_claude_excludes). The yes to setting up the
folder approves it, and the question says so, so every run, quiet ones included, makes the change
when it's missing: it saves a dated backup of the file, then writes the change, and says so. A no
to the folder takes it back out the same way. In a Claude Code folder set up, every run also keeps
only the last copy of a recommended setting written more than once in settings.json, the one
Claude Code uses, so nothing it does changes (decision 0032, "Recommended settings"); and any
rewrite of that file keeps only the last copy of a key written more than once, and says so. It
never edits a file it can't fully parse (a settings.json with comments, for example), or a
read-only one; it reports it, and a run by hand prints what to change by hand.

Run it by hand once per PC. After that, each sync runs it with --quiet, so changes to the
skills, and skills added on another PC, reach this one.

Claude Code gets the skills' links and its rules file in each folder answered yes under
claudeCode.folders in
local-settings.json. Setup offers each Claude Code folder it finds, in a list, each recommended:
~/.claude, once Claude Code has made it; each extra one, one per account, such as
~/.claude-<name>; and the folder in CLAUDE_CONFIG_DIR. It saves a no there too, and a reminder,
the answer to ask again in a number of days. A folder with no yes or no isn't set up: setup adds
no links there and removes none. A sync names each one with no answer yet, or a reminder that's
due, in a NEW line, which says how to answer; until a reminder is due, setup doesn't ask about
its folder, and syncs don't name it. In a folder answered no, setup removes the links it made and
its rules file, once the lines it didn't write there are saved in rules/, and takes dev-home and
dev-home-toolkit, and its claudeMdExcludes patterns, back out of its settings.json, and leaves the
rest alone. One answered yes that no longer exists is skipped. Setup keeps the folders in order,
in claudeCode.folders and wherever it goes through them: ~/.claude first, then each
~/.claude-<name> by name, then each other folder by full path.

Codex homes are saved the same way, under codex.homes, but every home reads the same skills, from
~/.agents/skills, so every home has the same answer: setup sets up all of them, or none, and asks
one question for them all. The homes are ~/.codex, once Codex has made it; each ~/.codex-<name>
that holds a config.toml or an auth.json; the folder in CODEX_HOME; and each other one with an
entry. The main home is ~/.codex when it's there, otherwise the first ~/.codex-<name> there by
name, otherwise the first other home there by full path; codex.homes keeps its entries in that
order too. A home whose answer differs from the main home's, or that has none, such as a new one,
gets the main home's answer, with a line saying so; when the main home has none, the next home
there in that order that has one gives it. A yes gets each home its rules and settings, and the
skills linked into ~/.agents/skills. A no removes the rules file setup wrote in each home, as for
a Claude Code folder, and the links it made in ~/.agents/skills, and takes dev-home back out of
each home's writable_roots. Until Codex is answered yes or no, setup adds no links and removes none,
and a sync names its homes in a NEW line, as for a folder. One reminder covers every home.

Each skill is added to the agents on this PC, or not, by its answer in
skills.<name>.addedToAgents, and dev-home always. A skill this PC has no answer for follows its
default, from its dev-home-skill.json: added, unless it says it isn't recommended. Setup saves
such a skill as unanswered, the one thing a quiet run writes for it, and names it once in a NEW
line, with whether it was added. A skill goes into each skills folder whose agents meet its
supportedOn, the operating system and the agent, and anything there setup can't use keeps it off;
setup removes its links where it isn't added, with a line saying why, and records each skill's
state in internal/.generated/skill-states.json, which /dev-home skills shows. What its dependsOn
lists that this PC seems to lack, a program or a Python version, never keeps it off: the NEW line
says so, and /dev-home skills checks again where the agent runs. A skill whose
dev-home-skill.json can't be read is left as it is. One of the end user's own whose name breaks
the rule for names is a PROBLEM on every run, and still added, except one named synced, which
Claude Code keeps for the skills it downloads, and which setup never adds.

Each link to a folder is a junction on Windows, which needs no Developer Mode, and a symbolic link
elsewhere.

The skills run their scripts with Python 3.12 or later, as internal/.python/python.exe in
dev-home-toolkit's folder: a junction setup makes to the folder of a Python it finds, so the
skills' commands name the same short path on every PC.

For testing, the tests in internal/development/tests/ run a throwaway copy of this repo whose
local-settings.json sets testHomeDir. Setup then uses that folder instead of your profile, and
says so on every run. It ignores a CLAUDE_CONFIG_DIR outside that folder. Setup never writes
testHomeDir itself.

Options:

    --quiet                 Print only changes and problems. Prints nothing when everything is
                            already in place. Never asks anything, because agents run setup
                            this way: anything that needs an answer is reported instead.
    --content-dir <folder>  Your dev-home folder. Saved in local-settings.json, so later runs
                            don't need it.
    --configure             Changes a setting after the first run. At a console, every run
                            shows a menu of every setting after its questions, with or without
                            this: pick one to change, or go through them all. Without a
                            console, it shows what waits for an answer, then the settings and
                            how to change them.
    --configure '<name>=<value>'
                            Changes one setting, or answers one question, the way an agent
                            does, with no questions, then prints only changes and problems.
                            --configure with no setting says which names and values it takes,
                            and how to answer each question that waits.
    --what-if               Shows what it would change, without changing anything.

It asks a question only when a person can see it and answer: never with --quiet, and only when
its input comes from a real console and its output goes to one. Input that ends without an
answer counts as no.

Examples, in dev-home-toolkit's folder, with Python 3.12 or later:

    py setup.py --what-if
    py setup.py

The sync runs main(["--quiet"]) inside its own process, so keep main's name and arguments.
"""

import contextlib
import copy
import importlib
import json
import os
import re
import stat
import subprocess
from collections.abc import Collection, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from . import (
    claude_settings,
    codex_config,
    configure,
    console,
    generated,
    python_link,
    recycle_bin,
    requirements,
    rules,
)
from .computer import computer_name
from .git import run_git, with_pc_name
from .links import LinkInfo, is_link, link_info, make_folder_link, remove_folder_link
from .output import GREEN, RED, YELLOW, color, describe, first_line, status_line
from .paths import (
    comparable,
    forward,
    is_inside,
    real_path,
    resolve_home,
    same_path,
    unsafe_reason,
)
from .programs import SYNC_HOLDS_LOCK, by_hand, find_program
from .recommended_settings import (
    DONE,
    OLDER,
    Current,
    RecommendedSetting,
    for_agent,
    keys_for,
    offer_text,
    state_of,
)
from .recommended_settings import MISSING as MISSING_VALUE
from .recommended_settings import shown as json_text
from .settings import (
    ADDED_TO_AGENTS,
    AUTO_UPDATE,
    BY_PATH,
    CLAUDE_CODE,
    CODEX,
    CODEX_INSTRUCTIONS_MAX,
    DEV_HOME_SETTINGS,
    KNOWLEDGE_INDEX,
    MISSING,
    RULES_WARN_ABOVE,
    SCHEMA_VERSION,
    SETTINGS_PATH,
    STATE,
    TOOLKIT_ROOT,
    Agent,
    Checked,
    LocalSettings,
    Reminder,
    Setting,
    Skill,
    SkillDeclarations,
    answered,
    apply_changes,
    check_settings,
    dev_home_text,
    folder_rank,
    folder_reminders,
    get,
    layout,
    listed_entries,
    load_local_settings,
    local_settings_data,
    local_settings_text,
    order_folders,
    put,
    put_folder_state,
    put_recommended,
    read_dev_home_settings,
    read_value,
    recommended_answers,
    same_apart_from_order,
    saved_answer,
    saved_skill_path,
    setting_value,
    settings_in,
    settings_text,
    skill_declarations,
    written_alike,
    written_entry,
)
from .settings_files import (
    Plan,
    SettingsFile,
    line_diff,
    read_settings_file,
    to_lines,
    write_settings_file,
)

# What each folder Claude Code's settings.json gets in additionalDirectories is called, in the
# order settings_checks lists them.
ALLOWED_NAMES = ("dev-home", "dev-home-toolkit")
# Characters a claudeMdExcludes pattern reads as more than themselves. A backslash doesn't escape
# them on Windows, so home_claude_excludes writes ? for each, which matches any one character.
GLOB_SPECIAL = "*?[]{}()!@+\\"
GENERATED_ROOT = TOOLKIT_ROOT / "internal" / ".generated"
PYTHON_LINK = TOOLKIT_ROOT / "internal" / ".python"
GENERATED_FOLDERS = ("skills", "shared-skill-scripts", "last-written")
# A copy of the rules file setup last wrote in each agent's folder, and of dev-home's AGENTS.md
# and CLAUDE.md, by which it tells each from one an end user changed (decision 0064, "Each agent's
# rules file"), on this PC only.
LAST_WRITTEN = GENERATED_ROOT / "last-written"
# What setup decided for each skill on this PC, which facts.py's skills topic shows.
SKILL_STATES = GENERATED_ROOT / "skill-states.json"
# The Pythons that didn't run when setup checked them, which syncs skip (see sync_python_link).
# There only while one is noted.
FAILED_PYTHONS = GENERATED_ROOT / "failed-pythons.json"
FOLDER_NOTE = (
    "Setup writes everything in this folder: the files from templates/skills/ and\n"
    "templates/shared-skill-scripts/, with this PC's paths filled in; last-written/, a copy of\n"
    "the rules file it last wrote in each agent's folder, and of dev-home's AGENTS.md and\n"
    "CLAUDE.md; skill-states.json, what it decided for each skill on this PC; and, while there\n"
    "are any, failed-pythons.json, the Pythons that didn't run when setup checked them. Don't\n"
    "edit it: the next setup run rewrites it. Python writes the __pycache__ folders when the\n"
    "scripts run, to start them faster, and setup leaves those alone.\n"
)
OPERATING_TEMPLATE = TOOLKIT_ROOT / "templates" / "operating-rules" / "operating-rules.md"
# The rules file setup writes in each Claude Code folder's rules/, which Claude Code loads with
# every other .md file there, and in each Codex home, the one file Codex reads there.
CLAUDE_RULES_FILE = "dev-home-rules.md"
CODEX_RULES_FILE = "AGENTS.md"
# The file Codex reads in a home in place of AGENTS.md while it has text, which its docs call a
# temporary override. Setup never changes it, and reports it (decision 0064).
CODEX_OVERRIDE = "AGENTS.override.md"
# What the note of each file setup moves into rules/ from an agent's rules file says it holds
# (decision 0066).
MOVED_WHOLE = "The whole file, as it was before setup wrote its own there."
MOVED_LINES = "Lines setup didn't write in that file, under the headings they were under there."
# Each agent setup sets up, by the name a skill's supportedOn gives it, such as claude-code.
REQUIRES_NAMES = {shown: name for name, shown in requirements.AGENT_NAMES.items()}
# The files dev-home-toolkit owns in a dev-home that a new one starts with, filled in with this
# PC's paths (decision 0070, "Who owns each file in dev-home").
DEV_HOME_TEMPLATES = TOOLKIT_ROOT / "templates" / "dev-home"
# The two of those with this PC's commands, which setup writes in dev-home on every run and never
# commits, since dev-home's .gitignore lists them: its guidance for agents working there.
DEV_HOME_GUIDANCE = ("AGENTS.md", "CLAUDE.md")
# A test profile's Recycle Bin, a folder in the profile, so the tests never reach the real one
# (see Setup.to_the_bin).
TEST_BIN = "Recycle Bin"
# What setup creates the knowledge index with when it's missing: only its title.
KNOWLEDGE_INDEX_TEXT = "# Knowledge base\n"
# The skills folder every Codex home reads, in the profile folder. Of the agents setup sets up, only
# Codex reads it, so setup links the skills here for a yes to Codex, and removes its links here
# for a no.
# Adding an agent: other agents read this folder too, such as GitHub Copilot, Gemini CLI,
# and Cursor (their docs, read 2026-10-16). If setup ever sets up one of them, a no to Codex alone
# must no longer remove these links: setup links here while any agent that reads the folder is
# answered yes, and removes its links only once every one of them is answered no. See
# docs/development/decisions/0054-removing-what-setup-set-up.md.
AGENTS_SKILLS = Path(".agents") / "skills"


class CannotGoOnError(Exception):
    """Ends the run early, after a problem that the rest of setup can't get past."""


@dataclass(frozen=True)
class SettingsChange:
    """A change one of the agents' settings files needs: what it's for, the file, what the file
    needs, the plan, what to change by hand where setup can't make it, and what the change does,
    as the line saying it's made puts it, such as "added dev-home to writable_roots". recommended
    is the id of each recommended setting it writes, a person's yes, which is saved once the
    change is."""

    subject: str
    path: Path
    need: str
    plan: Plan
    how_to: str
    snippet: str
    done: str
    recommended: tuple[str, ...] = ()


# What a check of one settings file found: a line to report as it is, or a change it needs.
SettingsCheck = tuple[str, str] | SettingsChange


@dataclass(frozen=True)
class SkillPlan:
    """What setup does with one skill on this PC: the skills folders it's linked in, and those it's
    left out of, each with why, said to follow "which", such as "works only in Claude Code". state
    is how /dev-home skills and the NEW line show it, such as "added to your agents". told says
    whether the NEW line names it: not when the only reason it's left out is one nobody can act
    on, such as the operating system. warnings says what it needs that this PC seems to lack, such
    as a program, which the NEW line adds to its state; needs is every requirement of that kind,
    which /dev-home skills checks again where the agent runs. Both are empty for a skill that
    isn't added anywhere, since no agent uses it. A skill whose dev-home-skill.json can't be read
    is left as it is: in neither list."""

    name: str
    added_to: tuple[Path, ...]
    left_out: tuple[tuple[Path, str], ...]
    state: str
    told: bool
    warnings: tuple[str, ...] = ()
    needs: tuple[requirements.Requirement, ...] = ()


@dataclass(frozen=True)
class AgentFolders:
    """Where setup sets up each agent, by full path: each Claude Code folder and Codex home answered
    yes. And where it removes what it set up: each one answered no."""

    claude_dirs: list[str]
    codex_homes: list[str]
    declined_claude_dirs: list[str]
    declined_codex_homes: list[str]


@dataclass(frozen=True)
class Settled:
    """This PC's settings as the work saves them and acts on them (see Setup.settle). changes is
    what the check of the file moved, removed, and merged; matched has, by each shared agent's
    setting, the line saying which of its folders got the main folder's answer; new_skills names
    each skill marked as new to this PC; answered says whether a person changed a setting in this
    run;
    problem is why the settings can't be saved, or "" when they can; and out_of_order says the
    file as it is now lists an agent's folders out of order."""

    settings: LocalSettings
    changes: Checked
    matched: dict[str, str]
    new_skills: list[str]
    answered: bool
    problem: str = ""
    out_of_order: bool = False


@dataclass(frozen=True)
class Guidance:
    """One of dev-home's AGENTS.md and CLAUDE.md as setup finds it: its path; the copy setup keeps
    of what it last wrote there; data, what it writes there now, from the template with this PC's
    paths filled in; current, what's there, or None when nothing is; and kept, the copy's text, or
    None when there's no copy."""

    name: str
    path: Path
    copy: Path
    data: bytes
    current: bytes | None
    kept: bytes | None

    @property
    def edited(self) -> bool:
        """Whether it has a hand edit: text that's neither what setup writes now nor what it last
        wrote. With no copy, that's any text but what setup writes now, so text that may be setup's
        own older version goes to the Recycle Bin too, and nothing is lost."""
        return self.current is not None and self.current not in (self.data, self.kept)

    @property
    def before(self) -> bytes:
        """What the hand edit changed: the copy of what setup last wrote, or with no copy, what it
        writes now."""
        return self.data if self.kept is None else self.kept


@dataclass(frozen=True)
class GuidanceChoice:
    """What became of a hand edit at this run's questions (see Setup.ask_about_guidance), or by
    an answer through --configure (see Setup.answer_question): "sent", the Recycle Bin took it;
    "delete", a person chose to delete it for good, once the bin couldn't take it at a console;
    or "leave", the bin couldn't, and they chose to leave the file as edited, with why_not, why the
    bin couldn't take it. current is the file as it was then."""

    choice: str
    current: bytes
    why_not: str = ""


@dataclass(frozen=True)
class RulesTarget:
    """An agent's rules file: folder, the agent's folder; path, the file; agent, the agent's name
    in rules/, such as codex; and setting_up, whether the folder is answered yes, so setup writes
    the file, or no, so it removes it."""

    folder: Path
    path: Path
    agent: str
    setting_up: bool


@dataclass(frozen=True)
class FoundLines:
    """Lines setup didn't write in an agent's rules file: target, the file; current, its bytes;
    and moving, what moves into rules/ (see rules.to_move)."""

    target: RulesTarget
    current: bytes
    moving: rules.ToMove


@dataclass(frozen=True)
class RulesChoice:
    """What a person chose at this run's questions for lines setup didn't write in an agent's
    rules file, or for a file in unanswered/, there or through --configure (see
    Setup.answer_question): "move", into the mine/ of level, a level folder relative to rules/,
    such as codex; "sent", the Recycle Bin took them; or "delete", they chose to delete them for
    good. current is the file as it was then: the work acts on the choice only while the file is
    still the same (see Setup.ask_about_rules)."""

    choice: str
    current: bytes
    level: str = ""


@dataclass
class RulesChanges:
    """What a run changes in rules/ to save lines setup didn't write, all in one commit (see
    Setup.save_lines): the paths to commit; what each change does, for the commit's message;
    each file it wrote; each it removed, with what it held; and each file in unanswered/ a
    person answered, by how setup names it. A failed commit takes the writes and removals back,
    so nothing setup couldn't commit stays."""

    paths: list[Path] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    written: list[Path] = field(default_factory=list)
    removed: dict[Path, bytes] = field(default_factory=dict)
    answered: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WaitingFile:
    """A file in this PC's unanswered/ folders that setup asks about: path; agent, its agent's
    name in rules/, such as codex; current, its bytes; text, its rules without the note, as
    shown; source, the rules file its note's from field names, or "" for none; and loads, that
    rules file, where setup writes it, or None when the file loads nowhere."""

    path: Path
    agent: str
    current: bytes
    text: str
    source: str
    loads: Path | None


@dataclass(frozen=True)
class Waiting:
    """What waits for a person's answer, as --configure lists it for an agent and takes answers
    to it (see Setup.waiting): dev-home's folder; this PC's folder under rules/pcs/; each file in
    unanswered/ that setup asks about; and each of dev-home's AGENTS.md and CLAUDE.md with a hand
    edit."""

    content_root: Path
    pc: str
    files: list[WaitingFile]
    guidance: list[Guidance]


@dataclass(frozen=True)
class RecommendedOffer:
    """A recommended setting in a Claude Code folder set up (decision 0032): the folder, by its
    full path; its entry in this PC's settings, as written; the setting; what the folder has now;
    and its answer, if any: yes, no, or a reminder, as saved, or a yes this run has given, which
    pending marks, since the work writes and saves it later."""

    folder: Path
    entry: str
    setting: RecommendedSetting
    current: Current
    answer: bool | Reminder | None = None
    pending: bool = False

    @property
    def state(self) -> str:
        """What the folder's value is: the recommended one, missing, an older form, or another
        (see recommended_settings.state_of)."""
        return state_of(self.setting.agents[CLAUDE_CODE.group], self.current)

    @property
    def recommended(self) -> bool:
        """Whether a yes is what dev-home-toolkit recommends for this folder, which Enter gives:
        where the setting is missing or in an older form, and not where the folder has any other
        value, known, custom, or unknown, which Enter keeps."""
        return self.state in (MISSING_VALUE, OLDER)

    def waiting(self, today: date) -> bool:
        """Whether it waits for an answer: it has no yes or no, and no reminder before its date,
        and the folder's value isn't the recommended one already."""
        return self.state != DONE and not answered_for_now(self.answer, today)

    @property
    def about(self) -> tuple[console.Row, ...]:
        """What the offer says about it, fitted to what the folder has now."""
        rows = offer_text(self.setting, CLAUDE_CODE.group, self.current, "settings.json")
        return tuple(console.Row(*row) for row in rows)

    @property
    def question(self) -> str:
        return f"{self.setting.summary}?"

    @property
    def answer_text(self) -> str:
        """Its answer as the settings menu and the list for an agent show it."""
        if self.pending:
            return "yes, which setup writes once its questions are done"
        if self.answer is True:
            return "yes" if self.state == DONE else "yes, but the value changed since"
        if self.answer is False:
            return "no"
        if isinstance(self.answer, Reminder):
            on = self.answer.on
            return f"remind me on {on.isoformat()}" if on else "remind me"
        if self.state == DONE:
            return "none needed: it has the recommended value"
        return "not answered yet"

    @property
    def fingerprint(self) -> str:
        """What a yes to it through --configure carries, so setup writes it only while the folder
        has what the person saw (decision 0038)."""
        return configure.fingerprint(self.current.described.encode("utf-8"))


def cleanup(checked: Checked) -> list[str]:
    """What check_settings removed, moved, and merged, a sentence for each, for the line that says
    so."""
    sentences = []
    if checked.removed:
        them = "it" if len(checked.removed) == 1 else "them"
        sentences.append(f"Removed {', '.join(checked.removed)}: nothing declares {them} any more")
    if checked.moved:
        names = "its new name" if len(checked.moved) == 1 else "their new names"
        sentences.append(f"Moved {', '.join(checked.moved)}, {names}")
    sentences += [
        f"Merged {merge.path} {and_list(merge.entries)}, which name the same folder, into "
        f"{merge.kept}, keeping the answer: {configure.answer_text(merge.answer)}"
        for merge in checked.merged
    ]
    return sentences


class Setup:
    """One run of setup."""

    def __init__(
        self,
        *,
        quiet: bool,
        what_if: bool,
        configure: str | None = None,
        sync_holds_lock: bool = False,
    ) -> None:
        # --configure: None without it, "" alone (the menu, or the settings shown), or one
        # assignment, such as updates.installAutomatically=true, which an agent gives instead of
        # answering.
        self.configure = configure
        # Set when a sync runs this setup, holding the lock that its save would otherwise take.
        self.sync_holds_lock = sync_holds_lock
        self.assigned = bool(configure)
        # An agent reads only what changed and what's wrong, as with --quiet.
        self.quiet = quiet or self.assigned
        self.what_if = what_if
        self.can_ask = not self.quiet and console.is_console()
        # dev-home.json's answer that a question, the menu, or --configure chose, which
        # confirm_copies shows, and the work then writes.
        self.wanted_copies: bool | None = None
        # That change once shown, and confirmed: dev-home.json's layout and text as shown, the
        # new text, and the answer.
        self.copies_change: tuple[str, str, str, bool] | None = None
        # Set once the menu changes a setting, so the save keeps a backup.
        self.changed_by_hand = False
        # Set when --configure only shows the settings, so the run ends with no summary.
        self.just_showing = False
        self.problems: list[str] = []
        self.unknown_placeholders: list[str] = []
        self.generated_changes = 0
        # The least each Codex home's project_doc_max_bytes is set to, from this PC's settings as
        # this run has them (see codex_doc_bytes).
        self.codex_doc_bytes = codex_doc_bytes({})
        # The line saying which of a shared agent's folders got the main folder's answer, by the
        # agent's setting, printed once the settings are saved, unless a person answers for the
        # agent's folders first.
        self.matched: dict[str, str] = {}
        # What a person changed in this PC's settings in this run, as the settings before and
        # after each step that takes their answers, apart from setup's own changes in between,
        # which the work makes in the file as it is by then (see answering and settle).
        self.answers: list[tuple[dict[str, Any], dict[str, Any]]] = []
        # What the check of this PC's settings at the start of the run moved, removed, and merged.
        self.checked = Checked({})
        # What the profile folder holds, listed once a run (see profile_folders).
        self.profile_entries: list[Path] | None = None
        # What the skills declare, read once a run with this PC's settings, for the dev-home
        # folder named here (see skills_declared).
        self.declared: tuple[str, SkillDeclarations] | None = None
        # Set once this run clones dev-home, which then may have another copy still in use, or
        # creates one, which nothing else can be using yet.
        self.cloned = False
        self.created = False
        # The profile folder to set up: yours, unless local-settings.json sets testHomeDir.
        self.home = Path.home()
        # Set when local-settings.json sets testHomeDir, whose profile has its own Recycle Bin.
        self.test_profile = False
        # What became of each hand edit to dev-home's AGENTS.md and CLAUDE.md at this run's
        # questions, by the file's name (see ask_about_guidance).
        self.guidance_choices: dict[str, GuidanceChoice] = {}
        # Where a person chose at this run's questions that lines setup didn't write go, by the
        # path of the agent's rules file or of the file in unanswered/ (see ask_about_rules).
        self.rules_choices: dict[str, RulesChoice] = {}
        # Each yes to a recommended setting in this run, by the Claude Code folder's full path and
        # the setting's id, with what the folder had when the person answered. The work writes it
        # only while the folder still has that, then saves the yes (see save_recommended).
        self.recommended_yes: dict[tuple[str, str], Current] = {}
        # Each such yes whose folder has the recommended value by the work, so it's saved with no
        # write; and each the work leaves out, whose answer goes, so its offer comes back; by the
        # folder's full path and the setting's id.
        self.recommended_already: list[tuple[Path, str]] = []
        self.recommended_left_out: list[tuple[Path, str]] = []
        # Set once this run's save backs up this PC's settings, so a later save in the run
        # doesn't back them up again; and when the save couldn't be made, so no later one is.
        self.settings_backed_up = False
        self.save_failed = False

    # Talking to the person

    def line(self, text: str = "", code: str = "") -> None:
        print(color(text, code) if code else text, flush=True)

    def status(self, state: str, message: str) -> None:
        """A status line, counted: problems set the exit code. With --quiet, OK lines are left
        out."""
        if state == "PROBLEM":
            self.problems.append(message)
        if self.quiet and state == "OK":
            return
        status_line(state, message)

    def should(self, target: object, action: str) -> bool:
        """Whether to make a change. With --what-if, says what it would do instead."""
        if self.what_if:
            self.line(f"What if: {action}: {target}")
            return False
        return True

    def ask(self, question: str, default: str = "") -> str | None:
        return console.ask(question, default) if self.can_ask else None

    def confirm(self, question: str) -> bool:
        return console.confirm(question) if self.can_ask else False

    def choose(self, question: str, default: bool | None = None) -> bool | None:
        return console.choose(question, default) if self.can_ask else None

    def choose_from_list(
        self,
        intro: str,
        question: str,
        items: Sequence[console.ListItem],
        details: str = "",
        marks: tuple[str, str] = console.MARKS,
    ) -> console.ListAnswer | None:
        """The shared prompt for every list of optional items, or None without a console."""
        if not self.can_ask:
            return None
        return console.choose_from_list(intro, question, items, details, marks)

    def choose_offer(
        self, question: str, recommended: bool, reminder: Reminder | None = None
    ) -> console.OfferAnswer | None:
        """The question about one offer (see console.choose_offer), or None without a console.
        With a reminder, Enter keeps it."""
        if not self.can_ask:
            return None
        return console.choose_offer(question, recommended, keep_text(reminder))

    def choose_or_default(self, question: str, setting: Setting, data: dict[str, Any]) -> object:
        """Asks about a yes-or-no setting with a default, one of dev-home-toolkit's own or a
        skill's preference, saved in data: yes, no, or follow the default. Returns the answer as
        it's saved (see saved_answer), or MISSING when no answer came. Enter keeps a saved yes or
        no, and otherwise follows the default."""
        if not self.can_ask:
            return MISSING
        saved = get(data, setting.path, MISSING)
        enter: bool | str = saved if isinstance(saved, bool) else console.DEFAULT
        answer = console.choose_or_default(question, bool(setting.default), enter)
        return MISSING if answer is None else saved_answer(answer)

    # The questions about settings, which the first run and --configure's menu both ask.

    def ask_auto_update(self, data: dict[str, Any]) -> object:
        """Whether a sync installs updates by itself, as choose_or_default returns it."""
        self.line(
            "sync.py can pull dev-home-toolkit updates on every sync, or only tell you when there "
            "are some,"
        )
        self.line("so you can look at them first and pull them with update.py.")
        return self.choose_or_default("Pull updates automatically?", BY_PATH[AUTO_UPDATE], data)

    def introduce_folders(self, agent: Agent, folders: Sequence[Path]) -> None:
        """Before a question about an agent's folders: which they are, then what a yes does (see
        yes_does), each after a blank line."""
        several = len(folders) > 1 or agent.shared
        kind = f"{agent.name} {agent.folder}{'s' if several else ''}"
        self.line()
        self.line(f"{kind}: {folder_list(folders) or 'none found yet'}")
        self.line()
        does = yes_does(
            agent,
            several=len(folders) > 1,
            guarded=self.any_guarded(agent, folders),
            doc_bytes=self.codex_doc_bytes,
        )
        for text in console.wrap(does):
            self.line(text)
        self.line()

    def any_guarded(self, agent: Agent, folders: Sequence[Path]) -> bool:
        """Whether any of the folders a question is about gets home_claude_excludes (see
        guarded)."""
        return agent == CLAUDE_CODE and any(self.guarded(folder) for folder in folders)

    def ask_folder(
        self, agent: Agent, folder: Path, current: bool | Reminder | None
    ) -> console.OfferAnswer | None:
        """Whether to set up one of an agent's folders: yes or no for one answered already, with
        Enter keeping its answer; otherwise an offer, recommended, where Enter keeps a reminder,
        and takes yes for one with no answer yet. None when no answer came."""
        question = folder_question(agent, folder)
        if isinstance(current, bool):
            return self.choose(question, current)
        return self.choose_offer(question, True, current)

    def ask_codex(
        self, homes: Sequence[Path], current: bool | Reminder | None
    ) -> console.OfferAnswer | None:
        """Whether to set up Codex, in every Codex home, which all read the same skills, asked as
        ask_folder asks about a folder. None when no answer came."""
        self.introduce_folders(CODEX, homes)
        if isinstance(current, bool):
            return self.choose(CODEX_QUESTION, current)
        return self.choose_offer(CODEX_QUESTION, True, current)

    def ask_copies(self, current: bool | None) -> bool | None:
        """Whether dev-home is in active use anywhere besides this PC. With no answer yet, there's
        no default: both wrong answers cost something."""
        self.line(
            "dev-home can live on one PC (single-PC mode), as a private backup with its history on "
            "GitHub,"
        )
        self.line(
            "or be used from several (multi-PC mode), which then check GitHub before each command."
        )
        return self.choose(
            "Is dev-home in active use anywhere besides this PC, such as on another PC or in a "
            "cloud session?",
            current,
        )

    def print_diff(self, old_text: str, new_text: str, indent: str = " " * 12) -> None:
        """The lines a change adds (+) and removes (-), with a few around them, each set in by
        indent."""
        diff = line_diff(to_lines(old_text), to_lines(new_text))
        limit = 40
        for diff_line in diff[:limit]:
            code = (
                GREEN if diff_line.startswith("+ ") else RED if diff_line.startswith("- ") else ""
            )
            self.line(indent + diff_line, code)
        if len(diff) > limit:
            self.line(f"{indent}...and {len(diff) - limit} more lines.")

    def finish(self) -> int:
        """Prints the summary, and returns 0 when there were no problems, 1 otherwise."""
        if self.what_if and not self.quiet:
            self.line()
            self.line("This was a preview (--what-if). Nothing was changed.", YELLOW)
        if not self.problems:
            if not (self.quiet or self.what_if or self.just_showing):
                self.line()
                self.line("All checks passed.", GREEN)
            return 0
        if not self.quiet:
            self.line()
            self.line(f"{len(self.problems)} problem(s) to fix. Run setup.py again afterward.", RED)
        return 1

    def not_a_dev_home_problem(self, folder: Path) -> None:
        self.status(
            "PROBLEM",
            f"{folder} doesn't look like a dev-home: it has no {DEV_HOME_SETTINGS}, which every "
            "dev-home has, so setup stopped before setting anything in it. If it is your dev-home, "
            f"put {DEV_HOME_SETTINGS} back from its git history; if not, point setup at your "
            "dev-home with --content-dir.",
        )

    def set_aside_settings(self, settings: LocalSettings) -> LocalSettings:
        """A local-settings.json from before the settings were grouped can't be read. A person can
        have it renamed to a dated backup, and answer setup's questions again. Only testHomeDir
        comes along, so a test sandbox's setup never reaches the real profile."""
        if not self.can_ask:
            self.status(
                "PROBLEM",
                f"{SETTINGS_PATH} is in an older layout, from before its settings were grouped, so "
                f"setup can't read it. Run {by_hand('setup.py')} in a terminal: it offers to set "
                "the file aside and ask its questions again.",
            )
            raise CannotGoOnError
        self.line(f"{SETTINGS_PATH} is in an older layout, from before its settings were grouped.")
        self.line("Setup can rename it to a dated backup, then ask its questions again.")
        if not self.choose("Set it aside and answer the questions again?", True):
            self.status("PROBLEM", f"Stopped: {SETTINGS_PATH} is in an older layout.")
            raise CannotGoOnError
        fresh = LocalSettings(test_home_dir=settings.test_home_dir, found=True)
        if self.should(SETTINGS_PATH, "Rename it to a dated backup, and start a new one"):
            try:
                backup = write_settings_file(
                    SETTINGS_PATH, local_settings_text(fresh), bom=False, backup=True
                )
            except OSError as error:
                self.status("PROBLEM", f"Could not set {SETTINGS_PATH} aside. {error}")
                raise CannotGoOnError from error
            self.status("SET", f"The old settings, set aside: {backup}")
        return fresh

    @contextlib.contextmanager
    def work_lock(self, content_root: Path) -> Iterator[bool]:
        """The sync's lock on dev-home, held for setup's work, after its questions, so a sync in
        another session can't set up at the same moment, or save this PC's settings in between,
        and no sync waits while a question does. A sync that runs setup holds it already, and a
        preview changes nothing. Yields whether the work may go on: True also when there's no
        lock to take, for a dev-home whose .git isn't a folder, or a lock file that can't be
        opened, which nothing else can hold either."""
        git_dir = content_root / ".git"
        if self.sync_holds_lock or self.what_if or not git_dir.is_dir():
            yield True
            return
        # Loaded only now, as for committing dev-home.json.
        sync = importlib.import_module(f"{__package__}.sync")
        with contextlib.ExitStack() as held:
            owned = True
            with contextlib.suppress(sync.LockError):
                owned = held.enter_context(sync.one_run_at_a_time(git_dir))
            if not owned:
                self.status(
                    "PROBLEM",
                    f"Setup changed nothing: a sync, or an update, has been using dev-home for "
                    f"{sync.LOCK_WAIT_SECONDS // 60} minutes. Run {by_hand('setup.py')} again "
                    "shortly.",
                )
            yield owned

    def save(self, settled: Settled) -> bool:
        """Saves this PC's settings as the work settled them, when anything changed, and returns
        whether it saved. When a person changed a setting, or the check moved, removed, or merged
        one, the save says so in one line, which names what was moved, removed, or merged, and
        backs the file up first when a person changed a setting, through the menu or --configure,
        or a setting was removed, or entries were merged. When the only changes are what
        setup records by itself, the answers a shared
        agent's folders got from the main one and the skills new to this PC, it keeps no backup,
        since nobody changed a setting, and the lines saying what it records stand for its own.
        With no change at all, it only puts an agent's folders back in order."""
        changes = settled.changes
        changed = settled.answered or bool(changes.moved or changes.removed or changes.merged)
        if not (changed or settled.matched or settled.new_skills):
            if settled.out_of_order and not self.what_if:
                self.put_in_order()
            return False
        if changed and not self.should(SETTINGS_PATH, "Save this PC's settings"):
            for sentence in cleanup(changes):
                self.line(f"What if: {sentence}")
            return False
        if self.what_if:
            return False
        if settled.problem:
            self.status("PROBLEM", settled.problem)
            self.save_failed = True
            return False
        backup = changed and (
            self.changed_by_hand or self.assigned or bool(changes.removed or changes.merged)
        )
        text = local_settings_text(settled.settings)
        try:
            kept = write_settings_file(SETTINGS_PATH, text, bom=False, backup=backup)
        except OSError as error:
            self.status("PROBLEM", f"Could not save this PC's settings in {SETTINGS_PATH}. {error}")
            self.save_failed = True
            return False
        self.settings_backed_up = bool(kept)
        if changed:
            notes = "".join(f". {sentence}" for sentence in cleanup(changes))
            if backup:
                notes += f". Backup of the old file: {kept}" if kept else " (new file)"
            self.status("SET", f"This PC's settings: {SETTINGS_PATH}{notes}")
        return True

    def put_in_order(self) -> None:
        """Puts an agent's folders back in order in this PC's settings, such as after a hand edit,
        with no backup and no line, once it's sure only their order changes."""
        try:
            text = SETTINGS_PATH.read_text(encoding="utf-8-sig")
            data = json.loads(text)
        except (OSError, ValueError):
            # Changed since this run read it: the next run puts it in order.
            return
        moved = order_folders(data, self.home) if isinstance(data, dict) else []
        if not moved:
            return
        ordered = settings_text(data)
        if not same_apart_from_order(text, ordered):
            kinds = and_list([f"{agent.name} {agent.folder}s" for agent in moved])
            self.status(
                "PROBLEM",
                f"{SETTINGS_PATH} lists {kinds} out of order, and putting them in order would "
                "change more than their order, so setup left the file as it is. Look for a key "
                "written twice, and fix it there.",
            )
            return
        try:
            write_settings_file(SETTINGS_PATH, ordered, bom=False, backup=False)
        except OSError as error:
            self.status("PROBLEM", f"Could not save this PC's settings in {SETTINGS_PATH}. {error}")

    @contextlib.contextmanager
    def answering(self, settings: LocalSettings) -> Iterator[None]:
        """Around a step that takes a person's answers, at a question, in the menu, or through
        --configure or --content-dir: records what they changed in this PC's settings, which the
        work makes in the file as it is by then (see settle). A change setup makes by itself
        between two such steps is no answer of theirs, so it's left out."""
        before = local_settings_data(settings)
        yield
        self.answers.append((before, local_settings_data(settings)))

    def settle(
        self, settings: LocalSettings, read: dict[str, Any] | None, declared: SkillDeclarations
    ) -> Settled:
        """This PC's settings as the work saves them and acts on them, worked out while it holds
        the sync's lock, so no other run saves in between. It reads the file again, since another
        run may have saved it while this one asked its questions or waited for the lock, such as a
        sync, or --configure in another session. It makes there only the changes a person made in
        this run (see answering), which win over the other run's where both changed a setting.
        Then it works out again from that each change setup makes by itself, so none comes from an
        earlier read: the check's moves, removals, and merges (see check_settings, which removes
        a setting nothing declares only when read held it), the answer a shared agent's folders
        share (see match_shared_answer), and the marks for skills new to this PC (see
        note_new_skills).

        A sync's setup reads nothing again: it has held the lock since before it read the file,
        so nothing else has saved it, and its own settings, checked and matched at its start, are
        the file's. When the file is missing now, this run's own settings stand for it. When it
        can't be read now, or is in a layout this setup doesn't know, they're worked out for the
        work alone, with the reason they can't be saved."""
        answered = any(not written_alike(before, after) for before, after in self.answers)
        problem = ""
        # The file as it is now, when the work goes on from it.
        newer: LocalSettings | None = None
        if not self.sync_holds_lock:
            now = load_local_settings()
            if now is None:
                problem = (
                    f"This PC's settings weren't saved: {SETTINGS_PATH} changed while setup ran, "
                    "and can't be read now. Fix it, then run setup.py again."
                )
            elif now.found and layout(now.data, SCHEMA_VERSION):
                problem = (
                    f"This PC's settings weren't saved: {SETTINGS_PATH} changed while setup ran, "
                    "to a layout this setup doesn't know. Run setup.py again."
                )
            elif now.found:
                newer = now
        if newer is None:
            result = settings_in(local_settings_data(settings))
            new_skills = self.note_new_skills(result, declared)
            return Settled(
                result,
                self.checked,
                dict(self.matched),
                new_skills,
                answered,
                problem,
                read is not None and bool(order_folders(copy.deepcopy(read), self.home)),
            )
        changes = check_settings(
            newer.data,
            declared,
            home=self.home,
            remove_gone_skills=False,
            seen=read if read is not None else {},
        )
        for found in changes.problems:
            if found not in self.problems:
                self.status("PROBLEM", found)
        start = local_settings_data(settings_in(changes.data))
        for before, after in self.answers:
            apply_changes(start, before, after)
        result = settings_in(start)
        self.matched = {}
        for agent in (CLAUDE_CODE, CODEX):
            if agent.shared:
                self.match_shared_answer(agent, result)
        new_skills = self.note_new_skills(result, declared)
        return Settled(
            settings_in(local_settings_data(result)),
            changes,
            dict(self.matched),
            new_skills,
            answered,
            out_of_order=bool(order_folders(copy.deepcopy(newer.data), self.home)),
        )

    # The agents' folders: Claude Code folders and Codex homes

    def found_folders(self, agent: Agent) -> list[Path]:
        """Each of an agent's folders setup finds, to offer: those in the profile folder (see
        profile_folders), then the session's own (see session_folder)."""
        found = self.profile_folders(agent)
        session = self.session_folder(agent)
        if session is not None and not any(same_path(session, folder) for folder in found):
            found.append(session)
        return found

    def profile_folders(self, agent: Agent) -> list[Path]:
        """An agent's folders in the profile folder: its default one, such as ~/.claude, once the
        agent has made it, which is how setup knows the agent is on this PC, then each extra one,
        such as ~/.claude-<name>, for another account, which the agent's variable, such as
        CLAUDE_CONFIG_DIR, points a session to. A profile folder that can't be listed has only the
        default one to offer."""
        default = self.home / agent.default
        found = [default] if default.is_dir() else []
        if self.profile_entries is None:
            try:
                self.profile_entries = list(self.home.iterdir())
            except OSError:
                return found
        # The name first, so only a folder with the right name costs a look on disk.
        return found + sorted(
            f
            for f in self.profile_entries
            if f.name.lower().startswith(agent.default + "-")
            and f.is_dir()
            and (not agent.marks or any((f / mark).is_file() for mark in agent.marks))
        )

    def session_folder(self, agent: Agent) -> Path | None:
        """The folder in the agent's variable, such as CLAUDE_CONFIG_DIR, when that's set and the
        folder exists: the one the session running setup uses. A test profile takes it only from
        inside itself, so the real one is never touched."""
        value = os.environ.get(agent.variable)
        if not value:
            return None
        folder = Path(comparable(resolve_home(value, self.home)))
        inside_home = os.path.normcase(str(folder)).startswith(
            os.path.normcase(comparable(self.home)) + os.sep
        )
        if not (same_path(self.home, Path.home()) or inside_home) or not folder.is_dir():
            return None
        return folder

    def known_folders(self, agent: Agent, settings: LocalSettings) -> list[Path]:
        """Each of an agent's folders setup knows of that's there, each once: those it finds (see
        found_folders), and the others with an entry, in order, the default one first (see
        folder_rank), which for a shared agent is the main one."""
        folders = self.found_folders(agent)
        for entry in listed_entries(get(settings.data, agent.setting)):
            folder = Path(comparable(resolve_home(entry, self.home)))
            if folder.is_dir() and not any(same_path(folder, f) for f in folders):
                folders.append(folder)
        folders.sort(key=lambda folder: folder_rank(agent, folder, self.home))
        return folders

    def entry_named(self, folder: str | Path, entries: Iterable[str]) -> str | None:
        """The first of the entries, as written, such as those with an answer, that names this
        folder, if any."""
        return next(
            (
                entry
                for entry in entries
                if entry.strip() and same_path(resolve_home(entry, self.home), folder)
            ),
            None,
        )

    def entry_for(self, agent: Agent, settings: LocalSettings, folder: Path) -> str:
        """The entry to write a folder's answer in: the one that names it already, with an answer
        or not, as written, or a new one, as setup writes folders (see folder_entry)."""
        entries = [
            *settings.folders[agent.setting],
            *listed_entries(get(settings.data, agent.setting)),
        ]
        return self.entry_named(folder, entries) or self.folder_entry(folder)

    def shared_answer(
        self, agent: Agent, settings: LocalSettings, folders: Sequence[Path] | None = None
    ) -> tuple[bool | None, Path | None]:
        """A shared agent's answer for all its folders, and the folder that gives it: the first
        of the folders there, in order (see known_folders), that has an answer, which is the main
        folder unless it has none. None, None when none has one."""
        answers = settings.folders[agent.setting]
        for folder in self.known_folders(agent, settings) if folders is None else folders:
            entry = self.entry_named(folder, answers)
            if entry is not None:
                return answers[entry], folder
        return None, None

    def answer_every_folder(self, agent: Agent, settings: LocalSettings, answer: bool) -> None:
        """Gives a shared agent's answer, from a person, to every one of its folders: each entry,
        those for folders that are gone and those with a reminder included, and each folder there
        without one. That replaces any answer the folders got from the main one in this run, so
        its line goes."""
        self.matched.pop(agent.setting, None)
        answers = settings.folders[agent.setting]
        for entry in [*answers, *self.reminders(agent, settings)]:
            answers[entry] = answer
        for folder in self.known_folders(agent, settings):
            if self.entry_named(folder, answers) is None:
                answers[self.entry_for(agent, settings, folder)] = answer

    def reminders(self, agent: Agent, settings: LocalSettings) -> dict[str, Reminder]:
        """Each of an agent's folders whose answer is a reminder, by its entry as written, with
        it. A yes or a no given in this run wins over a reminder its entry still holds."""
        answers = settings.folders[agent.setting]
        found = folder_reminders(get(settings.data, agent.setting))
        return {entry: reminder for entry, reminder in found.items() if entry not in answers}

    def reminder_of(
        self,
        agent: Agent,
        settings: LocalSettings,
        folder: Path,
        known: Sequence[Path] | None = None,
    ) -> Reminder | None:
        """A folder's reminder, if its answer is one. A shared agent has one for all its folders:
        the first of those there, in order, that has one (see shared_answer), from known, when the
        caller has them already."""
        found = self.reminders(agent, settings)
        if not agent.shared:
            folders: Sequence[Path] = [folder]
        else:
            folders = self.known_folders(agent, settings) if known is None else known
        for each in folders:
            entry = self.entry_named(each, found)
            if entry is not None:
                return found[entry]
        return None

    def answer_offer(
        self, agent: Agent, settings: LocalSettings, folder: Path, answer: console.OfferAnswer
    ) -> None:
        """Saves a person's answer to the offer to set up one of an agent's folders, in the entry
        that names it, or a new one: a yes or a no, which the save writes over a reminder, in its
        place; a reminder; or skip, which ends a reminder that was due, so it's unanswered again.
        KEEP changes nothing."""
        entry = self.entry_for(agent, settings, folder)
        if isinstance(answer, bool):
            settings.folders[agent.setting][entry] = answer
        elif isinstance(answer, console.RemindIn):
            settings.folders[agent.setting].pop(entry, None)
            put_folder_state(settings.data, agent.setting, entry, Reminder(answer.on).saved)
        elif answer == console.SKIP:
            put_folder_state(settings.data, agent.setting, entry, None)

    def answer_offer_every_folder(
        self, agent: Agent, settings: LocalSettings, answer: console.OfferAnswer
    ) -> None:
        """Saves a person's answer to the offer to set up a shared agent for every one of its
        folders (see answer_offer): each entry, and each folder there without one, as
        answer_every_folder gives a yes or a no."""
        if isinstance(answer, bool):
            self.answer_every_folder(agent, settings, answer)
            return
        if answer == console.KEEP:
            return
        entries = [*settings.folders[agent.setting], *self.reminders(agent, settings)]
        folders = [Path(comparable(resolve_home(entry, self.home))) for entry in entries]
        for folder in [*folders, *self.known_folders(agent, settings)]:
            self.answer_offer(agent, settings, folder, answer)

    def match_shared_answer(self, agent: Agent, settings: LocalSettings) -> None:
        """Gives each of a shared agent's folders that's there the shared answer (see
        shared_answer), when its own differs or it has none, such as a new folder, or one whose
        answer was changed by hand, and keeps a line saying so for after the save."""
        folders = self.known_folders(agent, settings)
        answer, source = self.shared_answer(agent, settings, folders)
        if answer is None or source is None:
            return
        answers = settings.folders[agent.setting]
        changed: list[str] = []
        for folder in folders:
            entry = self.entry_named(folder, answers)
            if entry is None or answers[entry] is not answer:
                entry = entry or self.entry_for(agent, settings, folder)
                answers[entry] = answer
                changed.append(entry)
        if not changed:
            return
        done = "set up" if answer else "turned off"
        self.matched[agent.setting] = (
            f"dev-home is now {done} for {agent.name} in {and_list(changed)}, to match "
            f"{self.entry_named(source, answers)}. {agent.name} only supports one set of skills "
            f"for all your {agent.name} {agent.folder}s, so they share one setting."
        )

    def folder_entry(self, folder: Path) -> str:
        """How a folder is written in local-settings.json (see written_entry)."""
        return written_entry(folder, self.home)

    def listed(self, folder: str | Path, entries: list[str]) -> bool:
        """Whether a folder is one of the entries, which may start with ~."""
        return any(
            same_path(resolve_home(entry, self.home), folder) for entry in entries if entry.strip()
        )

    # Recommended settings, in each Claude Code folder set up (decision 0032)

    def older_place_file(self, claude_dir: Path, place: str) -> Path:
        """The file older versions of Claude Code kept a setting in, for a Claude Code folder, by
        its name, such as .claude.json: in the profile folder for ~/.claude, and inside the
        folder for any other."""
        if same_path(claude_dir, self.home / CLAUDE_CODE.default):
            return self.home / place
        return claude_dir / place

    def current_values(
        self,
        claude_dir: Path,
        ids: Collection[str] | None = None,
        file: SettingsFile | None = None,
    ) -> tuple[dict[str, Current], str]:
        """Each recommended setting as a Claude Code folder has it now, by its id, or only those
        in ids: from its settings.json, as file has it when the caller read it already, or where
        that has none and the setting has an older place, from there, which Claude Code uses
        only then. None, with why, when setup won't rewrite the settings.json, so a yes couldn't
        be written."""
        if file is None:
            file = claude_settings.read_file(claude_dir / "settings.json")
        data, reason = claude_settings.settings_object(file)
        if data is None:
            return {}, reason
        found: dict[str, Current] = {}
        older: dict[str, dict[str, Any] | None] = {}
        for entry in for_agent(CLAUDE_CODE.group):
            if ids is not None and entry.id not in ids:
                continue
            form = entry.agents[CLAUDE_CODE.group]
            if form.key in data:
                found[entry.id] = Current("settings.json", data[form.key])
                continue
            if form.older_place:
                if form.older_place not in older:
                    place = self.older_place_file(claude_dir, form.older_place)
                    older[form.older_place] = read_json_object(place)
                kept = older[form.older_place]
                if kept is not None and form.key in kept:
                    found[entry.id] = Current(form.older_place, kept[form.key])
                    continue
            found[entry.id] = Current()
        return found, ""

    def recommended_in(
        self, settings: LocalSettings, entry: str, folder: Path
    ) -> tuple[list[RecommendedOffer], str]:
        """Every recommended setting in one Claude Code folder, by its entry and full path, with
        what the folder has now and its answer: the one saved, or a yes this run has given, which
        the work writes. None, with why, when setup won't rewrite the folder's settings.json."""
        current, reason = self.current_values(folder)
        if reason:
            return [], reason
        return self.offers_of(settings, entry, folder, current), ""

    def offers_of(
        self, settings: LocalSettings, entry: str, folder: Path, current: Mapping[str, Current]
    ) -> list[RecommendedOffer]:
        """Each recommended setting in current, what one Claude Code folder has now, by id, with
        its answer: the one saved in the folder's entry, or a yes this run has given."""
        answers = recommended_answers(get(settings.data, CLAUDE_CODE.setting), entry)
        offers = []
        for setting in for_agent(CLAUDE_CODE.group):
            if setting.id not in current:
                continue
            pending = (yes_key(folder), setting.id) in self.recommended_yes
            answer = True if pending else answers.get(setting.id)
            offers.append(
                RecommendedOffer(folder, entry, setting, current[setting.id], answer, pending)
            )
        return offers

    def recommended_offers(
        self, settings: LocalSettings
    ) -> list[tuple[str, Path, list[RecommendedOffer]]]:
        """For each Claude Code folder set up that's there, by its entry and full path, the
        recommended settings that wait for an answer there (see RecommendedOffer.waiting). None
        where setup won't rewrite the folder's settings.json, since a yes couldn't be written."""
        today = date.today()
        found: list[tuple[str, Path, list[RecommendedOffer]]] = []
        for entry, full in self.folders_answered(CLAUDE_CODE, settings, True):
            # Only one with no yes or no, and no reminder before its date, can wait, so once
            # none can, every sync after that reads none of the folder's files, and none but
            # those is read for.
            answers = recommended_answers(get(settings.data, CLAUDE_CODE.setting), entry)
            open_ids = [
                setting.id
                for setting in for_agent(CLAUDE_CODE.group)
                if not answered_for_now(answers.get(setting.id), today)
                and (yes_key(full), setting.id) not in self.recommended_yes
            ]
            if not open_ids:
                continue
            current, _ = self.current_values(Path(full), open_ids)
            offers = self.offers_of(settings, entry, Path(full), current)
            waiting = [offer for offer in offers if offer.waiting(today)]
            if waiting:
                found.append((entry, Path(full), waiting))
        return found

    def ask_about_recommended(self, settings: LocalSettings) -> None:
        """Offers the recommended settings with no answer yet, or a reminder that's due, in each
        Claude Code folder set up: at a console, in the shared prompt for optional lists, one list
        for each folder, each setting described in plain words, fitted to what the folder has
        now. A quiet run, or one where no answer came, names the folders in a NEW line instead."""
        offers = self.recommended_offers(settings)
        if not offers:
            return
        unanswered: list[tuple[str, int]] = []
        for entry, folder, items in offers:
            answer = self.choose_recommended(folder, items) if self.can_ask else None
            if answer is None:
                unanswered.append((entry, len(items)))
            else:
                self.answer_recommended(settings, items, answer.answers)
        if unanswered:
            self.status("NEW", recommended_new_text(unanswered))

    def choose_recommended(
        self, folder: Path, offers: Sequence[RecommendedOffer]
    ) -> console.ListAnswer | None:
        """The answer to one folder's list of recommended settings, by each setting's summary,
        after the list, each with what a yes changes there. A list of one asks its question alone,
        so its folder and what a yes changes come first."""
        items = [
            console.ListItem(offer.setting.summary, offer.recommended, offer.question, offer.about)
            for offer in offers
        ]
        intro = f"Settings dev-home-toolkit recommends for Claude Code in {folder}:"
        self.line()
        if len(items) == 1:
            self.line(intro)
            self.line()
            console.show_items(items, RECOMMENDED_MARKS)
            self.line()
            return self.choose_from_list("", "", items)
        return self.choose_from_list(
            intro, "Make these changes in its settings.json?", items, marks=RECOMMENDED_MARKS
        )

    def answer_recommended(
        self,
        settings: LocalSettings,
        offers: Sequence[RecommendedOffer],
        answers: Mapping[str, console.OfferAnswer],
    ) -> None:
        """Keeps a person's answers to a folder's recommended settings, by each one's summary: a
        no or a reminder in the folder's entry, and skip ending a reminder that's due, so it's
        unanswered again. A yes waits for the work, which saves it once its change is written
        (see recommended_yes). KEEP changes nothing."""
        for offer in offers:
            answer = answers.get(offer.setting.summary, console.KEEP)
            if answer is True:
                self.recommended_yes[(yes_key(offer.folder), offer.setting.id)] = offer.current
            elif answer is False:
                put_recommended(
                    settings.data, CLAUDE_CODE.setting, offer.entry, offer.setting.id, False
                )
            elif isinstance(answer, console.RemindIn):
                put_recommended(
                    settings.data,
                    CLAUDE_CODE.setting,
                    offer.entry,
                    offer.setting.id,
                    Reminder(answer.on),
                )
            elif answer == console.SKIP and isinstance(offer.answer, Reminder):
                put_recommended(
                    settings.data, CLAUDE_CODE.setting, offer.entry, offer.setting.id, None
                )

    def recommended_to_write(
        self, claude_dir: Path, file: SettingsFile | None
    ) -> tuple[dict[str, Any], list[str], list[str], list[str], str]:
        """What the work does with this run's yeses to recommended settings in one Claude Code
        folder (see recommended_yes), from what the folder has now, with its settings.json as
        file has it, the read the write plans on: the values to write, by key, with each one's
        id; the ids whose folder has the recommended value already, so the yes is saved with no
        write; the id of each the work leaves out, since the folder's value changed after the
        person answered, or setup won't rewrite its settings.json any more; and then why not, or
        "" for none."""
        wanted = self.yeses_in(claude_dir)
        if not wanted:
            return {}, [], [], [], ""
        current, reason = self.current_values(claude_dir, list(wanted), file)
        values: dict[str, Any] = {}
        ids: list[str] = []
        already: list[str] = []
        left: list[str] = []
        for setting in for_agent(CLAUDE_CODE.group):
            if setting.id not in wanted:
                continue
            form = setting.agents[CLAUDE_CODE.group]
            now = current.get(setting.id)
            if now is None or now.described != wanted[setting.id].described:
                left.append(setting.id)
            elif state_of(form, now) == DONE:
                already.append(setting.id)
            else:
                values[form.key] = form.value
                ids.append(setting.id)
        return values, ids, already, left, reason

    def yeses_in(self, claude_dir: Path) -> dict[str, Current]:
        """This run's yeses to recommended settings in one Claude Code folder, by each setting's
        id, with what the folder had when the person answered."""
        key = yes_key(claude_dir)
        return {
            setting_id: offered
            for (folder, setting_id), offered in self.recommended_yes.items()
            if folder == key
        }

    def leave_out(self, claude_dir: Path, ids: Sequence[str], why: str) -> None:
        """Leaves out of the work each of this run's yeses to recommended settings in a Claude
        Code folder that it can't write, saying why, so its offer comes back: any answer the
        folder had for it goes too (see save_recommended), since the yes replaced it."""
        if not ids:
            return
        self.recommended_left_out += [(claude_dir, setting_id) for setting_id in ids]
        keys = [
            setting.agents[CLAUDE_CODE.group].key
            for setting in for_agent(CLAUDE_CODE.group)
            if setting.id in ids
        ]
        one = len(keys) == 1
        self.status(
            "NEW",
            f"Claude Code settings in {claude_dir.name}: left {and_list(keys)} as "
            f"{'it is' if one else 'they are'} in {claude_dir / 'settings.json'}, since {why}. "
            "Setup asks again.",
        )

    def save_recommended(self, settled: Settled, written: Sequence[tuple[Path, str]]) -> None:
        """Saves each yes to a recommended setting whose change the work wrote, by its Claude Code
        folder's full path and the setting's id, and takes out any answer for one the work left
        out, so its offer comes back, each in the folder's entry the offers read (see
        set_up_entry), in this PC's settings as the work saved them, while it still
        holds the sync's lock. It backs the file up as the save does, unless this run backed it up
        already. Nothing when the save couldn't be made, or the file couldn't be read again."""
        if self.save_failed or settled.problem:
            return
        data = settled.settings.data
        before = local_settings_text(settled.settings)
        yeses: list[tuple[str, str]] = []
        for folder, setting_id in written:
            entry = self.set_up_entry(CLAUDE_CODE, settled.settings, folder)
            if entry is None:
                continue
            put_recommended(data, CLAUDE_CODE.setting, entry, setting_id, True)
            if (entry, setting_id) not in yeses:
                yeses.append((entry, setting_id))
        for folder, setting_id in self.recommended_left_out:
            entry = self.set_up_entry(CLAUDE_CODE, settled.settings, folder)
            if entry is not None:
                put_recommended(data, CLAUDE_CODE.setting, entry, setting_id, None)
        text = local_settings_text(settled.settings)
        if text == before:
            return
        names = yes_names(yeses)
        if not self.should(SETTINGS_PATH, f"Save the yes to {names}" if yeses else "Save it"):
            return
        backup = (self.changed_by_hand or self.assigned) and not self.settings_backed_up
        try:
            kept = write_settings_file(SETTINGS_PATH, text, bom=False, backup=backup)
        except OSError as error:
            about = f"your yes to {names}" if yeses else "this PC's settings"
            self.status(
                "PROBLEM",
                f"Could not save {about} in {SETTINGS_PATH}, so setup asks again. {error}",
            )
            return
        saved = f". Backup of the old file: {kept}" if kept else ""
        with_yes = f", with your yes to {names}" if yeses else ""
        self.status("SET", f"This PC's settings: {SETTINGS_PATH}{with_yes}{saved}")

    # Generated files

    def sync_generated_folder(
        self, destination: Path, values: dict[str, str], source: Path | None = None
    ) -> None:
        """Makes destination hold exactly the files in source, with the placeholders filled in.
        With no source, empties destination and removes it."""
        # Something else made a link here, or in a folder above here, and it may point anywhere,
        # so setup neither writes through it nor empties it.
        linked = linked_folder(destination)
        if linked is not None:
            self.status(
                "PROBLEM",
                f"{linked} is a link, so setup left it alone. Setup writes that folder "
                "itself: remove the link with cmd /c rmdir, then run setup.py again.",
            )
            return

        source_files = list(generated.generated_items(source)) if source else []
        wanted = {os.path.normcase(os.path.relpath(f, source)) for f in source_files if source}

        # Old files and empty folders go first, so that a path that was a folder can become a
        # file, and the other way around. Python's bytecode cache stays while the folder has
        # templates.
        if destination.exists():
            for file in list(generated.generated_items(destination, with_cache=source is None)):
                if os.path.normcase(os.path.relpath(file, destination)) in wanted:
                    continue
                if not self.should(file, "Remove a generated file whose template is gone"):
                    continue
                try:
                    remove_generated_file(file)
                except OSError as error:
                    self.status("PROBLEM", f"Could not remove the generated file {file}. {error}")
                    continue
                self.generated_changes += 1
            # Empty folders, deepest first.
            folders = sorted(
                generated.generated_items(destination, directories=True, with_cache=source is None),
                key=lambda folder: len(str(folder)),
                reverse=True,
            )
            if source is None:
                folders.append(destination)
            for folder in folders:
                if any(folder.iterdir()):
                    continue
                if self.should(folder, "Remove an empty generated folder"):
                    try:
                        folder.rmdir()
                    except OSError as error:
                        self.status(
                            "PROBLEM",
                            f"Could not remove the empty generated folder {folder}. {error}",
                        )

        for file in source_files:
            assert source is not None
            target = destination / os.path.relpath(file, source)
            rendered = generated.render(file, values)
            self.unknown_placeholders.extend(rendered.unknown)
            # A link to a file may point anywhere, so setup doesn't write through it.
            if is_link(target):
                self.status(
                    "PROBLEM",
                    f"{target} is a link, so setup left it alone. Setup writes that file itself: "
                    "remove the link, then run setup.py again.",
                )
                continue
            if target.is_file() and target.read_bytes() == rendered.data:
                continue
            if not self.should(target, "Write a generated file"):
                continue
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.is_file():
                    make_writable(target)
                target.write_bytes(rendered.data)
            except OSError as error:
                self.status("PROBLEM", f"Could not write the generated file {target}. {error}")
                continue
            self.generated_changes += 1

    # dev-home itself

    def initialize_content_repo(self, path: Path, values: dict[str, str]) -> None:
        """Offers to clone the person's dev-home from GitHub, or to create a new private one: the
        files in templates/dev-home/, filled in, with dev-home.json, set to one active copy, and
        the knowledge index. The caller checks the folder afterward."""
        if not self.can_ask:
            self.status(
                "PROBLEM",
                f"There is no dev-home at {path}. Run setup.py in a terminal without --quiet, and "
                "it offers to clone yours from GitHub or create a new one.",
            )
            return
        gh = find_program("gh")
        if gh is None:
            self.status(
                "PROBLEM",
                f"There is no dev-home at {path}, and cloning or creating one needs the GitHub "
                "CLI (gh). Install it, sign in with gh auth login, then run setup.py again.",
            )
            return
        if run_tool(gh, "auth", "status")[0] != 0:
            self.status(
                "PROBLEM",
                f"There is no dev-home at {path}, and the GitHub CLI is not signed in. Run gh "
                "auth login, then run setup.py again.",
            )
            return

        self.line(f"There is no dev-home at {path} yet.")
        choice = self.ask(
            "Clone your existing dev-home from GitHub (c), create a new private one (n), or stop "
            "here (s)?",
            "s",
        )
        stopped = f"Stopped: there is no dev-home at {path} yet."
        if choice is not None and re.fullmatch(r"\s*(c|clone)\s*", choice, re.IGNORECASE):
            name = self.ask(
                "Your dev-home repo on GitHub: owner/name, or just the name if it is under your "
                "account",
                "dev-home",
            )
            # Input that ends without an answer counts as no, here as anywhere.
            if name is None:
                self.status("PROBLEM", stopped)
                return
            if not self.should(path, f"Clone {name} from GitHub"):
                return
            # git's long-path option, which gh passes on to git, is on before the checkout: set
            # afterward with the other git settings, it would come too late for a path in
            # dev-home past Windows' limit (decision 0065).
            code, lines = run_tool(
                gh, "repo", "clone", name, str(path), "--", "-c", "core.longpaths=true"
            )
            if code != 0:
                self.status("PROBLEM", f"Could not clone {name}. gh: {first_line(lines)}")
                return
            self.cloned = True
            self.status("CREATED", f"Cloned {name} into {path}")
            return
        if choice is None or not re.fullmatch(r"\s*(n|new)\s*", choice, re.IGNORECASE):
            self.status("PROBLEM", stopped)
            return

        name = self.ask("Name for the new private repo on GitHub", "dev-home")
        if name is None:
            self.status("PROBLEM", stopped)
            return
        action = f"Create a private repo named {name} on GitHub, from templates/dev-home/"
        if not self.should(path, action):
            return
        path.mkdir(parents=True, exist_ok=True)
        contents: dict[str, bytes] = {}
        # AGENTS.md and CLAUDE.md are never committed: the work writes them for this PC.
        templates = [
            f
            for f in DEV_HOME_TEMPLATES.rglob("*")
            if f.is_file() and f.relative_to(DEV_HOME_TEMPLATES).as_posix() not in DEV_HOME_GUIDANCE
        ]
        for file in sorted(templates):
            rendered = generated.render(file, values)
            self.unknown_placeholders.extend(rendered.unknown)
            contents[file.relative_to(DEV_HOME_TEMPLATES).as_posix()] = rendered.data
        # A new dev-home has one active copy: nothing else can be using it yet.
        contents[DEV_HOME_SETTINGS] = dev_home_text({}, False).encode("utf-8")
        contents[KNOWLEDGE_INDEX] = KNOWLEDGE_INDEX_TEXT.encode("utf-8")
        for relative, data in contents.items():
            target = path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        steps = [
            ["init", "--quiet", "-b", "main"],
            ["config", "--local", "commit.gpgsign", "false"],
            ["config", "--local", "pull.rebase", "false"],
            ["add", "--", *contents],
            ["commit", "--quiet", "-m", with_pc_name("dev-home: new dev-home")],
        ]
        for step in steps:
            done = run_git(path, *step)
            if done.code != 0:
                self.status(
                    "PROBLEM",
                    f"Could not set up the repo in {path}: git {step[0]} failed. "
                    f"git: {first_line(done.err + done.out)}",
                )
                return
        self.created = True
        code, lines = run_tool(
            gh,
            "repo",
            "create",
            name,
            "--private",
            "--source",
            str(path),
            "--remote",
            "origin",
            "--push",
        )
        if code != 0:
            self.status(
                "PROBLEM",
                f"Created dev-home in {path}, but not on GitHub. gh: {first_line(lines)}. Once "
                f"that is fixed, run: gh repo create {name} --private --source {path} --remote "
                "origin --push",
            )
            return
        self.status("CREATED", f"New private repo {name} on GitHub, with this PC's copy in {path}")

    def ask_about_copies(
        self, settings: LocalSettings, content_root: Path, *, first_setup: bool
    ) -> None:
        """dev-home.json says whether dev-home has one active copy or several, and the sync acts
        on it. A new dev-home starts with one, and nothing else can be using one this run created,
        so it isn't asked about. Otherwise setup asks on a PC's first setup, since adding a PC is
        when the answer most often changes; when the file has no answer yet; after a clone set to
        one; and when the file has no schemaVersion, from before the layout was versioned, which
        then is rewritten in place even with the same answer, since git has its history. Wherever
        the file has an answer, the question takes it as the default. The answer is shown with
        the change it makes (see confirm_copies), and written by the work. A file with a version
        the code doesn't know is left alone."""
        path = content_root / DEV_HOME_SETTINGS
        found = read_dev_home_settings(content_root)
        if found.layout == "unreadable":
            self.status(
                "PROBLEM",
                f"{path} could not be read as a JSON object of settings, so setup left it alone, "
                f"and each sync checks GitHub every time. Fix it by hand. {found.error}",
            )
            return
        if found.layout == "unknown":
            self.status(
                "PROBLEM",
                f"{path} has a schemaVersion this dev-home-toolkit doesn't know, perhaps written "
                "by a newer one on another copy, so setup left it alone, and each sync checks "
                f"GitHub every time. Update dev-home-toolkit: {by_hand('update.py')}",
            )
            return
        older = found.layout == "older"
        answer = found.answer
        # --configure's answer, already given, which a person or an agent's chat approved.
        if self.wanted_copies is not None:
            return
        due = (
            older
            or answer is None
            or (first_setup and not self.created)
            or (answer is False and self.cloned)
        )
        if not due:
            return
        if not self.can_ask:
            if older:
                self.status(
                    "PROBLEM",
                    f"{path} is in an older layout, without a schemaVersion, so each sync checks "
                    f"GitHub every time. Run {by_hand('setup.py')} in a terminal: it asks its "
                    "question again, then rewrites the file.",
                )
            elif answer is None:
                self.status(
                    "PROBLEM",
                    "dev-home has no answer yet to whether it's in active use anywhere besides "
                    f"this PC, so each sync checks GitHub every time. Run {by_hand('setup.py')} "
                    "in a terminal, and it asks.",
                )
            return
        if older:
            self.line(
                f"{path} is in an older layout. Setup asks its question again, with its old answer "
                "as the default, then rewrites it."
            )
        configure.change_copies(self, settings)
        if self.wanted_copies is None and (older or answer is None):
            self.status(
                "PROBLEM",
                f"{path} was left as it is, so each sync checks GitHub every time. Run setup.py "
                "again to answer the question.",
            )

    def confirm_copies(self, content_root: Path) -> None:
        """Shows the change to dev-home.json that a question, the menu, or --configure chose. A
        person then says whether to save it, while an agent's --configure was approved in chat.
        The work writes it to that file alone, then commits and pushes it, so every copy
        agrees."""
        several = self.wanted_copies
        if several is None:
            return
        found = read_dev_home_settings(content_root)
        if found.layout in ("unreadable", "unknown"):
            return
        if several == found.answer and found.layout != "older":
            return
        path = content_root / DEV_HOME_SETTINGS
        new_text = dev_home_text(found.data, several)
        self.status("CHANGE", f"dev-home's copies: {path}")
        self.print_diff(found.text, new_text)
        if not self.should(path, "Write this, then commit and push it"):
            return
        if not self.assigned and not self.confirm(
            "          Save it, commit it, and push it to GitHub?"
        ):
            self.status(
                "PROBLEM", f"{path} was left as it is. Run setup.py again to answer the question."
            )
            return
        self.copies_change = (found.layout, found.text, new_text, several)

    def write_copies(self, content_root: Path) -> None:
        """Writes the change to dev-home.json that confirm_copies showed, as long as the file is
        still as it was then, and commits and pushes it. The work runs this while it holds the
        sync's lock, so the commit's sync doesn't wait for it."""
        if self.copies_change is None:
            return
        layout_shown, text_shown, new_text, several = self.copies_change
        path = content_root / DEV_HOME_SETTINGS
        now = read_dev_home_settings(content_root)
        if (now.layout, now.text) != (layout_shown, text_shown):
            self.status(
                "PROBLEM",
                f"{path} changed after setup showed its change, perhaps through a sync from "
                "another copy, so it was left as it is. Run setup.py again to answer the question.",
            )
            return
        try:
            # No backup: git's history is dev-home.json's.
            write_settings_file(path, new_text, bom=False, backup=False)
        except OSError as error:
            self.status("PROBLEM", f"Could not write {path}. {error}")
            return
        self.status("SET", f"dev-home's copies: {'several' if several else 'one'}, in {path}")
        # Loaded only now, so a sync that can't load stops only this commit, not setup.
        try:
            sync = importlib.import_module(f"{__package__}.sync")
            message = f"dev-home: {'several active copies' if several else 'one active copy'}"
            code = sync.commit_for_setup(
                content_root, [DEV_HOME_SETTINGS], message, holds_lock=True
            )
        except Exception as error:
            self.status("PROBLEM", f"Could not commit {path}: {describe(error)}")
            return
        if code != 0:
            # The sync has said what went wrong.
            self.problems.append(f"Committing {path}")
        elif several:
            self.line(
                "          On each other copy, run /dev-home sync, or sync.py in a terminal, so it "
                "starts checking GitHub before each command now."
            )

    # Links

    def sync_link(self, link: Path, target: Path, label: str) -> None:
        existing = link_info(link)
        wanted = comparable(target)

        # A link whose target is gone has nothing to lose, such as one left from an older layout.
        if (
            existing is not None
            and existing.is_link
            and existing.target is not None
            and not same_path(existing.target, wanted)
            and not Path(existing.target).exists()
        ):
            if not self.should(link, f"Replace a link to {existing.target}, which is gone"):
                return
            try:
                remove_folder_link(link)
                existing = None
            except OSError as error:
                self.status("PROBLEM", f"{label}: could not remove the broken link {link}. {error}")
                return

        if existing is None:
            if not self.should(link, f"Create a link to {target}"):
                return
            try:
                kind = make_folder_link(link, target)
                self.status("LINKED", f"{label} ({kind}): {link}")
            except OSError as error:
                self.status("PROBLEM", f"{label}: could not create {link}. {error}")
            return
        if not existing.is_link:
            self.status(
                "PROBLEM",
                f"{label}: {link} already exists and is not a link. Move anything you need from "
                "it into dev-home, delete it, then run setup.py again.",
            )
            return
        if existing.target is not None and same_path(existing.target, wanted):
            self.status("OK", label)
            return
        self.status(
            "PROBLEM",
            f"{label}: {link} links to {existing.target}, not to {target}. Left alone. If you no "
            "longer need it, remove it with cmd /c rmdir, then run setup.py again.",
        )

    def sync_own_files(self, content_root: Path, pc: str, agents: Sequence[str]) -> None:
        """Makes sure dev-home has the end user's files that setup keeps there (decision 0070,
        "Who owns each file in dev-home"): the knowledge index, and a my-rules.md at each level of
        rules/, for every agent and for each agent set up here, at both the every-PC level and
        this PC's, the file an agent opens to add one of the end user's rules at that level. Each
        one missing that git doesn't have either is created, the index with only its title and
        my-rules.md empty, then committed and pushed together. One git still has is the end
        user's delete or rename, not committed yet, which a commit would carry to every copy: a
        my-rules.md then waits for that commit, since moving rules to another file is a normal
        rename, while the index, which nothing renames, is put back as git has it. Setup never
        changes them, or any other file there, otherwise."""
        index = content_root / KNOWLEDGE_INDEX
        missing = [] if index.is_file() else [index]
        if agents:
            missing += rules.missing_my_rules(content_root / rules.RULES, pc, agents)
        if not missing:
            return
        in_git = self.files_in_git(content_root)
        if in_git is None:
            return
        wanted: list[tuple[Path, str, str]] = []
        for path in missing:
            if path.relative_to(content_root).as_posix().lower() not in in_git:
                wanted.append(
                    (path, KNOWLEDGE_INDEX_TEXT, "the knowledge index")
                    if path == index
                    else (path, "", "an empty my-rules.md, for your rules at this level")
                )
            elif path == index:
                self.restore_knowledge_index(content_root)
        created: list[Path] = []
        for path, text, what in wanted:
            if not self.should(path, f"Create {what}"):
                continue
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(text.encode("utf-8"))
            except OSError as error:
                self.status("PROBLEM", f"Could not create {path}. {error}")
                continue
            created.append(path)
        if not created:
            return
        names = [path.relative_to(content_root).as_posix() for path in created]
        rules_files = [name for name in names if name != KNOWLEDGE_INDEX]
        if KNOWLEDGE_INDEX in names:
            self.status("WROTE", f"The knowledge index, with only its title: {KNOWLEDGE_INDEX}")
        if rules_files:
            self.status(
                "WROTE",
                f"An empty my-rules.md, for your rules, in dev-home: {', '.join(rules_files)}",
            )
        message = (
            "rules: add my-rules.md"
            if KNOWLEDGE_INDEX not in names
            else "knowledge: add README.md"
            if not rules_files
            else "dev-home: add knowledge/README.md and my-rules.md"
        )
        # Loaded only now, so a sync that can't load stops only this commit, not setup.
        try:
            sync = importlib.import_module(f"{__package__}.sync")
            code = sync.commit_for_setup(content_root, names, message, holds_lock=True)
        except Exception as error:
            self.status("PROBLEM", f"Could not commit {', '.join(names)}: {describe(error)}")
            return
        if code != 0:
            # The sync has said what went wrong.
            self.problems.append(f"Committing {', '.join(names)}")

    def files_in_git(self, content_root: Path) -> set[str] | None:
        """The paths, in lowercase, of the knowledge index and the files in rules/ as dev-home's
        last commit has them, or None, said in a PROBLEM line, when git can't tell. One git call,
        made only when one of those files is missing."""
        listed = run_git(
            content_root, "ls-tree", "-r", "--name-only", "HEAD", "--", rules.RULES, KNOWLEDGE_INDEX
        )
        if listed.code != 0:
            self.status(
                "PROBLEM",
                "Could not tell from git whether a missing my-rules.md or knowledge index is a "
                "change not committed yet, so setup left them missing. "
                f"git: {first_line(listed.err + listed.out)}",
            )
            return None
        return {line.lower() for line in listed.out}

    def restore_knowledge_index(self, content_root: Path) -> None:
        """Puts back the knowledge index as dev-home's last commit has it, when it's missing but
        git still has it."""
        path = content_root / KNOWLEDGE_INDEX
        if not self.should(path, "Put back the knowledge index as git has it"):
            return
        where = ("--source=HEAD", "--staged", "--worktree")
        restored = run_git(content_root, "restore", *where, "--", KNOWLEDGE_INDEX)
        if restored.code != 0:
            error = first_line(restored.err + restored.out)
            self.status("PROBLEM", f"Could not put back {path} from git. git: {error}")
            return
        self.status("WROTE", f"The knowledge index, put back from the last commit: {path}")

    # dev-home's AGENTS.md and CLAUDE.md

    def find_guidance(
        self, content_root: Path, values: dict[str, str], name: str
    ) -> Guidance | str:
        """One of dev-home's AGENTS.md and CLAUDE.md as it is now (see Guidance), or why setup
        can't work with it, as a sentence for a PROBLEM line. A link whose target is gone counts
        as no file, and the work replaces it; any other link stays, as setup never writes through
        one."""
        path = content_root / name
        copy = LAST_WRITTEN / rules.copy_name(path)
        rendered = generated.render(DEV_HOME_TEMPLATES / name, values)
        self.unknown_placeholders.extend(rendered.unknown)
        existing = link_info(path)
        current = None
        if existing is not None and existing.is_link:
            if existing.target is not None and Path(existing.target).exists():
                return (
                    f"dev-home's {name}: {path} links to {existing.target}, so setup left it "
                    "alone. Setup writes this file on every run: move anything you want to keep "
                    f"into your rules, in {content_root / rules.RULES}, delete the link, then run "
                    "setup.py again."
                )
        elif existing is not None:
            try:
                current = path.read_bytes()
            except OSError as error:
                return f"dev-home's {name}: {path} couldn't be read, so setup left it. {error}"
        try:
            kept = copy.read_bytes() if copy.is_file() else None
        except OSError as error:
            return (
                f"dev-home's {name}: setup couldn't read its copy, {copy}, so it left it. {error}"
            )
        return Guidance(name, path, copy, rendered.data, current, kept)

    def ask_about_guidance(self, content_root: Path) -> None:
        """At a console, before the work: sends each hand edit to dev-home's AGENTS.md and
        CLAUDE.md to the Recycle Bin, so the work can put the file back. When the bin can't take
        it, shows the edit and asks whether to delete it for good or leave the file as edited
        (decision 0069, "Dropped text"). The file stays as it is until the work, which acts on
        what happened here only while the file is still the same. A run that can't ask leaves it
        all to the work (see sync_guidance)."""
        if not self.can_ask or self.what_if:
            return
        values = template_values(content_root)
        for name in DEV_HOME_GUIDANCE:
            found = self.find_guidance(content_root, values, name)
            if isinstance(found, str) or found.current is None or not found.edited:
                continue
            sent = self.edit_to_the_bin(found)
            if sent.in_bin:
                self.guidance_choices[name] = GuidanceChoice("sent", found.current)
                continue
            rules_root = content_root / rules.RULES
            self.line()
            self.line(
                f"dev-home's {name} has edits setup didn't make. Setup sent a copy of the file to "
                f"the Recycle Bin, and the bin couldn't take it. {sentence(sent.why_not)}"
            )
            self.line(
                "Setup rewrites this file on every run. Your guidance for every session goes in "
                f"your rules, in {rules_root}."
            )
            against = "what setup last wrote" if found.kept is not None else "what setup writes now"
            self.line(f"The edits, against {against}:")
            self.print_diff(
                found.before.decode("utf-8", errors="replace"),
                found.current.decode("utf-8", errors="replace"),
            )
            self.line(
                f"The file stays as it is until you answer, so you can copy anything from "
                f"{found.path} first. {console.key('n')} leaves it as edited, and each sync names "
                "it until the bin takes the edits."
            )
            delete = self.choose(
                f"Delete these edits for good, and put back setup's {name}?", False
            )
            self.guidance_choices[name] = GuidanceChoice(
                "delete" if delete else "leave", found.current, sent.why_not
            )

    def sync_guidance(self, content_root: Path, values: dict[str, str]) -> None:
        """Writes dev-home's AGENTS.md and CLAUDE.md with this PC's commands (decision 0070, "Who
        owns each file in dev-home") when there's none, or when it's what setup last wrote, such
        as setup's own older version. A hand edit goes to the Recycle Bin first, or as a person
        chose at this run's questions (see ask_about_guidance); then setup puts the file back and
        says so. When the bin can't take it, the file stays as edited, named in a PROBLEM line,
        and the next run tries again (decision 0069, "Dropped text"). Setup keeps a copy of what
        it wrote, as for the agents' rules files."""
        rules_root = content_root / rules.RULES
        for name in DEV_HOME_GUIDANCE:
            found = self.find_guidance(content_root, values, name)
            if isinstance(found, str):
                self.status("PROBLEM", found)
                continue
            label = f"dev-home's {name}"
            if found.current == found.data:
                self.status("OK", label)
            elif not found.edited:
                if not self.write_guidance(found, f"Write {name} with this PC's commands"):
                    continue
                self.status("WROTE", f"{label}, with this PC's commands: {found.path}")
            elif not self.put_back_guidance(found, rules_root):
                continue
            if found.kept != found.data and self.should(
                found.copy, f"Keep a copy of the {name} setup wrote"
            ):
                try:
                    found.copy.parent.mkdir(parents=True, exist_ok=True)
                    found.copy.write_bytes(found.data)
                except OSError as error:
                    self.status("PROBLEM", f"Could not write {found.copy}. {error}")

    def put_back_guidance(self, found: Guidance, rules_root: Path) -> bool:
        """Puts back setup's text over a hand edit, once the Recycle Bin has the edit or a person
        chose to delete it, and says so. Returns whether it did."""
        if found.current is None:
            return False
        chosen = self.guidance_choices.get(found.name)
        # A file that changed after the question has a new edit, which goes to the bin.
        if chosen is not None and chosen.current != found.current:
            chosen = None
        if chosen is not None and chosen.choice == "leave":
            self.status("PROBLEM", left_text(found, rules_root, chosen.why_not))
            return False
        if chosen is None:
            if not self.should(
                found.path, "Send its edits to the Recycle Bin, then put back setup's file"
            ):
                return False
            sent = self.edit_to_the_bin(found)
            if not sent.in_bin:
                self.status("PROBLEM", left_text(found, rules_root, sent.why_not))
                return False
            chosen = GuidanceChoice("sent", found.current)
        if not self.write_guidance(found, "Put back setup's file"):
            return False
        if chosen.choice == "sent":
            said = (
                "it had edits setup didn't make, which are in the Recycle Bin as "
                f'"{bin_name(found.name)}"'
            )
        else:
            said = "its edits are deleted, as you chose"
        self.status(
            "WROTE",
            f"dev-home's {found.name}, put back: {said}. Setup rewrites this file on every run, "
            f"so put guidance for every session in your rules, in {rules_root}.",
        )
        return True

    def write_guidance(self, found: Guidance, action: str) -> bool:
        """Writes setup's text in one of dev-home's AGENTS.md and CLAUDE.md, in place of a link
        whose target is gone, if that's there. Returns whether it did."""
        if not self.should(found.path, action):
            return False
        try:
            if is_link(found.path):
                found.path.unlink()
            elif found.current is not None:
                make_writable(found.path)
            found.path.write_bytes(found.data)
        except OSError as error:
            self.status(
                "PROBLEM", f"dev-home's {found.name}: could not write {found.path}. {error}"
            )
            return False
        return True

    def edit_to_the_bin(self, found: Guidance) -> recycle_bin.Sent:
        """Sends a copy of the file with its hand edit, byte for byte, to the Recycle Bin, named
        for what it holds (see bin_name)."""
        return self.to_the_bin(found.current or b"", bin_name(found.name))

    def to_the_bin(self, data: bytes, name: str) -> recycle_bin.Sent:
        """Sends data to the Recycle Bin as a file called name, and says whether the bin has it
        (decision 0069, "Dropped text"). A test profile's bin is its folder TEST_BIN, so the tests
        never reach the real one, and a file in that folder's place stands for a bin that can't
        take it."""
        if not self.test_profile:
            return recycle_bin.send_data(data, name)
        try:
            folder = self.home / TEST_BIN
            folder.mkdir(exist_ok=True)
            (folder / name).write_bytes(data)
        except OSError as error:
            return recycle_bin.Sent(False, f"The test profile's bin couldn't take it: {error}")
        return recycle_bin.Sent(True)

    # Each agent's rules file

    def rules_targets(self, agent_folders: AgentFolders) -> list[RulesTarget]:
        """Each agent's rules file: the one setup writes in each folder answered yes, then the one
        it removes in each folder answered no, unless that folder's rules are really a folder set
        up here, through a junction, whose file stays (see remove_rules_file)."""
        claude_code, codex = REQUIRES_NAMES[CLAUDE_CODE.name], REQUIRES_NAMES[CODEX.name]

        def claude(dirs: Iterable[str], setting_up: bool) -> list[RulesTarget]:
            within = Path("rules") / CLAUDE_RULES_FILE
            return [RulesTarget(Path(d), Path(d) / within, claude_code, setting_up) for d in dirs]

        def codex_homes(homes: Iterable[str], setting_up: bool) -> list[RulesTarget]:
            return [
                RulesTarget(Path(h), Path(h) / CODEX_RULES_FILE, codex, setting_up) for h in homes
            ]

        targets = claude(agent_folders.claude_dirs, True)
        targets += codex_homes(agent_folders.codex_homes, True)
        declined = claude(agent_folders.declined_claude_dirs, False)
        declined += codex_homes(agent_folders.declined_codex_homes, False)
        if declined:
            set_up = {real_path(target.path.parent) for target in targets}
            declined = [t for t in declined if real_path(t.path.parent) not in set_up]
        return targets + declined

    def join_rules(
        self,
        operating: Mapping[str, str],
        rules_root: Path,
        pc: str,
        targets: Sequence[RulesTarget],
    ) -> dict[str, rules.Joined]:
        """What setup writes in each agent's rules file in a folder set up, by the file's path: the
        operating rules for that agent, from operating, by its name in rules/ (see
        operating_by_agent), then the end user's rules for that agent on this PC, joined (see
        rules.joined_rules), with each file in unanswered/ only in the rules file it came from.
        So each of an agent's files is joined on its own only while that agent has files in
        unanswered/; otherwise they share one join."""
        system = requirements.operating_system()
        joined: dict[str, rules.Joined] = {}
        shared: dict[str, rules.Joined] = {}
        for target in targets:
            if not target.setting_up:
                continue
            waiting = rules_root / rules.PCS / pc / target.agent / rules.UNANSWERED
            mine = operating[target.agent]
            if rules.markdown_files(waiting):
                result = rules.joined_rules(mine, rules_root, pc, target.agent, system, target.path)
            elif target.agent in shared:
                result = shared[target.agent]
            else:
                result = rules.joined_rules(mine, rules_root, pc, target.agent, system)
                shared[target.agent] = result
            joined[str(target.path)] = result
        return joined

    def lines_found(self, target: RulesTarget, new: str, operating: str) -> FoundLines | None:
        """An agent's rules file that's neither what setup last wrote there nor, in a folder set
        up, new, what it writes there now, with the lines setup didn't write in it, which go into
        rules/ before setup writes or removes the file (see rules.to_move): none, when someone
        only took lines out. None for any other file; for a link, or a file that can't be read,
        which writing it reports; and in a folder answered no, for a file setup has no copy of:
        one it never wrote isn't its to remove. operating is the operating rules for the file's
        agent."""
        copy = LAST_WRITTEN / rules.copy_name(target.folder)
        try:
            if is_link(target.path) or not target.path.is_file():
                return None
            current = target.path.read_bytes()
            kept = copy.read_bytes() if copy.is_file() else None
        except OSError:
            return None
        if current == kept or (target.setting_up and current == new.encode("utf-8")):
            return None
        if kept is None and not target.setting_up:
            return None
        moving = rules.to_move(
            rules.decode(target.path, current)[0],
            None if kept is None else rules.decode(copy, kept)[0],
            new,
            operating,
        )
        return FoundLines(target, current, moving)

    def ask_about_rules(self, content_root: Path, settings: LocalSettings) -> None:
        """At a console, before the work: asks where the lines setup didn't write in each agent's
        rules file go, a file at a time, and where each file in this PC's unanswered/ folders goes
        (decision 0064, "Each agent's rules file"): into one of the four mine/ folders that join
        for that agent here, or to the Recycle Bin, which takes them at once. When the bin can't,
        it asks again: one of those, or delete them for good (decision 0069, "Dropped text").
        Enter leaves them for later, in unanswered/. The files stay as they are until the work,
        which acts on what was chosen here only while each file is still the same. A run that
        can't ask leaves it all to the work, which sets the lines aside (see save_lines).

        Each file is asked about once, though two folders lead to it through a junction, as the
        work handles it once. Lines a file in rules/ already holds aren't asked about, nor is that
        file, while they're still in the agent's file: a run stopped by Ctrl+C, say, didn't
        finish saving them, and the work finishes it. Nor is a waiting file a mine/ file already
        holds: the work removes it (see answer_waiting)."""
        if not self.can_ask or self.what_if:
            return
        pc = rules.pc_folder(computer_name())
        found, waiting = self.rules_questions(content_root, settings, pc)
        for lines in found:
            self.ask_where_lines_go(lines, pc)
        for file in waiting:
            self.ask_where_file_goes(file, content_root / rules.RULES, pc)

    def rules_questions(
        self, content_root: Path, settings: LocalSettings, pc: str
    ) -> tuple[list[FoundLines], list[WaitingFile]]:
        """What setup asks about rules, at a console or through --configure (see ask_about_rules):
        the lines setup didn't write in each agent's rules file, a file at a time, and each file
        in this PC's unanswered/ folders, pc being this PC's folder under rules/pcs/."""
        system = requirements.operating_system()
        rules_root = content_root / rules.RULES
        agent_folders = self.agent_folders(settings)
        targets = self.rules_targets(agent_folders)
        paths = unanswered_files(rules_root, pc)
        if not targets and not paths:
            return [], []
        # The operating rules as the work writes them for each agent, with the blocks of the
        # skills added for it, so none of setup's own lines reads as one someone added. The
        # skills' problems are said by the work, not here.
        declared = skill_declarations(settings.content_dir)
        folders = self.skills_folders(agent_folders, declared)
        plans = self.plan_skills(settings.data, declared, folders)
        rendered = generated.render(OPERATING_TEMPLATE, template_values(content_root))
        operating = operating_by_agent(rendered.data.decode("utf-8"), targets, plans, folders)
        joined = self.join_rules(operating, rules_root, pc, targets)
        asked: set[str] = set()
        pending: set[str] = set()
        lines: list[FoundLines] = []
        for target in targets:
            real = real_path(target.path)
            if real in asked:
                continue
            asked.add(real)
            new = joined[str(target.path)].text if target.setting_up else ""
            found = self.lines_found(target, new, operating[target.agent])
            if found is None or not found.moving.text:
                continue
            holder = rules.already_held(
                found.moving.text, rules_root, pc, target.agent, system, target.path
            )
            if holder is not None:
                pending.add(str(holder))
                continue
            lines.append(found)
        # Each rules file setup writes, by its real path, where a waiting file loads.
        written = {real_path(target.path): target.path for target in targets if target.setting_up}
        files = [
            file
            for path in paths
            if str(path) not in pending
            and (file := self.waiting_file(path, rules_root, pc, system, written)) is not None
        ]
        return lines, files

    def waiting_file(
        self, path: Path, rules_root: Path, pc: str, system: str, written: dict[str, Path]
    ) -> WaitingFile | None:
        """A file in this PC's unanswered/ folders as setup asks about it (see WaitingFile), or None
        when it can't be read, or a mine/ file that joins for its agent here already holds it,
        which the work removes (see answer_waiting). written has each rules file setup writes, by
        its real path: the file loads only in the one its note's from field names, if any."""
        agent = path.relative_to(rules_root).parts[2]
        try:
            current = path.read_bytes()
        except OSError:
            return None
        text = rules.decode(path, current)[0]
        if rules.already_held(text, rules_root, pc, agent, system, None, skip=path):
            return None
        lines = text.split("\n")
        source = rules.note_fields(lines).get("from") or ""
        loads = written.get(real_path(source)) if source else None
        shown = "\n".join(rules.trimmed(rules.without_note(lines)))
        return WaitingFile(path, agent, current, shown, source, loads)

    def ask_where_lines_go(self, found: FoundLines, pc: str) -> None:
        """Shows the lines setup didn't write in an agent's rules file, and asks where they go (see
        ask_about_rules)."""
        target, moving = found.target, found.moving
        shown = requirements.AGENT_NAMES[target.agent]
        self.line()
        if moving.whole:
            self.line(
                f"{target.path} was there before setup wrote {shown}'s rules there. Setup writes "
                "its own file there, so these rules move into your rules, in dev-home:"
            )
            data, kept = found.current, "as it was before setup"
        else:
            does = (
                "rewrites that file on every run"
                if target.setting_up
                else f"removes that file, since you said no to setting up {target.folder}"
            )
            self.line(
                f"{shown}'s rules file, {target.path}, has lines setup didn't write. Setup "
                f"{does}, so they move into your rules, in dev-home, with the headings they were "
                "under:"
            )
            data, kept = f"{moving.text}\n".encode(), "lines setup didn't write"
        self.show_rules(moving.text)
        waiting = f"rules/{rules.PCS}/{pc}/{target.agent}/{rules.UNANSWERED}/"
        loads = f"load only in {target.path}" if target.setting_up else "load nowhere"
        self.choose_where(
            str(target.path),
            found.current,
            (data, f"{target.path.stem} from {target.folder.name}, {kept}.md"),
            (target.agent, pc),
            f"they wait in {waiting}, and {loads}",
        )

    def ask_where_file_goes(self, file: WaitingFile, rules_root: Path, pc: str) -> None:
        """Shows a file in this PC's unanswered/ folders, and asks where it goes (see
        ask_about_rules)."""
        where = f" from {file.source}" if file.source else ""
        self.line()
        self.line(
            f"Rules setup set aside{where}, in dev-home's {relative(rules_root.parent, file.path)}:"
        )
        self.show_rules(file.text)
        loads = f"load only in {file.loads}" if file.loads else "load nowhere"
        self.choose_where(
            str(file.path),
            file.current,
            (file.current, file.path.name),
            (file.agent, pc),
            f"they stay there, and {loads}",
        )

    def show_rules(self, text: str) -> None:
        """Rules shown in a question, set in from the left, between blank lines."""
        self.line()
        for line in text.split("\n"):
            self.line(f"    {line}" if line else "")
        self.line()

    def choose_where(
        self,
        key: str,
        current: bytes,
        dropped: tuple[bytes, str],
        agent_pc: tuple[str, str],
        later: str,
    ) -> None:
        """Asks where rules go (see ask_where), and keeps the answer for the work, by key, with
        current, the file as it is now. A drop sends dropped, its data and the name it gets, to
        the Recycle Bin at once. later says where Enter leaves them, and where they load."""
        agent, pc = agent_pc
        self.line(f"Where do they go? Until you say, {later}.")
        level = self.ask_where(agent, pc, drop=True)
        if level == "drop":
            sent = self.to_the_bin(*dropped)
            if sent.in_bin:
                self.rules_choices[key] = RulesChoice("sent", current)
                return
            self.line(
                f"The Recycle Bin couldn't take them. {sentence(sent.why_not)} Keep them as one of "
                "your rules instead, or delete them for good?"
            )
            level = self.ask_where(agent, pc, drop=False)
        if level == "delete":
            self.rules_choices[key] = RulesChoice("delete", current)
        elif level is not None:
            self.rules_choices[key] = RulesChoice("move", current, level)

    def ask_where(self, agent: str, pc: str, *, drop: bool) -> str | None:
        """Where rules go: the level whose mine/ they go into, one of the four that join for the
        agent on this PC, relative to rules/; "drop", for the Recycle Bin; or, once the bin
        couldn't take them, "delete", for good. None when no answer came."""
        levels = level_choices(agent, pc)
        width = max(len(label) for _, label in levels) + 2
        for number, (level, label) in enumerate(levels, 1):
            self.line(f"  {color(str(number), GREEN)}  {label:<{width}}rules/{level}/{rules.MINE}/")
        self.line(
            f"  {color('5', GREEN)}  "
            + ("drop them, to the Recycle Bin" if drop else "delete them for good")
        )
        while True:
            answer = self.ask("Number, or Enter to decide later")
            if not answer:
                return None
            if answer in ("1", "2", "3", "4"):
                return levels[int(answer) - 1][0]
            if answer == "5":
                return "drop" if drop else "delete"
            self.line("Type a number from 1 to 5, or press Enter to decide later.")

    # Setup's questions, answered through --configure

    def waiting(self, settings: LocalSettings) -> Waiting | None:
        """What waits for a person's answer (see Waiting): what --configure lists for an agent, and
        takes answers to, as setup's questions at a console ask about it. None while no dev-home
        folder is set, or it isn't a dev-home."""
        if not settings.content_dir:
            return None
        content_root = Path(comparable(settings.content_dir))
        if not is_dev_home(content_root):
            return None
        pc = rules.pc_folder(computer_name())
        _, files = self.rules_questions(content_root, settings, pc)
        values = template_values(content_root)
        guidance = [
            found
            for name in DEV_HOME_GUIDANCE
            if isinstance(found := self.find_guidance(content_root, values, name), Guidance)
            and found.edited
        ]
        return Waiting(content_root, pc, files, guidance)

    def answer_question(
        self, settings: LocalSettings, name: str, operator: str, value: str
    ) -> bool:
        """Takes an agent's answer through --configure to a question setup waits on (see waiting),
        named by its file's path in dev-home, as <name>=<answer>@<fingerprint>, where the
        fingerprint is the one --configure showed with it, so setup acts only on what the person
        saw. The work then acts on it, as on an answer at a console. A drop goes to the Recycle Bin
        at once, and when the bin can't take it, setup says so and stops. Returns False for a name
        that isn't a question's, which may be a setting's; raises configure.AnswerError for an
        answer setup can't take."""
        if "/" not in name and name not in DEV_HOME_GUIDANCE:
            return False
        waiting = self.waiting(settings)
        file: WaitingFile | None = None
        guidance: Guidance | None = None
        if waiting is not None:
            file = next(
                (f for f in waiting.files if relative(waiting.content_root, f.path) == name), None
            )
            guidance = next((g for g in waiting.guidance if g.name == name), None)
        if waiting is None or (file is None and guidance is None):
            raise configure.AnswerError(f"Nothing waits for an answer under {name}.")
        if file is not None:
            answers = [level for level, _ in level_choices(file.agent, waiting.pc)] + ["drop"]
            # Named only once the bin can't take a drop, as at a console.
            taken = [*answers, "delete"]
            current = file.current
        else:
            assert guidance is not None and guidance.current is not None
            answers = taken = ["delete"]
            current = guidance.current
        answer, at, typed = value.rpartition("@")
        answer = answer.strip() if at else value
        if operator != "=" or answer not in taken:
            given = answer if operator == "=" else f"{operator}{answer}"
            raise configure.AnswerError(
                f"{name} takes one of these answers: {', '.join(answers)}, not {given}."
            )
        if not at or not typed.strip():
            raise configure.AnswerError(
                f"{name} needs the fingerprint --configure showed, as in "
                f"{name}=<answer>@<fingerprint>."
            )
        if configure.fingerprint(current) != typed.strip():
            raise configure.AnswerError(
                f"{name} changed since --configure showed it. Run --configure again to see it as "
                "it is now."
            )
        if guidance is not None:
            self.guidance_choices[name] = GuidanceChoice("delete", current)
            return True
        assert file is not None
        if answer == "drop":
            if self.what_if:
                self.line(f"What if: Send it to the Recycle Bin: {file.path}")
            else:
                sent = self.to_the_bin(current, file.path.name)
                if not sent.in_bin:
                    self.status(
                        "PROBLEM",
                        f"{name}: the Recycle Bin couldn't take it, so setup left it where it is. "
                        f"{sentence(sent.why_not)} Keep it as one of your rules instead, with one "
                        "of the other answers --configure lists for it, or delete it for good: "
                        f"--configure '{name}=delete@{typed.strip()}'.",
                    )
                    raise CannotGoOnError
            choice = RulesChoice("sent", current)
        elif answer == "delete":
            choice = RulesChoice("delete", current)
        else:
            choice = RulesChoice("move", current, answer)
        self.rules_choices[str(file.path)] = choice
        return True

    def save_lines(
        self,
        content_root: Path,
        pc: str,
        targets: Sequence[RulesTarget],
        operating: Mapping[str, str],
        joined: dict[str, rules.Joined],
    ) -> tuple[dict[str, bytes | None], bool]:
        """Saves the lines setup didn't write in each agent's rules file, before setup writes or
        removes it (decision 0064, "Each agent's rules file"): into the mine/ a person chose at
        this run's questions, or else set aside in this PC's unanswered/ for that agent, which
        joins after mine/ only in the file it came from. Each goes in a file of its own, with a
        note saying where it came from, unless a file that joins for that agent already holds the
        same text (decision 0066, "Notes in rule files"). Lines a person chose to drop, which the
        Recycle Bin has, or to delete for good,
        go nowhere. A file in unanswered/ a person answered moves into the mine/ they chose, or is
        removed, and one whose text a mine/ file that joins for it already holds is removed. All
        of it is committed and pushed in one commit; when that fails, setup takes it all back, so
        nothing it couldn't commit stays, and the next run tries again.

        operating has the operating rules for each agent (see operating_by_agent). Returns each
        rules file that's neither what setup last wrote nor what it writes now, by
        its path, with what it held when its lines were saved, which setup may overwrite or
        remove only while the file still holds that, or None when they couldn't be saved, since a
        write or the commit failed; and whether anything in rules/ may have changed, so the
        agents' rules are joined again."""
        rules_root = content_root / rules.RULES
        when = datetime.now().astimezone()
        system = requirements.operating_system()
        checked: dict[str, bytes | None] = {}
        # Each rules file whose lines are in a file in rules/ this run commits, by its path, with
        # what setup found, and that file.
        saved: dict[str, tuple[FoundLines, Path]] = {}
        # Each rules file handled, by its real path, with its path; and each other rules file
        # that leads to one of them through a junction, by its path, with that one's.
        handled: dict[str, str] = {}
        aliases: dict[str, str] = {}
        changes = RulesChanges()
        for target in targets:
            key = str(target.path)
            real = real_path(target.path)
            if real in handled:
                aliases[key] = handled[real]
                continue
            handled[real] = key
            new = joined[key].text if target.setting_up else ""
            found = self.lines_found(target, new, operating[target.agent])
            if found is None:
                continue
            # What the file holds now, which setup may overwrite once its lines are saved, or at
            # once when it has none to save, as when someone only took lines out.
            checked[key] = found.current
            if not found.moving.text:
                continue
            what = (
                f"The rules in {target.path}, from before setup"
                if found.moving.whole
                else f"Lines setup didn't write in {target.path}"
            )
            chosen = self.rules_choices.get(key)
            if chosen is not None and chosen.current != found.current:
                # The file changed after the question: its new lines have no answer yet.
                chosen = None
            if chosen is not None and chosen.choice != "move":
                done = "in the Recycle Bin" if chosen.choice == "sent" else "deleted for good"
                self.status("REMOVED", f"{what}: {done}, as you chose")
                self.keep_saved(found)
                continue
            level = chosen.level if chosen else f"{rules.PCS}/{pc}/{target.agent}"
            folder = rules_root / level / (rules.MINE if chosen else rules.UNANSWERED)
            inside = target.path.relative_to(target.folder)
            # Wherever it joins for this file, such as where a run stopped by Ctrl+C left it:
            # added again, the lines would load twice.
            holder = rules.already_held(
                found.moving.text, rules_root, pc, target.agent, system, target.path
            )
            if holder is not None:
                if not self.should(holder, f"{what}: already in dev-home, in"):
                    continue
                self.status(
                    "REMOVED",
                    f"{what}, which dev-home's {relative(content_root, holder)} already holds, so "
                    "setup didn't add them again",
                )
            else:
                holder = folder / rules.moved_name(pc, target.folder, inside, names_in(folder))
                place = "moved into your rules" if chosen else "set aside in dev-home"
                if not self.should(holder, f"{what}, {place}, then committed and pushed"):
                    continue
                about = MOVED_WHOLE if found.moving.whole else MOVED_LINES
                text = rules.moved_file(
                    found.moving.text, when=when, pc=pc, source=target.path, about=about
                )
                if not self.write_new_file(holder, text, f"{what}: setup couldn't save them in"):
                    checked[key] = None
                    continue
                self.status("WROTE", f"{what}, {place}: {relative(content_root, holder)}")
                changes.written.append(holder)
            saved[key] = (found, holder)
            changes.paths.append(holder)
            label = f"{target.folder.name}/{inside.as_posix()}"
            # Named for where the lines are, which may be where an earlier run put them.
            into = holder.parent.relative_to(rules_root).as_posix()
            changes.actions.append(
                f"set aside lines setup didn't write in {label}"
                if rules.UNANSWERED in holder.relative_to(rules_root).parts
                else f"move lines setup didn't write in {label} into {into}"
            )
        # The files a person answered first, so that one moved into a mine/ is found holding the
        # text of any other left waiting, which would load twice.
        waiting = unanswered_files(rules_root, pc)
        for path in sorted(waiting, key=lambda path: str(path) not in self.rules_choices):
            self.answer_waiting(content_root, pc, system, path, changes)
        # Its sync may also merge in other PCs' commits, which change rules/ too.
        changed = bool(changes.paths)
        if changes.paths:
            if self.commit_rules(content_root, changes.paths, changes.actions):
                for found, _ in saved.values():
                    self.keep_saved(found)
            else:
                self.take_back(content_root, changes)
                for key in saved:
                    checked[key] = None
                    self.status(
                        "PROBLEM",
                        f"{key} has lines setup didn't write, which setup couldn't commit in "
                        "dev-home, so it left the file as it is. Setup tries again on its next "
                        "run.",
                    )
        for alias, key in aliases.items():
            if key in checked:
                checked[alias] = checked[key]
        return checked, changed

    def take_back(self, content_root: Path, changes: RulesChanges) -> None:
        """After a failed commit: removes each file this run wrote in rules/, and puts back each
        it removed, so nothing it couldn't commit stays there, where it would join, and might
        never be committed. Says so for each file in unanswered/ a person answered, which waits
        for their answer again."""
        for path in changes.written:
            try:
                remove_generated_file(path)
            except OSError as error:
                self.status(
                    "PROBLEM", f"Could not take back {path}, which isn't committed. {error}"
                )
        for path, data in changes.removed.items():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            except OSError as error:
                self.status("PROBLEM", f"Could not put back {path}. {error}")
        for shown in changes.answered:
            self.status(
                "PROBLEM",
                f"{shown}: setup couldn't commit what you chose for it, so it put the file back, "
                "where it waits for your answer again.",
            )

    def keep_saved(self, found: FoundLines) -> None:
        """Keeps what an agent's rules file held once the lines setup didn't write in it are
        saved, as setup's copy for that folder, in place of what it last wrote there. A later run
        then finds only the lines added since, even when the file can't be written this run, such
        as when it changed meanwhile, and never saves the same lines twice."""
        copy = LAST_WRITTEN / rules.copy_name(found.target.folder)
        if not self.should(
            copy, "Keep a copy of the rules file as it was when its lines were saved"
        ):
            return
        try:
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes(found.current)
        except OSError as error:
            self.status("PROBLEM", f"Could not write {copy}. {error}")

    def answer_waiting(
        self, content_root: Path, pc: str, system: str, path: Path, changes: RulesChanges
    ) -> None:
        """A file in this PC's unanswered/ folders, while it's still as it was at this run's
        questions: moved into the mine/ a person chose, or removed, which the Recycle Bin has, or
        a person chose to delete for good. One whose text a mine/ file that joins for that agent
        on this PC already holds is only removed, answered or not, such as one whose twin from
        another folder a person moved into a mine/: it would load twice. What it does goes in
        changes."""
        chosen = self.rules_choices.get(str(path))
        try:
            current = path.read_bytes()
        except OSError:
            return
        if chosen is not None and current != chosen.current:
            chosen = None
        rules_root = content_root / rules.RULES
        text = rules.decode(path, current)[0]
        agent = path.relative_to(rules_root).parts[2]
        # Only a mine/ counts: a file set aside counts only for where it came from.
        holder = rules.already_held(text, rules_root, pc, agent, system, None, skip=path)
        if chosen is None and holder is None:
            return
        shown = relative(content_root, path)
        wrote: Path | None = None
        # The file in rules/ that holds the text once this one is gone, committed with it.
        keeps: list[Path] = []
        if holder is not None:
            held = relative(content_root, holder)
            if not self.should(path, f"Remove it: dev-home's {held} already holds it"):
                return
            state, said = "REMOVED", f"{held} already holds it, so setup removed it"
            action = f"remove {shown}, which {held} already holds"
            keeps.append(holder)
        elif chosen is not None and chosen.choice == "move":
            folder = rules_root / chosen.level / rules.MINE
            wrote = folder / rules.free_name(path.stem, names_in(folder))
            moved = relative(content_root, wrote)
            if not self.should(path, f"Move it into your rules, as {moved}"):
                return
            if not self.write_new_file(wrote, text, f"{shown}: setup couldn't move it into"):
                return
            state, said = "WROTE", f"moved into your rules, as you chose: {moved}"
            action = f"move {shown} into {chosen.level}/{rules.MINE}"
            keeps.append(wrote)
        else:
            if not self.should(path, "Remove it"):
                return
            state = "REMOVED"
            said = (
                "in the Recycle Bin, as you chose"
                if chosen is not None and chosen.choice == "sent"
                else "deleted for good, as you chose"
            )
            action = f"drop {shown}"
        try:
            remove_generated_file(path)
        except OSError as error:
            self.status("PROBLEM", f"Could not remove {path}. {error}")
            # The copy would load beside it, and never be committed.
            if wrote is not None:
                with contextlib.suppress(OSError):
                    remove_generated_file(wrote)
            return
        if wrote is not None:
            changes.written.append(wrote)
        changes.removed[path] = current
        changes.paths += [*keeps, path]
        changes.actions.append(action)
        if chosen is not None:
            changes.answered.append(shown)
        # Setup owns unanswered/, so it doesn't leave one empty. Git keeps no empty folder.
        with contextlib.suppress(OSError):
            path.parent.rmdir()
        self.status(state, f"{shown}: {said}")

    def write_new_file(self, path: Path, text: str, failed: str) -> bool:
        """Writes text to path, a file setup moves into rules/, as UTF-8 with LF line breaks, never
        over a file already there. Says what failed, and returns whether it wrote it."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="\n") as file:
                file.write(text)
        except OSError as error:
            self.status("PROBLEM", f"{failed} {path}. {error}")
            return False
        return True

    def commit_rules(
        self, content_root: Path, paths: Sequence[Path], actions: Sequence[str]
    ) -> bool:
        """Commits and pushes the files in rules/ that save lines setup didn't write, in one
        commit, through the sync, as sync_own_files does. Returns whether the commit is made,
        whatever happened after it: a push that waits for GitHub, or a merge the sync couldn't
        make, which it reports, leaves the lines committed on this PC."""
        names = sorted({relative(content_root, path) for path in paths})
        message = f"rules: {'; '.join(dict.fromkeys(actions))}"
        # Loaded only now, so a sync that can't load stops only this commit, not setup.
        try:
            sync = importlib.import_module(f"{__package__}.sync")
            result = sync.setup_commit(content_root, names, message, holds_lock=True)
        except Exception as error:
            self.status("PROBLEM", f"Could not commit {', '.join(names)}: {describe(error)}")
            return False
        if result.code != 0:
            # The sync has said what went wrong.
            self.problems.append(f"Committing {', '.join(names)}")
        return bool(result.committed)

    def report_waiting(self, content_root: Path, pc: str) -> None:
        """The NEW line naming each file in this PC's unanswered/ folders, on every run until a
        person says where each goes, through /dev-home configure or at a console (decision
        0064)."""
        waiting = unanswered_files(content_root / rules.RULES, pc)
        if not waiting:
            return
        listed = ", ".join(relative(content_root, path) for path in waiting)
        self.status(
            "NEW",
            f"Setup set aside rules it didn't write, found in an agent's rules file: {listed}. "
            "Until you say where they go, each loads only in the file it came from. Answer with "
            f"/dev-home configure, or run {by_hand('setup.py')} in a terminal, and it asks.",
        )

    def report_overrides(self, homes: Sequence[str]) -> None:
        """A PROBLEM line for each Codex home whose AGENTS.override.md has text, on every run while
        it does: Codex reads it there in place of setup's AGENTS.md. Setup never changes it."""
        for home in homes:
            path = Path(home) / CODEX_OVERRIDE
            try:
                data = path.read_bytes() if path.is_file() else b""
            except OSError:
                continue
            if data.decode("utf-8-sig", errors="replace").strip():
                self.status(
                    "PROBLEM",
                    f"Codex home {home}: its {CODEX_OVERRIDE} has text, so Codex reads it instead "
                    f"of setup's {CODEX_RULES_FILE} there, and loads neither the operating rules "
                    "nor your rules. Codex's docs call it a temporary override: remove it to load "
                    "setup's file again.",
                )

    def sync_rules_file(
        self, target: RulesTarget, text: str, rules_root: Path, checked: dict[str, bytes | None]
    ) -> None:
        """Writes an agent's rules file in its folder: when there's none; when it still matches
        the copy setup keeps of what it last wrote there; when it already holds what setup would
        write; or while it still holds what it held once the lines setup didn't write in it were
        saved in rules/, as checked has it (see save_lines). Any other file stays as it is: one
        whose lines setup couldn't save, which save_lines has said, or one that changed since, and
        the next run saves its lines. A link whose target is gone is replaced; any other link
        stays, as setup never writes through one."""
        folder, path = target.folder, target.path
        label = f"Rules file in {folder.name}"
        copy = LAST_WRITTEN / rules.copy_name(folder)
        data = text.encode("utf-8")
        existing = link_info(path)
        if existing is not None and existing.is_link:
            if existing.target is not None and Path(existing.target).exists():
                self.status(
                    "PROBLEM",
                    f"{label}: {path} links to {existing.target}, so setup left it alone. Move "
                    f"anything you want to keep into {rules_root}, delete the link, then run "
                    "setup.py again.",
                )
                return
            if not self.should(
                path, "Replace this link, whose target is gone, with the rules file"
            ):
                return
            try:
                path.unlink()
            except OSError as error:
                self.status("PROBLEM", f"{label}: could not remove the link {path}. {error}")
                return
            existing = None
        try:
            current = path.read_bytes() if existing is not None else None
            kept = copy.read_bytes() if copy.is_file() else None
        except OSError as error:
            self.status("PROBLEM", f"{label}: {path} couldn't be read, so setup left it. {error}")
            return
        if (
            current is not None
            and current not in (data, kept)
            and checked.get(str(path)) != current
        ):
            return
        if current == data:
            self.status("OK", label)
        elif self.should(path, "Write the operating rules and your rules, joined"):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_file():
                    make_writable(path)
                path.write_bytes(data)
            except OSError as error:
                self.status("PROBLEM", f"{label}: could not write {path}. {error}")
                return
            self.status("WROTE", f"{label}: {path}")
        else:
            return
        if kept != data and self.should(copy, "Keep a copy of the rules file setup wrote"):
            try:
                copy.parent.mkdir(parents=True, exist_ok=True)
                copy.write_bytes(data)
            except OSError as error:
                self.status("PROBLEM", f"Could not write {copy}. {error}")

    # Python, for the skills' scripts

    def sync_python_link(self, local_app_data: Path, *, skip_registry: bool) -> None:
        """Points internal/.python, a junction, at the folder of the first of
        python_link.candidates that runs, so the skills' commands name the same short path on
        every PC, with no spaces to quote, and move on to a newer Python once one is installed.
        Setup only uses Pythons already installed, and never installs one. Most runs find that
        the link already points at the first candidate, which starts no process: setup starts a
        Python only to check it before pointing the link at it. One that doesn't run is noted
        in FAILED_PYTHONS, and a quiet run with a working link, such as a sync's, skips it until
        its python.exe changes, so a broken install holds up at most one sync. A run by hand
        checks it again."""
        label = "Python for the skills"
        existing = link_info(PYTHON_LINK)
        if existing is not None and not existing.is_link:
            self.status(
                "PROBLEM",
                f"{label}: {PYTHON_LINK} already exists and is not a link. Setup makes a junction "
                "there to a Python install. Move it aside, then run setup.py again.",
            )
            return
        current = None
        if existing is not None and existing.target and (PYTHON_LINK / "python.exe").is_file():
            current = Path(existing.target)
        # Read only once a Python would be started.
        failures: dict[str, list[int]] | None = None
        for candidate in python_link.candidates(local_app_data, skip_registry=skip_registry):
            if not (candidate / "python.exe").is_file():
                continue
            if current is not None and same_path(candidate, current):
                break
            if failures is None:
                failures = python_link.read_failures(FAILED_PYTHONS)
            key = python_link.failure_key(candidate)
            found = python_link.fingerprint(candidate)
            noted = found is not None and failures.get(key) == found
            if noted and current is not None and self.quiet:
                continue
            version = python_link.python_version(candidate)
            if version is None:
                self.status(
                    "PROBLEM",
                    f"{label}: the Python in {candidate} didn't run as Python 3.12 or later. "
                    "Syncs skip it until its python.exe changes, and running setup.py in a "
                    "terminal checks it again.",
                )
                if found is not None and not noted:
                    failures[key] = found
                    self.write_failures(failures)
                continue
            if failures.pop(key, None) is not None:
                self.write_failures(failures)
            self.point_python_link(existing, current, candidate, version, skip_registry)
            return
        if current is not None:
            self.status("OK", f"{label}: {current}")
            return
        self.status(
            "PROBLEM",
            f"{label}: no Python 3.12 or later was found, and the skills run their scripts "
            "with it. Install it with the Python install manager (see the README's "
            "Requirements), then run setup.py again.",
        )

    def point_python_link(
        self,
        existing: LinkInfo | None,
        current: Path | None,
        folder: Path,
        version: str,
        skip_registry: bool,
    ) -> None:
        """Points internal/.python at folder, whose Python is version, and says so. A switch from
        current, a Python that still works, names both versions."""
        label = "Python for the skills"
        if not self.should(PYTHON_LINK, f"Link to the Python in {folder}"):
            return
        try:
            if existing is not None:
                remove_folder_link(PYTHON_LINK)
            kind = make_folder_link(PYTHON_LINK, folder)
        except OSError as error:
            self.status("PROBLEM", f"{label}: could not link {PYTHON_LINK} to {folder}. {error}")
            return
        if current is None:
            self.status("LINKED", f"{label} ({kind}): {PYTHON_LINK} -> {folder}")
            return
        # The registry has the version of the Python it switched from, unless that one isn't
        # registered, or this is a test profile, which doesn't read it.
        was = None if skip_registry else python_link.registered_version(current)
        self.status(
            "LINKED",
            f"{label} ({kind}): now {version}, was {was or f'the Python in {current}'}. "
            f"{PYTHON_LINK} -> {folder}",
        )

    def write_failures(self, failures: dict[str, list[int]]) -> None:
        """Saves the note of Pythons that didn't run, or removes it once none is left."""
        if linked_folder(GENERATED_ROOT) is not None or not self.should(
            FAILED_PYTHONS, "Note which Pythons didn't run"
        ):
            return
        try:
            if FAILED_PYTHONS.is_file():
                make_writable(FAILED_PYTHONS)
            if not failures:
                FAILED_PYTHONS.unlink(missing_ok=True)
            else:
                FAILED_PYTHONS.parent.mkdir(parents=True, exist_ok=True)
                FAILED_PYTHONS.write_text(
                    json.dumps(failures, indent=2) + "\n", encoding="utf-8", newline="\n"
                )
        except OSError as error:
            self.status("PROBLEM", f"Could not write {FAILED_PYTHONS}. {error}")
            return
        self.generated_changes += 1

    # Settings changes. Each is the change a folder setup sets up needs in its settings file,
    # which the yes to setting up that folder approved, so no run asks about it, and every run,
    # quiet ones included, makes it again if it goes missing. Each is planned in full first,
    # checked by reading the new text back, and written with a backup, while the file is as it
    # was planned.

    def show_setting(self, change: SettingsChange) -> None:
        """Shows a planned settings change: what it's for, then the changed lines."""
        self.status("CHANGE", f"{change.subject}: {change.path} needs {change.need}.")
        self.line(
            "          Setup would make this change, and keep a backup of the file first. Lines "
            "marked + are added, - removed:"
        )
        if change.plan.note:
            self.line("          " + change.plan.note)
        self.print_diff(change.plan.file.text, change.plan.new_text or "")

    def repair_setting(self, change: SettingsChange) -> bool:
        """Makes a settings change a folder needs, or one answered no needs, and writes the file
        with a backup, saying so. When the change can't be made safely, it reports a problem and
        leaves the file alone, and, except with --quiet, says what to change by hand. Returns
        whether it wrote the change."""
        plan = change.plan
        problem = f"{change.subject}: {change.path} needs {change.need}."
        if plan.reason:
            if self.quiet:
                self.status(
                    "PROBLEM",
                    f"{problem} Setup won't change this file itself: {plan.reason}. Run "
                    f"{by_hand('setup.py')} in a terminal to see what to change by hand.",
                )
                return False
            self.status("PROBLEM", problem)
            self.line(f"          Setup won't change this file itself: {plan.reason}.")
            self.line("          " + change.how_to)
            if change.snippet:
                self.line(change.snippet, YELLOW)
            return False
        if self.what_if:
            self.show_setting(change)
            self.should(change.path, "Change the lines shown, and keep a backup")
            return False
        try:
            now = read_settings_file(change.path)
            if now.reason or now.text != plan.file.text:
                raise OSError(
                    "The file changed while setup was planning its change, so it was left alone. "
                    "The next run makes the change."
                )
            backup = write_settings_file(
                change.path, plan.new_text or "", bom=plan.file.bom, backup=True
            )
            saved = f". Backup of the old file: {backup}" if backup else " (new file)"
            self.status("SET", f"{change.subject}: {change.done} in {change.path}{saved}")
        except (OSError, ValueError) as error:
            self.status("PROBLEM", f"{change.subject}: could not write {change.path}. {error}")
            return False
        return True

    # The run, in order: where things are; dev-home; the questions not answered yet; at a
    # console, the settings menu; the change to dev-home.json to confirm; then the work, which
    # asks nothing and holds the sync's lock, the agents' settings files last, since a sync makes
    # their changes too.

    def run(self, content_dir_option: str) -> None:
        settings, read = self.read_settings()
        self.codex_doc_bytes = codex_doc_bytes(settings.data)
        # A PC's first setup: no dev-home folder saved yet, such as after settings are set aside.
        first_setup = not settings.content_dir
        if self.configure is not None:
            with self.answering(settings):
                try:
                    configure.change_settings(self, settings)
                except configure.SettingError as error:
                    self.status("PROBLEM", f"{error} Nothing was changed.")
                    if not isinstance(error, configure.AnswerError):
                        self.line(configure.USAGE)
                    raise CannotGoOnError from error
            if self.just_showing:
                raise CannotGoOnError
        # Each of a shared agent's folders gets the answer they share, so the questions and the
        # menu show it. It's setup's own change, not an answer, so the work works it out again
        # (see settle).
        for agent in (CLAUDE_CODE, CODEX):
            if agent.shared:
                self.match_shared_answer(agent, settings)

        with self.answering(settings):
            # 1. dev-home first: its folder, then, when it's missing, clone or create it. Nothing
            # is saved before it's in place.
            self.choose_dev_home_folder(settings, content_dir_option)
            while True:
                content_root = self.find_dev_home(settings)
                # 2. The questions not answered yet.
                self.ask_unanswered(settings, content_root, first_setup=first_setup)
                # 3. At a console, the settings menu, so any setting can be changed.
                if not self.can_ask:
                    break
                folder = settings.content_dir
                if configure.menu(self, settings):
                    self.changed_by_hand = True
                if same_path(folder, settings.content_dir):
                    break
                # Another dev-home folder: its checks again, and its own answer about copies.
                self.wanted_copies = None
                self.cloned = self.created = False
        declared = self.skills_declared(settings)

        # 4. The change to dev-home.json to confirm, shown and asked about before the work; what
        # to do with a hand edit to dev-home's AGENTS.md or CLAUDE.md that the Recycle Bin can't
        # take; and where lines setup didn't write in each agent's rules file go.
        self.confirm_copies(content_root)
        self.ask_about_guidance(content_root)
        self.ask_about_rules(content_root, settings)

        # 5. The work, on this PC's settings as it saves them: the file as it is by then, with
        # this run's answers, and setup's own changes worked out again (see settle). Skills this
        # PC has no answer for yet each follow their default, and the NEW line names them, once.
        with self.work_lock(content_root) as owned:
            if not owned:
                raise CannotGoOnError
            settled = self.settle(settings, read, declared)
            saved = self.save(settled)
            if settled.problem and self.recommended_yes:
                # A yes to a recommended setting couldn't be saved, so it isn't written either,
                # and its offer comes back.
                if not self.save_failed:
                    self.status("PROBLEM", settled.problem)
                self.recommended_yes.clear()
            self.codex_doc_bytes = codex_doc_bytes(settled.settings.data)
            for matched in settled.matched.values():
                if self.what_if:
                    self.line(f"What if: {matched}")
                elif saved:
                    self.status("SET", matched)
            agent_folders = self.agent_folders(settled.settings)
            folders = self.skills_folders(agent_folders, declared)
            plans = self.plan_skills(settled.settings.data, declared, folders)
            told = new_skills_text(settled.new_skills, plans)
            if told and self.what_if:
                self.line(f"What if: {told}")
            elif told and saved:
                self.status("NEW", told)
            self.set_up(settled.settings, content_root, agent_folders, folders, plans)
            # The agents' settings files: the change each folder set up needs, which its yes
            # approved, with each recommended setting a person said yes to in this run, and the
            # access taken back out of each one answered no, which the no approved, each made with
            # a backup. See repair_setting. Then each such yes whose change is written is saved.
            checks = self.settings_checks(content_root, agent_folders)
            # A yes whose folder has the recommended value already needs no write.
            written: list[tuple[Path, str]] = list(self.recommended_already)
            for check in checks:
                if isinstance(check, SettingsChange):
                    # A preview says what it would save too.
                    shown = self.what_if and not check.plan.reason
                    if self.repair_setting(check) or shown:
                        written += [(check.path.parent, done) for done in check.recommended]
                    elif not self.what_if:
                        self.leave_out(
                            check.path.parent, check.recommended, "setup couldn't write the file"
                        )
                else:
                    self.status(*check)
            self.save_recommended(settled, written)

    def read_settings(self) -> tuple[LocalSettings, dict[str, Any] | None]:
        """Where things are: dev-home-toolkit's folder, the profile to set up, and this PC's
        settings, checked, with what the check moved or removed, which it keeps in self.checked.
        Returns them, and the file as this run read it, or None when there was none: the work
        removes only what that held (see settle)."""
        toolkit_problem = unsafe_reason(comparable(TOOLKIT_ROOT))
        if toolkit_problem:
            self.status(
                "PROBLEM",
                f"dev-home-toolkit is at {comparable(TOOLKIT_ROOT)}, which {toolkit_problem}. "
                "Setup writes this path into commands as it is, so move the folder, then run "
                "setup.py again.",
            )
            raise CannotGoOnError
        loaded = load_local_settings()
        if loaded is None:
            self.status(
                "PROBLEM",
                f"{SETTINGS_PATH} could not be read as a JSON object of settings. Fix it, or "
                "delete it and answer the questions again, then run setup.py again.",
            )
            raise CannotGoOnError
        settings: LocalSettings = loaded
        if settings.test_home_dir:
            self.home = Path(comparable(settings.test_home_dir))
            self.test_profile = True
            if not self.home.is_dir():
                self.status(
                    "PROBLEM",
                    f"local-settings.json sets testHomeDir to {self.home}, which does not exist.",
                )
                raise CannotGoOnError
            self.status(
                "TEST",
                f"Using the test profile {self.home} instead of {Path.home()}, because "
                "local-settings.json sets testHomeDir.",
            )
        read: dict[str, Any] | None = copy.deepcopy(settings.data) if settings.found else None
        file_layout = layout(settings.data, SCHEMA_VERSION) if settings.found else ""
        if file_layout == "older":
            settings = self.set_aside_settings(settings)
            read = local_settings_data(settings)
        elif file_layout == "unknown":
            self.status(
                "PROBLEM",
                f"{SETTINGS_PATH} has a schemaVersion this dev-home-toolkit doesn't know, perhaps "
                "written by a newer one, so setup left it alone and stopped. Update "
                f"dev-home-toolkit ({by_hand('update.py')}), or set the file aside and run "
                "setup.py again.",
            )
            raise CannotGoOnError
        declared = skill_declarations(settings.content_dir)
        self.declared = (settings.content_dir, declared)
        # Only a run that holds the sync's lock from its start, a sync's setup, removes the answers
        # of a skill that's gone.
        self.checked = check_settings(
            settings.data, declared, home=self.home, remove_gone_skills=self.sync_holds_lock
        )
        for problem in declared.problems + self.checked.problems:
            self.status("PROBLEM", problem)
        if self.checked.moved or self.checked.removed or self.checked.merged:
            settings = settings_in(self.checked.data)
        return settings, read

    # dev-home first

    def choose_dev_home_folder(self, settings: LocalSettings, content_dir_option: str) -> None:
        """The dev-home folder: --content-dir's, the saved one, or the person's answer."""
        if content_dir_option:
            settings.content_dir = forward(content_dir_option)
        elif not settings.content_dir:
            default = forward(TOOLKIT_ROOT.parent / "dev-home")
            if self.can_ask:
                self.line(
                    "dev-home is your private repo for handoffs and a knowledge base. Setup needs "
                    "its folder on this PC:"
                )
                self.line(
                    "where it is now, or where it should go. Press Enter to accept the suggestion "
                    "in brackets."
                )
            answer = self.ask("Your dev-home folder", default)
            if answer is None:
                self.status(
                    "PROBLEM",
                    "This PC has no dev-home folder set. Run setup.py once in a terminal without "
                    "--quiet, and it asks for one.",
                )
                raise CannotGoOnError
            settings.content_dir = forward(answer)

    def find_dev_home(self, settings: LocalSettings) -> Path:
        """dev-home's folder on this PC, once it's there: a folder that must look like a dev-home
        when it has files, or, when it's missing or empty, one cloned or created there. Setup
        stops when it can't be."""
        while True:
            # Checked as setup will use it, so a hand-edited C:/dev-home/.. counts as the drive
            # root it leads to.
            content_problem = unsafe_reason(forward(settings.content_dir))
            if content_problem:
                self.status(
                    "PROBLEM",
                    f"The dev-home folder {settings.content_dir} {content_problem}. Setup writes "
                    "this path into commands as it is. Choose another folder with --content-dir.",
                )
                raise CannotGoOnError
            if is_inside(settings.content_dir, TOOLKIT_ROOT):
                self.status(
                    "PROBLEM",
                    f"The dev-home folder {settings.content_dir} is dev-home-toolkit's own folder, "
                    "or inside it. Choose your dev-home's folder with --content-dir.",
                )
                raise CannotGoOnError
            # An empty or missing folder gets a dev-home below. One with files must already be
            # one, before anything is saved or set in it.
            folder = Path(comparable(settings.content_dir))
            if is_dev_home(folder) or not is_in_use(folder):
                break
            if not self.can_ask:
                self.not_a_dev_home_problem(folder)
                raise CannotGoOnError
            self.line(
                f"{folder} doesn't look like a dev-home: it has no {DEV_HOME_SETTINGS}, which "
                "every dev-home has."
            )
            answer = self.ask("Your dev-home folder, or Enter to stop")
            if not answer:
                self.status("PROBLEM", f"Stopped: {folder} doesn't look like a dev-home.")
                raise CannotGoOnError
            settings.content_dir = forward(answer)

        # Clone or create it when it's missing.
        content_root = Path(comparable(settings.content_dir))
        if not is_in_use(content_root):
            self.initialize_content_repo(content_root, template_values(content_root))
            if not (content_root / ".git").exists():
                if self.what_if:
                    self.line(
                        "What if: the rest of setup works with dev-home, so it can't be previewed "
                        "until dev-home exists."
                    )
                raise CannotGoOnError
        if not (content_root / ".git").exists():
            self.status(
                "PROBLEM",
                f"{content_root} is not a git repo. Point setup at your dev-home with "
                "--content-dir, or move that folder aside so setup can clone or create one there.",
            )
            raise CannotGoOnError
        # A repo with no commits is most likely a new dev-home that setup couldn't finish, for
        # example because git doesn't know the person's name and email yet. Starting over is the
        # simple fix. Only exit code 1 means no commits: anything else is git failing to read
        # the repo, which says nothing about what's in it.
        head = run_git(content_root, "rev-parse", "--verify", "--quiet", "HEAD")
        if head.code == 1:
            self.status(
                "PROBLEM",
                f"{content_root} is a git repo with no commits, probably from a setup run that "
                "stopped partway. If it holds nothing you need, delete the folder, fix what "
                "stopped setup, then run setup.py again to clone or create dev-home there.",
            )
            raise CannotGoOnError
        if head.code != 0:
            self.status(
                "PROBLEM",
                f"git could not read {content_root}, so setup stopped. "
                f"git: {first_line(head.err + head.out)}",
            )
            raise CannotGoOnError

        # A clone of the wrong repo gets no further than a wrong folder would.
        if not is_dev_home(content_root):
            self.not_a_dev_home_problem(content_root)
            raise CannotGoOnError
        return content_root

    # The questions not answered yet

    def ask_unanswered(
        self, settings: LocalSettings, content_root: Path, *, first_setup: bool
    ) -> None:
        """Asks each question whose answer isn't saved yet. A quiet run asks nothing, and names
        what's unanswered instead."""
        if self.can_ask and not setting_value(settings.data, AUTO_UPDATE)[1]:
            updates = self.ask_auto_update(settings.data)
            if updates is not MISSING:
                put(settings.data, AUTO_UPDATE, updates)
        for agent in (CLAUDE_CODE, CODEX):
            self.ask_about_folders(agent, settings)
        self.ask_about_copies(settings, content_root, first_setup=first_setup)
        self.ask_about_recommended(settings)

    def ask_about_folders(self, agent: Agent, settings: LocalSettings) -> None:
        """Asks about each of an agent's folders that setup knows of with no answer yet, or a
        reminder that's due, and keeps every answer, a no included, so it's asked about once: in
        the shared prompt for optional lists, a list of the agent's own, each one recommended, or
        for a shared agent, one question for them all, whose answer goes to every folder. Once one
        of a shared agent's folders has an answer, the others have it too (see
        match_shared_answer), so it asks only while none has. A reminder covers a shared agent's
        folders together too. A folder with a reminder that isn't due isn't asked about.

        A folder with no yes or no isn't set up: setup adds no links there and removes none. A
        quiet run names those it would ask about in a NEW line instead, on every run, and so does
        one where no answer came; one where the person skipped them says nothing more."""
        answers = settings.folders[agent.setting]
        known = self.known_folders(agent, settings)
        today = date.today()

        def waiting(folder: Path) -> bool:
            reminder = self.reminder_of(agent, settings, folder, known)
            return reminder is not None and not reminder.due(today)

        unanswered = [f for f in known if self.entry_named(f, answers) is None and not waiting(f)]
        if not unanswered:
            return
        if self.can_ask:
            if agent.shared:
                shared = self.ask_codex(known, None)
                if shared is not None:
                    self.answer_offer_every_folder(agent, settings, shared)
                    return
            else:
                if len(unanswered) == 1:
                    # A list of one asks its item's question alone, so the folder and what a
                    # yes does come first, as for Codex.
                    self.introduce_folders(agent, unanswered)
                    question = f"Set up {agent.name} in this {agent.folder}?"
                    items = [console.ListItem(str(unanswered[0]), True, question)]
                    answer = self.choose_from_list("", "", items)
                else:
                    self.line()
                    answer = self.choose_from_list(
                        f"{agent.name} {agent.folder}s with no answer yet, one for each "
                        f"{agent.account} account:",
                        f"Set up {agent.name} in them with dev-home's skills and rules?",
                        [
                            console.ListItem(str(f), True, folder_question(agent, f))
                            for f in unanswered
                        ],
                        yes_does(
                            agent,
                            several=True,
                            guarded=self.any_guarded(agent, unanswered),
                            doc_bytes=self.codex_doc_bytes,
                        ),
                    )
                if answer is not None:
                    for folder in unanswered:
                        self.answer_offer(agent, settings, folder, answer.answers[str(folder)])
                    return
        self.name_unanswered(agent, settings, known, unanswered)

    def name_unanswered(
        self,
        agent: Agent,
        settings: LocalSettings,
        known: Sequence[Path],
        unanswered: Sequence[Path],
    ) -> None:
        """The NEW lines naming an agent's folders with no answer yet, which setup leaves as they
        are, with how to answer: in chat, or in a terminal. A NEW line, not a PROBLEM, since
        nothing is wrong: the folder waits for an answer."""
        # The session's own folder, when it's in the profile folder under another name or outside
        # it, comes only from the agent's variable, which a terminal usually doesn't have.
        visible = self.profile_folders(agent) + [
            f for f in known if self.listed(f, listed_entries(get(settings.data, agent.setting)))
        ]
        unseen = [f for f in unanswered if not any(same_path(f, v) for v in visible)]
        # A shared agent's yes covers every folder.
        set_up = f"set up {agent.name}" if agent.shared else "set it up"
        for folder in unseen:
            self.status(
                "NEW",
                f"Setup has no answer yet {unanswered_text(agent, [folder], session=True)}. "
                f"{answer_in_chat()}. Setup in a terminal usually can't see it: to {set_up} "
                f"there, run {by_hand('setup.py')} --configure "
                f"'{agent.setting}+={self.folder_entry(folder)}'.",
            )
        seen = [f for f in unanswered if f not in unseen]
        if seen:
            for_each = len(seen) > 1 and not agent.shared
            self.status(
                "NEW",
                f"Setup has no answer yet {unanswered_text(agent, seen)}. "
                f"{answer_in_chat(for_each=for_each)}. Or run {by_hand('setup.py')} in a "
                "terminal, and it asks.",
            )

    def agent_folders(self, settings: LocalSettings) -> AgentFolders:
        """Where setup sets up each agent, from the answers: each Claude Code folder and Codex home
        answered yes. And each one answered no, unless a yes covers it too: a folder saved under
        two names, or reached through a junction, or a Codex home while another is answered yes,
        since every home shares one answer."""
        claude_dirs = [full for _, full in self.folders_answered(CLAUDE_CODE, settings, True)]
        codex_homes = [full for _, full in self.folders_answered(CODEX, settings, True)]
        declined_claude_dirs = [
            full for _, full in self.folders_answered(CLAUDE_CODE, settings, False)
        ]
        # Following links takes a little time, so only a run with a folder answered no does it.
        if declined_claude_dirs:
            set_up = {real_path(d) for d in claude_dirs}
            declined_claude_dirs = [d for d in declined_claude_dirs if real_path(d) not in set_up]
        declined_codex_homes = (
            []
            if codex_homes
            else [full for _, full in self.folders_answered(CODEX, settings, False)]
        )
        return AgentFolders(claude_dirs, codex_homes, declined_claude_dirs, declined_codex_homes)

    def folders_answered(
        self, agent: Agent, settings: LocalSettings, answer: bool
    ) -> list[tuple[str, str]]:
        """Each of an agent's folders with that answer that's there, each once: its entry in the
        settings, and its full path, in order, the default one first (see folder_rank), so the
        questions, the menu, and the work all go through them alike, however the file lists
        them."""
        folders: list[tuple[str, str]] = []
        for entry in answered(settings.folders[agent.setting], answer):
            if not entry.strip():
                continue
            full = comparable(resolve_home(entry, self.home))
            # A folder answered yes that's gone, such as an account removed on purpose, keeps its
            # answer, so it's set up again if it comes back. The settings menu shows it.
            if not Path(full).exists():
                continue
            if not any(same_path(full, d) for _, d in folders):
                folders.append((entry, full))
        return sorted(folders, key=lambda pair: folder_rank(agent, pair[1], self.home))

    def set_up_entry(self, agent: Agent, settings: LocalSettings, folder: str | Path) -> str | None:
        """The entry of one of an agent's folders answered yes that's there, as folders_answered
        gives it, which the offers of recommended settings and the menu read. None when there's no
        such entry."""
        return next(
            (
                entry
                for entry, full in self.folders_answered(agent, settings, True)
                if same_path(full, folder)
            ),
            None,
        )

    # Skills: which are added to the agents on this PC, and where

    def skills_declared(self, settings: LocalSettings) -> SkillDeclarations:
        """What the skills declare, as this run read them with this PC's settings, or read again
        once dev-home is in place, when it wasn't at first, such as one this run just cloned, or
        another dev-home folder was chosen since. A second read reports only the problems the
        first didn't."""
        first = self.declared
        if first is not None and first[0] == settings.content_dir and first[1].complete:
            return first[1]
        declared = skill_declarations(settings.content_dir)
        for problem in declared.problems:
            if first is None or problem not in first[1].problems:
                self.status("PROBLEM", problem)
        self.declared = (settings.content_dir, declared)
        return declared

    def note_new_skills(self, settings: LocalSettings, declared: SkillDeclarations) -> list[str]:
        """Saves each skill this PC has no answer for, about adding it to the agents, as
        unanswered, the one state a quiet run writes, so it follows its default, and the NEW line
        names it once (see new_skills_text). The work runs this on the settings as it saves them,
        so a mark never replaces an answer, and a skill another run marked meanwhile, and named,
        isn't named again. A value of the wrong kind stays as it is, since setup reports it.
        Returns the names of the skills it saved."""
        if not isinstance(settings.data.get("skills", {}), dict):
            return []
        new: list[str] = []
        for name, skill in declared.skills.items():
            if skill.added_setting is None:
                continue
            # A setting's name is its path, with dots between its parts, so a skill with a dot in
            # its name has none, and follows its default. A test keeps dots out of
            # dev-home-toolkit's skills, and the PROBLEM line for the name says so for the end
            # user's own (see name_problem in settings.py).
            if "." in name:
                continue
            path = saved_skill_path(settings.data, name, ADDED_TO_AGENTS)
            entry = get(settings.data, path.rsplit(".", 1)[0], MISSING)
            if entry is MISSING or (isinstance(entry, dict) and ADDED_TO_AGENTS not in entry):
                put(settings.data, path, {STATE: "unanswered"})
                new.append(name)
        return new

    def skills_folders(
        self, agent_folders: AgentFolders, declared: SkillDeclarations
    ) -> list[tuple[Path, frozenset[str]]]:
        """Each skills folder setup links skills into, with the agents it sets up that read it,
        each by its name in a skill's supportedOn: each Claude Code folder's skills/, and for Codex,
        ~/.agents/skills. Adding an agent: see AGENTS_SKILLS, which other agents read too,
        so its set of agents would grow.

        A folder that is really another one, through a junction, such as ~/.claude/skills made a
        junction to ~/.agents/skills to share skills, is one folder that both agents read, under
        the first name it has here. Only a skill supported on one agent tells them apart, so only
        then does setup follow the links, which takes a little time."""
        claude_code = frozenset({REQUIRES_NAMES[CLAUDE_CODE.name]})
        folders = [(Path(d) / "skills", claude_code) for d in agent_folders.claude_dirs]
        if agent_folders.codex_homes:
            folders.append((self.home / AGENTS_SKILLS, frozenset({REQUIRES_NAMES[CODEX.name]})))
        if not any(r.kind == "agent" for s in declared.skills.values() for r in s.requires):
            return folders
        merged: dict[str, tuple[Path, frozenset[str]]] = {}
        for folder, readers in folders:
            real = real_path(folder)
            first, before = merged.get(real, (folder, frozenset()))
            merged[real] = (first, before | readers)
        return list(merged.values())

    def plan_skills(
        self,
        data: dict[str, Any],
        declared: SkillDeclarations,
        folders: Sequence[tuple[Path, frozenset[str]]],
    ) -> dict[str, SkillPlan]:
        """What setup does with each skill on this PC (see plan_skill), by its name in lowercase,
        from its answer in data and what it requires, checked against this PC's facts, gathered
        once."""
        pc = requirements.this_pc(
            requirements.programs_named(
                requirement for skill in declared.skills.values() for requirement in skill.requires
            )
        )
        plans = {
            name.lower(): plan_skill(skill, data, pc, folders)
            for name, skill in declared.skills.items()
        }
        for name in sorted(declared.unread):
            plans[name] = SkillPlan(
                name, (), (), "left as it is: its dev-home-skill.json can't be read", told=False
            )
        return plans

    def write_skill_states(self, plans: dict[str, SkillPlan]) -> None:
        """Records each skill's state on this PC (see SkillPlan), which /dev-home skills shows:
        facts.py reads it, so it never works out whether a skill is added itself. It only checks
        again, where the agent runs, what each skill needs that setup only warns about."""
        text = (
            json.dumps(
                {plan.name: recorded_state(plan) for plan in plans.values()},
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
        try:
            if SKILL_STATES.is_file() and SKILL_STATES.read_text(encoding="utf-8") == text:
                return
        except OSError:
            pass
        if linked_folder(GENERATED_ROOT) is not None or not self.should(
            SKILL_STATES, "Write what setup decided for each skill"
        ):
            return
        try:
            SKILL_STATES.parent.mkdir(parents=True, exist_ok=True)
            if SKILL_STATES.is_file():
                make_writable(SKILL_STATES)
            SKILL_STATES.write_text(text, encoding="utf-8", newline="\n")
        except OSError as error:
            self.status("PROBLEM", f"Could not write {SKILL_STATES}. {error}")
            return
        self.generated_changes += 1

    # The work, which asks nothing

    def set_up(
        self,
        settings: LocalSettings,
        content_root: Path,
        agent_folders: AgentFolders,
        folders: Sequence[tuple[Path, frozenset[str]]],
        plans: dict[str, SkillPlan],
    ) -> None:
        """Everything setup sets up besides this PC's settings and the agents' settings files, in
        order: dev-home's git config, its dev-home.json, the end user's files setup keeps there,
        and its AGENTS.md and CLAUDE.md, Python for the skills' scripts, the
        generated files and each skill's state, the skills' links in each skills folder in
        folders, as plans says, and the always-on rules."""
        values = template_values(content_root)

        # 1. dev-home: no signing prompts for agent commits; pulls that merge rather than rebase,
        # as sync.py does, because a rebase refuses to run while any file is uncommitted; and
        # paths longer than Windows' default limit, which rules/ can need (decision 0065). One
        # git call reads all three, and a path that's too long anyway is a PROBLEM.
        wanted = {"commit.gpgsign": "false", "pull.rebase": "false", "core.longpaths": "true"}
        listed = run_git(content_root, "config", "--local", "--list")
        current: dict[str, str] = {}
        for line in listed.out:
            key, _, value = line.partition("=")
            current[key.lower()] = value
        for key, value in wanted.items():
            if current.get(key) == value:
                self.status("OK", f"dev-home git config {key} = {value}")
            elif self.should(f"git config --local {key} in {content_root}", f"Set to {value}"):
                if run_git(content_root, "config", "--local", key, value).code == 0:
                    self.status("SET", f"dev-home git config {key} = {value}")
                else:
                    self.status("PROBLEM", f"Could not set git config {key} in {content_root}.")
        # A test profile's dev-home sits deep inside this repo's folder, past that length, so the
        # tests check path_problem by itself.
        too_long = "" if settings.test_home_dir else rules.path_problem(content_root)
        if too_long:
            self.status("PROBLEM", too_long)
        # With signing off, so a commit needs no prompt. A skill a merge here brings in is linked
        # by the next run, which names it in its NEW line first.
        self.write_copies(content_root)
        # The end user's files setup keeps in dev-home, for the agents set up on this PC.
        pc = rules.pc_folder(computer_name())
        claude_code, codex = REQUIRES_NAMES[CLAUDE_CODE.name], REQUIRES_NAMES[CODEX.name]
        agents = [
            *([claude_code] if agent_folders.claude_dirs else []),
            *([codex] if agent_folders.codex_homes else []),
        ]
        self.sync_own_files(content_root, pc, agents)
        self.sync_guidance(content_root, values)

        # 2. Python, for the skills' scripts. A test profile has its own AppData folder.
        if settings.test_home_dir:
            local_app_data = self.home / "AppData" / "Local"
        else:
            local_app_data = Path(
                os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
            )
        self.sync_python_link(local_app_data, skip_registry=bool(settings.test_home_dir))

        # 3. Generated files: the skills and the scripts they share, with this PC's paths filled
        # in, at the same paths they have under templates/. None carries a note saying not to edit
        # it: each would cost tokens on every load (decision 0064). The operating rules go into
        # each agent's rules file instead (step 5).
        skill_sources = skill_templates()
        generated_skills = GENERATED_ROOT / "skills"
        for skill in skill_sources:
            destination = generated_skills / skill.name
            skill_values = dict(values)
            skill_values["SKILL_DIR"] = forward(destination)
            skill_values["SKILL_STAMP"] = generated.skill_stamp(skill / "SKILL.md", skill_values)
            self.sync_generated_folder(destination, skill_values, skill)
        skill_names = {os.path.normcase(skill.name) for skill in skill_sources}
        if generated_skills.exists():
            for folder in sorted(generated_skills.iterdir()):
                stale = os.path.normcase(folder.name) not in skill_names
                if folder.is_dir() and not is_link(folder) and stale:
                    self.sync_generated_folder(folder, values)
        # The scripts the skills share. The skills run them from here, at the path
        # SHARED_SKILL_SCRIPTS_DIR gives.
        self.sync_generated_folder(
            GENERATED_ROOT / "shared-skill-scripts",
            values,
            TOOLKIT_ROOT / "templates" / "shared-skill-scripts",
        )
        # The operating rules, filled in here so a placeholder they don't know is reported with
        # the others, below; step 5 writes them into each agent's rules file.
        operating_rendered = generated.render(OPERATING_TEMPLATE, values)
        self.unknown_placeholders.extend(operating_rendered.unknown)
        # A folder here with no templates, such as one left from an older layout, is removed.
        # A link here isn't setup's, so it stays.
        if GENERATED_ROOT.exists():
            for folder in sorted(GENERATED_ROOT.iterdir()):
                stale = folder.name.lower() not in GENERATED_FOLDERS
                if folder.is_dir() and not is_link(folder) and stale:
                    self.sync_generated_folder(folder, values)
        note_path = GENERATED_ROOT / "README.txt"
        note_differs = not note_path.exists() or note_path.read_bytes() != FOLDER_NOTE.encode(
            "utf-8"
        )
        if (
            note_differs
            and GENERATED_ROOT.exists()
            and linked_folder(GENERATED_ROOT) is None
            and self.should(note_path, "Write a note about this folder")
        ):
            with note_path.open("w", encoding="utf-8", newline="") as file:
                file.write(FOLDER_NOTE)
        self.write_skill_states(plans)

        for unknown in dict.fromkeys(self.unknown_placeholders):
            self.status("PROBLEM", f"A placeholder setup does not know, left as it is: {unknown}")
        label = "Skills and their shared scripts with this PC's paths"
        if self.generated_changes > 0:
            self.status(
                "WROTE", f"{label}: {self.generated_changes} file(s) changed in {GENERATED_ROOT}"
            )
        else:
            self.status("OK", label)

        # 4. Skills, linked into each agent's personal skills folder: the dev-home-toolkit skills,
        # then the personal skills in dev-home, each where its plan adds it. Every Codex home
        # reads ~/.agents/skills.
        tool_skill_folders = [folder for folder, _ in folders]

        links, same_names = skill_links(content_root, skill_sources)
        for name in same_names:
            self.status(
                "PROBLEM",
                f"Your personal skill '{name}' has the same name as a dev-home-toolkit skill, so "
                "it isn't linked. Rename its folder and its name field.",
            )
        personal_skills = content_root / "skills"

        # Links into these folders are setup's own, so one whose skill is gone can be removed.
        # A link for a skill that's still here stays, even when its generated folder is missing.
        skill_targets = (generated_skills, personal_skills)
        current_skills = {os.path.normcase(name) for name, _ in links}
        for folder in tool_skill_folders:
            for name, target in links:
                plan = plans.get(name.lower())
                # A skill that arrived during this run, in a merge, is planned by the next.
                if plan is None:
                    continue
                link = folder / name
                if folder in plan.added_to:
                    self.sync_link(link, target, f"Skill '{name}' in {folder}")
                    continue
                why = next((why for left, why in plan.left_out if left == folder), None)
                if why is not None and setup_link_target(link, skill_targets) is not None:
                    self.remove_link(
                        link,
                        f"Remove a link to the skill '{name}', which {why}",
                        f"Link to the skill '{name}', which {why}",
                    )
            if not folder.exists():
                continue
            for entry in sorted(folder.iterdir()):
                if os.path.normcase(entry.name) in current_skills:
                    continue
                points_to = setup_link_target(entry, skill_targets)
                if points_to is not None and not Path(points_to).exists():
                    self.remove_link(
                        entry, "Remove a link to a deleted skill", "Link to a deleted skill"
                    )

        # 5. Always-on rules: one file in each agent's folder, the operating rules, with the
        # blocks of the skills added for that agent, and then the end user's rules from dev-home's
        # rules/, joined for that agent on this PC (see the description above). First the lines
        # setup didn't write in each agent's file go into rules/, so the files are joined from
        # what rules/ holds then. Each line about a problem in the end user's files is said once,
        # though a file in _all-agents/ joins for every agent.
        rules_root = content_root / rules.RULES
        targets = self.rules_targets(agent_folders)
        operating = operating_by_agent(
            operating_rendered.data.decode("utf-8"), targets, plans, folders
        )
        joined = self.join_rules(operating, rules_root, pc, targets)
        checked, changed = self.save_lines(content_root, pc, targets, operating, joined)
        if changed:
            joined = self.join_rules(operating, rules_root, pc, targets)
        # The most the end user's rules take in any of each agent's files on this PC, which differ
        # only by the files in unanswered/ that came from each.
        sizes: dict[str, int] = {}
        for rules_file in targets:
            if rules_file.setting_up:
                result = joined[str(rules_file.path)]
                self.sync_rules_file(rules_file, result.text, rules_root, checked)
                sizes[rules_file.agent] = max(sizes.get(rules_file.agent, 0), result.own_bytes)
        problems = [problem for result in joined.values() for problem in result.problems]
        problems += [
            rules.stray_file_problem(rules_root, path)
            for path in rules.stray_files(rules_root, pc, agents)
        ]
        for problem in dict.fromkeys(problems):
            self.status("PROBLEM", problem)
        # Rules every session loads, big enough to cost tokens worth noticing: said on every sync,
        # until they shrink or the end user raises the size (decision 0065).
        warn_kib = int(setting_value(settings.data, RULES_WARN_ABOVE)[0])
        large = [
            (requirements.AGENT_NAMES[agent], size)
            for agent, size in sizes.items()
            if warn_kib and size > warn_kib * 1024
        ]
        if large:
            self.status("LARGE", large_rules_text(large, warn_kib))
        self.report_waiting(content_root, pc)
        self.report_overrides(agent_folders.codex_homes)

        # 6. What setup set up in each folder answered no, each removal listed as it goes: the
        # links it made in a Claude Code folder, and for Codex, the links it made in
        # ~/.agents/skills; and the rules file it wrote in each, once the lines it didn't write
        # there are saved in rules/ (step 5). A link counts as setup's when it points where
        # setup's links point, so one of the person's own stays, as does anything that isn't a
        # link. A folder that is really one setup sets up, through a junction, such as
        # ~/.claude/skills made a junction to ~/.agents/skills to share skills, keeps its links
        # and its rules file. What a yes added to the agents' settings files is taken out last,
        # with the other settings changes (see settings_checks).
        set_up: set[str] = set()
        if agent_folders.declined_claude_dirs or agent_folders.declined_codex_homes:
            set_up = {real_path(folder) for folder in tool_skill_folders}
            set_up |= {real_path(target.path.parent) for target in targets if target.setting_up}
        for claude_dir in agent_folders.declined_claude_dirs:
            self.remove_links_in(
                Path(claude_dir) / "skills",
                skill_targets,
                set_up,
                "Remove a link in a folder you said no to",
                "Link in a folder you said no to",
            )
            path = Path(claude_dir) / "rules" / CLAUDE_RULES_FILE
            self.remove_rules_file(Path(claude_dir), path, set_up, checked)
        for home in agent_folders.declined_codex_homes:
            self.remove_rules_file(Path(home), Path(home) / CODEX_RULES_FILE, set_up, checked)
        # Adding an agent: see AGENTS_SKILLS. Only Codex reads that folder today, of the
        # agents setup sets up, so a no to Codex is enough to remove the links there.
        if agent_folders.declined_codex_homes:
            self.remove_links_in(
                self.home / AGENTS_SKILLS,
                skill_targets,
                set_up,
                "Remove a link for Codex, which you said no to",
                "Link for Codex, which you said no to",
            )

    def remove_links_in(
        self,
        folder: Path,
        targets: Sequence[Path],
        set_up: set[str],
        action: str,
        what: str,
    ) -> None:
        """Removes each of setup's links directly in folder (see setup_link_target), one at a
        time. Anything else there stays: a link of the person's own, a file, or a folder. A folder
        whose real path is in set_up is one setup sets up this run, so it's left alone. action
        says what --what-if would do, and what starts each REMOVED line, which names the link."""
        if not folder.is_dir() or real_path(folder) in set_up:
            return
        for entry in sorted(folder.iterdir()):
            if setup_link_target(entry, targets) is not None:
                self.remove_link(entry, action, what)

    def remove_link(self, link: Path, action: str, what: str) -> None:
        """Removes one of setup's links, never anything it points to. action says what --what-if
        would do, and what starts the REMOVED line, which names the link."""
        if not self.should(link, action):
            return
        try:
            remove_folder_link(link)
            self.status("REMOVED", f"{what}: {link}")
        except OSError as error:
            self.status("PROBLEM", f"Could not remove the link {link}. {error}")

    def remove_rules_file(
        self, folder: Path, path: Path, set_up: set[str], checked: dict[str, bytes | None]
    ) -> None:
        """Removes the rules file setup wrote in a folder answered no, path, and its copy of it,
        while the file still matches that copy, or still holds what it held once the lines setup
        didn't write in it were saved in rules/, as checked has it (see save_lines). Any other
        file stays, as does setup's copy, and the next run tries again: one whose lines setup
        couldn't save, which save_lines has said, or one that changed since. One setup has no
        copy of isn't setup's, and stays, as does a link. In a folder that's really one setup sets
        up, through a junction, the file is that folder's, so only this folder's copy goes."""
        copy = LAST_WRITTEN / rules.copy_name(folder)
        if not copy.is_file():
            return
        try:
            shared = real_path(path.parent) in set_up
            current = None if shared or is_link(path) else path.read_bytes()
            kept = copy.read_bytes()
        except FileNotFoundError:
            current = None
            kept = b""
        except OSError as error:
            self.status("PROBLEM", f"{path} couldn't be read, so setup left it as it is. {error}")
            return
        if current is not None and current != kept and checked.get(str(path)) != current:
            return
        if current is not None:
            if not self.should(
                path, "Remove the rules file setup wrote in a folder you said no to"
            ):
                return
            try:
                remove_generated_file(path)
            except OSError as error:
                self.status("PROBLEM", f"Could not remove {path}. {error}")
                return
            self.status("REMOVED", f"Rules file in a folder you said no to: {path}")
        if self.should(copy, "Remove setup's copy of that rules file"):
            with contextlib.suppress(OSError):
                copy.unlink()

    def settings_checks(
        self, content_root: Path, agent_folders: AgentFolders
    ) -> list[SettingsCheck]:
        """What each agent's settings file needs, planned from the file as it is now: each Claude
        Code folder's and each Codex home's set up, and what a yes added taken back out of each one
        answered no, which that no approves as the yes approved adding it."""
        wanted_dirs = [comparable(content_root), comparable(TOOLKIT_ROOT)]
        checks: list[SettingsCheck] = [
            self.check_claude_settings(Path(claude_dir), wanted_dirs)
            for claude_dir in agent_folders.claude_dirs
        ]
        checks += [
            self.check_codex_config(Path(home), comparable(content_root))
            for home in agent_folders.codex_homes
        ]
        # A file that is really one a folder set up uses, through a link, keeps what that folder
        # needs.
        set_up = (
            {real_path(Path(d) / "settings.json") for d in agent_folders.claude_dirs}
            if agent_folders.declined_claude_dirs
            else set()
        )
        removals: list[SettingsCheck | None] = [
            self.claude_changes_to_remove(Path(claude_dir), wanted_dirs)
            for claude_dir in agent_folders.declined_claude_dirs
            if real_path(Path(claude_dir) / "settings.json") not in set_up
        ]
        removals += [
            self.codex_access_to_remove(Path(home), comparable(content_root))
            for home in agent_folders.declined_codex_homes
        ]
        checks += [removal for removal in removals if removal is not None]
        return checks

    def guarded(self, claude_dir: Path) -> bool:
        """Whether a Claude Code folder's settings.json gets home_claude_excludes: every folder
        but ~/.claude, unless its settings.json is really ~/.claude's, through a link, where the
        patterns would keep that account's own instructions out."""
        default = self.home / CLAUDE_CODE.default
        return real_path(claude_dir) != real_path(default) and real_path(
            claude_dir / "settings.json"
        ) != real_path(default / "settings.json")

    def check_claude_settings(self, claude_dir: Path, wanted_dirs: list[str]) -> SettingsCheck:
        """What a Claude Code folder set up needs in its settings.json: dev-home and
        dev-home-toolkit in permissions.additionalDirectories; in a folder other than ~/.claude,
        the patterns in claudeMdExcludes that keep ~/.claude's instructions out of its sessions
        (see home_claude_excludes); only the last copy of a recommended setting written more
        than once, the one Claude Code uses, which changes nothing it does; and each recommended
        setting a person said yes to in this run, while the folder still has what they saw
        (decision 0032), judged on the one read of the file the write plans on. One whose value
        changed since is left out, with a NEW line saying so, and its offer comes back."""
        claude_name = claude_dir.name
        path = claude_dir / "settings.json"
        wanted_excludes = home_claude_excludes(self.home) if self.guarded(claude_dir) else []
        file = claude_settings.read_file(path) if self.yeses_in(claude_dir) else None
        values, ids, already, left, reason = self.recommended_to_write(claude_dir, file)
        self.recommended_already += [(claude_dir, setting_id) for setting_id in already]
        one = len(left) == 1
        self.leave_out(
            claude_dir,
            left,
            f"setup won't change the file now: {reason}"
            if reason
            else f"{'it' if one else 'they'} changed after you answered",
        )
        present: list[str] = []
        excludes: list[str] = []
        twice: list[str] = []
        if path.exists():
            try:
                text = path.read_bytes().decode("utf-8-sig", errors="replace")
            except OSError as error:
                return (
                    "PROBLEM",
                    f"{path} could not be read, so its settings were not checked. {error}",
                )
            folders = claude_settings.folders_allowed(text)
            if folders is None:
                return (
                    "PROBLEM",
                    f"{path} could not be read as JSON, so its settings were not checked.",
                )
            present = [comparable(resolve_home(folder, self.home)) for folder in folders]
            excludes = claude_settings.listed(text, claude_settings.EXCLUDES) or []
            repeated = claude_settings.repeated_keys(text) or []
            # One this run sets has one copy afterwards anyway, which its value says.
            twice = [
                key for key in keys_for(CLAUDE_CODE.group) if key in repeated and key not in values
            ]
        missing = [d for d in wanted_dirs if not any(same_path(d, p) for p in present)]
        missing_excludes = [pattern for pattern in wanted_excludes if pattern not in excludes]
        subject = f"Claude Code settings in {claude_name}"
        if not missing and not missing_excludes and not twice and not values:
            kept_out = ", and claudeMdExcludes keeps .claude's out" if wanted_excludes else ""
            return (
                "OK",
                f"{subject}: additionalDirectories includes dev-home and "
                f"dev-home-toolkit{kept_out}",
            )
        try:
            plan = claude_settings.plan(path, missing, missing_excludes, values, file)
        except Exception as error:
            plan = Plan(SettingsFile(), reason=f"planning the change failed ({describe(error)})")
        needs: list[str] = []
        dones: list[str] = []
        merges: list[str] = []
        hows: list[str] = []
        if values:
            each = [(key, json_text(value)) for key, value in values.items()]
            needs.append(and_list([f"{key} set to {value}" for key, value in each]))
            set_to = and_list([f"{key} to {value}" for key, value in each])
            dones.append(f"set {set_to}")
            hows.append(f"Set {set_to}, at the top of the file.")
        if twice:
            needs.append(f"only the last copy of {and_list(twice)}, the one Claude Code uses")
            hows.append(
                f"Take out the earlier copies of {and_list(twice)}, keeping the last, which "
                "Claude Code uses."
            )
        if missing or missing_excludes:
            hows.append("Merge this into the file.")
        if missing:
            entries = ", ".join(claude_settings.dump(entry) for entry in missing)
            needs.append(f"{' and '.join(missing)} in permissions.additionalDirectories")
            added = and_list(
                [name for d, name in zip(wanted_dirs, ALLOWED_NAMES, strict=True) if d in missing]
            )
            dones.append(f"added {added} to permissions.additionalDirectories")
            merges.append(
                '            "permissions": {\n'
                f'              "additionalDirectories": [{entries}]\n'
                "            }"
            )
            hows.append(
                'If it already has "permissions", put additionalDirectories inside that block.'
            )
        if missing_excludes:
            patterns = ", ".join(claude_settings.dump(pattern) for pattern in missing_excludes)
            needs.append(
                f"{' and '.join(missing_excludes)} in claudeMdExcludes, to keep the CLAUDE.md and "
                "rules in .claude out of its sessions"
            )
            one = len(missing_excludes) == 1
            dones.append(
                f"added {'a pattern' if one else 'patterns'} to claudeMdExcludes that "
                f"{'keeps' if one else 'keep'} the CLAUDE.md and rules in .claude out of its "
                "sessions"
            )
            merges.append(f'            "claudeMdExcludes": [{patterns}]')
            hows.append('If it already has "claudeMdExcludes", add these to that list.')
        how_to = " ".join(hows)
        snippet = ""
        if merges:
            how_to = how_to[:-1] + ":"
            snippet = "          {\n" + ",\n".join(merges) + "\n          }"
        dones.extend(copies_kept([key for key in plan.repeated if key not in values]))
        return SettingsChange(
            subject,
            path,
            " and ".join(needs),
            plan,
            how_to,
            snippet,
            ", and ".join(dones),
            tuple(ids),
        )

    def check_codex_config(self, home: Path, content_root: str) -> SettingsCheck:
        """What a Codex home needs in its config.toml: dev-home in writable_roots, and
        project_doc_max_bytes big enough."""
        path = home / "config.toml"
        try:
            text = path.read_bytes().decode("utf-8-sig", errors="replace") if path.exists() else ""
        except OSError as error:
            return (
                "PROBLEM",
                f"{path} could not be read, so its settings were not checked. {error}",
            )
        subject = f"Codex config in {home.name}"
        doc_bytes = self.codex_doc_bytes
        has_root, has_doc_bytes = codex_config.configured_parts(text, content_root, doc_bytes)
        if has_root and has_doc_bytes:
            return ("OK", f"{subject}: writable_roots and project_doc_max_bytes")
        doc_done = (
            f"raised project_doc_max_bytes to {doc_bytes}"
            if re.search(r"(?m)^\s*project_doc_max_bytes\s*=", text)
            else f"added project_doc_max_bytes = {doc_bytes}"
        )
        done = (
            doc_done
            if has_root
            else "added dev-home to writable_roots"
            if has_doc_bytes
            else f"added dev-home to writable_roots, and {doc_done.removeprefix('added ')}"
        )
        try:
            plan = codex_config.plan(path, content_root, doc_bytes)
        except Exception as error:
            plan = Plan(SettingsFile(), reason=f"planning the change failed ({describe(error)})")
        needs = [] if has_root else ["dev-home in writable_roots"]
        how_to = "Merge this into the file."
        snippet = (
            f"          [sandbox_workspace_write]\n          writable_roots = ['{content_root}']"
        )
        # Only to raise what Codex reads: the setting never lowers it.
        if not has_doc_bytes:
            needs.append(
                f"project_doc_max_bytes of at least {doc_bytes} (Codex stops reading AGENTS.md "
                "files at 32 KiB by default)"
            )
            how_to += " project_doc_max_bytes goes above the first [section]."
            snippet = f"          project_doc_max_bytes = {doc_bytes}\n\n{snippet}"
        how_to += (
            " If the file already has [sandbox_workspace_write], add only the writable_roots line "
            "under it:"
        )
        need = ", and ".join(needs)
        return SettingsChange(subject, path, need, plan, how_to, snippet, done)

    def claude_changes_to_remove(
        self, claude_dir: Path, wanted_dirs: list[str]
    ) -> SettingsCheck | None:
        """What a Claude Code folder answered no needs in its settings.json: dev-home and
        dev-home-toolkit taken back out of permissions.additionalDirectories, written however they
        are, such as with ~, and setup's patterns out of claudeMdExcludes. A problem when the file
        isn't JSON but names any of them. None when none is there, or there's no file to read."""
        path = claude_dir / "settings.json"
        try:
            text = path.read_bytes().decode("utf-8-sig", errors="replace")
        except OSError:
            return None
        patterns = home_claude_excludes(self.home) if self.guarded(claude_dir) else []
        folders = claude_settings.folders_allowed(text)
        if folders is None:
            named = list(ALLOWED_NAMES) if mentions_folder(text, wanted_dirs) else []
            if any(pattern in text for pattern in patterns):
                named.append("the patterns setup adds to claudeMdExcludes")
            if not named:
                return None
            return (
                "PROBLEM",
                f"{path} could not be read as JSON, so setup could not take {and_list(named)} out "
                "of it, since you said no to this folder.",
            )
        found = [
            folder
            for folder in folders
            if any(same_path(resolve_home(folder, self.home), d) for d in wanted_dirs)
        ]
        listed = claude_settings.listed(text, claude_settings.EXCLUDES) or []
        found_patterns = [pattern for pattern in patterns if pattern in listed]
        if not found and not found_patterns:
            return None
        names = and_list(
            [
                name
                for d, name in zip(wanted_dirs, ALLOWED_NAMES, strict=True)
                if any(same_path(resolve_home(folder, self.home), d) for folder in found)
            ]
        )
        try:
            plan = claude_settings.plan_removal(path, found, found_patterns)
        except Exception as error:
            plan = Plan(SettingsFile(), reason=f"planning the change failed ({describe(error)})")
        needs: list[str] = []
        dones: list[str] = []
        lines: list[str] = []
        if found:
            needs.append(f"{names} taken out of permissions.additionalDirectories")
            dones.append(f"removed {names} from permissions.additionalDirectories")
            lines.append(
                "          From permissions.additionalDirectories: "
                + ", ".join(claude_settings.dump(folder) for folder in found)
            )
        if found_patterns:
            which = "setup's pattern" if len(found_patterns) == 1 else "setup's patterns"
            needs.append(f"{which} taken out of claudeMdExcludes")
            dones.append(f"removed {which} from claudeMdExcludes")
            lines.append(
                "          From claudeMdExcludes: "
                + ", ".join(claude_settings.dump(pattern) for pattern in found_patterns)
            )
        dones.extend(copies_kept(plan.repeated))
        return SettingsChange(
            f"Claude Code settings in {claude_dir.name}",
            path,
            " and ".join(needs) + ", since you said no to this folder",
            plan,
            "Take these out:",
            "\n".join(lines),
            ", and ".join(dones),
        )

    def codex_access_to_remove(self, home: Path, content_root: str) -> SettingsChange | None:
        """What a Codex home needs in its config.toml after a no to Codex: dev-home taken back
        out of writable_roots. project_doc_max_bytes stays, since it gives Codex no access. dev-home
        in a form setup can't edit gets the plan's reason, as a problem. None when dev-home isn't
        there, or there's no file to read."""
        path = home / "config.toml"
        try:
            text = path.read_bytes().decode("utf-8-sig", errors="replace")
        except OSError:
            return None
        if not codex_config.mentions_root(text, content_root):
            return None
        try:
            plan = codex_config.plan_removal(path, content_root)
        except Exception as error:
            plan = Plan(SettingsFile(), reason=f"planning the change failed ({describe(error)})")
        return SettingsChange(
            f"Codex config in {home.name}",
            path,
            "dev-home taken out of writable_roots, since you said no to Codex",
            plan,
            "Take this out of writable_roots, under [sandbox_workspace_write]:",
            f"          '{content_root}'",
            "removed dev-home from writable_roots",
        )


# How the list of a folder's recommended settings marks each, where only some are recommended
# there: one where a yes is recommended, and one with any other value, which Enter keeps. It
# doesn't call that value the person's own, which setup can't know.
RECOMMENDED_MARKS = ("recommended", "Enter keeps its value")


def recommended_new_text(waiting: Sequence[tuple[str, int]]) -> str:
    """The NEW line naming each Claude Code folder, by its entry, with how many recommended
    settings wait for an answer there, and how to answer."""
    counts = [f"{count} in {entry}" for entry, count in waiting]
    first = waiting[0][1]
    counts[0] = f"{first} setting{'' if first == 1 else 's'} dev-home-toolkit recommends for " + (
        f"Claude Code in {waiting[0][0]}"
    )
    total = sum(count for _, count in waiting)
    them = "it as it is" if total == 1 else "them as they are"
    # A comma before the last even with two, since the first part is long.
    listed = counts[0] if len(counts) == 1 else ", ".join(counts[:-1]) + ", and " + counts[-1]
    return (
        f"Setup has no answer yet about {listed}, so it leaves {them}. Answer with "
        "/dev-home configure: all recommended, none, each, or remind me in N days. Or run "
        f"{by_hand('setup.py')} in a terminal, and it asks."
    )


def yes_key(folder: str | Path) -> str:
    """A Claude Code folder as Setup.recommended_yes keys it: its full path, in one case where
    the file system ignores case, so it's the same however a person typed it."""
    return os.path.normcase(comparable(folder))


def yes_names(yeses: Sequence[tuple[str, str]]) -> str:
    """The recommended settings a person said yes to, by each folder's entry and the setting's
    id, as a line saying they're saved names them: by id alone, for one folder, and otherwise
    each with its folder."""
    entries = list(dict.fromkeys(entry for entry, _ in yeses))
    if len(entries) == 1:
        return and_list([setting_id for _, setting_id in yeses])
    return and_list(
        [
            f"{and_list([setting_id for each, setting_id in yeses if each == entry])} in {entry}"
            for entry in entries
        ]
    )


def answered_for_now(answer: bool | Reminder | None, today: date) -> bool:
    """Whether an answer to an offer leaves nothing to ask now: a yes, a no, or a reminder before
    its date."""
    return isinstance(answer, bool) or (isinstance(answer, Reminder) and not answer.due(today))


def read_json_object(path: Path) -> dict[str, Any] | None:
    """A file's JSON object, or None when it's missing, can't be read, or isn't one."""
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def copies_kept(repeated: Sequence[str]) -> list[str]:
    """What a SET line says rewriting Claude Code's settings.json did to the keys it had more than
    once, which keep only their last copy (see claude_settings.read_object): nothing when there
    were none."""
    if not repeated:
        return []
    each = "" if len(repeated) == 1 else "each of "
    names = and_list(list(repeated))
    return [f"kept only the last copy, the one Claude Code uses, of {each}{names}"]


def home_claude_excludes(home: Path) -> list[str]:
    """The claudeMdExcludes patterns that keep ~/.claude's CLAUDE.md and rules out of the sessions
    of another Claude Code folder's account. Claude Code reads CLAUDE.md, .claude/CLAUDE.md, and
    .claude/rules/ in every folder above where a session starts, so a session started anywhere in
    the profile folder takes ~/.claude's for a project's own instructions (anthropics/claude-code
    issues 80580 and 79233). Each pattern names the profile folder by its name alone, because a
    whole path has to match the drive letter's case, which differs from session to session."""
    name = "".join("?" if char in GLOB_SPECIAL else char for char in home.name)
    return [f"**/{name}/.claude/CLAUDE.md", f"**/{name}/.claude/rules/**"]


def folder_question(agent: Agent, folder: Path) -> str:
    return f"Set up {agent.name} in {folder}?"


def codex_doc_bytes(data: dict[str, Any]) -> int:
    """The least each Codex home's project_doc_max_bytes is set to, in bytes, from this PC's
    settings, given as the file's data. Codex joins its global AGENTS.md with the project's
    AGENTS.md files and stops reading at project_doc_max_bytes, 32 KiB by default. The global
    file comes first, so the cut would fall on the project's own instructions, without a
    warning. A size past what config.toml can hold, which can only mean all of it, is that
    most."""
    kib = int(setting_value(data, CODEX_INSTRUCTIONS_MAX)[0])
    return min(kib * 1024, codex_config.TOML_MAX_INTEGER)


def yes_does(agent: Agent, *, several: bool, doc_bytes: int, guarded: bool = False) -> str:
    """What a yes to setting up an agent's folders does, and a no, said before the question: the
    change setup also makes in each folder's settings file, which the yes approves (see
    repair_setting), and its removal, which the no approves, included. guarded says some of the
    folders get home_claude_excludes, and why. doc_bytes is the least a Codex home's
    project_doc_max_bytes is set to (see codex_doc_bytes)."""
    yes, no = console.key("yes"), console.key("no")
    # Adding an agent: see AGENTS_SKILLS. An agent that reads ~/.agents/skills, as Codex
    # does, shares that folder's links with Codex, and its question says so.
    if agent.shared:
        raises = (
            f", and raises project_doc_max_bytes to {doc_bytes} where it's lower, so "
            f"{agent.name} reads all of your rules"
            if not codex_config.reads_enough(None, doc_bytes)
            else ""
        )
        return (
            f"Every {agent.name} {agent.folder} reads the same skills, so they share one answer. A "
            f"{yes} sets up dev-home's skills and rules in each {agent.folder}. In each "
            f"{agent.folder}'s config.toml, it also adds your dev-home folder to writable_roots, "
            f"so {agent.name} can write there from any project{raises}. A {no} removes all of "
            "that but project_doc_max_bytes, if it's there. Setup backs up each file first."
        )
    where, settings_file, backup, adds, whose = (
        (
            "in each",
            f"each {agent.folder}'s settings.json",
            "each file",
            f"In each {agent.folder} other than .claude, it also adds two patterns to "
            "claudeMdExcludes.",
            "that",
        )
        if several
        else (
            "there",
            "its settings.json",
            "the file",
            "It also adds two patterns to claudeMdExcludes there.",
            "this",
        )
    )
    guard = (
        f" {adds} {agent.name} loads the CLAUDE.md and rules in .claude, the default account's "
        "folder, into a session started anywhere under your user folder, as if they were the "
        f"project's own instructions, and the patterns keep them out of {whose} {agent.folder}'s "
        "sessions."
        if guarded
        else ""
    )
    return (
        f"A {yes} sets up dev-home's skills and rules {where}. It also adds your dev-home and "
        f"dev-home-toolkit folders to permissions.additionalDirectories in {settings_file}, so "
        f"{agent.name} can use them from any project.{guard} A {no} removes all of that, if it's "
        f"there. Setup backs up {backup} first."
    )


CODEX_QUESTION = "Set up Codex in every Codex home?"


def folder_list(folders: Sequence[Path]) -> str:
    return ", ".join(str(folder) for folder in folders)


def and_list(items: Sequence[str]) -> str:
    """Items in a sentence: a, a and b, or a, b, and c."""
    if len(items) < 3:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def large_rules_text(large: Sequence[tuple[str, int]], warn_kib: int) -> str:
    """The LARGE line: each agent, by its name, whose rules on this PC, the end user's part of its
    rules file, pass warn_kib, with their size in bytes."""
    names = and_list([name for name, _ in large])
    sizes = and_list([f"{size / 1024:.1f} KiB" for _, size in large])
    return (
        f"Your rules for {names} on this PC are {sizes}, past {warn_kib} KiB. Every session loads "
        "them, so they cost tokens in every session: shorten them, or raise "
        f'"{BY_PATH[RULES_WARN_ABOVE].label}" with /dev-home configure.'
    )


def level_choices(agent: str, pc: str) -> list[tuple[str, str]]:
    """The four levels of rules/ whose mine/ joins for agent on the PC whose folder is pc, from
    the widest, each relative to rules/, with what it applies to (decision 0065)."""
    shown = requirements.AGENT_NAMES[agent]
    this_pc = f"{rules.PCS}/{pc}"
    return [
        (rules.ALL_AGENTS, "every agent, on every PC"),
        (agent, f"{shown}, on every PC"),
        (f"{this_pc}/{rules.ALL_AGENTS}", "every agent, on this PC"),
        (f"{this_pc}/{agent}", f"{shown}, on this PC"),
    ]


def unanswered_files(rules_root: Path, pc: str) -> list[Path]:
    """Each file in this PC's unanswered/ folders, for each agent setup knows, which joins for it
    after mine/ until a person says where it goes (decision 0064)."""
    return [
        path
        for agent in requirements.AGENT_NAMES
        for path in rules.markdown_files(rules_root / rules.PCS / pc / agent / rules.UNANSWERED)
    ]


def names_in(folder: Path) -> list[str]:
    """The names of what's in folder, or none when it isn't there."""
    try:
        return [entry.name for entry in os.scandir(folder)]
    except OSError:
        return []


def relative(content_root: Path, path: Path) -> str:
    """path as dev-home's own files name it, relative to its folder, with forward slashes."""
    return path.relative_to(content_root).as_posix()


def bin_name(name: str) -> str:
    """What the copy of one of dev-home's AGENTS.md and CLAUDE.md with a hand edit is called in
    the Recycle Bin, so an end user can tell what it holds."""
    return f"{Path(name).stem} from dev-home, as edited.md"


def left_text(found: Guidance, rules_root: Path, why_not: str) -> str:
    """The PROBLEM line for one of dev-home's AGENTS.md and CLAUDE.md left as edited, since the
    Recycle Bin couldn't take a copy of its hand edit: on each run, until a run whose bin takes it,
    or a person's answer, through /dev-home configure or at a console."""
    return (
        f"dev-home's {found.name}: {found.path} has edits setup didn't make, and the Recycle Bin "
        f"couldn't take a copy of them, so setup left the file as edited. {sentence(why_not)} "
        "Setup rewrites this file on every run, and puts it back once the bin takes the edits: "
        f"move anything you want to keep into your rules, in {rules_root}, first. To delete the "
        "edits for good instead, answer with /dev-home configure, or run "
        f"{by_hand('setup.py')} in a terminal."
    )


def sentence(text: str) -> str:
    """text as a sentence, ending with a full stop, for a reason such as the Recycle Bin's, which
    may end with an error's own text."""
    return text if text.endswith((".", "!", "?")) else f"{text}."


def unanswered_text(agent: Agent, folders: Sequence[Path], *, session: bool = False) -> str:
    """Which of an agent's folders setup has no answer for yet, and that it leaves them as they
    are, as in "Setup has no answer yet <this>". session marks the one folder as the session's
    own."""
    if agent.shared:
        own = f", the session's own, in {agent.variable}," if session else ""
        which = (
            f"the {agent.name} {agent.folder} {folders[0]}{own} as it is"
            if len(folders) == 1
            else f"the {agent.name} {agent.folder}s {folder_list(folders)} as they are"
        )
        return f"about setting up {agent.name}, so it leaves {which}"
    kind = f"{agent.name} {agent.folder}"
    if session:
        return (
            f"about setting up the {kind} {folders[0]}, the session's own, in {agent.variable}, "
            "so it leaves it as it is"
        )
    if len(folders) == 1:
        return f"about setting up the {kind} {folders[0]}, so it leaves it as it is"
    return f"about setting up these {kind}s: {folder_list(folders)}, so it leaves them as they are"


def answer_in_chat(*, for_each: bool = False) -> str:
    """How a NEW line about folders with no answer says to answer in chat, with the answers it
    offers, for each folder when it names several. "Remind me next session" isn't one: the line
    comes back every session anyway."""
    each = ", for each" if for_each else ""
    return f"Answer with /dev-home configure{each}: set it up, no, or remind me in N days"


def keep_text(reminder: Reminder | None) -> str:
    """How a question about an item names the reminder it has, which Enter keeps, such as "the
    reminder for 2026-10-27", or "" for none."""
    if reminder is None:
        return ""
    return f"the reminder for {reminder.on.isoformat()}" if reminder.on else "the reminder"


def setup_link_target(entry: Path, targets: Sequence[Path]) -> str | None:
    """Where a link points, when it points where setup's links do: to one of targets, or into
    one. None for anything else, such as a link of the person's own, a file, or a folder."""
    found = link_info(entry)
    if found is None or not found.is_link or found.target is None:
        return None
    if not any(is_inside(found.target, target) for target in targets):
        return None
    return found.target


def mentions_folder(text: str, folders: Sequence[str]) -> bool:
    """Whether a file's text names one of folders, with either kind of slash, single or doubled,
    in any case: a rough check for a file that can't be read as a whole."""
    plain = text.replace("\\\\", "/").replace("\\", "/").casefold()
    return any(forward(folder).casefold() in plain for folder in folders)


def skill_templates() -> list[Path]:
    """The folder of each of dev-home-toolkit's skills, in templates/skills/."""
    return sorted(
        folder
        for folder in (TOOLKIT_ROOT / "templates" / "skills").iterdir()
        if folder.is_dir() and (folder / "SKILL.md").is_file()
    )


def skill_links(
    content_root: Path, skill_sources: Sequence[Path]
) -> tuple[list[tuple[str, Path]], list[str]]:
    """Each skill setup links into the agents, by its name and the folder its link points to:
    dev-home-toolkit's skills, generated with this PC's paths from skill_sources, the same list the
    generated files come from, then the person's own in dev-home. Also the name of each of the
    person's own that has the same name as one of dev-home-toolkit's, which isn't linked."""
    links = [(skill.name, GENERATED_ROOT / "skills" / skill.name) for skill in skill_sources]
    same_names: list[str] = []
    personal_skills = content_root / "skills"
    if personal_skills.exists():
        for folder in sorted(personal_skills.iterdir()):
            if not (folder.is_dir() and (folder / "SKILL.md").is_file()):
                continue
            if any(os.path.normcase(name) == os.path.normcase(folder.name) for name, _ in links):
                same_names.append(folder.name)
                continue
            links.append((folder.name, folder))
    return links, same_names


def plan_skill(
    skill: Skill,
    data: dict[str, Any],
    pc: requirements.ThisPC,
    folders: Sequence[tuple[Path, frozenset[str]]],
) -> SkillPlan:
    """What setup does with one skill on this PC (see SkillPlan): with a yes, its default, or for
    a skill that's always added, it goes into each skills folder whose agents meet its
    supportedOn, the operating system and the agent; with a no, or a name Claude Code keeps
    (kept_off), into none. Its dependsOn, a program or a Python version, never keeps it off: setup
    only warns about it."""
    setting = skill.added_setting
    said_no = False
    wanted = True
    if setting is not None:
        saved = get(data, saved_skill_path(data, skill.name, ADDED_TO_AGENTS), MISSING)
        wanted = bool(read_value(saved, setting)[0])
        said_no = saved is False
    needs = requirements.warned_about(skill.requires)
    warnings = tuple(dict.fromkeys(u.reason for u in requirements.unmet(needs, pc, frozenset())))

    def plan(
        added: Sequence[Path], left_out: Sequence[tuple[Path, str]], state: str, told: bool
    ) -> SkillPlan:
        # What's missing is said only for a skill that's added somewhere, which an agent can use.
        missing = (warnings, needs) if added else ((), ())
        return SkillPlan(skill.name, tuple(added), tuple(left_out), state, told, *missing)

    def keeping_off(agents: frozenset[str]) -> list[requirements.Unmet]:
        return [u for u in requirements.unmet(skill.requires, pc, agents) if u.keeps_off]

    # A name Claude Code keeps, whatever the answer. Its PROBLEM line names it, so the NEW line
    # doesn't (see name_problem in settings.py).
    if skill.kept_off:
        out_of_each = [(f, skill.kept_off) for f, _ in folders]
        return plan((), out_of_each, f"not added: {skill.kept_off}", told=False)

    # What keeps it off this whole PC, with no agents to check: the operating system, or an entry
    # about it or the agent with a mistake. A reason nobody can act on stays unsaid.
    everywhere = keeping_off(frozenset())
    on_this_pc = and_list(list(dict.fromkeys(u.reason for u in everywhere)))
    if not wanted:
        if everywhere and not any(u.can_act for u in everywhere):
            # It couldn't be added here even with a yes, so that's what its state says.
            out_of_each = [(f, on_this_pc) for f, _ in folders]
            return plan((), out_of_each, f"not added: {on_this_pc}", told=False)
        why = "you said no to" if said_no else "isn't added by default"
        state = "not added: you said no" if said_no else "not added by default"
        return plan((), [(f, why) for f, _ in folders], state, told=True)
    if not folders:
        if not everywhere:
            return plan((), (), "not added: no Claude Code folder or Codex home is set up", True)
        return plan((), (), f"not added: {on_this_pc}", any(u.can_act for u in everywhere))
    added: list[Path] = []
    left_out: list[tuple[Path, str]] = []
    reasons: list[str] = []
    can_act = False
    # The agents of the folders it goes into, and of those it's left out of.
    agents_added: list[str] = []
    agents_left: list[str] = []
    for folder, agents in folders:
        unmet = keeping_off(agents)
        names = agents_left if unmet else agents_added
        for name in (requirements.AGENT_NAMES[agent] for agent in sorted(agents)):
            if name not in names:
                names.append(name)
        if not unmet:
            added.append(folder)
            continue
        left_out.append((folder, and_list([u.reason for u in unmet])))
        reasons += [u.reason for u in unmet if u.reason not in reasons]
        can_act = can_act or any(u.can_act for u in unmet)
    whole = "always added to your agents" if setting is None else "added to your agents"
    if not left_out:
        state = whole
    elif not added:
        state = f"not added: {and_list(reasons)}"
    else:
        state = (
            f"{whole} in {and_list(agents_added)}, not in {and_list(agents_left)}: "
            f"{and_list(reasons)}"
        )
    return plan(added, left_out, state, not left_out or can_act)


def skills_by_agent(
    plans: Mapping[str, SkillPlan], folders: Sequence[tuple[Path, frozenset[str]]]
) -> dict[str, set[str]]:
    """The skills added for each agent on this PC, by the agent's name in rules/, such as codex:
    each skill whose plan adds it to a skills folder in folders that the agent reads. So all of one
    agent's rules files get the same skills' blocks (decision 0058, "Skills' always-on lines")."""
    readers = dict(folders)
    added: dict[str, set[str]] = {}
    for plan in plans.values():
        for folder in plan.added_to:
            for agent in readers.get(folder, frozenset()):
                added.setdefault(agent, set()).add(plan.name)
    return added


def operating_by_agent(
    operating: str,
    targets: Sequence[RulesTarget],
    plans: Mapping[str, SkillPlan],
    folders: Sequence[tuple[Path, frozenset[str]]],
) -> dict[str, str]:
    """The operating rules for each agent with a rules file in targets, by its name in rules/:
    operating, their template with this PC's paths filled in, with the blocks of the skills added
    for that agent (see skills_by_agent and rules.operating_for)."""
    added = skills_by_agent(plans, folders)
    return {
        agent: rules.operating_for(operating, added.get(agent, set()))
        for agent in dict.fromkeys(target.agent for target in targets)
    }


def recorded_state(plan: SkillPlan) -> dict[str, Any]:
    """One skill's entry in skill-states.json: its state, and what it needs that setup only
    warns about, for /dev-home skills to check again where the agent runs: each program, by its
    name, with what the skill uses it for, if its entry says; and the lowest Python it runs on,
    the highest any entry asks for."""
    entry: dict[str, Any] = {"state": plan.state}
    programs: dict[str, dict[str, str]] = {}
    for need in plan.needs:
        if need.kind == "program" and need.names[0] not in programs:
            programs[need.names[0]] = {"name": need.names[0]}
            if need.used_for:
                programs[need.names[0]]["usedFor"] = need.used_for
    if programs:
        entry["programs"] = list(programs.values())
    versions = [need.version for need in plan.needs if need.kind == "python"]
    if versions:
        entry["python"] = requirements.version_text(max(versions))
    return entry


def new_skills_text(new: Sequence[str], plans: dict[str, SkillPlan]) -> str:
    """The NEW line naming the skills new to this PC, each with its state and what it needs that
    this PC seems to lack, or "" with none to name. One left out only for a reason nobody can act
    on, such as the operating system, isn't named (see SkillPlan)."""
    named = [plans[name.lower()] for name in new if name.lower() in plans]
    items = [
        f"'{plan.name}' ({'; '.join([plan.state, *plan.warnings])})" for plan in named if plan.told
    ]
    if not items:
        return ""
    one = len(items) == 1
    return (
        f"New skill{'' if one else 's'} on this PC, following "
        f"{'its default' if one else 'their defaults'} until you choose: {', '.join(items)}. To "
        "choose, use /dev-home configure."
    )


def template_values(content_root: Path) -> dict[str, str]:
    """What setup fills in for each placeholder in the templates: this PC's paths."""
    return {
        "TOOLKIT_DIR": forward(TOOLKIT_ROOT),
        "CONTENT_DIR": forward(content_root),
        "SHARED_SKILL_SCRIPTS_DIR": forward(GENERATED_ROOT / "shared-skill-scripts"),
        "PYTHON": forward(PYTHON_LINK / "python.exe"),
    }


def is_in_use(folder: Path) -> bool:
    """Whether a folder exists with anything in it, so setup won't clone or create a dev-home
    there. One that can't be read counts as in use."""
    try:
        return folder.is_dir() and any(folder.iterdir())
    except OSError:
        return True


def is_dev_home(folder: Path) -> bool:
    """Whether a folder is a dev-home: whether it has dev-home.json, which only dev-home-toolkit
    writes, and every dev-home has from its start. The end user's own files, such as the
    knowledge index, don't count, since setup recreates them when they're missing."""
    return (folder / DEV_HOME_SETTINGS).is_file()


def make_writable(path: Path) -> None:
    """Clears the read-only mark from one of setup's own generated files, so it can be rewritten
    or removed."""
    if not os.access(path, os.W_OK):
        path.chmod(stat.S_IREAD | stat.S_IWRITE)


def remove_generated_file(path: Path) -> None:
    make_writable(path)
    path.unlink()


def linked_folder(destination: Path) -> Path | None:
    """The first folder that is a link, from destination up to the generated folder, or None."""
    root = os.path.normcase(comparable(GENERATED_ROOT))
    for folder in (destination, *destination.parents):
        full = os.path.normcase(comparable(folder))
        if full != root and not full.startswith(root + os.sep):
            return None
        if is_link(folder):
            return folder
    return None


def run_tool(program: str, *args: str) -> tuple[int, list[str]]:
    """Runs a program such as gh without printing its output. Returns the exit code and the
    output and error lines together."""
    done = subprocess.run(
        [program, *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return done.returncode, done.stdout.splitlines()


def parse_arguments(argv: Sequence[str]) -> tuple[bool, bool, str, str | None] | str:
    """--quiet, --what-if, --content-dir's folder, and --configure's assignment ("" for none,
    None without --configure), or why the arguments can't be used."""
    quiet = False
    what_if = False
    content_dir = ""
    configure_with: str | None = None
    rest = list(argv)
    while rest:
        word = rest.pop(0)
        if word == "--quiet":
            quiet = True
        elif word == "--what-if":
            what_if = True
        elif word == "--content-dir":
            if not rest:
                return "--content-dir needs a folder after it."
            content_dir = rest.pop(0)
        elif word == "--configure":
            configure_with = rest.pop(0) if rest and not rest[0].startswith("--") else ""
        else:
            return (
                f"No such option: {word}. The options are --quiet, --content-dir, --configure, "
                "and --what-if."
            )
    if configure_with is not None and (quiet or content_dir):
        return (
            "--configure doesn't go with --quiet or --content-dir: it shows the settings, or "
            "changes the one it's given, such as --configure "
            "'devHome.folder=C:/Users/you/dev-home'."
        )
    return quiet, what_if, content_dir, configure_with


def main(argv: Sequence[str], *, sync_holds_lock: bool = False) -> int:
    """Runs setup. A sync that runs it says it holds its lock: inside its own process with
    sync_holds_lock, and in a process of setup's own with SYNC_HOLDS_LOCK in its environment."""
    if any(word in ("--help", "-h") for word in argv):
        print(__doc__)
        return 0
    parsed = parse_arguments(argv)
    if isinstance(parsed, str):
        status_line("PROBLEM", parsed)
        return 1
    quiet, what_if, content_dir, configure_with = parsed
    holds_lock = sync_holds_lock or os.environ.get(SYNC_HOLDS_LOCK) == "1"
    # The sync runs this inside its own process, so nothing here may raise.
    try:
        run = Setup(
            quiet=quiet, what_if=what_if, configure=configure_with, sync_holds_lock=holds_lock
        )
    except Exception as error:
        with contextlib.suppress(Exception):
            status_line("PROBLEM", f"setup.py stopped: {describe(error)}")
        return 1
    try:
        run.run(content_dir)
    except CannotGoOnError:
        pass
    except Exception as error:
        # Even this line may fail, such as when the output is closed.
        with contextlib.suppress(Exception):
            run.status("PROBLEM", f"setup.py stopped: {describe(error)}")
    try:
        return run.finish()
    except Exception:
        return 1
