"""Asking the person at the console a question, only when someone is there to answer."""

import os
import re
import sys
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TextIO

from .output import GREEN, color

# How wide lines of text get at the console, wrapped at spaces.
LINE_WIDTH = 100

if sys.platform == "win32":
    import ctypes
    import msvcrt


def is_console() -> bool:
    """Whether a person at a real console can see a question and answer it: input comes from a
    console, and output goes to one. Output sent to a file would hide the question, so setup
    would wait for an answer to something nobody sees."""
    return is_console_stream(sys.stdin) and is_console_stream(sys.stdout)


def is_console_stream(stream: TextIO | None) -> bool:
    """On Windows, isatty() is the wrong check: it's true for the NUL input that agents'
    commands get. So this asks Windows for the stream's console mode, which only a console
    has."""
    if stream is None:
        return False
    try:
        fd = stream.fileno()
    except (OSError, ValueError, AttributeError):
        return False
    if sys.platform == "win32":
        try:
            handle = msvcrt.get_osfhandle(fd)
        except OSError:
            return False
        mode = ctypes.c_ulong()
        return bool(ctypes.WinDLL("kernel32").GetConsoleMode(handle, ctypes.byref(mode)))
    return os.isatty(fd)


def key(text: str) -> str:
    """What to type, such as a or yes, set apart from the words around it: in single quotes, and
    green at a console that shows color, as the menu's numbers are. A capital letter already
    marks what Enter gives, and brackets the hint, such as [Y/n], so neither can mark a key; and
    color alone is lost with NO_COLOR, in copied text, and to people who can't tell green
    apart."""
    return color(f"'{text}'", GREEN)


def ask(question: str, default: str = "") -> str | None:
    """The answer to a question, or default when the answer is blank. None when input ends
    without one."""
    prompt = f"{question} [{default}]: " if default else f"{question}: "
    try:
        answer = input(prompt)
    except EOFError:
        return None
    return answer.strip() or default


def confirm(question: str) -> bool:
    """True only for yes. Input that ends without an answer counts as no."""
    try:
        answer = input(f"{question} [y/N]: ")
    except EOFError:
        return False
    return re.fullmatch(r"\s*(y|yes)\s*", answer, re.IGNORECASE) is not None


# The answer that follows a setting's default, whatever it becomes, rather than choosing a value.
DEFAULT = "default"


def choose_or_default(question: str, default: bool, enter: bool | str) -> bool | str | None:
    """True for yes, False for no, and DEFAULT to follow the setting's default, which the
    question names. enter is what Enter gives, shown as the capital letter: the saved yes or no,
    or DEFAULT when nothing is saved yet, or the saved answer already follows the default, so
    Enter never turns a choice into following the default unnoticed. None when input ends
    without an answer."""
    letters = {True: "y", False: "n", DEFAULT: "d"}
    hint = "/".join(
        letter.upper() if value == enter else letter for value, letter in letters.items()
    )
    words = "yes" if default else "no"
    offered = f"{key('y')}, {key('n')}, or {key('d')} for the default ({words})"
    while True:
        try:
            answer = input(f"{question} {offered} [{hint}]: ")
        except EOFError:
            return None
        text = answer.strip().lower()
        if text in ("y", "yes"):
            return True
        if text in ("n", "no"):
            return False
        if text in ("d", "default"):
            return DEFAULT
        if not text:
            return enter
        print(f"Type {key('y')}, {key('n')}, or {key('d')}.", flush=True)


def choose(question: str, default: bool | None = None) -> bool | None:
    """True for yes and False for no. Enter gives the default, shown as the capital letter; with
    no default, Enter says to type y or n and asks again, as any other answer does. None when
    input ends without an answer."""
    hint = "[y/n]" if default is None else "[Y/n]" if default else "[y/N]"
    while True:
        try:
            answer = input(f"{question} {hint}: ")
        except EOFError:
            return None
        if re.fullmatch(r"\s*(y|yes)\s*", answer, re.IGNORECASE):
            return True
        if re.fullmatch(r"\s*(n|no)\s*", answer, re.IGNORECASE):
            return False
        if not answer.strip() and default is not None:
            return default
        # Without this, the same question coming back looks as if the answer went unseen.
        print(f"Type {key('y')} or {key('n')}.", flush=True)


