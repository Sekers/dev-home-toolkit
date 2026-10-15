"""Sets up dev-home-tools on this PC: finds or creates your dev-home, fills in the skills and
operating rules with this PC's paths, links them into Claude Code and Codex, and checks the
settings they need.

Safe to run any number of times. It rewrites only its own generated files, creates missing links,
replaces links whose target is gone, removes links it made to skills that no longer exist, and
reports anything else without changing it.

A run goes in this order, so the questions come first and the work after:

1. dev-home first. On the first run it asks where your dev-home is (the private repo that holds
   your handoffs and knowledge base). If that folder doesn't exist yet, it offers to clone your
   dev-home from GitHub, or to create a new private one from the files in
   templates/dev-home-starter/. A folder that exists must look like a dev-home: it has the files
   the starter makes, global-rules/global-rules.md and knowledge/README.md. Setup sets that
   repo's own git config, so it never works on a folder without them, such as a project's repo
   named by mistake. When dev-home can't be put in place, setup stops, and saves nothing.
2. The questions not answered yet: whether to pull updates automatically, whether to set up each
   Claude Code folder it finds, whether to set up Codex, in every Codex home, and how many copies
   of dev-home are in active use. Each is asked whenever its answer isn't saved yet, not only on
   the first run. A no is saved too, so it's asked about once.
3. At a console, the settings menu that --configure shows, so any setting can be changed.
4. The changes to confirm: to dev-home.json, and to Claude Code's and Codex's settings files.
5. The work, which asks nothing, and holds the sync's lock, so a sync in another session waits
   for it, while no sync ever waits for a person's answer: it saves this PC's answers in
   local-settings.json in dev-home-tools' folder, commits dev-home.json, and sets up everything
   else.
6. Last, the changes to the tools' settings files. No sync writes them, so the lock doesn't
   cover them, and a file that changed after setup showed its change is shown and asked about
   again.

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

The templates in this repo hold placeholders where paths go. Setup writes copies of the skills,
the scripts they share, and the operating rules, with this PC's paths filled in, to
internal/.generated/, at the same paths they have under templates/, and links the skills and
rules into the tools. Pre-approved commands must match the command text exactly, so the paths
can't be variables.

When a settings file is missing something, it shows the exact lines it would change and asks
first. On yes, it saves a dated backup of the file, then writes the change. It never edits a file
it can't fully parse (a settings.json with comments, for example), or a read-only one; it prints
what to add by hand instead.

Run it by hand once per PC. After that, each sync runs it with --quiet, so changes to the
skills, and skills added on another PC, reach this one.

Claude Code gets the links and rules in each folder answered yes under claudeCode.folders in
local-settings.json. Setup offers each Claude Code folder it finds, in a list, each recommended:
~/.claude, once Claude Code has made it; each extra one, one per account, such as
~/.claude-<name>; and the folder in CLAUDE_CONFIG_DIR. It saves a no there too. A folder nobody
has answered for isn't set up: setup adds no links there and removes none, and a quiet run names
it. A folder answered no is left alone, and one answered yes that no longer exists is skipped.

Codex has one answer for every Codex home, codex.setUp, since every home reads the same skills,
from ~/.agents/skills: setup sets up all of them, or none. A yes gets each home its rules and
settings, and the skills linked into ~/.agents/skills. The homes are ~/.codex, once Codex has
made it; each ~/.codex-<name> that holds a config.toml or an auth.json; the folder in CODEX_HOME;
and each listed by its path in codex.homes, for a home setup can't find by itself. Until
Codex is answered, setup adds no links and removes none, and a quiet run names its homes.

Each link to a folder is a junction on Windows, which needs no Developer Mode, and a symbolic link
elsewhere.

The skills run their scripts with Python 3.12 or later, as internal/.python/python.exe in
dev-home-tools' folder: a junction setup makes to the folder of a Python it finds, so the
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
                            console, it shows the settings and how to change them.
    --configure '<name>=<value>'
                            Changes one setting, the way an agent does, with no questions, then
                            prints only changes and problems. --configure with no setting says
                            which names and values it takes.
    --what-if               Shows what it would change, without changing anything.

It asks a question only when a person can see it and answer: never with --quiet, and only when
its input comes from a real console and its output goes to one. Input that ends without an
answer counts as no.

Examples, in dev-home-tools' folder, with Python 3.12 or later:

    py setup.py --what-if
    py setup.py

The sync runs main(["--quiet"]) inside its own process, so keep main's name and arguments.
"""

import contextlib
import copy
import importlib
import os
import re
import stat
import subprocess
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import claude_settings, codex_config, configure, console, generated, python_link
from .git import run_git
from .links import is_link, link_info, make_folder_link, remove_folder_link
from .output import GREEN, RED, YELLOW, color, describe, first_line, status_line
from .paths import comparable, forward, is_inside, resolve_home, same_path, unsafe_reason
from .programs import SYNC_HOLDS_LOCK, by_hand, find_program
from .settings import (
    ANSWER_SETTINGS,
    AUTO_UPDATE,
    BY_PATH,
    CLAUDE_CODE,
    CODEX,
    CODEX_HOMES,
    CODEX_SETUP,
    DEV_HOME_SETTINGS,
    MISSING,
    SCHEMA_VERSION,
    SETTINGS_PATH,
    TOOLS_ROOT,
    Checked,
    LocalSettings,
    Setting,
    Tool,
    answered,
    apply_changes,
    check_settings,
    dev_home_text,
    folder_answers,
    get,
    layout,
    listed_entries,
    load_local_settings,
    local_settings_data,
    local_settings_text,
    put,
    read_dev_home_settings,
    saved_answer,
    setting_value,
    settings_text,
    skill_preferences,
)
from .settings_files import (
    Plan,
    SettingsFile,
    line_diff,
    read_settings_file,
    to_lines,
    write_settings_file,
)

