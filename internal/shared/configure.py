"""setup.py --configure: changing a setting after the first run.

At a console, it shows a menu of every setting with its current value: a number changes one, a
goes through them all, and Enter finishes. Each entry asks the question the first run asks, from
setup's own steps, so a setting is asked about, checked, and written one way.

An agent can't answer at a console, so it gives one setting instead, as <name>=<value>, such as
updates.installAutomatically=true, which its user approved in chat; nothing is asked. A setting's
name is its path in local-settings.json. With neither a console nor a setting, it shows the
settings and how to change them.

This PC's settings go in local-settings.json, which setup saves with a dated backup. dev-home's
own setting, how many copies are in active use, goes in dev-home.json, which setup writes later in
its run, then commits and pushes, once dev-home's git config is in place.
"""

import copy
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from .output import CYAN, GREEN, color, status_line
from .paths import comparable, forward, is_inside, resolve_home, same_path, unsafe_reason
from .settings import (
    CLAUDE_FOLDERS,
    DEFAULT_HOURS,
    DEV_HOME_SETTINGS,
    MISSING,
    SETTINGS_PATH,
    TOOLS_ROOT,
    LocalSettings,
    find_skill,
    get,
    hours_setting,
    hours_text,
    local_settings_text,
    put,
    read_dev_home_settings,
    skill_preferences,
)

if TYPE_CHECKING:
    from .setup import Setup

NAMES = (
    "devHome.folder",
    "updates.installAutomatically",
    "updates.checkEveryHours",
    "devHome.checkEveryHours",
    CLAUDE_FOLDERS,
    "multiMachine",
)
# A name is a path, which may hold dots and, in a skill's name, hyphens. The shortest name that
# leaves an operator after it, so claudeCode.folders-=<folder> reads as -=.
ASSIGNMENT = re.compile(r"([A-Za-z][\w.-]*?)(\+=|-=|=)(.*)", re.DOTALL)
USAGE = """\
To change one setting, as an agent does, run setup.py --configure '<name>=<value>', in single
quotes, which every shell passes on as they are. A name is the setting's path in
local-settings.json:

  devHome.folder=<folder>           Your dev-home folder: one that is already a dev-home.
  devHome.checkEveryHours=<hours>   How often a sync checks GitHub for dev-home's changes, with
                                    one active copy, and for a plain /knowledge. 0 checks every
                                    time.
  updates.installAutomatically=true|false
                                    Whether a sync installs dev-home-tools updates as soon as it
                                    finds them.
  updates.checkEveryHours=<hours>   How often a sync checks GitHub for dev-home-tools updates.
                                    0 checks every time.
  claudeCode.folders+=<folder>      Set up another Claude Code folder, such as
                                    ~/.claude-second.
  claudeCode.folders-=<folder>      Stop setting one up.
  skills.<skill>.<name>=true|false  A preference a skill declares.
  multiMachine=true|false           Whether dev-home is in active use anywhere besides this PC.
                                    Every copy shares it, so setup commits and pushes the change.

Add --what-if to see the change without making it. In a terminal, --configure alone shows a menu
of every setting instead."""
# What follows dev-home.json's name when its answer can't be used, by its layout.
LAYOUT_NOTES = {
    "unreadable": "can't be read",
    "older": "is in an older layout, so each sync checks GitHub",
    "unknown": "has a schemaVersion this dev-home-tools doesn't know",
}


class SettingError(Exception):
    """An assignment --configure can't make, and why."""


def change_settings(run: "Setup", settings: LocalSettings) -> bool:
    """Makes --configure's change to this PC's settings, or chooses dev-home.json's answer, which
    setup writes later in its run. Returns whether this PC's settings changed. With nobody to
    answer and no setting given, shows the settings and how to change them, and sets
    run.just_showing."""
    if run.assigned:
        return assign(run, settings, run.configure or "")
    if run.can_ask:
        return menu(run, settings)
    for line in overview(run, settings):
        run.line(line)
    run.line()
    run.line(USAGE)
    run.just_showing = True
    return False


# What the settings are now


def copies_answer(settings: LocalSettings) -> tuple[bool | None, str]:
    """dev-home.json's answer to whether more than one copy is in active use, None for none
    yet, whatever the file's layout, and that layout (see settings.layout): "missing" also when
    no dev-home folder is set."""
    if not settings.content_dir:
        return None, "missing"
    found = read_dev_home_settings(Path(comparable(settings.content_dir)))
    return found.answer, found.layout


