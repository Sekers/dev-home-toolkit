"""What a skill needs to run, as the requires list in its dev-home-skill.json declares it, and
whether this PC meets it.

Each entry has a type, and each type has a rule here: what the entry takes, whether it's checked
for each skills folder or once for the whole PC, whether the person can do anything about it, and
the reason it gives when it isn't met. settings.py reads a skill's file through parse_requires,
this_pc gathers this PC's facts without starting a process, and unmet says which requirements a
skill doesn't meet in one skills folder. The design and its reasons are in
docs/development/decisions/skills-and-releases-declare-their-requirements-as-facts.md."""

import os
import re
import sys
from collections.abc import Callable, Collection, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

# The operating systems and tools a requirement can name, each by the name requires uses, with
# the name people know it by.
OPERATING_SYSTEMS = {"windows": "Windows", "macos": "macOS", "linux": "Linux"}
TOOLS = {"claude-code": "Claude Code", "codex": "Codex"}
# A program's name alone, such as gh, never a path.
PROGRAM_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")
# A Python version, such as 3.13 or 3.13.1, in quotes, since a JSON number would read 3.10 as 3.1.
VERSION = re.compile(r"\d+\.\d+(\.\d+)?")
# The reasons for a requirement no rule here can check.
MISTAKE = "has a mistake in its dev-home-skill.json"
NEWER = "needs a newer dev-home-tools"


@dataclass(frozen=True)
class Requirement:
    """One entry of a skill's requires, as this copy of dev-home-tools reads it. kind is its type
    as written: os, tool, program, python, or one this copy doesn't know. names holds the
    operating systems or tools it takes any one of, only ones this copy knows, or the program it
    needs, whose description says what it is, if the entry says. version is the lowest Python it
    takes. mistake marks an entry this copy can't use, which nothing meets."""

    kind: str
    names: tuple[str, ...] = ()
    description: str = ""
    version: tuple[int, ...] = ()
    mistake: bool = False


@dataclass(frozen=True)
class ThisPC:
    """This PC's facts that requirements are checked against. os is its operating system, by the
    name requires uses; python, the version of the Python setup runs with, which is the skills'
    own on every sync a skill starts; programs, each program asked about that's on the PATH."""

    os: str
    python: tuple[int, ...]
    programs: frozenset[str]


@dataclass(frozen=True)
class Unmet:
    """A requirement a skill doesn't meet. reason says what it needs, such as "needs the jira
    program". can_act says whether the person can do something about it, such as install a
    program, where an operating system they can't change is no use telling them about.
    per_folder says it was checked for one skills folder, against the tools that read it, rather
    than once for the whole PC."""

    reason: str
    can_act: bool
    per_folder: bool


@dataclass(frozen=True)
class Rule:
    """How one type of requirement is checked: per_folder and can_act, as in Unmet; met, from
    the requirement, this PC's facts, and the tools that read the skills folder; and the reason
    when it isn't met."""

    per_folder: bool
    can_act: bool
    met: Callable[[Requirement, ThisPC, frozenset[str]], bool]
    reason: Callable[[Requirement], str]


def either(names: Sequence[str], known: dict[str, str]) -> str:
    """Names as people know them, joined with "or", such as "Windows or macOS"."""
    shown = [known.get(name, name) for name in names]
    if len(shown) < 3:
        return " or ".join(shown)
    return f"{', '.join(shown[:-1])}, or {shown[-1]}"


def version_text(version: Sequence[int]) -> str:
    return ".".join(str(part) for part in version)


RULES: dict[str, Rule] = {
    "os": Rule(
        per_folder=False,
        can_act=False,
        met=lambda requirement, pc, _tools: pc.os in requirement.names,
        reason=lambda requirement: f"works only on {either(requirement.names, OPERATING_SYSTEMS)}",
    ),
    # Every tool setup sets up that reads the folder has to be one the skill works in.
    "tool": Rule(
        per_folder=True,
        can_act=True,
        met=lambda requirement, _pc, tools: tools <= set(requirement.names),
        reason=lambda requirement: f"works only in {either(requirement.names, TOOLS)}",
    ),
    "program": Rule(
        per_folder=False,
        can_act=True,
        met=lambda requirement, pc, _tools: requirement.names[0] in pc.programs,
        reason=lambda requirement: f"needs the {requirement.names[0]} program",
    ),
    "python": Rule(
        per_folder=False,
        can_act=True,
        met=lambda requirement, pc, _tools: (
            pc.python[: len(requirement.version)] >= requirement.version
        ),
        reason=lambda requirement: f"needs Python {version_text(requirement.version)} or later",
    ),
}


def quoted(names: Iterable[str]) -> str:
    """Names in quotes, joined with "and", such as "windows", "macos", and "linux"."""
    shown = [f'"{name}"' for name in names]
    if len(shown) < 3:
        return " and ".join(shown)
    return f"{', '.join(shown[:-1])}, and {shown[-1]}"