# Codex joins its global AGENTS.md with the project's AGENTS.md files and stops reading at
# project_doc_max_bytes, 32 KiB by default. The global file comes first, so the cut would fall on
# the project's own instructions, without a warning. Twice the default leaves room for long
# project files.
CODEX_DOC_BYTES = 65536
GENERATED_ROOT = TOOLS_ROOT / "internal" / ".generated"
PYTHON_LINK = TOOLS_ROOT / "internal" / ".python"
GENERATED_FOLDERS = ("skills", "shared-skill-scripts", "operating-rules")
FOLDER_NOTE = (
    "Setup writes everything in this folder from templates/skills/, "
    "templates/shared-skill-scripts/,\nand templates/operating-rules/, with this PC's paths "
    "filled in. Don't edit it: the next setup\nrun rewrites it. Python writes the __pycache__ "
    "folders when the scripts run, to start them\nfaster, and setup leaves those alone.\n"
)
QUIET_ADVICE = "Run setup.py without --quiet, and it offers to make the change."
# Files every dev-home starts with, from templates/dev-home-starter/.
DEV_HOME_FILES = ("global-rules/global-rules.md", "knowledge/README.md")


class CannotGoOnError(Exception):
    """Ends the run early, after a problem that the rest of setup can't get past."""


@dataclass(frozen=True)
class SettingsChange:
    """A change one of the tools' settings files needs: what it's for, the file, what the file
    needs, the plan, and what to add by hand where setup can't make it."""

    subject: str
    path: Path
    need: str
    plan: Plan
    how_to: str
    snippet: str


# What a check of one settings file found: a line to report as it is, or a change it needs.
SettingsCheck = tuple[str, str] | SettingsChange


@dataclass(frozen=True)
class ToolFolders:
    """Where setup sets up each tool, by full path: each Claude Code folder answered yes, and each
    Codex home, once Codex is answered yes."""

    claude_dirs: list[str]
    codex_homes: list[str]


def approval_key(path: Path) -> str:
    """A settings file's path, as the answers given before the work are kept by."""
    return os.path.normcase(comparable(path))


