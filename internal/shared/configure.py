"""setup.py --configure: changing a setting after the first run.

At a console, every run of setup shows a menu of every setting with its current value, after its
questions, --configure or not: a number changes one, a goes through them all, and Enter goes on
with setup's work. Each entry asks the question the first run asks, from setup's own steps, so a
setting is asked about, checked, and written one way.

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
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from .output import CYAN, GREEN, color, status_line
from .paths import comparable, forward, is_inside, resolve_home, same_path, unsafe_reason
from .settings import (
    AUTO_UPDATE,
    BY_PATH,
    CLAUDE_CODE,
    CODEX,
    DEFAULT_HOURS,
    DEV_HOME_SETTINGS,
    FOLDER_SETTINGS,
    MISSING,
    SETTINGS,
    SETTINGS_PATH,
    STATE,
    TOOLS,
    TOOLS_ROOT,
    LocalSettings,
    Setting,
    Tool,
    find_skill,
    folder_rank,
    get,
    local_settings_text,
    put,
    read_dev_home_settings,
    read_value,
    setting_value,
    skill_preferences,
    value_text,
)

if TYPE_CHECKING:
    from .setup import Setup

NAMES = (*(setting.path for setting in SETTINGS), *FOLDER_SETTINGS, "multiMachine")
# Each tool by the name of its folders' setting.
TOOL_FOR = {tool.setting: tool for tool in TOOLS}
# A name is a path, which may hold dots and, in a skill's name, hyphens. The shortest name that
# leaves an operator after it, so claudeCode.folders-=<folder> reads as -=.
ASSIGNMENT = re.compile(r"([A-Za-z][\w.-]*?)(\+=|-=|=)(.*)", re.DOTALL)
# What each type of setting takes, as USAGE shows it.
PLACEHOLDERS = {"folder": "<folder>", "hours": "<hours>", "yes-no": "true|false"}
USAGE_COLUMN = 36
USAGE_WIDTH = 100


def usage_entry(name: str, text: str) -> list[str]:
    """One entry of USAGE: the assignment, then what it does beside it, or below it when the
    assignment is too long."""
    wrapped = textwrap.wrap(text, USAGE_WIDTH - USAGE_COLUMN)
    first = f"  {name}"
    if len(first) <= USAGE_COLUMN - 2:
        lines = [first.ljust(USAGE_COLUMN) + wrapped[0]]
        wrapped = wrapped[1:]
    else:
        lines = [first]
    return lines + [" " * USAGE_COLUMN + line for line in wrapped]


def usage() -> str:
    """How to change one setting, with every setting's name; the help of dev-home-tools' own comes
    from setting-definitions.json."""
    entries = [
        (f"{setting.path}={PLACEHOLDERS[setting.type]}", setting.help) for setting in SETTINGS
    ]
    for tool in TOOLS:
        shared = (
            f" Every {tool.name} {tool.folder} reads the same skills, so all of them share one "
            f"answer: a change to the main one, ~/{tool.default} when it's there, changes them all."
            if tool.shared
            else ""
        )
        entries += [
            (
                f"{tool.setting}+=<folder>",
                f"Set up a {tool.name} {tool.folder}, such as ~/{tool.default} or "
                f"~/{tool.default}-second.{shared}",
            ),
            (f"{tool.setting}-=<folder>", "Stop setting one up."),
        ]
    entries += [
        ("skills.<skill>.preferences.<name>=true|false", "A preference a skill declares."),
        (
            "multiMachine=true|false",
            "Whether dev-home is in active use anywhere besides this PC. Every copy shares it, so "
            "setup commits and pushes the change.",
        ),
    ]
    lines = [
        "To change one setting, as an agent does, run setup.py --configure '<name>=<value>', in",
        "single quotes, which every shell passes on as they are. A name is the setting's path in",
        "local-settings.json:",
        "",
    ]
    for name, text in entries:
        lines += usage_entry(name, text)
    lines += [
        "",
        "A setting with a default also takes default, such as updates.checkEveryHours=default, to",
        "follow its default again. Add --what-if to see the change without making it. In a",
        "terminal, --configure alone shows a menu of every setting instead.",
    ]
    return "\n".join(lines)


USAGE = usage()
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
    run.just_showing. At a console, setup shows the menu later in its run, as every run by hand
    does."""
    if run.assigned:
        return assign(run, settings, run.configure or "")
    if run.can_ask:
        return False
    for line in overview(run, settings) + preferences_overview(settings):
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