def parse_entry(entry: object, number: int) -> tuple[Requirement, list[str]]:
    """One entry of requires, and a mistake for each part of it this copy can't use."""
    where = f"entry {number} of requires"
    if not isinstance(entry, dict) or not isinstance(entry.get("type"), str):
        return Requirement("", mistake=True), [
            f"{where} isn't a JSON object with a type, so the skill counts as not meeting it"
        ]
    kind = entry["type"]
    where = f'{where} (type "{kind}")'
    if kind not in RULES:
        # A newer dev-home-tools may know it, so it's no mistake: see unmet.
        return Requirement(kind), []

    def wrong(needs: str) -> tuple[Requirement, list[str]]:
        return Requirement(kind, mistake=True), [
            f"{where} needs {needs}, so the skill counts as not meeting it"
        ]

    if kind in ("os", "tool"):
        known = OPERATING_SYSTEMS if kind == "os" else TOOLS
        names = entry.get("anyOf")
        if (
            not isinstance(names, list)
            or not names
            or not all(isinstance(name, str) for name in names)
        ):
            return wrong(f"anyOf: a list of one or more of {quoted(known)}")
        # A name this copy doesn't know is left out, so a misspelling never matches by accident.
        mistakes = [
            f'{where} names "{name}", which this dev-home-tools doesn\'t know: it knows '
            f"{quoted(known)}"
            for name in names
            if name not in known
        ]
        kept = tuple(dict.fromkeys(name for name in names if name in known))
        return Requirement(kind, kept, mistake=not kept), mistakes
    if kind == "program":
        name = entry.get("name")
        if not isinstance(name, str) or not PROGRAM_NAME.fullmatch(name):
            return wrong('name: the program\'s name alone, such as "gh"')
        description = entry.get("description", "")
        if not isinstance(description, str):
            mistake = f"{where}: description isn't text, so it was left out"
            return Requirement(kind, (name,)), [mistake]
        return Requirement(kind, (name,), description.strip()), []
    at_least = entry.get("atLeast")
    if not isinstance(at_least, str) or not VERSION.fullmatch(at_least):
        return wrong('atLeast: the lowest version it runs on, in quotes, such as "3.13"')
    return Requirement(kind, version=tuple(int(part) for part in at_least.split("."))), []


def parse_requires(value: object) -> tuple[tuple[Requirement, ...], list[str]]:
    """The requirements in a skill's requires, and a mistake for each part of it this copy can't
    use, said as what's wrong, for a line that names the file. A requires that isn't a list counts
    as one entry with a mistake, so nothing meets it."""
    if not isinstance(value, list):
        return (Requirement("", mistake=True),), [
            "requires isn't a list, so the skill counts as not meeting it"
        ]
    found: list[Requirement] = []
    mistakes: list[str] = []
    for number, entry in enumerate(value, 1):
        requirement, wrong = parse_entry(entry, number)
        found.append(requirement)
        mistakes += wrong
    return tuple(found), mistakes


def programs_named(requires: Iterable[Requirement]) -> set[str]:
    """Each program the requirements name, to look for once a run (see this_pc)."""
    return {
        requirement.names[0]
        for requirement in requires
        if requirement.kind == "program" and not requirement.mistake
    }


def is_file(path: Path) -> bool:
    """Whether a file is there, counting one that can't be looked at, such as in a folder this
    user can't read, as not there."""
    try:
        return path.is_file()
    except OSError:
        return False


def on_path(name: str) -> bool:
    """Whether a program is in one of the folders in PATH, as a shell finds it: on Windows, with
    any of the extensions in PATHEXT, such as .exe or .cmd. Only full paths in PATH count, never
    the current folder, which may be a project's, as programs.find_program has it."""
    folders = [
        Path(folder)
        for folder in os.environ.get("PATH", "").split(os.pathsep)
        if folder and Path(folder).is_absolute()
    ]
    if sys.platform == "win32":
        extensions = [
            extension
            for extension in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")
            if extension
        ]
        if Path(name).suffix.lower() in {extension.lower() for extension in extensions}:
            candidates = [name]
        else:
            candidates = [name + extension for extension in extensions]
        return any(is_file(folder / candidate) for folder in folders for candidate in candidates)
    return any(is_file(folder / name) and os.access(folder / name, os.X_OK) for folder in folders)


def operating_system() -> str:
    """This PC's operating system, by the name requires uses, or Python's own name for one that
    has none."""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    return sys.platform


def this_pc(programs: Iterable[str]) -> ThisPC:
    """This PC's facts, with each of programs looked for in PATH once. None of it starts a
    process."""
    return ThisPC(
        operating_system(),
        tuple(sys.version_info[:3]),
        frozenset(name for name in set(programs) if on_path(name)),
    )


def unmet(requires: Iterable[Requirement], pc: ThisPC, tools: Collection[str]) -> list[Unmet]:
    """Each of a skill's requirements it doesn't meet in a skills folder that tools read, each by
    its name in requires, such as codex. A type this copy doesn't know counts as not met, since
    only a newer dev-home-tools could check it, and so does an entry with a mistake."""
    read_by = frozenset(tools)
    found: list[Unmet] = []
    for requirement in requires:
        rule = RULES.get(requirement.kind)
        if requirement.mistake:
            found.append(Unmet(MISTAKE, can_act=True, per_folder=False))
        elif rule is None:
            found.append(Unmet(NEWER, can_act=True, per_folder=False))
        elif not rule.met(requirement, pc, read_by):
            found.append(Unmet(rule.reason(requirement), rule.can_act, rule.per_folder))
    return found