# The answers to an offer besides yes and no (see choose_offer): skip it for now, or, at a
# question about an item that has a reminder, keep it, which Enter gives there.
SKIP = "skip"
KEEP = "keep"
# What a person types for a reminder: a whole number of days, 1 or more. Five digits at most, so
# the date it gives is one Python can hold.
DAYS = re.compile(r"\d{1,5}")
# How an offer's question names that answer.
DAYS_ANSWER = "a number of days until setup asks again"


@dataclass(frozen=True)
class RemindIn:
    """The answer to an offer that asks again later: in that many days, on the date that gives,
    worked out from this PC's clock when the answer came."""

    days: int
    on: date

    @classmethod
    def after(cls, days: int) -> "RemindIn":
        return cls(days, date.today() + timedelta(days=days))


# An answer to an offer: True for yes, False for no, SKIP, KEEP, or a RemindIn.
OfferAnswer = bool | str | RemindIn


def reminder_days(text: str) -> int | None:
    """The days a reminder takes, as typed, or None when the text isn't a whole number from 1
    up."""
    text = text.strip()
    if not DAYS.fullmatch(text) or int(text) < 1:
        return None
    return int(text)


def reminded(days: int) -> RemindIn:
    """The reminder for days typed at a question, said back with the date it gives, so a typo
    shows right away."""
    later = RemindIn.after(days)
    print(f"Setup asks again from {later.on.isoformat()}.", flush=True)
    return later


def choose_offer(question: str, recommended: bool, keep: str = "") -> OfferAnswer | None:
    """The answer to one offer, something a person can take or turn down: True for yes, False for
    no, SKIP to leave it unanswered for now, or a RemindIn for a number of days typed. Enter gives
    the recommendation, shown as the capital letter. For an item that has a reminder, keep names
    it, such as "the reminder for 2026-10-27": Enter keeps it, giving KEEP, and skip isn't offered,
    since saying nothing there is Enter. None when input ends without an answer."""
    if keep:
        offered = f"{key('y')}, {key('n')}, {DAYS_ANSWER}, or Enter to keep {keep}"
        hint = "y/n/<days>"
        letters = f"{key('y')}, {key('n')}"
    else:
        offered = f"{key('y')}, {key('n')}, {key('s')} to skip for now, or {DAYS_ANSWER}"
        hint = ("Y/n" if recommended else "y/N") + "/s/<days>"
        letters = f"{key('y')}, {key('n')}, {key('s')}"
    while True:
        try:
            typed = input(f"{question} {offered} [{hint}]: ")
        except EOFError:
            return None
        text = typed.strip().lower()
        if text in ("y", "yes"):
            return True
        if text in ("n", "no"):
            return False
        if not text:
            return KEEP if keep else recommended
        if text in ("s", "skip") and not keep:
            return SKIP
        days = reminder_days(text)
        if days is not None:
            return reminded(days)
        print(f"Type {letters}, or a number of days, 1 or more.", flush=True)


# The answers to a list of optional items, as choose_from_list returns them: ALL, RECOMMENDED,
# NONE, and EACH, then SKIP, and REMIND for a number of days.
ALL = "all"
RECOMMENDED = "recommended"
NONE = "none"
EACH = "each"
REMIND = "remind"


@dataclass(frozen=True)
class ListItem:
    """One optional item: its name in the list, whether dev-home-toolkit recommends it, and its own
    question, such as "Set up ~/.claude-<name>?", for when the items are asked one at a time."""

    name: str
    recommended: bool
    question: str


@dataclass(frozen=True)
class ListAnswer:
    """The answer to the whole list, one of ALL, RECOMMENDED, NONE, EACH, SKIP, and REMIND, and
    what it means for each item, by name, as choose_offer gives it: True for yes, False for no,
    SKIP, or a RemindIn. The caller decides what to save, so a list whose items have a default can
    save RECOMMENDED as following it."""

    choice: str
    answers: dict[str, OfferAnswer]