def hours_value(settings: LocalSettings, path: str) -> str:
    hours, usable = hours_setting(settings.data, path)
    value = get(settings.data, path, MISSING)
    if value is MISSING:
        return hours_text(hours) + " (the default)"
    if not usable:
        return f"{hours_text(hours)} (the file says {json.dumps(value)}, which isn't whole hours)"
    return hours_text(hours)


def entry_for(run: "Setup", folders: dict[str, bool], folder: str | Path) -> str | None:
    """The entry in a tool's folders, as written, that names this folder, if any."""
    return next(
        (
            entry
            for entry in folders
            if entry.strip() and same_path(resolve_home(entry, run.home), folder)
        ),
        None,
    )


def folder_answers(run: "Setup", settings: LocalSettings) -> list[tuple[str, bool | None]]:
    """Each Claude folder setup knows of, as written in the settings, with its answer: each
    ~/.claude-* folder found, then any other folder with an answer, the default one included."""
    answers: list[tuple[str, bool | None]] = []
    for folder in run.claude_folders():
        entry = entry_for(run, settings.claude_folders, folder)
        answers.append(
            ("~/" + folder.name, None if entry is None else settings.claude_folders[entry])
        )
    for entry, answer in settings.claude_folders.items():
        full = resolve_home(entry, run.home)
        if not any(same_path(full, resolve_home(name, run.home)) for name, _ in answers):
            answers.append((entry, answer))
    return answers


def overview(run: "Setup", settings: LocalSettings) -> list[str]:
    """Every setting and its value, numbered as the menu numbers them."""
    if settings.auto_update is None:
        auto_update = "not answered yet, so no"
    else:
        auto_update = "yes" if settings.auto_update else "no"
    words = {True: "yes", False: "no", None: "not asked yet"}
    folders = ", ".join(
        f"{name}: {words[answer]}"
        + ("" if Path(resolve_home(name, run.home)).is_dir() else " (not found)")
        for name, answer in folder_answers(run, settings)
    )
    answer, found = copies_answer(settings)
    if run.wanted_copies is not None:
        copies = "several" if run.wanted_copies else "one"
    elif found in LAYOUT_NOTES:
        copies = f"{DEV_HOME_SETTINGS} {LAYOUT_NOTES[found]}"
    elif answer is None:
        copies = "not answered yet, so each sync checks GitHub"
    else:
        copies = "several" if answer else "one"
    this_pc = [
        ("dev-home folder", settings.content_dir or "not set yet"),
        ("Install dev-home-tools updates automatically", auto_update),
        (
            "Check GitHub for dev-home-tools updates",
            hours_value(settings, "updates.checkEveryHours"),
        ),
        ("Check GitHub for dev-home's changes", hours_value(settings, "devHome.checkEveryHours")),
        ("Claude Code folders to set up", folders or "none found"),
    ]
    shared = [("Copies of dev-home in active use", copies)]
    width = max(len(label) for label, _ in this_pc + shared) + 2

    def row(number: int, label: str, value: str) -> str:
        return f"  {color(str(number), GREEN)}  {label:<{width}}{value}"

    lines = [color("dev-home-tools settings", CYAN), "", color("This PC", CYAN)]
    lines += [row(number, label, value) for number, (label, value) in enumerate(this_pc, 1)]
    lines += ["", color("Shared by every copy of dev-home", CYAN)]
    lines += [row(len(this_pc) + 1, label, value) for label, value in shared]
    return lines


# The menu


def menu(run: "Setup", settings: LocalSettings) -> bool:
    """Shows every setting, and changes the ones the person picks, until Enter."""
    steps: dict[str, Callable[[Setup, LocalSettings], bool]] = {
        "1": change_content_dir,
        "2": change_auto_update,
        "3": change_update_hours,
        "4": change_content_hours,
        "5": change_claude_folders,
        "6": change_copies,
    }
    changed = False
    while True:
        run.line()
        for line in overview(run, settings):
            run.line(line)
        run.line()
        choice = run.ask("Number to change, a to go through them all, or Enter to finish")
        if not choice:
            return changed
        picked = list(steps) if choice.strip().lower() == "a" else [choice.strip()]
        if not all(number in steps for number in picked):
            run.line(f"Type a number from 1 to {len(steps)}, or a, or press Enter to finish.")
            continue
        for number in picked:
            changed = steps[number](run, settings) or changed


