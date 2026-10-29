"""setup.py --configure: changing a setting after the first run.

At a console, every run of setup shows a menu of every setting with its current value, after its
questions, --configure or not: a number changes one, a goes through them all, and Enter goes on
with setup's work. Each entry asks the question the first run asks, from setup's own steps, so a
setting is asked about, checked, and written one way.

An agent can't answer at a console, so it gives one setting instead, as <name>=<value>, such as
updates.installAutomatically=true, which its user approved in chat; nothing is asked. A setting's
name is its path in local-settings.json. With neither a console nor a setting, it shows what waits
for a person's answer, then the settings and how to change them.

What waits is what setup's questions at a console ask about files: a file setup set aside in this
PC's unanswered/ folders, and a hand edit to dev-home's AGENTS.md or CLAUDE.md. For each, the
listing shows what it holds, the answers, and the command that gives one, named by the file's path
in dev-home, as <path>=<answer>@<fingerprint>. The fingerprint is of the file as the listing shows
it, so setup acts on an answer only while the file is still what the person saw. The person's
answer is the go-ahead, so an agent runs it with no preview, and the work acts on it as on an
answer at a console (see Setup.answer_question).

This PC's settings go in local-settings.json, which setup saves with a dated backup. dev-home's
own setting, how many copies are in active use, goes in dev-home.json, which setup writes later in
its run, then commits and pushes, once dev-home's git config is in place.
"""

import copy
import hashlib
import json
import re
import textwrap
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from . import console, rules
from .output import CYAN, GREEN, color, status_line
from .paths import comparable, forward, is_inside, resolve_home, same_path, unsafe_reason
from .recommended_settings import DONE, ids_for
from .settings import (
    ADDED_TO_AGENTS,
    AGENTS,
    AUTO_UPDATE,
    BY_PATH,
    CLAUDE_CODE,
    CODEX,
    CODEX_INSTRUCTIONS_MAX,
    DEV_HOME_SETTINGS,
    FOLDER_SETTINGS,
    MISSING,
    RECOMMENDED_ANSWERS,
    RULES_WARN_ABOVE,
    SETTINGS,
    SETTINGS_PATH,
    STATE,
    TOOLKIT_ROOT,
    TYPE_TEXT,
    UNITS,
    Agent,
    LocalSettings,
    Reminder,
    Setting,
    find_skill,
    folder_rank,
    get,
    local_settings_text,
    put,
    put_recommended,
    read_dev_home_settings,
    read_value,
    remove_folder_entry,
    setting_value,
    skill_declarations,
    value_text,
)

if TYPE_CHECKING:
    from .setup import Guidance, RecommendedOffer, Setup, Waiting, WaitingFile

NAMES = (*(setting.path for setting in SETTINGS), *FOLDER_SETTINGS, "multiMachine")
# The name of the answers to the recommended settings in a Claude Code folder, as --configure
# takes them, followed by a setting's id for one alone (decision 0032).
RECOMMENDED_NAME = f"{CLAUDE_CODE.group}.{RECOMMENDED_ANSWERS}"
# How the list for an agent marks each recommended setting, where only some are recommended in a
# folder: one where a yes is recommended, and one with a value someone chose, which a no keeps.
CHAT_MARKS = ("recommended", "your own value, which all recommended keeps")
# Each agent by the name of its folders' setting.
AGENT_FOR = {agent.setting: agent for agent in AGENTS}
# A name is a setting's path, which may hold dots and, in a skill's name, hyphens, or the path in
# dev-home of a file setup waits on an answer about, with slashes. The shortest name that leaves an
# operator after it, so claudeCode.folders-=<folder> reads as -=.
ASSIGNMENT = re.compile(r"([A-Za-z][\w./-]*?)(\+=|-=|\?=|=)(.*)", re.DOTALL)
# What each type of setting takes, as USAGE shows it.
PLACEHOLDERS = {"folder": "<folder>", "hours": "<hours>", "kib": "<KiB>", "yes-no": "true|false"}
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


def reminder_help(agent: Agent) -> str:
    """What a reminder about one of an agent's folders does, as USAGE says."""
    if agent.shared:
        return (
            f"Ask again in that many days whether to set up {agent.name}, while it has no answer "
            f"yet, for every {agent.name} {agent.folder}. Until then, setup leaves them as they "
            "are, and syncs don't mention them."
        )
    return (
        f"Ask again in that many days whether to set up a {agent.folder} with no answer yet. "
        "Until then, setup leaves it as it is, and syncs don't mention it."
    )