def setting_text(settings: LocalSettings, path: str) -> str:
    """One of dev-home-tools' own settings as the menu shows it (see value_shown)."""
    return value_shown(BY_PATH[path], get(settings.data, path, MISSING))


def value_shown(setting: Setting, saved: object) -> str:
    """A setting's value as the menu shows it: its value, and whether that's the default, isn't
    answered yet, or is a value the file has that setup can't use."""
    value, answered, usable = read_value(saved, setting)
    if not setting.has_default:
        shown = "not set yet" if value is None else value_text(setting, value)
    elif setting.asked and not answered:
        shown = f"not answered yet, so {value_text(setting, value)}"
    elif saved is MISSING or isinstance(saved, dict):
        shown = f"{value_text(setting, value)} (the default)"
    else:
        shown = value_text(setting, value)
    if not usable:
        shown += f" (the file says {json.dumps(saved)}, which setup can't use)"
    return shown


def folder_answers(
    run: "Setup", settings: LocalSettings, tool: Tool
) -> list[tuple[str, bool | None]]:
    """Each of a tool's folders setup knows of, as written in the settings, with its answer: each
    one there (see known_folders), then any other folder with an answer."""
    saved = settings.folders[tool.setting]
    answers: list[tuple[str, bool | None]] = []
    for folder in run.known_folders(tool, settings):
        entry = run.entry_named(folder, saved)
        answers.append((entry or run.folder_entry(folder), None if entry is None else saved[entry]))
    for entry, answer in saved.items():
        full = resolve_home(entry, run.home)
        if not any(same_path(full, resolve_home(name, run.home)) for name, _ in answers):
            answers.append((entry, answer))
    return answers


def folders_text(run: "Setup", settings: LocalSettings, tool: Tool) -> str:
    """A tool's folders as the menu shows them, each with its answer."""
    words = {True: "yes", False: "no", None: "not asked yet"}
    folders = ", ".join(
        f"{name}: {words[answer]}"
        + ("" if Path(resolve_home(name, run.home)).is_dir() else " (not found)")
        for name, answer in folder_answers(run, settings, tool)
    )
    return folders or "none found"