def cleanup(checked: Checked) -> list[str]:
    """What check_settings removed and moved, a sentence for each, for the line that says so."""
    sentences = []
    if checked.removed:
        them = "it" if len(checked.removed) == 1 else "them"
        sentences.append(f"Removed {', '.join(checked.removed)}: nothing declares {them} any more")
    if checked.moved:
        names = "its new name" if len(checked.moved) == 1 else "their new names"
        sentences.append(f"Moved {', '.join(checked.moved)}, {names}")
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
        # Each settings change shown before the work, by the file's path (see approval_key): the
        # file's text as shown, and the answer.
        self.approved: dict[str, tuple[str, bool]] = {}
        # Set once the menu changes a setting, so the save keeps a backup.
        self.changed_by_hand = False
        # Set when --configure only shows the settings, so the run ends with no summary.
        self.just_showing = False
        self.problems: list[str] = []
        self.unknown_placeholders: list[str] = []
        self.unplaced_notes: list[str] = []
        self.generated_changes = 0
        # Set once this run clones dev-home, which then may have another copy still in use, or
        # creates one, which nothing else can be using yet.
        self.cloned = False
        self.created = False
        # The profile folder to set up: yours, unless local-settings.json sets testHomeDir.
        self.home = Path.home()

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
        self, intro: str, question: str, items: Sequence[console.ListItem]
    ) -> console.ListAnswer | None:
        """The shared prompt for every list of optional items, or None without a console."""
        return console.choose_from_list(intro, question, items) if self.can_ask else None

    def choose_or_default(self, question: str, setting: Setting, data: dict[str, Any]) -> object:
        """Asks about a yes-or-no setting with a default, one of dev-home-tools' own or a
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
            "sync.py can pull dev-home-tools updates on every sync, or only tell you when there "
            "are some,"
        )
        self.line("so you can look at them first and pull them with update.py.")
        return self.choose_or_default("Pull updates automatically?", BY_PATH[AUTO_UPDATE], data)

    def ask_folder(self, tool: Tool, folder: Path, current: bool | None) -> bool | None:
        """Whether to set up one of a tool's folders. Enter keeps its answer, and takes yes for one
        with no answer yet. None when no answer came."""
        return self.choose(folder_question(tool, folder), True if current is None else current)

    def ask_codex(self, homes: Sequence[Path], current: bool | None) -> bool | None:
        """Whether to set up Codex, in every Codex home, which all read the same skills. Enter
        keeps its answer, and takes yes with no answer yet. None when no answer came."""
        found = folder_list(homes) or "none found yet"
        self.line(f"Codex homes on this PC, one for each Codex account: {found}")
        self.line(
            "Every Codex home reads the same skills, so setup sets up all of them, homes found "
            "later included, or none."
        )
        return self.choose(CODEX_QUESTION, True if current is None else current)

    def ask_copies(self, current: bool | None) -> bool | None:
        """Whether dev-home is in active use anywhere besides this PC. With no answer yet, there's
        no default: both wrong answers cost something."""
        self.line(
            "dev-home can live on one PC, as a private backup with its history on GitHub, or be "
            "used from several,"
        )
        self.line("which then check GitHub before each command.")
        return self.choose(
            "Is dev-home in active use anywhere besides this PC, such as on another PC or in a "
            "cloud session?",
            current,
        )

    def print_diff(self, old_text: str, new_text: str) -> None:
        """The lines a change adds (+) and removes (-), with a few around them."""
        diff = line_diff(to_lines(old_text), to_lines(new_text))
        limit = 40
        for diff_line in diff[:limit]:
            code = (
                GREEN if diff_line.startswith("+ ") else RED if diff_line.startswith("- ") else ""
            )
            self.line("            " + diff_line, code)
        if len(diff) > limit:
            self.line(f"            ...and {len(diff) - limit} more lines.")

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

    def not_a_dev_home_problem(self, folder: Path, missing_files: str) -> None:
        self.status(
            "PROBLEM",
            f"{folder} doesn't look like a dev-home: it has no {missing_files}, which every "
            "dev-home starts with, so setup stopped before setting anything in it. If it is your "
            "dev-home, put the missing files back; if not, point setup at your dev-home with "
            "--content-dir.",
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

    def save_settings(
        self, settings: LocalSettings, read: dict[str, Any] | None, checked: Checked
    ) -> None:
        """Saves this PC's settings, and says so in one line, which names any setting this run
        moved or removed. The file is backed up first when a person changed a setting, through
        the menu or --configure, or a setting was removed. The work that runs this holds the
        sync's lock, so a sync's own save can't come in between."""
        backup = self.changed_by_hand or self.assigned or bool(checked.removed)
        try:
            kept = self.write_settings(settings, read, backup=backup)
        except OSError as error:
            self.status("PROBLEM", f"Could not save this PC's settings in {SETTINGS_PATH}. {error}")
            return
        if kept is None:
            return
        notes = "".join(f". {sentence}" for sentence in cleanup(checked))
        if backup:
            notes += f". Backup of the old file: {kept}" if kept else " (new file)"
        self.status("SET", f"This PC's settings: {SETTINGS_PATH}{notes}")

    def write_settings(
        self, settings: LocalSettings, read: dict[str, Any] | None, *, backup: bool
    ) -> str | None:
        """Writes this PC's settings, and returns the backup's path, "" when it made none, or None
        when it wrote nothing, having said why. When the file changed since this run read it, such
        as by a sync while a question waited, only this run's changes go into the newer file."""
        wanted = local_settings_data(settings)
        now = load_local_settings()
        if now is None:
            self.status(
                "PROBLEM",
                f"This PC's settings weren't saved: {SETTINGS_PATH} changed while setup ran, and "
                "can't be read now. Fix it, then run setup.py again.",
            )
            return None
        if now.found and now.data != read:
            if layout(now.data, SCHEMA_VERSION):
                self.status(
                    "PROBLEM",
                    f"This PC's settings weren't saved: {SETTINGS_PATH} changed while setup ran, "
                    "to a layout this setup doesn't know. Run setup.py again.",
                )
                return None
            merged = copy.deepcopy(now.data)
            apply_changes(merged, read or {}, wanted)
            text = settings_text(merged)
        else:
            text = settings_text(wanted)
        return write_settings_file(SETTINGS_PATH, text, bom=False, backup=backup)

    # The tools' folders: Claude Code folders and Codex homes

    def found_folders(self, tool: Tool) -> list[Path]:
        """Each of a tool's folders setup finds, to offer: those in the profile folder (see
        profile_folders), then the session's own (see session_folder)."""
        found = self.profile_folders(tool)
        session = self.session_folder(tool)
        if session is not None and not any(same_path(session, folder) for folder in found):
            found.append(session)
        return found

    def profile_folders(self, tool: Tool) -> list[Path]:
        """A tool's folders in the profile folder: its default one, such as ~/.claude, once the
        tool has made it, which is how setup knows the tool is on this PC, then each extra one,
        such as ~/.claude-<name>, for another account, which the tool's variable, such as
        CLAUDE_CONFIG_DIR, points a session to. A profile folder that can't be listed has only the
        default one to offer."""
        default = self.home / tool.default
        found = [default] if default.is_dir() else []
        try:
            entries = list(self.home.iterdir())
        except OSError:
            return found
        # The name first, so only a folder with the right name costs a look on disk.
        return found + sorted(
            f
            for f in entries
            if f.name.lower().startswith(tool.default + "-")
            and f.is_dir()
            and (not tool.marks or any((f / mark).is_file() for mark in tool.marks))
        )

    def session_folder(self, tool: Tool) -> Path | None:
        """The folder in the tool's variable, such as CLAUDE_CONFIG_DIR, when that's set and the
        folder exists: the one the session running setup uses. A test profile takes it only from
        inside itself, so the real one is never touched."""
        value = os.environ.get(tool.variable)
        if not value:
            return None
        folder = Path(comparable(resolve_home(value, self.home)))
        inside_home = os.path.normcase(str(folder)).startswith(
            os.path.normcase(comparable(self.home)) + os.sep
        )
        if not (same_path(self.home, Path.home()) or inside_home) or not folder.is_dir():
            return None
        return folder

    def added_homes(self, settings: LocalSettings) -> list[Path]:
        """Each Codex home listed by its path in codex.homes that's there."""
        homes = [
            Path(comparable(resolve_home(entry, self.home)))
            for entry in listed_entries(get(settings.data, CODEX_HOMES))
        ]
        return [home for home in homes if home.is_dir()]

    def codex_homes(self, settings: LocalSettings) -> list[Path]:
        """Every Codex home setup knows of that's there, each once: those it finds (see
        found_folders), then those listed by their paths."""
        homes = self.found_folders(CODEX)
        for home in self.added_homes(settings):
            if not any(same_path(home, found) for found in homes):
                homes.append(home)
        return homes

    def folder_entry(self, folder: Path) -> str:
        """How a folder is written in local-settings.json: from ~ when it's in the profile folder,
        and in full otherwise."""
        return "~/" + folder.name if same_path(folder.parent, self.home) else forward(folder)

    def listed(self, folder: str | Path, entries: list[str]) -> bool:
        """Whether a folder is one of the entries, which may start with ~."""
        return any(
            same_path(resolve_home(entry, self.home), folder) for entry in entries if entry.strip()
        )

    # Generated files

    def sync_generated_folder(
        self,
        destination: Path,
        values: dict[str, str],
        source: Path | None = None,
        note_file: str = "",
        note_text: str = "",
    ) -> None:
        """Makes destination hold exactly the files in source, with the placeholders filled in,
        and note_text added to note_file (a path relative to source). With no source, empties
        destination and removes it."""
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
            relative = os.path.relpath(file, source)
            target = destination / relative
            same_note_file = os.path.normcase(relative) == os.path.normcase(note_file)
            rendered = generated.render(
                file, values, note_text if note_file and same_note_file else ""
            )
            self.unknown_placeholders.extend(rendered.unknown)
            if rendered.unplaced:
                self.unplaced_notes.append(str(file))
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
        """Offers to clone the person's dev-home from GitHub, or to create a new private one
        from templates/dev-home-starter/. The caller checks the folder afterward."""
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
            code, lines = run_tool(gh, "repo", "clone", name, str(path))
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
        action = f"Create a private repo named {name} on GitHub, from templates/dev-home-starter/"
        if not self.should(path, action):
            return
        path.mkdir(parents=True, exist_ok=True)
        starter = TOOLS_ROOT / "templates" / "dev-home-starter"
        files: list[str] = []
        for file in sorted(f for f in starter.rglob("*") if f.is_file()):
            relative = file.relative_to(starter)
            target = path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            rendered = generated.render(file, values)
            self.unknown_placeholders.extend(rendered.unknown)
            target.write_bytes(rendered.data)
            files.append(relative.as_posix())
        steps = [
            ["init", "--quiet", "-b", "main"],
            ["config", "--local", "commit.gpgsign", "false"],
            ["config", "--local", "pull.rebase", "false"],
            ["add", "--", *files],
            ["commit", "--quiet", "-m", "starter: new dev-home"],
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
                f"{path} has a schemaVersion this dev-home-tools doesn't know, perhaps written by "
                "a newer one on another copy, so setup left it alone, and each sync checks GitHub "
                f"every time. Update dev-home-tools: {by_hand('update.py')}",
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
            code = sync.commit_for_setup(content_root, DEV_HOME_SETTINGS, message, holds_lock=True)
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

    def sync_codex_rules(
        self,
        home: Path,
        operating_template: Path,
        global_path: Path,
        values: dict[str, str],
        note_text: str,
    ) -> None:
        """Codex reads a single always-on file in each home, so setup writes the operating rules
        and the person's global rules into it, joined, under one note naming both. The operating
        rules come from their template rather than Claude Code's generated copy, which has a note
        of its own. It replaces only a file it wrote, or a link whose target is gone."""
        path = home / "AGENTS.md"
        label = f"Codex always-on rules in {home.name}"
        parts = [
            note_text,
            generated.render(operating_template, values).data.decode("utf-8").rstrip("\n"),
        ]
        if global_path.is_file():
            parts.append(generated.read_text(global_path).rstrip("\n"))
        text = "\n\n".join(parts) + "\n"

        existing = link_info(path)
        if existing is not None:
            if existing.is_link:
                if existing.target is not None and Path(existing.target).exists():
                    self.status(
                        "PROBLEM",
                        f"{label}: {path} links to {existing.target}. Left alone. Move anything "
                        f"you want to keep into {global_path}, delete the link, then run setup.py "
                        "again.",
                    )
                    return
                if not self.should(path, "Replace this link with the joined rules file"):
                    return
                path.unlink()
            else:
                current = path.read_bytes().decode("utf-8-sig", errors="replace")
                if not current.startswith(generated.MARKER):
                    self.status(
                        "PROBLEM",
                        f"{label}: {path} already exists, and setup did not write it. Move "
                        f"anything you want to keep into {global_path}, delete the file, then run "
                        "setup.py again.",
                    )
                    return
                if current == text:
                    self.status("OK", label)
                    return
        if not self.should(path, "Write the operating and global rules, joined"):
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as file:
            file.write(text)
        self.status("WROTE", f"{label}: {path}")

    # Python, for the skills' scripts

    def sync_python_link(self, local_app_data: Path, *, skip_registry: bool) -> None:
        """Makes internal/.python a junction to the folder of a Python 3.12 or later, so the
        skills' commands name the same short path on every PC, with no spaces to quote. Each
        run only checks that the link's python.exe is there, which starts no process. It looks
        for a Python, which does, only to make the link, or to re-point it once that python.exe
        is gone."""
        label = "Python for the skills"
        existing = link_info(PYTHON_LINK)
        if existing is not None and not existing.is_link:
            self.status(
                "PROBLEM",
                f"{label}: {PYTHON_LINK} already exists and is not a link. Setup makes a junction "
                "there to a Python install. Move it aside, then run setup.py again.",
            )
            return
        if existing is not None and (PYTHON_LINK / "python.exe").is_file():
            self.status("OK", f"{label}: {existing.target}")
            return
        folder = next(
            (
                candidate
                for candidate in python_link.candidates(local_app_data, skip_registry=skip_registry)
                if python_link.is_new_enough(candidate)
            ),
            None,
        )
        if folder is None:
            self.status(
                "PROBLEM",
                f"{label}: no Python 3.12 or later was found, and the skills run their scripts "
                "with it. Install it with the Python install manager (see the README's "
                "Requirements), then run setup.py again.",
            )
            return
        if not self.should(PYTHON_LINK, f"Link to the Python in {folder}"):
            return
        try:
            if existing is not None:
                remove_folder_link(PYTHON_LINK)
            kind = make_folder_link(PYTHON_LINK, folder)
            self.status("LINKED", f"{label} ({kind}): {PYTHON_LINK} -> {folder}")
        except OSError as error:
            self.status("PROBLEM", f"{label}: could not link {PYTHON_LINK} to {folder}. {error}")

    # Settings changes. Each change is planned in full first, checked by reading the new text
    # back, shown as a line diff, and written only after a yes, with a backup. At a console, each
    # is shown and asked about before the work starts, so the work never waits for an answer;
    # the work plans each one again, and makes it while the file is as it was shown.

    def offer_settings_changes(self, checks: list[SettingsCheck]) -> None:
        """At a console, shows each settings change setup can make, and asks about it, before the
        work. A preview asks nothing, and shows each one in the work instead."""
        for check in checks:
            if isinstance(check, SettingsChange) and not check.plan.reason:
                yes = self.offer_setting(check)
                self.approved[approval_key(check.path)] = (check.plan.file.text, yes)

    def show_setting(self, change: SettingsChange, note: str = "") -> None:
        """Shows a planned settings change: what it's for, then the changed lines."""
        self.status("CHANGE", f"{change.subject}: {change.path} needs {change.need}.")
        if note:
            self.line("          " + note)
        self.line(
            "          Setup can make this change, and keeps a backup of the file first. Lines "
            "marked + are added, - removed:"
        )
        if change.plan.note:
            self.line("          " + change.plan.note)
        self.print_diff(change.plan.file.text, change.plan.new_text or "")

    def offer_setting(self, change: SettingsChange, note: str = "") -> bool:
        """Shows a planned settings change, and asks whether to make it."""
        self.show_setting(change, note)
        return self.confirm("          Make this change?")

    def repair_setting(self, change: SettingsChange) -> None:
        """Makes a planned settings change after a yes, and writes the file with a backup. The yes
        is the one given before the work while the file is still as it was then; otherwise setup
        shows the change it needs now, and asks again. When the change can't be made safely, the
        answer is no, or setup runs with --quiet, it reports a problem and leaves the file alone.
        With --quiet, the problem says how to make the change."""
        plan = change.plan
        problem = f"{change.subject}: {change.path} needs {change.need}."
        if plan.reason:
            self.status("PROBLEM", problem)
            if not self.quiet:
                self.line(f"          Setup won't change this file itself: {plan.reason}.")
                self.line("          " + change.how_to)
                self.line(change.snippet, YELLOW)
            return
        if self.quiet:
            self.status("PROBLEM", f"{problem} {QUIET_ADVICE}")
            return
        if self.what_if:
            self.show_setting(change)
            self.should(change.path, "Change the lines shown, after asking, and keep a backup")
            return

        shown = self.approved.get(approval_key(change.path))
        if shown is not None and shown[0] == plan.file.text:
            yes = shown[1]
        else:
            note = "" if shown is None else "The file changed after setup showed its change."
            yes = self.offer_setting(change, note)
        if not yes:
            self.status(
                "PROBLEM",
                f"{change.subject}: left unchanged. Make the change shown above by hand, or run "
                "setup.py again and answer y.",
            )
            return
        try:
            now = read_settings_file(change.path)
            if now.reason or now.text != plan.file.text:
                raise OSError(
                    "The file changed while setup was waiting for an answer, so it was left "
                    "alone. Run setup.py again."
                )
            backup = write_settings_file(
                change.path, plan.new_text or "", bom=plan.file.bom, backup=True
            )
            saved = f" Backup of the old file: {backup}" if backup else " (new file)"
            self.status("SET", f"{change.subject}: changed {change.path}.{saved}")
        except (OSError, ValueError) as error:
            self.status("PROBLEM", f"{change.subject}: could not write {change.path}. {error}")

    # The run, in order: where things are; dev-home; the questions not answered yet; at a
    # console, the settings menu; the changes to confirm; then the work, which asks nothing and
    # holds the sync's lock; and last, the settings files, which the lock doesn't cover, since
    # no sync writes them, and a file that changed after setup showed its change is asked about
    # again.

    def run(self, content_dir_option: str) -> None:
        settings, read, checked = self.read_settings()
        saved_folder = settings.content_dir
        # A PC's first setup: no dev-home folder saved yet, such as after settings are set aside.
        first_setup = not saved_folder
        # A setting moved or removed is saved, whether anything else changes or not.
        save = bool(checked.moved or checked.removed)
        if self.configure is not None:
            try:
                save = configure.change_settings(self, settings) or save
            except configure.SettingError as error:
                self.status("PROBLEM", f"{error} Nothing was changed.")
                self.line(configure.USAGE)
                raise CannotGoOnError from error
            if self.just_showing:
                raise CannotGoOnError

        # 1. dev-home first: its folder, then, when it's missing, clone or create it. Nothing is
        # saved before it's in place.
        self.choose_dev_home_folder(settings, content_dir_option)
        while True:
            content_root = self.find_dev_home(settings)
            # 2. The questions not answered yet.
            save = self.ask_unanswered(settings, content_root, first_setup=first_setup) or save
            # 3. At a console, the settings menu, so any setting can be changed.
            if not self.can_ask:
                break
            folder = settings.content_dir
            if configure.menu(self, settings):
                self.changed_by_hand = save = True
            if same_path(folder, settings.content_dir):
                break
            # Another dev-home folder: its checks again, and its own answer about copies.
            self.wanted_copies = None
            self.cloned = self.created = False
        if settings.content_dir != saved_folder:
            save = True

        # 4. The changes to confirm, shown and asked about before the work.
        tools = self.tool_folders(settings)
        self.confirm_copies(content_root)
        if self.can_ask and not self.what_if:
            self.offer_settings_changes(self.settings_checks(content_root, tools))

        # 5. The work.
        with self.work_lock(content_root) as owned:
            if not owned:
                raise CannotGoOnError
            if save:
                if self.should(SETTINGS_PATH, "Save this PC's settings"):
                    self.save_settings(settings, read, checked)
                else:
                    for sentence in cleanup(checked):
                        self.line(f"What if: {sentence}")
            self.set_up(settings, content_root, tools)

        # 6. The tools' settings files. A missing setting is offered as a change: shown first,
        # made only after a yes, and with a backup. See repair_setting.
        for check in self.settings_checks(content_root, tools):
            if isinstance(check, SettingsChange):
                self.repair_setting(check)
            else:
                self.status(*check)

    def read_settings(self) -> tuple[LocalSettings, dict[str, Any] | None, Checked]:
        """Where things are: dev-home-tools' folder, the profile to set up, and this PC's
        settings, checked. Returns them, the file as this run read it, which its save compares
        with, and what the check moved or removed."""
        tools_problem = unsafe_reason(comparable(TOOLS_ROOT))
        if tools_problem:
            self.status(
                "PROBLEM",
                f"dev-home-tools is at {comparable(TOOLS_ROOT)}, which {tools_problem}. Setup "
                "writes this path into commands as it is, so move the folder, then run setup.py "
                "again.",
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
        # The file as this run read it: its save makes only this run's changes, to whatever the
        # file holds by then.
        read: dict[str, Any] | None = copy.deepcopy(settings.data) if settings.found else None
        file_layout = layout(settings.data, SCHEMA_VERSION) if settings.found else ""
        if file_layout == "older":
            settings = self.set_aside_settings(settings)
            read = local_settings_data(settings)
        elif file_layout == "unknown":
            self.status(
                "PROBLEM",
                f"{SETTINGS_PATH} has a schemaVersion this dev-home-tools doesn't know, perhaps "
                "written by a newer one, so setup left it alone and stopped. Update dev-home-tools "
                f"({by_hand('update.py')}), or set the file aside and run setup.py again.",
            )
            raise CannotGoOnError
        declared = skill_preferences(settings.content_dir)
        # Only a run that holds the sync's lock from its start, a sync's setup, removes the answers
        # of a skill that's gone.
        checked = check_settings(settings.data, declared, remove_gone_skills=self.sync_holds_lock)
        for problem in declared.problems + checked.problems:
            self.status("PROBLEM", problem)
        if checked.moved or checked.removed:
            settings.data = checked.data
            folder = get(settings.data, "devHome.folder")
            settings.content_dir = folder if isinstance(folder, str) else ""
            settings.folders = {
                path: folder_answers(get(settings.data, path)) for path in ANSWER_SETTINGS
            }
        return settings, read, checked

    # dev-home first

    def choose_dev_home_folder(self, settings: LocalSettings, content_dir_option: str) -> None:
        """The dev-home folder: --content-dir's, the saved one, or the person's answer."""
        if content_dir_option:
            settings.content_dir = forward(content_dir_option)
        elif not settings.content_dir:
            default = forward(TOOLS_ROOT.parent / "dev-home")
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
            if is_inside(settings.content_dir, TOOLS_ROOT):
                self.status(
                    "PROBLEM",
                    f"The dev-home folder {settings.content_dir} is dev-home-tools' own folder, or "
                    "inside it. Choose your dev-home's folder with --content-dir.",
                )
                raise CannotGoOnError
            # An empty or missing folder gets a dev-home below. One with files must already be
            # one, before anything is saved or set in it.
            folder = Path(comparable(settings.content_dir))
            missing_files = missing_dev_home_files(folder)
            if not missing_files or not is_in_use(folder):
                break
            if not self.can_ask:
                self.not_a_dev_home_problem(folder, missing_files)
                raise CannotGoOnError
            self.line(
                f"{folder} doesn't look like a dev-home: it has no {missing_files}, which every "
                "dev-home starts with."
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
        missing_files = missing_dev_home_files(content_root)
        if missing_files:
            self.not_a_dev_home_problem(content_root, missing_files)
            raise CannotGoOnError
        return content_root

    # The questions not answered yet

    def ask_unanswered(
        self, settings: LocalSettings, content_root: Path, *, first_setup: bool
    ) -> bool:
        """Asks each question whose answer isn't saved yet, and returns whether this PC's
        settings changed. A quiet run asks nothing, and names what's unanswered instead."""
        changed = False
        if self.can_ask and not setting_value(settings.data, AUTO_UPDATE)[1]:
            updates = self.ask_auto_update(settings.data)
            if updates is not MISSING:
                put(settings.data, AUTO_UPDATE, updates)
                changed = True
        changed = self.ask_about_folders(CLAUDE_CODE, settings) or changed
        changed = self.ask_about_codex(settings) or changed
        self.ask_about_copies(settings, content_root, first_setup=first_setup)
        return changed

    def ask_about_folders(self, tool: Tool, settings: LocalSettings) -> bool:
        """Asks about each of a tool's folders that setup finds with no answer yet, in the shared
        prompt for optional lists, a list of the tool's own, each one recommended, and keeps every
        answer, a no included, so it's asked about once. A folder nobody has answered for isn't
        set up: setup adds no links there and removes none. A quiet run names those folders
        instead. Returns whether an answer came."""
        answers = settings.folders[tool.setting]
        unanswered = [f for f in self.found_folders(tool) if not self.listed(f, list(answers))]
        if not unanswered:
            return False
        kind = f"{tool.name} {tool.folder}"
        if self.can_ask:
            answer = self.choose_from_list(
                f"{kind}s setup hasn't asked about yet, one for each {tool.account} account:",
                f"Set up {tool.name} in them with dev-home's skills and rules?",
                [console.ListItem(str(f), True, folder_question(tool, f)) for f in unanswered],
            )
            if answer is not None:
                for folder in unanswered:
                    answers[self.folder_entry(folder)] = answer.answers[str(folder)]
                return True
            which = " and ".join(str(f) for f in unanswered)
            self.status(
                "PROBLEM",
                f"No answer came about {which}, so setup left them as they are. Run setup.py "
                "again to answer.",
            )
            return False
        # The session's own folder, when it's in the profile folder under another name or outside
        # it, comes only from the tool's variable, which a terminal usually doesn't have.
        found = self.profile_folders(tool)
        for folder in unanswered:
            if not any(same_path(folder, f) for f in found):
                self.status(
                    "PROBLEM",
                    f"Setup hasn't asked yet whether to set up the {kind} {folder}, the session's "
                    f"own, in {tool.variable}, so it leaves it as it is. Setup in a terminal "
                    f"usually can't see it: to set it up, run {by_hand('setup.py')} --configure "
                    f"'{tool.setting}+={self.folder_entry(folder)}'.",
                )
        asked_in_terminal = [f for f in unanswered if any(same_path(f, g) for g in found)]
        if asked_in_terminal:
            which = (
                f"the {kind} {asked_in_terminal[0]}, so it leaves it as it is"
                if len(asked_in_terminal) == 1
                else f"these {kind}s: "
                + ", ".join(str(f) for f in asked_in_terminal)
                + ", so it leaves them as they are"
            )
            self.status(
                "PROBLEM",
                f"Setup hasn't asked yet whether to set up {which}. Run {by_hand('setup.py')} in "
                "a terminal, and it asks.",
            )
        return False

    def ask_about_codex(self, settings: LocalSettings) -> bool:
        """Asks whether to set up Codex, in every Codex home, once setup finds one and Codex isn't
        answered yet, and keeps the answer, a no included, so it's asked about once. Until it's
        answered, setup adds no links and removes none. A quiet run names the homes instead.
        Returns whether an answer came."""
        if setting_value(settings.data, CODEX_SETUP)[1]:
            return False
        homes = self.codex_homes(settings)
        if not homes:
            return False
        if self.can_ask:
            answer = self.ask_codex(homes, None)
            if answer is not None:
                put(settings.data, CODEX_SETUP, answer)
                return True
            self.status(
                "PROBLEM",
                "No answer came about Codex, so setup left it as it is. Run setup.py again to "
                "answer.",
            )
            return False
        # A home only the session's own CODEX_HOME names, which a terminal usually doesn't have.
        visible = self.profile_folders(CODEX) + self.added_homes(settings)
        unseen = [home for home in homes if not any(same_path(home, v) for v in visible)]
        for home in unseen:
            self.status(
                "PROBLEM",
                f"Setup hasn't asked yet whether to set up Codex, so it leaves the Codex home "
                f"{home}, the session's own, in {CODEX.variable}, as it is. Setup in a terminal "
                f"usually can't see it: run {by_hand('setup.py')} --configure "
                f"'{CODEX_HOMES}+={self.folder_entry(home)}' so it can, then run "
                f"{by_hand('setup.py')} in a terminal, and it asks.",
            )
        seen = [home for home in homes if home not in unseen]
        if seen:
            which = (
                f"the Codex home {seen[0]} as it is"
                if len(seen) == 1
                else f"the Codex homes {folder_list(seen)} as they are"
            )
            self.status(
                "PROBLEM",
                f"Setup hasn't asked yet whether to set up Codex, so it leaves {which}. Run "
                f"{by_hand('setup.py')} in a terminal, and it asks.",
            )
        return False

    def tool_folders(self, settings: LocalSettings) -> ToolFolders:
        """Where setup sets up each tool, from the answers: each Claude Code folder answered yes,
        and every Codex home, once Codex is answered yes."""
        claude_dirs = [full for _, full in self.folders_answered(CLAUDE_CODE, settings, True)]
        codex_on = setting_value(settings.data, CODEX_SETUP)[0] is True
        codex_homes = [comparable(home) for home in self.codex_homes(settings)] if codex_on else []
        return ToolFolders(claude_dirs, codex_homes)

    def folders_answered(
        self, tool: Tool, settings: LocalSettings, answer: bool
    ) -> list[tuple[str, str]]:
        """Each of a tool's folders with that answer that's there, each once: its entry in the
        settings, and its full path."""
        folders: list[tuple[str, str]] = []
        for entry in answered(settings.folders[tool.setting], answer):
            if not entry.strip():
                continue
            full = comparable(resolve_home(entry, self.home))
            # A folder answered yes that's gone, such as an account removed on purpose, keeps its
            # answer, so it's set up again if it comes back. The settings menu shows it.
            if not Path(full).exists():
                continue
            if not any(same_path(full, d) for _, d in folders):
                folders.append((entry, full))
        return folders

    # The work, which asks nothing

    def set_up(self, settings: LocalSettings, content_root: Path, tools: ToolFolders) -> None:
        """Everything setup sets up besides this PC's settings and the tools' settings files, in
        order: dev-home's git config and its dev-home.json, Python for the skills' scripts, the
        generated files, the skills' links, and the always-on rules."""
        values = template_values(content_root)
        # The operating rules template and the person's global rules, each named once: setup
        # reads them from here, and the notes in generated files point to them.
        operating_template = TOOLS_ROOT / "templates" / "operating-rules" / "operating-rules.md"
        global_rules_file = content_root / "global-rules" / "global-rules.md"

        # 1. dev-home: no signing prompts for agent commits, and pulls that merge rather than
        # rebase, as sync.py does, because a rebase refuses to run while any file is uncommitted.
        for key, value in (("commit.gpgsign", "false"), ("pull.rebase", "false")):
            current = run_git(content_root, "config", "--local", "--get", key)
            if first_line(current.out) == value:
                self.status("OK", f"dev-home git config {key} = {value}")
            elif self.should(f"git config --local {key} in {content_root}", f"Set to {value}"):
                if run_git(content_root, "config", "--local", key, value).code == 0:
                    self.status("SET", f"dev-home git config {key} = {value}")
                else:
                    self.status("PROBLEM", f"Could not set git config {key} in {content_root}.")
        # With signing off, so a commit needs no prompt, and before linking skills, so a merge's
        # new ones are linked in this run.
        self.write_copies(content_root)

        # 2. Python, for the skills' scripts. A test profile has its own AppData folder.
        if settings.test_home_dir:
            local_app_data = self.home / "AppData" / "Local"
        else:
            local_app_data = Path(
                os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
            )
        self.sync_python_link(local_app_data, skip_registry=bool(settings.test_home_dir))

        # 3. Generated files: the skills, the scripts they share, and the operating rules, with
        # this PC's paths filled in, at the same paths they have under templates/. The file each
        # tool loads, a skill's SKILL.md or the operating rules, gets a note naming its
        # template, because an agent in another project only ever sees this copy, and an edit
        # here is lost at the next setup run. No other file gets one: the handoff template, for
        # one, is copied into every new handoff.
        skill_sources = skill_templates()
        generated_skills = GENERATED_ROOT / "skills"
        for skill in skill_sources:
            destination = generated_skills / skill.name
            skill_values = dict(values)
            skill_values["SKILL_DIR"] = forward(destination)
            skill_values["SKILL_STAMP"] = generated.skill_stamp(skill / "SKILL.md", skill_values)
            skill_note = generated.note(
                f"{forward(skill)}/",
                "Changing the skill there changes dev-home-tools itself; skills of your own go "
                f"in {values['CONTENT_DIR']}/skills/.",
            )
            self.sync_generated_folder(destination, skill_values, skill, "SKILL.md", skill_note)
        skill_names = {os.path.normcase(skill.name) for skill in skill_sources}
        if generated_skills.exists():
            for folder in sorted(generated_skills.iterdir()):
                stale = os.path.normcase(folder.name) not in skill_names
                if folder.is_dir() and not is_link(folder) and stale:
                    self.sync_generated_folder(folder, values)
        rules_note = generated.note(
            forward(operating_template),
            f"Put rules of your own in {forward(global_rules_file)}; changing the template "
            "changes dev-home-tools itself.",
        )
        self.sync_generated_folder(
            GENERATED_ROOT / "operating-rules",
            values,
            operating_template.parent,
            operating_template.name,
            rules_note,
        )
        # The scripts the skills share. The skills run them from here, at the path
        # SHARED_SKILL_SCRIPTS_DIR gives.
        self.sync_generated_folder(
            GENERATED_ROOT / "shared-skill-scripts",
            values,
            TOOLS_ROOT / "templates" / "shared-skill-scripts",
        )
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

        for unknown in dict.fromkeys(self.unknown_placeholders):
            self.status("PROBLEM", f"A placeholder setup does not know, left as it is: {unknown}")
        for unplaced in dict.fromkeys(self.unplaced_notes):
            self.status(
                "PROBLEM",
                f"{unplaced} starts with frontmatter that has no closing --- line, so its "
                "generated copy has no note saying not to edit it. Close the frontmatter with a "
                "line of three dashes.",
            )
        label = "Skills, their shared scripts, and operating rules with this PC's paths"
        if self.generated_changes > 0:
            self.status(
                "WROTE", f"{label}: {self.generated_changes} file(s) changed in {GENERATED_ROOT}"
            )
        else:
            self.status("OK", label)

        # 4. Skills, linked into each tool's personal skills folder: the dev-home-tools skills,
        # then the personal skills in dev-home. Every Codex home reads ~/.agents/skills.
        tool_skill_folders = [Path(d) / "skills" for d in tools.claude_dirs]
        if tools.codex_homes:
            tool_skill_folders.append(self.home / ".agents" / "skills")

        links, same_names = skill_links(content_root)
        for name in same_names:
            self.status(
                "PROBLEM",
                f"Your personal skill '{name}' has the same name as a dev-home-tools skill, so it "
                "isn't linked. Rename its folder and its name field.",
            )
        personal_skills = content_root / "skills"

        # Links into these folders are setup's own, so one whose skill is gone can be removed.
        # A link for a skill that's still here stays, even when its generated folder is missing.
        owned = [
            os.path.normcase(comparable(f)) + os.sep for f in (generated_skills, personal_skills)
        ]
        current_skills = {os.path.normcase(name) for name, _ in links}
        for folder in tool_skill_folders:
            for name, target in links:
                self.sync_link(folder / name, target, f"Skill '{name}' in {folder}")
            if not folder.exists():
                continue
            for entry in sorted(folder.iterdir()):
                if os.path.normcase(entry.name) in current_skills:
                    continue
                found = link_info(entry)
                if found is None or not found.is_link or found.target is None:
                    continue
                if Path(found.target).exists():
                    continue
                if not os.path.normcase(found.target).startswith(tuple(owned)):
                    continue
                if not self.should(entry, "Remove a link to a deleted skill"):
                    continue
                try:
                    remove_folder_link(entry)
                    self.status("REMOVED", f"Link to a deleted skill: {entry}")
                except OSError as error:
                    self.status("PROBLEM", f"Could not remove the stale link {entry}. {error}")

        # 5. Always-on rules: the operating rules from here, and the person's global rules from
        # dev-home. Claude Code loads every file in the rules folder of each Claude folder, where
        # each link is named dev-home- plus the folder it points to, since nothing there says
        # which repo a name belongs to. Codex reads one file in each home, so setup writes the
        # two joined there.
        operating_rules = GENERATED_ROOT / "operating-rules"
        global_rules = global_rules_file.parent
        for claude_dir in tools.claude_dirs:
            claude_name = Path(claude_dir).name
            rules = Path(claude_dir) / "rules"
            self.sync_link(
                rules / "dev-home-operating-rules",
                operating_rules,
                f"Claude Code operating rules in {claude_name}",
            )
            if global_rules.exists():
                self.sync_link(
                    rules / "dev-home-global-rules",
                    global_rules,
                    f"Claude Code global rules in {claude_name}",
                )
        codex_note = generated.note(
            f"{forward(operating_template)} and {forward(global_rules_file)}",
            "Put rules of your own in the second file; changing the first changes "
            "dev-home-tools itself.",
        )
        for home in tools.codex_homes:
            self.sync_codex_rules(
                Path(home), operating_template, global_rules_file, values, codex_note
            )

    def settings_checks(self, content_root: Path, tools: ToolFolders) -> list[SettingsCheck]:
        """What each tool's settings file needs, planned from the file as it is now: each Claude
        Code folder's and each Codex home's set up."""
        wanted_dirs = [comparable(content_root), comparable(TOOLS_ROOT)]
        checks = [
            self.check_claude_settings(Path(claude_dir), wanted_dirs)
            for claude_dir in tools.claude_dirs
        ]
        checks += [
            self.check_codex_config(Path(home), comparable(content_root))
            for home in tools.codex_homes
        ]
        return checks

    def check_claude_settings(self, claude_dir: Path, wanted_dirs: list[str]) -> SettingsCheck:
        claude_name = claude_dir.name
        path = claude_dir / "settings.json"
        present: list[str] = []
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
        missing = [d for d in wanted_dirs if not any(same_path(d, p) for p in present)]
        if not missing:
            return (
                "OK",
                f"Claude Code settings in {claude_name}: additionalDirectories includes dev-home "
                "and dev-home-tools",
            )
        try:
            plan = claude_settings.plan(path, missing)
        except Exception as error:
            plan = Plan(SettingsFile(), reason=f"planning the change failed ({describe(error)})")
        entries = ", ".join(claude_settings.dump(entry) for entry in missing)
        snippet = (
            "          {\n"
            '            "permissions": {\n'
            f'              "additionalDirectories": [{entries}]\n'
            "            }\n"
            "          }"
        )
        return SettingsChange(
            f"Claude Code settings in {claude_name}",
            path,
            f"{' and '.join(missing)} in permissions.additionalDirectories",
            plan,
            'Merge this into the file. If it already has "permissions", put '
            "additionalDirectories inside that block:",
            snippet,
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
        if codex_config.is_configured(text, content_root, CODEX_DOC_BYTES):
            return ("OK", f"{subject}: writable_roots and project_doc_max_bytes")
        try:
            plan = codex_config.plan(path, content_root, CODEX_DOC_BYTES)
        except Exception as error:
            plan = Plan(SettingsFile(), reason=f"planning the change failed ({describe(error)})")
        snippet = (
            f"          project_doc_max_bytes = {CODEX_DOC_BYTES}\n\n"
            "          [sandbox_workspace_write]\n"
            f"          writable_roots = ['{content_root}']"
        )
        return SettingsChange(
            subject,
            path,
            f"dev-home in writable_roots, and project_doc_max_bytes of at least {CODEX_DOC_BYTES} "
            "(Codex stops reading AGENTS.md files at 32 KiB by default)",
            plan,
            "Merge this into the file. project_doc_max_bytes goes above the first [section]. If "
            "the file already has [sandbox_workspace_write], add only the writable_roots line "
            "under it:",
            snippet,
        )


def folder_question(tool: Tool, folder: Path) -> str:
    return f"Set up {tool.name} in {folder} with dev-home's skills and rules?"


CODEX_QUESTION = "Set up Codex in every Codex home with dev-home's skills and rules?"


def folder_list(folders: Sequence[Path]) -> str:
    return ", ".join(str(folder) for folder in folders)


def skill_templates() -> list[Path]:
    """The folder of each of dev-home-tools' skills, in templates/skills/."""
    return sorted(
        folder
        for folder in (TOOLS_ROOT / "templates" / "skills").iterdir()
        if folder.is_dir() and (folder / "SKILL.md").is_file()
    )


def skill_links(content_root: Path) -> tuple[list[tuple[str, Path]], list[str]]:
    """Each skill setup links into the tools, by its name and the folder its link points to:
    dev-home-tools' skills, generated with this PC's paths, then the person's own in dev-home.
    Also the name of each of the person's own that has the same name as one of dev-home-tools',
    which isn't linked."""
    links = [(skill.name, GENERATED_ROOT / "skills" / skill.name) for skill in skill_templates()]
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


def template_values(content_root: Path) -> dict[str, str]:
    """What setup fills in for each placeholder in the templates: this PC's paths."""
    return {
        "TOOLS_DIR": forward(TOOLS_ROOT),
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


def missing_dev_home_files(folder: Path) -> str:
    """The files every dev-home starts with that a folder lacks, joined with "or", or "" when it
    has them all."""
    return " or ".join(name for name in DEV_HOME_FILES if not (folder / name).is_file())


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