def usage() -> str:
    """How to change one setting, with every setting's name; the help of dev-home-toolkit's own
    comes from setting-definitions.json."""
    entries = [
        (f"{setting.path}={PLACEHOLDERS[setting.type]}", setting.help) for setting in SETTINGS
    ]
    for agent in AGENTS:
        shared = (
            f" Every {agent.name} {agent.folder} reads the same skills, so all of them share one "
            f"answer: a change to the main one, ~/{agent.default} when it's there, changes them "
            "all."
            if agent.shared
            else ""
        )
        entries += [
            (
                f"{agent.setting}+=<folder>",
                f"Set up a {agent.name} {agent.folder}, such as ~/{agent.default} or "
                f"~/{agent.default}-second.{shared}",
            ),
            (
                f"{agent.setting}-=<folder>",
                "Stop setting one up, and remove what setup set up there.",
            ),
            (f"{agent.setting}?=<folder>@<days>", reminder_help(agent)),
        ]
    entries += [
        (
            f"{RECOMMENDED_NAME}.<id>+=<folder>@<fingerprint>",
            "Yes to a setting dev-home-toolkit recommends, in a Claude Code folder set up: setup "
            "writes it in the folder's settings.json. The listing gives the fingerprint, which "
            "makes setup write it only while the value is still what the user saw.",
        ),
        (
            f"{RECOMMENDED_NAME}.<id>-=<folder>",
            "No to it. Setup leaves the setting as it is in settings.json, and doesn't ask again. "
            "To change the setting itself, the user changes it in Claude Code's /config.",
        ),
        (
            f"{RECOMMENDED_NAME}.<id>?=<folder>@<days>",
            "Ask again in that many days, while it has no answer yet. Until then, syncs don't "
            "mention it.",
        ),
        (
            f"{RECOMMENDED_NAME}+=<folder>@<fingerprint>",
            "Every recommended setting waiting for an answer in that folder: yes to each one the "
            "listing marks recommended, and no to the others. -=<folder> says no to each, and "
            "?=<folder>@<days> asks again about each in that many days.",
        ),
        (
            f"skills.<skill>.{ADDED_TO_AGENTS}=true|false",
            "Whether to add a skill to your agents on this PC.",
        ),
        ("skills.<skill>.preferences.<name>=true|false", "A preference a skill declares."),
        (
            "multiMachine=true|false",
            "Whether dev-home is in active use anywhere besides this PC: true for multi-PC mode, "
            "false for single-PC mode. Every copy shares it, so setup commits and pushes the "
            "change.",
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
    "unknown": "has a schemaVersion this dev-home-toolkit doesn't know",
}


class SettingError(Exception):
    """An assignment --configure can't make, and why."""


class AnswerError(SettingError):
    """An answer to a question setup waits on that --configure can't take, and why. The listing
    says how to answer, so the settings' usage doesn't follow it."""


def change_settings(run: "Setup", settings: LocalSettings) -> None:
    """Makes --configure's change to this PC's settings, or chooses dev-home.json's answer, which
    setup writes later in its run. With nobody to answer and no setting given, shows the settings
    and how to change them, and sets run.just_showing. At a console, setup shows the menu later in
    its run, as every run by hand does."""
    if run.assigned:
        assign(run, settings, run.configure or "")
    elif not run.can_ask:
        show_waiting(run, settings)
        shown = overview(run, settings) + recommended_overview(run, settings)
        for line in shown + skills_overview(settings):
            run.line(line)
        run.line()
        run.line(USAGE)
        run.just_showing = True


# What waits for an answer

# How an agent asks about what waits, which the listing says before the first item.
WAITING_INTRO = (
    "Ask the user about each item, one at a time: show its text; for rules, say which of its "
    "lines are already in the rules this session loaded; recommend an answer, and say what it "
    "does. The "
    "go-ahead is the user's pick of exactly one answer the item lists, or that a PROBLEM line "
    "about it offers: run that command, and pass on what setup prints. Run nothing for any other "
    "reply: ask again, or, for not now, leave the item waiting. After a PROBLEM line or a "
    "refusal, show the user what it says, run --configure again if it says the item changed, and "
    "ask again."
)


def fingerprint(data: bytes) -> str:
    """What --configure shows with something that waits for an answer, and takes back with the
    answer, so setup acts on the answer only while that's still what the person saw: the first 12
    hex digits of its SHA-256, as a skill's stamp is."""
    return hashlib.sha256(data).hexdigest()[:12]


def wrapped(run: "Setup", text: str, indent: str = "") -> None:
    """Text as lines of USAGE's width, each set in by indent, broken only at spaces, so a path
    stays whole however long it is."""
    for line in textwrap.wrap(
        text,
        USAGE_WIDTH,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    ):
        run.line(line)


def answer_rows(run: "Setup", rows: list[tuple[str, str]]) -> None:
    """Each answer an item takes, with what it does beside it."""
    width = max(len(answer) for answer, _ in rows) + 2
    for answer, does in rows:
        run.line(f"    {answer:<{width}}{does}")


def show_waiting(run: "Setup", settings: LocalSettings) -> None:
    """For an agent, before the settings: what waits for a person's answer (see Setup.waiting,
    and Setup.recommended_offers), each item with what it is, its answers, and the command that
    gives one, after a paragraph on how to ask. Nothing while nothing waits."""
    waiting = run.waiting(settings)
    recommended = run.recommended_offers(settings)
    if not (recommended or (waiting is not None and (waiting.files or waiting.guidance))):
        return
    run.line(color("Waiting for your answer", CYAN))
    run.line()
    wrapped(run, WAITING_INTRO)
    if waiting is not None:
        for file in waiting.files:
            show_waiting_file(run, waiting, file)
        for found in waiting.guidance:
            show_waiting_guidance(run, waiting, found)
    for entry, folder, offers in recommended:
        show_waiting_recommended(run, entry, folder, offers)
    run.line()


def recommended_command(offer: "RecommendedOffer") -> str:
    """The command that gives a yes to one recommended setting in its folder, through
    --configure."""
    return f"--configure '{RECOMMENDED_NAME}.{offer.setting.id}+={offer.entry}@{offer.fingerprint}'"


def batch_fingerprint(offers: Sequence["RecommendedOffer"]) -> str:
    """What an answer to every recommended setting waiting in a folder carries, as one setting's
    fingerprint does, so setup takes it only while they're the same ones, with what the person
    saw."""
    seen = "\n".join(f"{offer.setting.id}={offer.current.described}" for offer in offers)
    return fingerprint(seen.encode("utf-8"))


def show_waiting_recommended(
    run: "Setup", entry: str, folder: Path, offers: Sequence["RecommendedOffer"]
) -> None:
    """The recommended settings waiting for an answer in one Claude Code folder, as the listing
    shows them: each as setup's question shows it, with its command for a yes, then the commands
    for all of them at once, and how to answer one by its id."""
    run.line()
    run.line(f"Recommended settings for Claude Code in {entry}")
    wrapped(
        run,
        "Settings dev-home-toolkit recommends there, with no answer yet. Until the user answers, "
        f"setup leaves them as they are. A yes is written in {folder / 'settings.json'}.",
        "  ",
    )
    run.line()
    items = [
        console.ListItem(offer.setting.summary, offer.recommended, offer.question, offer.about)
        for offer in offers
    ]
    for offer, item in zip(offers, items, strict=True):
        # Each marked, since the answers say what they do by the marks.
        console.show_items([item], CHAT_MARKS, among=items, mark_each=True)
        run.line(f"      {'Yes:':<14}{recommended_command(offer)}")
        run.line()
    run.line("  Answers, for all of them at once:")
    rows = [
        (
            "all recommended",
            f"--configure '{RECOMMENDED_NAME}+={entry}@{batch_fingerprint(offers)}' (yes to "
            "each marked recommended, and no to the others)",
        ),
        ("none", f"--configure '{RECOMMENDED_NAME}-={entry}'"),
        ("remind me in N days", f"--configure '{RECOMMENDED_NAME}?={entry}@<days>'"),
    ]
    # All is the same as all recommended when every one is recommended.
    if not all(offer.recommended for offer in offers):
        rows.insert(0, ("all", "each Yes command above, one after another"))
    answer_rows(run, rows)
    wrapped(
        run,
        "Or each one, by the id in its Yes command: no is "
        f"--configure '{RECOMMENDED_NAME}.<id>-={entry}', and remind me in N days is "
        f"--configure '{RECOMMENDED_NAME}.<id>?={entry}@<days>'.",
        "  ",
    )


def show_waiting_file(run: "Setup", waiting: "Waiting", file: "WaitingFile") -> None:
    """A file setup set aside in unanswered/, as the listing shows it."""
    # Loaded here, since setup loads this module.
    from .setup import level_choices, relative

    name = relative(waiting.content_root, file.path)
    if file.loads is not None:
        loads = "they load only there."
    elif file.source:
        loads = "they load nowhere, since setup doesn't write that file now."
    else:
        loads = "they load nowhere."
    source = f" from {file.source}" if file.source else ""
    run.line()
    run.line(name)
    wrapped(run, f"Rules setup set aside{source}. Until the user says where they go, {loads}", "  ")
    run.line()
    for line in file.text.split("\n"):
        run.line(f"      {line}" if line else "")
    run.line()
    run.line("  Answers, each committed and pushed in dev-home:")
    rows = [
        (level, f"into rules/{level}/{rules.MINE}/: {label}")
        for level, label in level_choices(file.agent, waiting.pc)
    ]
    answer_rows(run, [*rows, ("drop", "to the Recycle Bin")])
    run.line(f"  Command: --configure '{name}=<answer>@{fingerprint(file.current)}'")


def show_waiting_guidance(run: "Setup", waiting: "Waiting", found: "Guidance") -> None:
    """A hand edit to dev-home's AGENTS.md or CLAUDE.md, as the listing shows it."""
    current = found.current or b""
    against = "what setup last wrote" if found.kept is not None else "what setup writes now"
    run.line()
    run.line(found.name)
    wrapped(
        run,
        f"dev-home's {found.name} has edits setup didn't make. Each sync sends such edits to the "
        "Recycle Bin and puts back setup's file, but leaves the file as edited while the bin "
        "can't take them. Guidance for every session goes in the user's rules, in "
        f"{waiting.content_root / rules.RULES}. The edits, against {against}:",
        "  ",
    )
    run.line()
    run.print_diff(
        found.before.decode("utf-8", errors="replace"),
        current.decode("utf-8", errors="replace"),
        " " * 6,
    )
    run.line()
    run.line("  Answer:")
    answer_rows(run, [("delete", "deletes the edits for good, and puts back setup's file")])
    wrapped(
        run,
        "With no answer, each sync tries the bin again, and names the file while the bin can't "
        "take the edits.",
        "  ",
    )
    run.line(f"  Command: --configure '{found.name}=delete@{fingerprint(current)}'")


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
    """One of dev-home-toolkit's own settings as the menu shows it (see value_shown)."""
    return value_shown(BY_PATH[path], get(settings.data, path, MISSING))


def value_shown(setting: Setting, saved: object, default_note: str = "the default") -> str:
    """A setting's value as the menu shows it: its value, and whether that's the default, isn't
    answered yet, or is a value the file has that setup can't use. default_note marks the
    default."""
    value, answered, usable = read_value(saved, setting)
    if not setting.has_default:
        shown = "not set yet" if value is None else value_text(setting, value)
    elif setting.asked and not answered:
        shown = f"not answered yet (defaults to {value_text(setting, value)})"
    elif saved is MISSING or isinstance(saved, dict):
        shown = f"{value_text(setting, value)} ({default_note})"
    else:
        shown = value_text(setting, value)
    if not usable:
        shown += f" (the file says {json.dumps(saved)}, which setup can't use)"
    return shown


def folder_answers(
    run: "Setup", settings: LocalSettings, agent: Agent
) -> list[tuple[str, bool | Reminder | None]]:
    """Each of an agent's folders setup knows of, as written in the settings, with its answer, a
    reminder included: each one there (see known_folders), and any other folder with an answer,
    such as one that's gone, all in order (see folder_rank)."""
    saved: dict[str, bool | Reminder] = {**settings.folders[agent.setting]}
    saved.update(run.reminders(agent, settings))
    answers: list[tuple[str, bool | Reminder | None]] = []
    for folder in run.known_folders(agent, settings):
        entry = run.entry_named(folder, saved)
        answers.append((entry or run.folder_entry(folder), None if entry is None else saved[entry]))
    for entry, answer in saved.items():
        full = resolve_home(entry, run.home)
        if not any(same_path(full, resolve_home(name, run.home)) for name, _ in answers):
            answers.append((entry, answer))
    return sorted(answers, key=lambda pair: folder_rank(agent, pair[0], run.home))


def answer_text(answer: bool | Reminder | None) -> str:
    """A folder's answer as the menu shows it."""
    if isinstance(answer, Reminder):
        return f"remind me on {answer.on.isoformat()}" if answer.on else "remind me"
    return {True: "yes", False: "no", None: "no answer yet"}[answer]


def folders_text(run: "Setup", settings: LocalSettings, agent: Agent) -> str:
    """An agent's folders as the menu shows them, each with its answer."""
    folders = ", ".join(
        f"{name}: {answer_text(answer)}"
        + ("" if Path(resolve_home(name, run.home)).is_dir() else " (not found)")
        for name, answer in folder_answers(run, settings, agent)
    )
    return folders or "none found"


def several_copies(run: "Setup", settings: LocalSettings) -> tuple[bool | None, str]:
    """Whether dev-home is in multi-PC mode, as this run leaves it: the answer it's about to save,
    or else dev-home.json's, with None for no answer setup can use; and that file's layout (see
    copies_answer), or "" for an answer this run is about to save."""
    if run.wanted_copies is not None:
        return run.wanted_copies, ""
    answer, found = copies_answer(settings)
    return (None if found in LAYOUT_NOTES else answer), found


def content_hours_text(settings: LocalSettings, several: bool | None, found: str) -> str:
    """devHome.checkEveryHours as the menu shows it. Only single-PC mode uses it: otherwise each
    sync checks GitHub every time."""
    if several is False:
        setting = BY_PATH["devHome.checkEveryHours"]
        saved = get(settings.data, setting.path, MISSING)
        return value_shown(setting, saved, "the default in single-PC mode")
    if several:
        return "every time (fixed in multi-PC mode)"
    if found in LAYOUT_NOTES:
        return f"every time, while {DEV_HOME_SETTINGS} can't be used"
    return "every time (until you choose a mode)"


def overview(run: "Setup", settings: LocalSettings) -> list[str]:
    """Every setting and its value, numbered as the menu numbers them."""
    several, found = several_copies(run, settings)
    if found in LAYOUT_NOTES:
        copies = f"{DEV_HOME_SETTINGS} {LAYOUT_NOTES[found]}"
    elif several is None:
        copies = "not answered yet (until then, each sync checks GitHub)"
    else:
        copies = "several (multi-PC mode)" if several else "one (single-PC mode)"
    values = {
        # The dev-home folder shows what this run will use, which --content-dir can change.
        "devHome.folder": settings.content_dir or "not set yet",
        "devHome.checkEveryHours": content_hours_text(settings, several, found),
    }
    this_pc = [
        (setting.label, values.get(setting.path) or setting_text(settings, setting.path))
        for setting in SETTINGS
    ]
    this_pc += [
        (f"{agent.name} {agent.folder}s to set up", folders_text(run, settings, agent))
        for agent in AGENTS
    ]
    this_pc.append((RECOMMENDED_LABEL, recommended_summary(run, settings)))
    shared = [("Copies of dev-home in active use", copies)]
    width = max(len(label) for label, _ in this_pc + shared) + 2
    # The numbers' column, wide enough for the last, with at least two spaces after one digit.
    numbers = max(len(str(len(this_pc) + len(shared))), 2) + 1

    def row(number: int, label: str, value: str) -> str:
        # A value in parts, one for each folder, puts each after the first on a line of its own,
        # under the first, each but the last ending with a semicolon.
        gap = " " * (numbers - len(str(number)))
        under = ";\n" + " " * (2 + numbers + width)
        return f"  {color(str(number), GREEN)}{gap}{label:<{width}}{under.join(value.split(NEXT))}"

    lines = [color("dev-home-toolkit settings", CYAN), "", color("This PC", CYAN)]
    lines += [row(number, label, value) for number, (label, value) in enumerate(this_pc, 1)]
    lines += ["", color("Shared by every copy of dev-home", CYAN)]
    lines += [row(len(this_pc) + 1, label, value) for label, value in shared]
    return lines


# The menu's row for the recommended settings, and what separates its value's parts, one for each
# Claude Code folder set up, which the menu puts each on a line of its own.
RECOMMENDED_LABEL = f"Recommended {CLAUDE_CODE.name} settings"
NEXT = "\n"


def recommended_counts(offers: Sequence["RecommendedOffer"]) -> str:
    """One folder's answers to its recommended settings, counted, as the menu's row shows them,
    such as "3 yes (1 changed since), 1 no"."""
    yes = sum(1 for offer in offers if offer.answer is True)
    changed = sum(
        1 for offer in offers if offer.answer is True and not offer.pending and offer.state != DONE
    )
    counts = [
        f"{yes} yes" + (f" ({changed} changed since)" if changed else "") if yes else "",
        f"{sum(1 for offer in offers if offer.answer is False)} no",
        f"{sum(1 for offer in offers if isinstance(offer.answer, Reminder))} remind me",
        f"{sum(1 for o in offers if o.answer is None and o.state != DONE)} not answered yet",
        f"{sum(1 for o in offers if o.answer is None and o.state == DONE)} already set",
    ]
    return ", ".join(count for count in counts if count and not count.startswith("0 "))


def recommended_summary(run: "Setup", settings: LocalSettings) -> str:
    """The recommended settings' row in the menu: each Claude Code folder set up, with its answers
    counted, the parts separated by NEXT."""
    parts = []
    for entry, full in run.folders_answered(CLAUDE_CODE, settings, True):
        offers, reason = run.recommended_in(settings, entry, Path(full))
        parts.append(
            f"{entry}: setup can't change its settings.json"
            if reason
            else f"{entry}: {recommended_counts(offers)}"
        )
    return NEXT.join(parts) or f"no {CLAUDE_CODE.name} {CLAUDE_CODE.folder} set up"


def value_now(offer: "RecommendedOffer") -> str:
    """Where a recommended setting's value is now, and what it is, in words."""
    current = offer.current
    if not current.place:
        return "settings.json doesn't set it now"
    value = json.dumps(current.value, ensure_ascii=False)
    if current.place == "settings.json":
        return f"settings.json has {value} now"
    return f"settings.json doesn't set it, and {current.place} has {value} now"


def recommended_overview(run: "Setup", settings: LocalSettings) -> list[str]:
    """For an agent: each recommended setting in each Claude Code folder set up that has an
    answer or waits for one, by the folder and the setting's id, with its answer, and where its
    value isn't what the answer gave, the value, with the commands that change it."""
    lines: list[str] = []
    for entry, full in run.folders_answered(CLAUDE_CODE, settings, True):
        offers, reason = run.recommended_in(settings, entry, Path(full))
        if reason:
            lines.append(f"  {entry}: setup won't change its settings.json: {reason}.")
            continue
        today = date.today()
        for offer in offers:
            line = f"  {entry}, {offer.setting.id}: {offer.answer_text}"
            if offer.waiting(today):
                lines.append(line + " (see Waiting for your answer).")
                continue
            # One with the recommended value and no answer needs nothing.
            if offer.answer is None:
                continue
            done = offer.state == DONE
            if offer.answer is True and not done:
                line += f": {value_now(offer)}, which setup leaves as it is"
            if offer.answer is not True or not done:
                line += f". For yes: {recommended_command(offer)}"
            if offer.answer is not False:
                line += f". For no: --configure '{RECOMMENDED_NAME}.{offer.setting.id}-={entry}'"
            lines.append(line + ".")
    return ["", color(RECOMMENDED_LABEL, CYAN), *lines] if lines else []


def recorded_states() -> dict[str, str] | None:
    """Each skill's state on this PC, by its name in lowercase, as setup last recorded it, such
    as "not added: works only on macOS", or None when setup has recorded none."""
    # Loaded here, since setup loads this module.
    from .setup import SKILL_STATES

    try:
        data = json.loads(SKILL_STATES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return {
        name.lower(): entry["state"]
        for name, entry in data.items()
        if isinstance(entry, dict) and isinstance(entry.get("state"), str)
    }


def skills_overview(settings: LocalSettings) -> list[str]:
    """For an agent: whether each skill is added to the agents on this PC, then each preference
    the skills declare, by its label and skill, each with its value and the name --configure
    changes it by, so a skill can name a preference by its label alone. Where the state setup
    last recorded for a skill isn't what its answer alone gives, such as for one that works only
    on another operating system, the line says so, so nobody changes an answer for nothing."""
    skills = skill_declarations(settings.content_dir).skills
    states = recorded_states()
    added: list[str] = []
    for name, skill in skills.items():
        setting = skill.added_setting
        if setting is None:
            line, expected = f"  {name}: always", "always added to your agents"
        else:
            saved = get(settings.data, setting.path, MISSING)
            line = f"  {name}: {value_shown(setting, saved)}"
            if read_value(saved, setting)[0]:
                expected = "added to your agents"
            else:
                expected = "not added: you said no" if saved is False else "not added by default"
        if states is not None:
            state = states.get(name.lower(), "not added yet: setup hasn't seen it")
            if state != expected:
                line += f", but on this PC it's {state}"
        if setting is not None:
            line += f". To change it: {setting.path}=true|false|default"
        added.append(line)
    preferences: list[str] = []
    for name, skill in skills.items():
        for preference in skill.preferences.values():
            setting = preference.setting
            shown = value_shown(setting, get(settings.data, setting.path, MISSING))
            preferences.append(
                f"  {preference.label} ({name} skill): {shown}. To change it: "
                f"{setting.path}=true|false|default"
            )
    lines = ["", color("Skills added to your agents on this PC", CYAN), *added] if added else []
    return lines + (["", color("Skill preferences", CYAN), *preferences] if preferences else [])


# The menu


def menu(run: "Setup", settings: LocalSettings) -> bool:
    """Shows every setting, and changes the ones the person picks, until Enter, after which setup
    goes on. Returns whether this PC's settings changed."""
    changers: dict[str, Callable[[Setup, LocalSettings], bool]] = {
        "devHome.folder": change_content_dir,
        AUTO_UPDATE: change_auto_update,
        "updates.checkEveryHours": change_update_hours,
        "devHome.checkEveryHours": change_content_hours,
        RULES_WARN_ABOVE: change_rules_warning,
        CODEX_INSTRUCTIONS_MAX: change_codex_limit,
    }
    # Numbered as overview numbers the rows: dev-home-toolkit's own settings in the order
    # setting-definitions.json has them, then each agent's folders, then the recommended
    # settings, then the shared setting.
    order = [changers[setting.path] for setting in SETTINGS]
    order += [change_claude_folders, change_codex_homes, change_recommended, change_copies]
    steps = {str(number): step for number, step in enumerate(order, 1)}
    changed = False
    while True:
        run.line()
        for line in overview(run, settings):
            run.line(line)
        run.line()
        choice = run.ask(
            f"Number to change, {console.key('a')} to go through them all, or Enter to go on"
        )
        if not choice:
            return changed
        picked = list(steps) if choice.strip().lower() == "a" else [choice.strip()]
        if not all(number in steps for number in picked):
            run.line(
                f"Type a number from 1 to {len(steps)}, or {console.key('a')}, or press Enter to "
                "go on."
            )
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


def change_number(run: "Setup", settings: LocalSettings, path: str, question: str) -> bool:
    """Asks for a setting that holds a whole number, 0 or more, such as a number of hours."""
    current = setting_value(settings.data, path)[0]
    while True:
        answer = run.ask(question, str(current))
        if answer is None:
            return False
        if re.fullmatch(r"\d+", answer):
            break
        run.line(f"Type a whole number of {UNITS[BY_PATH[path].type]}: 0 or more.")
    number = int(answer)
    if keeps(settings, path, number):
        return False
    put(settings.data, path, number)
    return True


def change_update_hours(run: "Setup", settings: LocalSettings) -> bool:
    return change_number(
        run,
        settings,
        "updates.checkEveryHours",
        "Check GitHub for dev-home-toolkit updates every how many hours (0 for every sync)",
    )


def change_content_hours(run: "Setup", settings: LocalSettings) -> bool:
    several, _ = several_copies(run, settings)
    commands = "/handoff, plain /knowledge, and /knowledge add"
    if several is False:
        run.line(
            f"In single-PC mode, {commands} check GitHub for dev-home's changes this often. "
            "/dev-home sync always checks."
        )
    else:
        mode = "is in multi-PC mode" if several else "isn't in single-PC mode"
        run.line(
            f"dev-home {mode}, so {commands} check GitHub for its changes every time. The number "
            "you set here is used only in single-PC mode."
        )
    return change_number(
        run,
        settings,
        "devHome.checkEveryHours",
        "Check GitHub for dev-home's changes every how many hours (0 for every time)",
    )


def change_rules_warning(run: "Setup", settings: LocalSettings) -> bool:
    return change_number(
        run,
        settings,
        RULES_WARN_ABOVE,
        "Warn when your rules for one agent on this PC pass how many KiB (0 never warns)",
    )


def change_codex_limit(run: "Setup", settings: LocalSettings) -> bool:
    run.line(
        "Codex reads AGENTS.md, from its home and the project's folders together, up to this size, "
        "and leaves the rest out without saying so. Setup only ever raises project_doc_max_bytes "
        "in each Codex home's config.toml; with no value there, Codex reads 32 KiB."
    )
    return change_number(
        run, settings, CODEX_INSTRUCTIONS_MAX, "Codex's instruction limit, in how many KiB"
    )


def set_folder(settings: LocalSettings, run: "Setup", agent: Agent, full: Path, yes: bool) -> None:
    """Saves the answer for one of an agent's folders, by its full path, in the entry that already
    names it when there is one, and otherwise in a new one, written as setup writes folders."""
    settings.folders[agent.setting][run.entry_for(agent, settings, full)] = yes


def set_shared(settings: LocalSettings, run: "Setup", agent: Agent, full: Path, yes: bool) -> None:
    """Saves the answer for one of a shared agent's folders, by its full path. For the main
    folder, or while no folder has an answer, it goes to every folder. For another folder, it must
    match the answer they share: one that doesn't is refused, raising SettingError, since every
    folder reads the same skills."""
    folders = run.known_folders(agent, settings)
    if full.is_dir() and not any(same_path(full, folder) for folder in folders):
        folders = sorted([*folders, full], key=lambda f: folder_rank(agent, f, run.home))
    answer, _ = run.shared_answer(agent, settings, folders)
    if answer is None or (folders and same_path(full, folders[0])):
        run.answer_every_folder(agent, settings, yes)
        set_folder(settings, run, agent, full, yes)
    elif answer is yes:
        set_folder(settings, run, agent, full, yes)
    else:
        main = run.entry_named(folders[0], settings.folders[agent.setting]) or run.folder_entry(
            folders[0]
        )
        done = "set up" if answer else "not set up"
        operator = "-=" if yes is False else "+="
        raise SettingError(
            f"Every {agent.name} {agent.folder} reads the same skills, so all of them share one "
            f"answer, the main {agent.folder}'s: {main}, which is {done}. To change them all, "
            f"change it: {agent.setting}{operator}{main}."
        )


def changes_answer(answer: console.OfferAnswer | None, current: bool | Reminder | None) -> bool:
    """Whether an answer to a folder's question in the menu changes its saved answer: not when
    none came, Enter kept a reminder, the folder was skipped, which leaves one with no answer as
    it is, or it's the same yes or no."""
    if answer is None or answer in (console.KEEP, console.SKIP):
        return False
    return not (isinstance(answer, bool) and answer is current)


def reminder_value(name: str, agent: Agent, value: str) -> tuple[str, int]:
    """The folder and the days of a reminder's assignment, <folder>@<days>. Raises SettingError
    for one without a folder, or without a whole number of days, 1 or more."""
    folder, at, typed = value.rpartition("@")
    days = console.reminder_days(typed) if at else None
    if not folder.strip() or days is None:
        raise SettingError(
            f"{name}?= takes a folder and a whole number of days, 1 or more, as in "
            f"{name}?=~/{agent.default}-second@7."
        )
    return folder.strip(), days


def remind_folder(
    settings: LocalSettings, run: "Setup", agent: Agent, full: Path, days: int
) -> None:
    """Saves a reminder for one of an agent's folders, by its full path, which has no yes or no:
    setup asks about it again in that many days. A shared agent's reminder goes to every folder,
    as its answer would. Raises SettingError for a folder with an answer: a reminder brings back a
    question nobody has answered."""
    later = console.RemindIn.after(days)
    answers = settings.folders[agent.setting]
    if not agent.shared:
        entry = run.entry_named(full, answers)
        if entry is not None:
            raise SettingError(
                f"{entry} already has an answer, {'yes' if answers[entry] else 'no'}, and a "
                f"reminder is only for a {agent.folder} with no answer yet. To change the answer, "
                f"use {agent.setting}+={entry} or {agent.setting}-={entry}."
            )
        run.answer_offer(agent, settings, full, later)
        return
    folders = run.known_folders(agent, settings)
    if not any(same_path(full, folder) for folder in folders):
        folders = sorted([*folders, full], key=lambda f: folder_rank(agent, f, run.home))
    answer, _ = run.shared_answer(agent, settings, folders)
    if answer is not None:
        main = run.entry_named(folders[0], answers) or run.folder_entry(folders[0])
        raise SettingError(
            f"{agent.name} already has an answer, {'yes' if answer else 'no'}, for every "
            f"{agent.name} {agent.folder}, and a reminder is only for one with no answer yet. To "
            f"change the answer, use {agent.setting}+={main} or {agent.setting}-={main}."
        )
    run.answer_offer_every_folder(agent, settings, later)
    run.answer_offer(agent, settings, full, later)


def change_folders(run: "Setup", settings: LocalSettings, agent: Agent) -> bool:
    """Asks about each of an agent's folders, after offering to remove each one that's gone; for a
    shared agent, one question, whose answer goes to every folder. A folder answered yes or no is
    asked yes or no; one with no answer, or a reminder, is asked as an offer, as on a first run,
    where Enter keeps a reminder."""
    answers = folder_answers(run, settings, agent)
    if not answers:
        run.line(f"Setup found no {agent.name} {agent.folder}s.")
        return False
    changed = False
    explained = False
    for entry, current in answers:
        folder = Path(resolve_home(entry, run.home))
        if not folder.is_dir():
            # A folder that's gone keeps its answer, in case it comes back, until it's removed,
            # with the answers to its recommended settings.
            if run.choose(f"{folder} no longer exists. Remove it from the settings?", False):
                settings.folders[agent.setting].pop(entry, None)
                remove_folder_entry(settings.data, agent.setting, entry)
                changed = True
            continue
        if agent.shared:
            continue
        if not explained:
            present = [Path(resolve_home(name, run.home)) for name, _ in answers]
            run.introduce_folders(agent, [f for f in present if f.is_dir()])
            explained = True
        answer = run.ask_folder(agent, folder, current)
        if answer is not None and changes_answer(answer, current):
            run.answer_offer(agent, settings, Path(comparable(folder)), answer)
            changed = True
    folders = run.known_folders(agent, settings)
    if not agent.shared or not folders:
        return changed
    shared, _ = run.shared_answer(agent, settings, folders)
    every: bool | Reminder | None = shared
    if shared is None:
        every = run.reminder_of(agent, settings, folders[0], folders)
    answer = run.ask_codex(folders, every)
    if answer is None or answer in (console.KEEP, console.SKIP):
        return changed
    # The same yes or no still goes to every folder when one has another answer.
    saved = settings.folders[agent.setting].values()
    if answer is every and all(value is answer for value in saved):
        return changed
    run.answer_offer_every_folder(agent, settings, answer)
    return True


def change_claude_folders(run: "Setup", settings: LocalSettings) -> bool:
    return change_folders(run, settings, CLAUDE_CODE)


def change_codex_homes(run: "Setup", settings: LocalSettings) -> bool:
    return change_folders(run, settings, CODEX)


def change_recommended(run: "Setup", settings: LocalSettings) -> bool:
    """Goes through each recommended setting in each Claude Code folder set up, shown as setup's
    offer shows it, with its answer (see ask_recommended). Returns whether an answer changed."""
    # Loaded here, since setup loads this module.
    from .setup import RECOMMENDED_MARKS

    folders = run.folders_answered(CLAUDE_CODE, settings, True)
    if not folders:
        run.line(
            f"No {CLAUDE_CODE.name} {CLAUDE_CODE.folder} is set up, so there are no recommended "
            "settings to answer."
        )
        return False
    changed = False
    for entry, full in folders:
        folder = Path(full)
        offers, reason = run.recommended_in(settings, entry, folder)
        run.line()
        if reason:
            run.line(f"Setup won't change {folder / 'settings.json'}: {reason}.")
            continue
        run.line(f"Settings dev-home-toolkit recommends for Claude Code in {folder}:")
        items = [
            console.ListItem(
                offer.setting.summary,
                offer.recommended,
                offer.question,
                (*offer.about, console.Row("Your answer:", offer.answer_text)),
            )
            for offer in offers
        ]
        for offer, item in zip(offers, items, strict=True):
            run.line()
            console.show_items([item], RECOMMENDED_MARKS, among=items)
            changed = (
                record_recommended(run, settings, offer, ask_recommended(run, offer)) or changed
            )
    return changed


def ask_recommended(run: "Setup", offer: "RecommendedOffer") -> console.OfferAnswer | None:
    """The menu's question about one recommended setting in one folder: an offer for one with no
    yes or no, where Enter keeps a reminder; yes or no for one answered, with Enter keeping the
    answer; and for a yes whose value changed since, whether to set it again, with Enter keeping
    it as it is. None when it isn't asked, since it has the recommended value and no answer, or no
    answer came."""
    if not run.can_ask or (offer.answer is None and offer.state == DONE):
        return None
    if offer.answer is True and offer.state != DONE and not offer.pending:
        return console.choose_again(offer.question)
    if isinstance(offer.answer, bool):
        return run.choose(offer.question, offer.answer)
    return run.choose_offer(offer.question, offer.recommended, offer.answer)


def record_recommended(
    run: "Setup",
    settings: LocalSettings,
    offer: "RecommendedOffer",
    answer: console.OfferAnswer | None,
) -> bool:
    """Keeps an answer from the menu about one recommended setting, and returns whether it
    changed one: a yes waits for the work, which writes and saves it, unless it only keeps a yes
    whose folder has the value already; a no or a reminder goes in the folder's entry, a no
    taking back a yes this run gave; and skip ends a reminder. KEEP changes nothing."""
    # Loaded here, since setup loads this module.
    from .setup import yes_key

    key = (yes_key(offer.folder), offer.setting.id)
    keeps = offer.answer is True and offer.state == DONE and not offer.pending
    if answer is None or answer == console.KEEP or (answer is True and (keeps or offer.pending)):
        return False
    if answer is True:
        run.recommended_yes[key] = offer.current
        return True
    if answer is False and offer.answer is False:
        return False
    run.recommended_yes.pop(key, None)
    if answer is False:
        saved: bool | Reminder | None = False
    elif isinstance(answer, console.RemindIn):
        saved = Reminder(answer.on)
    elif answer == console.SKIP and isinstance(offer.answer, Reminder):
        saved = None
    else:
        return False
    put_recommended(settings.data, CLAUDE_CODE.setting, offer.entry, offer.setting.id, saved)
    return True


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


def assign(run: "Setup", settings: LocalSettings, text: str) -> None:
    """Makes one assignment, and shows the change to this PC's settings, if any, or takes one
    answer to a question setup waits on (see Setup.answer_question). Raises SettingError for one
    it can't make."""
    match = ASSIGNMENT.fullmatch(text.strip())
    if match is None:
        raise SettingError(f"--configure takes one setting as <name>=<value>, not {text}.")
    name, operator, value = match.group(1), match.group(2), match.group(3).strip()
    if run.answer_question(settings, name, operator, value):
        return
    if name == RECOMMENDED_NAME or name.startswith(RECOMMENDED_NAME + "."):
        assign_recommended(run, settings, name, operator, value)
        return
    if name not in NAMES and not name.startswith("skills."):
        raise SettingError(f"There is no setting named {name}.")
    agent = AGENT_FOR.get(name)
    if agent is not None and operator == "=":
        raise SettingError(
            f"{name} changes one {agent.folder} at a time: {name}+=<folder> sets one up, and "
            f"{name}-=<folder> stops."
        )
    if agent is None and operator != "=":
        raise SettingError(f"{name} is set with =, as in {name}=<value>.")
    before = copy.deepcopy(settings)
    if value == "default" and agent is None:
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
                return
            run.wanted_copies = yes
            return
    elif name in BY_PATH and BY_PATH[name].type in UNITS:
        if not re.fullmatch(r"\d+", value):
            raise SettingError(f"{name} is {TYPE_TEXT[BY_PATH[name].type]}, not {value}.")
        put(settings.data, name, int(value))
    elif name == "devHome.folder":
        settings.content_dir = checked_dev_home(value)
    else:
        assert agent is not None
        kind = f"{agent.name} {agent.folder}"
        days = None
        if operator == "?=":
            value, days = reminder_value(name, agent, value)
        if not value:
            raise SettingError(f"Name the {kind}, such as ~/{agent.default}-second.")
        # A folder as typed, such as ..\.claude-second, means one from where the command runs.
        full = Path(comparable(resolve_home(value, run.home)))
        if operator != "-=" and not full.is_dir():
            raise SettingError(f"There is no {kind} at {full}.")
        if days is not None:
            remind_folder(settings, run, agent, full, days)
        elif agent.shared:
            set_shared(settings, run, agent, full, operator == "+=")
        else:
            set_folder(settings, run, agent, full, operator == "+=")
    old_text, new_text = local_settings_text(before), local_settings_text(settings)
    if old_text == new_text:
        status_line("OK", f"{name} is already set that way, so nothing changed.")
        return
    run.status("CHANGE", f"This PC's settings: {SETTINGS_PATH}")
    run.print_diff(old_text, new_text)


def assign_recommended(
    run: "Setup", settings: LocalSettings, name: str, operator: str, value: str
) -> None:
    """Takes an agent's answer to recommended settings in a Claude Code folder set up: with an id
    after RECOMMENDED_NAME, to that setting alone, answered or not; without, to every one waiting
    for an answer there, as the listing shows them. += is yes, with the fingerprint the listing
    gave, which has to match what the folder has now; for all of them, it's yes to each one
    recommended there and no to the others. -= is no, and ?= a reminder, only for a setting with
    no yes or no. A yes waits for the work, which writes and saves it; a no or a reminder is shown
    as the change to this PC's settings. Raises SettingError for one it can't take."""
    setting_id = name[len(RECOMMENDED_NAME) + 1 :]
    known = ids_for(CLAUDE_CODE.group)
    if setting_id and setting_id not in known:
        raise SettingError(
            f"There is no recommended setting named {setting_id}. There are: {', '.join(known)}."
        )
    if operator == "=":
        raise SettingError(
            f"{name} takes +=<folder>@<fingerprint> for yes, -=<folder> for no, or "
            "?=<folder>@<days> for a reminder."
        )
    days = None
    seen = ""
    folder_text = value
    if operator == "?=":
        folder_text, days = reminder_value(name, CLAUDE_CODE, value)
    elif operator == "+=":
        folder_text, at, seen = value.rpartition("@")
        if not at or not folder_text.strip() or not seen.strip():
            raise SettingError(
                f"{name}+= takes a folder and the fingerprint the listing gives, as in "
                f"{name}+=~/.claude@<fingerprint>."
            )
    full = Path(comparable(resolve_home(folder_text.strip(), run.home)))
    entry = run.set_up_entry(CLAUDE_CODE, settings, full)
    if entry is None:
        raise SettingError(
            f"{full} isn't a {CLAUDE_CODE.name} {CLAUDE_CODE.folder} set up, so setup has no "
            "recommended settings for it."
        )
    offers, reason = run.recommended_in(settings, entry, full)
    if reason:
        raise AnswerError(f"Setup won't change {full / 'settings.json'}: {reason}.")
    if setting_id:
        targets = [offer for offer in offers if offer.setting.id == setting_id]
        shown_print = targets[0].fingerprint
    else:
        targets = [offer for offer in offers if offer.waiting(date.today())]
        shown_print = batch_fingerprint(targets)
    if not targets:
        status_line("OK", f"No recommended setting waits for an answer in {entry}.")
        return
    if operator == "+=" and seen.strip() != shown_print:
        raise AnswerError(
            f"{'That setting' if setting_id else 'What waits'} in {entry} changed since the "
            "listing showed it, so nothing was changed. Run --configure again to see it as it is "
            "now."
        )
    if days is not None and any(isinstance(offer.answer, bool) for offer in targets):
        answered = targets[0]
        raise SettingError(
            f"{answered.setting.id} in {entry} already has an answer, "
            f"{'yes' if answered.answer else 'no'}, and a reminder is only for one with no "
            f"answer yet. To change the answer, use {name}+= or {name}-=."
        )
    before = copy.deepcopy(settings)
    changed = False
    for offer in targets:
        if operator == "+=":
            answer: console.OfferAnswer = offer.recommended or bool(setting_id)
        elif operator == "-=":
            answer = False
        else:
            answer = console.RemindIn.after(days or 1)
        changed = record_recommended(run, settings, offer, answer) or changed
    old_text, new_text = local_settings_text(before), local_settings_text(settings)
    if old_text != new_text:
        run.status("CHANGE", f"This PC's settings: {SETTINGS_PATH}")
        run.print_diff(old_text, new_text)
    elif not changed:
        status_line("OK", f"{name} is already set that way in {entry}, so nothing changed.")


def declared_setting(settings: LocalSettings, name: str) -> Setting:
    """One of dev-home-toolkit's own settings; whether a skill is added to the agents, named as
    skills.<skill>.addedToAgents; or a skill's preference, named as
    skills.<skill>.preferences.<name>; with its path spelled as the skill declares it. Raises
    SettingError for a skill or a preference that isn't declared, a skill whose
    dev-home-skill.json can't be read, or a skill that's always added."""
    if not name.startswith("skills."):
        return BY_PATH[name]
    parts = name.split(".")
    if len(parts) == 3 and parts[2] == ADDED_TO_AGENTS and parts[1]:
        listed = skill_declarations(settings.content_dir)
        skills = listed.skills
        found = find_skill(skills, parts[1])
        if found is None and parts[1].lower() in listed.unread:
            raise SettingError(
                f"The {parts[1]} skill's dev-home-skill.json can't be read, so setup leaves the "
                "skill as it is. Fix the file first."
            )
        if found is None:
            raise SettingError(f"There is no skill named {parts[1]}.")
        added = skills[found].added_setting
        if added is None:
            raise SettingError(f"The {found} skill is always added to your agents.")
        return added
    if len(parts) != 4 or parts[2] != "preferences" or not all(parts):
        raise SettingError(
            f"A skill's setting is named skills.<skill>.{ADDED_TO_AGENTS}, or "
            f"skills.<skill>.preferences.<name> for a preference, not {name}."
        )
    preferences = skill_declarations(settings.content_dir).preferences
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
    from .setup import is_dev_home, is_in_use

    folder = forward(value)
    reason = unsafe_reason(folder)
    if reason:
        raise SettingError(f"The folder {folder} {reason}, so commands would need it quoted.")
    if is_inside(folder, TOOLKIT_ROOT):
        raise SettingError(f"The folder {folder} is dev-home-toolkit's own folder, or inside it.")
    full = Path(comparable(folder))
    if not is_in_use(full) or not is_dev_home(full):
        raise SettingError(
            f"{folder} isn't a dev-home: devHome.folder can only be a folder that already is one, "
            f"with {DEV_HOME_SETTINGS}. To clone or create one, the user runs setup.py in a "
            "terminal."
        )
    return folder