def choose_from_list(
    intro: str, question: str, items: Sequence[ListItem], details: str = ""
) -> ListAnswer | None:
    """One prompt for a list of optional items, with details, if any, between the list and the
    question, such as what a yes does: 'a' for all, 'r' for the recommended ones (what
    Enter gives), 'n' for none, 'e' to ask for each, whose question defaults to that item's
    recommendation, 's' to skip them all for now, or a number of days for a reminder about them
    all. An answer that would do the same as All recommended is left out, and its letter means
    All recommended: with every item recommended, a, and with none, n. So a letter and Enter,
    shown as the same, never give two answers that a caller could save differently.
    A list of one asks its item's question alone, since a list prompt for one item only adds a
    step, and its answer is the choice the list's own letters would give: RECOMMENDED for the
    recommendation, ALL or NONE for the other, and SKIP or REMIND, so one item and several are
    saved alike. An empty list asks nothing. None when input ends without an answer, even partway
    through the items, so nothing half answered is saved."""
    if not items:
        return ListAnswer(RECOMMENDED, {})
    if len(items) == 1:
        item = items[0]
        answer = choose_offer(item.question, item.recommended)
        if answer is None:
            return None
        if isinstance(answer, bool):
            alone = RECOMMENDED if answer == item.recommended else ALL if answer else NONE
        else:
            alone = REMIND if isinstance(answer, RemindIn) else SKIP
        return ListAnswer(alone, {item.name: answer})
    every = all(item.recommended for item in items)
    some = any(item.recommended for item in items)
    print(intro, flush=True)
    width = max(len(item.name) for item in items)
    for item in items:
        if some and not every:
            note = "recommended" if item.recommended else "not recommended"
            print(f"  {item.name.ljust(width)}    {note}", flush=True)
        else:
            print(f"  {item.name}", flush=True)
    if details:
        print(flush=True)
        for line in textwrap.wrap(details, LINE_WIDTH):
            print(line, flush=True)
        print(flush=True)
    if every:
        letters = {"a": RECOMMENDED, "n": NONE, "e": EACH}
    elif some:
        letters = {"a": ALL, "r": RECOMMENDED, "n": NONE, "e": EACH}
    else:
        letters = {"a": ALL, "n": RECOMMENDED, "e": EACH}
    words = {"a": "for all", "r": "for the recommended ones", "n": "for none"}
    offered = [f"{key(letter)} {words[letter]}" for letter in letters if letter != "e"]
    offered += [f"{key('e')} to ask for each", f"{key('s')} to skip for now"]
    enter = next(letter for letter, choice in letters.items() if choice == RECOMMENDED)
    hint = "/".join(letter.upper() if letter == enter else letter for letter in letters)
    later: RemindIn | None = None
    choice: str | None = None
    while choice is None:
        try:
            typed = input(f"{question} {', '.join(offered)}, or {DAYS_ANSWER} [{hint}/s/<days>]: ")
        except EOFError:
            return None
        text = typed.strip().lower() or enter
        days = reminder_days(text)
        if text == "s":
            choice = SKIP
        elif days is not None:
            later = reminded(days)
            choice = REMIND
        else:
            choice = letters.get(text)
        if choice is None:
            typable = ", ".join(key(letter) for letter in [*letters, "s"])
            print(f"Type {typable}, or a number of days, 1 or more.", flush=True)
    if choice == EACH:
        answers: dict[str, OfferAnswer] = {}
        for item in items:
            answer = choose_offer(item.question, item.recommended)
            if answer is None:
                return None
            answers[item.name] = answer
        return ListAnswer(EACH, answers)
    if choice == SKIP or later is not None:
        return ListAnswer(choice, {item.name: later or SKIP for item in items})
    return ListAnswer(
        choice,
        {
            item.name: choice == ALL or (choice == RECOMMENDED and item.recommended)
            for item in items
        },
    )