def overview(run: "Setup", settings: LocalSettings) -> list[str]:
    """Every setting and its value, numbered as the menu numbers them."""
    answer, found = copies_answer(settings)
    if run.wanted_copies is not None:
        copies = "several" if run.wanted_copies else "one"
    elif found in LAYOUT_NOTES:
        copies = f"{DEV_HOME_SETTINGS} {LAYOUT_NOTES[found]}"
    elif answer is None:
        copies = "not answered yet, so each sync checks GitHub"
    else:
        copies = "several" if answer else "one"
    # The dev-home folder shows what this run will use, which --content-dir can change.
    values = {"devHome.folder": settings.content_dir or "not set yet"}
    this_pc = [
        (setting.label, values.get(setting.path) or setting_text(settings, setting.path))
        for setting in SETTINGS
    ]
    this_pc += [
        (f"{tool.name} {tool.folder}s to set up", folders_text(run, settings, tool))
        for tool in TOOLS
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


def preferences_overview(settings: LocalSettings) -> list[str]:
    """Each preference the skills declare, for an agent: its label and skill, its value, and the
    name --configure changes it by, so a skill can name a preference by its label alone."""
    lines: list[str] = []
    for skill, declared in skill_preferences(settings.content_dir).preferences.items():
        for preference in declared.values():
            setting = preference.setting
            shown = value_shown(setting, get(settings.data, setting.path, MISSING))
            lines.append(
                f"  {preference.label} ({skill} skill): {shown}. To change it: "
                f"{setting.path}=true|false|default"
            )
    return ["", color("Skill preferences", CYAN), *lines] if lines else []


# The menu


def menu(run: "Setup", settings: LocalSettings) -> bool:
    """Shows every setting, and changes the ones the person picks, until Enter, after which setup
    goes on. Returns whether this PC's settings changed."""
    changers: dict[str, Callable[[Setup, LocalSettings], bool]] = {
        "devHome.folder": change_content_dir,
        AUTO_UPDATE: change_auto_update,
        "updates.checkEveryHours": change_update_hours,
        "devHome.checkEveryHours": change_content_hours,
    }
    # Numbered as overview numbers the rows: dev-home-tools' own settings in the order
    # setting-definitions.json has them, then each tool's folders, then the shared setting.
    order = [changers[setting.path] for setting in SETTINGS]
    order += [change_claude_folders, change_codex_homes, change_copies]
    steps = {str(number): step for number, step in enumerate(order, 1)}
    changed = False
    while True:
        run.line()
        for line in overview(run, settings):
            run.line(line)
        run.line()
        choice = run.ask("Number to change, a to go through them all, or Enter to go on")
        if not choice:
            return changed
        picked = list(steps) if choice.strip().lower() == "a" else [choice.strip()]
        if not all(number in steps for number in picked):
            run.line(f"Type a number from 1 to {len(steps)}, or a, or press Enter to go on.")
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


def keeps(settings: LocalSettings, path: str, answer: object) -> bool:
    """Whether an answer leaves a setting as it's saved: the same plain value, or, for a setting
    that follows its default, its current value, so Enter never pins a default. A setting with no
    answer yet gets one."""
    current, answered, usable = setting_value(settings.data, path)
    saved = get(settings.data, path, MISSING)
    if saved == answer and not isinstance(saved, dict):
        return True
    follows = usable and answered and isinstance(saved, dict)
    no_answer_needed = usable and saved is MISSING and not BY_PATH[path].asked
    return (follows or no_answer_needed) and answer == current


def change_auto_update(run: "Setup", settings: LocalSettings) -> bool:
    answer = run.ask_auto_update(settings.data)
    saved = get(settings.data, AUTO_UPDATE, MISSING)
    # By type too, since 1 == True: a value of the wrong kind is replaced by the answer.
    if answer is MISSING or (type(answer) is type(saved) and answer == saved):
        return False
    put(settings.data, AUTO_UPDATE, answer)
    return True


def change_hours(run: "Setup", settings: LocalSettings, path: str, question: str) -> bool:
    current = setting_value(settings.data, path)[0]
    while True:
        answer = run.ask(question, str(current))
        if answer is None:
            return False
        if re.fullmatch(r"\d+", answer):
            break
        run.line("Type a whole number of hours: 0 or more.")
    hours = int(answer)
    if keeps(settings, path, hours):
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


def set_folder(settings: LocalSettings, run: "Setup", tool: Tool, full: Path, yes: bool) -> None:
    """Saves the answer for one of a tool's folders, by its full path, in the entry that already
    names it when there is one, and otherwise in a new one, written as setup writes folders."""
    settings.folders[tool.setting][run.entry_for(tool, settings, full)] = yes


def set_shared(settings: LocalSettings, run: "Setup", tool: Tool, full: Path, yes: bool) -> None:
    """Saves the answer for one of a shared tool's folders, by its full path. For the main
    folder, or while no folder has an answer, it goes to every folder. For another folder, it must
    match the answer they share: one that doesn't is refused, raising SettingError, since every
    folder reads the same skills."""
    folders = run.known_folders(tool, settings)
    if full.is_dir() and not any(same_path(full, folder) for folder in folders):
        folders = sorted([*folders, full], key=lambda f: folder_rank(tool, f, run.home))
    answer, _ = run.shared_answer(tool, settings, folders)
    if answer is None or (folders and same_path(full, folders[0])):
        run.answer_every_folder(tool, settings, yes)
        set_folder(settings, run, tool, full, yes)
    elif answer is yes:
        set_folder(settings, run, tool, full, yes)
    else:
        main = run.entry_named(folders[0], settings.folders[tool.setting]) or run.folder_entry(
            folders[0]
        )
        done = "set up" if answer else "not set up"
        operator = "-=" if yes is False else "+="
        raise SettingError(
            f"Every {tool.name} {tool.folder} reads the same skills, so all of them share one "
            f"answer, the main {tool.folder}'s: {main}, which is {done}. To change them all, "
            f"change it: {tool.setting}{operator}{main}."
        )


def change_folders(run: "Setup", settings: LocalSettings, tool: Tool) -> bool:
    """Asks about each of a tool's folders, after offering to remove each one that's gone; for a
    shared tool, one question, whose answer goes to every folder."""
    answers = folder_answers(run, settings, tool)
    if not answers:
        run.line(f"Setup found no {tool.name} {tool.folder}s.")
        return False
    changed = False
    explained = False
    for entry, current in answers:
        folder = Path(resolve_home(entry, run.home))
        if not folder.is_dir():
            # A folder that's gone keeps its answer, in case it comes back, until it's removed.
            if run.choose(f"{folder} no longer exists. Remove it from the settings?", False):
                settings.folders[tool.setting].pop(entry, None)
                changed = True
            continue
        if tool.shared:
            continue
        if not explained:
            present = [Path(resolve_home(name, run.home)) for name, _ in answers]
            run.introduce_folders(tool, [f for f in present if f.is_dir()])
            explained = True
        answer = run.ask_folder(tool, folder, current)
        if answer is not None and answer != current:
            set_folder(settings, run, tool, Path(comparable(folder)), answer)
            changed = True
    folders = run.known_folders(tool, settings)
    if not tool.shared or not folders:
        return changed
    current, _ = run.shared_answer(tool, settings, folders)
    answer = run.ask_codex(folders, current)
    saved = settings.folders[tool.setting].values()
    if answer is None or (answer is current and all(value is answer for value in saved)):
        return changed
    run.answer_every_folder(tool, settings, answer)
    return True


def change_claude_folders(run: "Setup", settings: LocalSettings) -> bool:
    return change_folders(run, settings, CLAUDE_CODE)


def change_codex_homes(run: "Setup", settings: LocalSettings) -> bool:
    return change_folders(run, settings, CODEX)


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
    tool = TOOL_FOR.get(name)
    if tool is not None and operator == "=":
        raise SettingError(
            f"{name} changes one {tool.folder} at a time: {name}+=<folder> sets one up, and "
            f"{name}-=<folder> stops."
        )
    if tool is None and operator != "=":
        raise SettingError(f"{name} is set with =, as in {name}=<value>.")
    before = copy.deepcopy(settings)
    if value == "default" and tool is None:
        setting = None if name == "multiMachine" else declared_setting(settings, name)
        if setting is None or not setting.has_default:
            raise SettingError(f"{name} has no default, so it can't be set to default.")
        put(settings.data, setting.path, {STATE: "default"})
    elif name in (AUTO_UPDATE, "multiMachine") or name.startswith("skills."):
        if value.lower() not in ("true", "false"):
            raise SettingError(f"{name} is true or false, not {value}.")
        yes = value.lower() == "true"
        if name == AUTO_UPDATE:
            put(settings.data, name, yes)
        elif name.startswith("skills."):
            put(settings.data, declared_setting(settings, name).path, yes)
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
        assert tool is not None
        kind = f"{tool.name} {tool.folder}"
        if not value:
            raise SettingError(f"Name the {kind}, such as ~/{tool.default}-second.")
        # A folder as typed, such as ..\.claude-second, means one from where the command runs.
        full = Path(comparable(resolve_home(value, run.home)))
        if operator == "+=" and not full.is_dir():
            raise SettingError(f"There is no {kind} at {full}.")
        if tool.shared:
            set_shared(settings, run, tool, full, operator == "+=")
        else:
            set_folder(settings, run, tool, full, operator == "+=")
    old_text, new_text = local_settings_text(before), local_settings_text(settings)
    if old_text == new_text:
        status_line("OK", f"{name} is already set that way, so nothing changed.")
        return False
    run.status("CHANGE", f"This PC's settings: {SETTINGS_PATH}")
    run.print_diff(old_text, new_text)
    return True


def declared_setting(settings: LocalSettings, name: str) -> Setting:
    """One of dev-home-tools' own settings, or a skill's preference, named as
    skills.<skill>.preferences.<name>, with its path spelled as the skill declares it. Raises
    SettingError for a preference no skill declares."""
    if not name.startswith("skills."):
        return BY_PATH[name]
    parts = name.split(".")
    if len(parts) != 4 or parts[2] != "preferences" or not all(parts):
        raise SettingError(
            f"A skill's preference is named skills.<skill>.preferences.<name>, not {name}."
        )
    preferences = skill_preferences(settings.content_dir).preferences
    skill = find_skill(preferences, parts[1])
    if skill is None:
        raise SettingError(f"No skill named {parts[1]} declares preferences.")
    if parts[3] not in preferences[skill]:
        declared = ", ".join(preferences[skill]) or "none"
        raise SettingError(
            f"The {skill} skill declares no preference named {parts[3]}. It declares: {declared}."
        )
    return preferences[skill][parts[3]].setting


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