def change_content_dir(run: "Setup", settings: LocalSettings) -> bool:
    # Setup checks the folder next, as it does on a first run, and asks again if it isn't one.
    answer = run.ask("Your dev-home folder", settings.content_dir)
    if not answer or same_path(forward(answer), settings.content_dir or "."):
        return False
    settings.content_dir = forward(answer)
    return True


def change_auto_update(run: "Setup", settings: LocalSettings) -> bool:
    answer = run.ask_auto_update(settings.auto_update)
    if answer == settings.auto_update:
        return False
    settings.auto_update = answer
    return True


def change_hours(run: "Setup", settings: LocalSettings, path: str, question: str) -> bool:
    current = hours_setting(settings.data, path)[0]
    while True:
        answer = run.ask(question, str(current))
        if answer is None:
            return False
        if re.fullmatch(r"\d+", answer):
            break
        run.line("Type a whole number of hours: 0 or more.")
    hours = int(answer)
    # A default left unwritten moves with the default.
    written = get(settings.data, path, MISSING)
    if written == hours or (written is MISSING and hours == current):
        return False
    put(settings.data, path, hours)
    return True


def change_update_hours(run: "Setup", settings: LocalSettings) -> bool:
    return change_hours(
        run,
        settings,
        "updates.checkEveryHours",
        "Check GitHub for dev-home-tools updates every how many hours (0 for every sync)",
    )


def change_content_hours(run: "Setup", settings: LocalSettings) -> bool:
    run.line(
        "With one active copy, and for a plain /knowledge, a sync checks GitHub for dev-home's "
        "changes only this often."
    )
    return change_hours(
        run,
        settings,
        "devHome.checkEveryHours",
        "Check GitHub for dev-home's changes every how many hours (0 for every time)",
    )


def set_folder(settings: LocalSettings, run: "Setup", entry: str, yes: bool) -> None:
    """Saves a Claude folder's answer, in the entry that already names it when there is one."""
    found = entry_for(run, settings.claude_folders, resolve_home(entry, run.home))
    settings.claude_folders[found or entry] = yes


def change_claude_folders(run: "Setup", settings: LocalSettings) -> bool:
    answers = folder_answers(run, settings)
    if not answers:
        run.line("There are no ~/.claude-* folders to set up.")
        return False
    changed = False
    for entry, current in answers:
        folder = Path(resolve_home(entry, run.home))
        if not folder.is_dir():
            # A folder that's gone keeps its answer, in case it comes back, until it's removed.
            if run.choose(f"{folder} no longer exists. Remove it from the settings?", False):
                del settings.claude_folders[entry]
                changed = True
            continue
        answer = run.ask_claude_folder(folder, current)
        if answer != current:
            set_folder(settings, run, entry, answer)
            changed = True
    return changed


def change_copies(run: "Setup", settings: LocalSettings) -> bool:
    """Chooses dev-home.json's answer, which setup writes, commits, and pushes later in its run.
    Changes nothing in this PC's settings."""
    answer, found = copies_answer(settings)
    if found in ("unreadable", "unknown"):
        run.line(
            f"{DEV_HOME_SETTINGS} in dev-home {LAYOUT_NOTES[found]}, so setup leaves it alone."
        )
        return False
    current = answer if run.wanted_copies is None else run.wanted_copies
    several = run.ask_copies(current)
    if several is None or (several == current and found != "older"):
        return False
    if current is True and several is False:
        retired = run.choose(
            "Have all the other copies been retired, so this PC is the only one using dev-home?",
            False,
        )
        if not retired:
            run.line("dev-home stays set to several copies.")
            return False
    # An older file is rewritten even with the same answer, to give it a schemaVersion.
    run.wanted_copies = None if several == answer and found != "older" else several
    return False


# One setting, from an agent


