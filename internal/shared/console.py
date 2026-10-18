"""Asking the person at the console a question, only when someone is there to answer."""

import os
import re
import sys
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
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


# The answers to a list of optional items, as choose_from_list returns them.
ALL = "all"
RECOMMENDED = "recommended"
NONE = "none"
EACH = "each"


@dataclass(frozen=True)
class ListItem:
    """One optional item: its name in the list, whether dev-home-toolkit recommends it, and its own
    question, such as "Set up ~/.claude-<name>?", for when the items are asked one at a time."""

    name: str
    recommended: bool
    question: str


@dataclass(frozen=True)
class ListAnswer:
    """The answer to the whole list, one of ALL, RECOMMENDED, NONE, and EACH, and what it means
    for each item, by name: True for yes and False for no. The caller decides what to save, so
    a list whose items have a default can save RECOMMENDED as following it."""

    choice: str
    answers: dict[str, bool]


def choose_from_list(
    intro: str, question: str, items: Sequence[ListItem], details: str = ""
) -> ListAnswer | None:
    """One prompt for a list of optional items, with details, if any, between the list and the
    question, such as what a yes does: 'a' for all, 'r' for the recommended ones (what
    Enter gives), 'n' for none, or 'e' to ask for each, whose question defaults to that item's
    recommendation. An answer that would do the same as All recommended is left out, and its
    letter means All recommended: with every item recommended, a, and with none, n. So a letter
    and Enter, shown as the same, never give two answers that a caller could save differently.
    A list of one asks its item's question alone, since a list prompt for one item only adds a
    step, and its answer is the choice the list's own letters would give: RECOMMENDED for the
    recommendation, and ALL or NONE for the other, so one item and several are saved alike. An
    empty list asks nothing. None when input ends without an answer, even partway through the
    items, so nothing half answered is saved."""
    if not items:
        return ListAnswer(RECOMMENDED, {})
    if len(items) == 1:
        item = items[0]
        answer = choose(item.question, item.recommended)
        if answer is None:
            return None
        return ListAnswer(
            RECOMMENDED if answer == item.recommended else ALL if answer else NONE,
            {item.name: answer},
        )
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
    enter = next(letter for letter, choice in letters.items() if choice == RECOMMENDED)
    hint = "/".join(letter.upper() if letter == enter else letter for letter in letters)
    each = f"{key('e')} to ask for each"
    choice = None
    while choice is None:
        try:
            typed = input(f"{question} {', '.join(offered)}, or {each} [{hint}]: ")
        except EOFError:
            return None
        text = typed.strip().lower() or enter
        choice = letters.get(text)
        if choice is None:
            others = ", ".join(key(letter) for letter in list(letters)[:-1])
            print(f"Type {others}, or {key('e')}.", flush=True)
    if choice == EACH:
        answers: dict[str, bool] = {}
        for item in items:
            answer = choose(item.question, item.recommended)
            if answer is None:
                return None
            answers[item.name] = answer
        return ListAnswer(EACH, answers)
    return ListAnswer(
        choice,
        {
            item.name: choice == ALL or (choice == RECOMMENDED and item.recommended)
            for item in items
        },
    )