def assign(run: "Setup", settings: LocalSettings, text: str) -> bool:
    """Makes one assignment, and shows the change to this PC's settings, if any. Raises
    SettingError for one it can't make."""
    match = ASSIGNMENT.fullmatch(text.strip())
    if match is None:
        raise SettingError(f"--configure takes one setting as <name>=<value>, not {text}.")
    name, operator, value = match.group(1), match.group(2), match.group(3).strip()
    if name not in NAMES and not name.startswith("skills."):
        raise SettingError(f"There is no setting named {name}.")
    if name == CLAUDE_FOLDERS and operator == "=":
        raise SettingError(
            f"{CLAUDE_FOLDERS} changes one folder at a time: {CLAUDE_FOLDERS}+=<folder> sets one "
            f"up, and {CLAUDE_FOLDERS}-=<folder> stops."
        )
    if name != CLAUDE_FOLDERS and operator != "=":
        raise SettingError(f"{name} is set with =, as in {name}=<value>.")
    before = copy.deepcopy(settings)
    if name in ("updates.installAutomatically", "multiMachine") or name.startswith("skills."):
        if value.lower() not in ("true", "false"):
            raise SettingError(f"{name} is true or false, not {value}.")
        yes = value.lower() == "true"
        if name == "updates.installAutomatically":
            settings.auto_update = yes
        elif name.startswith("skills."):
            put(settings.data, preference_path(settings, name), yes)
        else:
            answer, found = copies_answer(settings)
            if found in ("unreadable", "unknown"):
                raise SettingError(
                    f"{DEV_HOME_SETTINGS} in dev-home {LAYOUT_NOTES[found]}. The user fixes it by "
                    "hand."
                )
            if answer == yes and found != "older":
                status_line("OK", f"dev-home is already set to {'several' if yes else 'one'}.")
                return False
            run.wanted_copies = yes
            return False
    elif name in DEFAULT_HOURS:
        if not re.fullmatch(r"\d+", value):
            raise SettingError(f"{name} is a whole number of hours, 0 or more, not {value}.")
        put(settings.data, name, int(value))
    elif name == "devHome.folder":
        settings.content_dir = checked_dev_home(value)
    else:
        if not value:
            raise SettingError("Name the Claude Code folder, such as ~/.claude-second.")
        full = Path(resolve_home(value, run.home))
        if operator == "+=" and not full.is_dir():
            raise SettingError(f"There is no Claude Code folder at {full}.")
        set_folder(settings, run, value, operator == "+=")
    old_text, new_text = local_settings_text(before), local_settings_text(settings)
    if old_text == new_text:
        status_line("OK", f"{name} is already set that way, so nothing changed.")
        return False
    run.status("CHANGE", f"This PC's settings: {SETTINGS_PATH}")
    run.print_diff(old_text, new_text)
    return True


def preference_path(settings: LocalSettings, name: str) -> str:
    """The path of a preference a skill declares, named as skills.<skill>.<name>, spelled as
    the skill declares it. Raises SettingError for one no skill declares."""
    parts = name.split(".")
    if len(parts) != 3 or not all(parts):
        raise SettingError(f"A skill's preference is named skills.<skill>.<name>, not {name}.")
    preferences = skill_preferences(settings.content_dir)[0]
    skill = find_skill(preferences, parts[1])
    if skill is None:
        raise SettingError(f"No skill named {parts[1]} declares preferences.")
    if parts[2] not in preferences[skill]:
        declared = ", ".join(preferences[skill]) or "none"
        raise SettingError(
            f"The {skill} skill declares no preference named {parts[2]}. It declares: {declared}."
        )
    return f"skills.{skill}.{parts[2]}"


def checked_dev_home(value: str) -> str:
    """A folder for devHome.folder, which must already be a dev-home: cloning or creating one
    takes a person's answers at a console."""
    # Loaded here, since setup loads this module.
    from .setup import is_in_use, missing_dev_home_files

    folder = forward(value)
    reason = unsafe_reason(folder)
    if reason:
        raise SettingError(f"The folder {folder} {reason}, so commands would need it quoted.")
    if is_inside(folder, TOOLS_ROOT):
        raise SettingError(f"The folder {folder} is dev-home-tools' own folder, or inside it.")
    full = Path(comparable(folder))
    if not is_in_use(full) or missing_dev_home_files(full):
        raise SettingError(
            f"{folder} isn't a dev-home: devHome.folder can only be a folder that already is one, "
            "with global-rules/global-rules.md and knowledge/README.md. To clone or create one, "
            "the user runs setup.py in a terminal."
        )
    return folder
