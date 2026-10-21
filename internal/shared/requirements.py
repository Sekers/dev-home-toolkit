"""What a skill needs to run, as the supportedOn and dependsOn lists in its dev-home-skill.json
declare it, and whether this PC meets it.

supportedOn says where the skill works, the operating system and the agent, which nobody can work
around, so a skill that doesn't meet it is kept off, and so is one with anything there this copy
can't use. dependsOn says what the skill uses, a program or a Python version, which the end user
can fix and the agent can work around, so setup only warns about it, and ignores anything there
this copy can't use. Each entry has a type, and each type has a rule here: what the entry takes;
whether it's checked for each skills folder or once for the whole PC; whether the end user can do
anything about it; and what it says when it isn't met. settings.py reads a skill's file through
parse_list, this_pc gathers this PC's facts without starting a process, and unmet says which
requirements a skill doesn't meet in one skills folder.
The design and its reasons are in docs/development/decisions/, in "Skills and releases declare
their requirements as facts" and "Setup keeps a skill off only for its operating system or
agent"."""

import os
import re
import sys
from collections.abc import Callable, Collection, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

if sys.platform == "win32":
    import winreg

# The operating systems and agents a requirement can name, each by the name a skill's file uses,
# with the name people know it by.
OS_NAMES = {"windows": "Windows", "macos": "macOS", "linux": "Linux"}
AGENT_NAMES = {"claude-code": "Claude Code", "codex": "Codex"}
# The lists a dev-home-skill.json declares requirements in, each with the types it takes. A type
# under the other list is one that list doesn't know.
SUPPORTED_ON = "supportedOn"
LISTS = {SUPPORTED_ON: ("os", "agent"), "dependsOn": ("program", "python")}
# The fields each type's entries take.
FIELDS = {
    "os": ("type", "anyOf"),
    "agent": ("type", "anyOf"),
    "program": ("type", "name", "usedFor"),
    "python": ("type", "atLeast"),
}
# A program's name alone, such as gh, never a path.
PROGRAM_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*")
# A Python version, such as 3.13 or 3.13.1, in quotes, since a JSON number would read 3.10 as 3.1.
VERSION = re.compile(r"\d+\.\d+(\.\d+)?")
# Why a skill is kept off for anything under supportedOn that can't be used.
MISTAKE = "has a mistake in its dev-home-skill.json"


@dataclass(frozen=True)
class Requirement:
    """One entry of a skill's supportedOn or dependsOn, as this copy of dev-home-toolkit reads it.
    kind is its type: os, agent, program, or python, or "" for one this copy doesn't know. names
    holds the operating systems or agents it takes any one of, only ones this copy knows, or the
    program it needs, and used_for says what the skill uses that program for, if the entry says.
    version is the lowest Python it takes. mistake marks anything under supportedOn that can't be
    used, which nothing meets."""

    kind: str
    names: tuple[str, ...] = ()
    used_for: str = ""
    version: tuple[int, ...] = ()
    mistake: bool = False


@dataclass(frozen=True)
class ThisPC:
    """This PC's facts that requirements are checked against. os is its operating system, by the
    name a skill's file uses; python, the version of the Python setup runs with, which is the
    skills' own on every sync a skill starts; programs, each program asked about that a newly
    started shell would find (see this_pc)."""

    os: str
    python: tuple[int, ...]
    programs: frozenset[str]


@dataclass(frozen=True)
class Unmet:
    """A requirement a skill doesn't meet. reason says what's missing, such as "works only on
    macOS". keeps_off says the skill is kept off for it, rather than added with a warning.
    can_act says whether the end user can do something about it, such as set up another agent,
    where an operating system they can't change is no use telling them about. per_folder says it
    was checked for one skills folder, against the agents that read it, rather than once for the
    whole PC."""

    reason: str
    keeps_off: bool
    can_act: bool
    per_folder: bool


@dataclass(frozen=True)
class Rule:
    """How one type of requirement is checked: keeps_off, can_act, and per_folder, as in Unmet;
    met, from the requirement, this PC's facts, and the agents that read the skills folder; and
    the reason when it isn't met."""

    keeps_off: bool
    can_act: bool
    per_folder: bool
    met: Callable[[Requirement, ThisPC, frozenset[str]], bool]
    reason: Callable[[Requirement, ThisPC], str]


def either(names: Sequence[str], known: dict[str, str]) -> str:
    """Names as people know them, joined with "or", such as "Windows or macOS"."""
    shown = [known.get(name, name) for name in names]
    if len(shown) < 3:
        return " or ".join(shown)
    return f"{', '.join(shown[:-1])}, or {shown[-1]}"


def version_text(version: Sequence[int]) -> str:
    return ".".join(str(part) for part in version)


def program_missing(name: str, used_for: str) -> str:
    """The warning for a program a newly started shell wouldn't find. facts.py's skills topic
    words its own check the same way (a test checks)."""
    uses = f", and the skill uses it for {used_for}" if used_for else ""
    return f"{name} isn't on the PATH{uses}"


def python_too_old(needs: Sequence[int], uses: Sequence[int]) -> str:
    """The warning for a skill that needs a newer Python than the one dev-home-toolkit uses: the
    installed one setup links internal/.python to, which runs the skills' scripts. facts.py's
    skills topic words its own check the same way (a test checks)."""
    return (
        f"the skill needs Python {version_text(needs)} or later, and this PC's is "
        f"{version_text(uses)}"
    )


RULES: dict[str, Rule] = {
    "os": Rule(
        keeps_off=True,
        can_act=False,
        per_folder=False,
        met=lambda requirement, pc, _agents: pc.os in requirement.names,
        reason=lambda requirement, _pc: f"works only on {either(requirement.names, OS_NAMES)}",
    ),
    # Every agent setup sets up that reads the folder has to be one the skill works in.
    "agent": Rule(
        keeps_off=True,
        can_act=True,
        per_folder=True,
        met=lambda requirement, _pc, agents: agents <= set(requirement.names),
        reason=lambda requirement, _pc: f"works only in {either(requirement.names, AGENT_NAMES)}",
    ),
    "program": Rule(
        keeps_off=False,
        can_act=True,
        per_folder=False,
        met=lambda requirement, pc, _agents: requirement.names[0] in pc.programs,
        reason=lambda requirement, _pc: program_missing(requirement.names[0], requirement.used_for),
    ),
    "python": Rule(
        keeps_off=False,
        can_act=True,
        per_folder=False,
        met=lambda requirement, pc, _agents: (
            pc.python[: len(requirement.version)] >= requirement.version
        ),
        reason=lambda requirement, pc: python_too_old(requirement.version, pc.python),
    ),
}


def quoted(names: Iterable[str]) -> str:
    """Names in quotes, joined with "and", such as "windows", "macos", and "linux"."""
    shown = [f'"{name}"' for name in names]
    if len(shown) < 3:
        return " and ".join(shown)
    return f"{', '.join(shown[:-1])}, and {shown[-1]}"


def closest(word: str, known: Iterable[str]) -> str:
    """The known word that a word this copy doesn't know most likely misspells, compared in any
    case, or "" when none is close enough to suggest. The cutoff takes "progam" for "program" and
    "usedFr" for "usedFor", and nothing for an invented word such as "vpn"."""
    # Imported here, since only a file with a mistake needs it.
    import difflib

    spelled = {name.lower(): name for name in known}
    found = difflib.get_close_matches(word.lower(), spelled, n=1, cutoff=0.8)
    return spelled[found[0]] if found else ""


def outcome(listed: str) -> str:
    """What setup does with an entry of the list that it can't use, said to end a sentence:
    under supportedOn it keeps the skill off, and under dependsOn it ignores the entry."""
    if listed == SUPPORTED_ON:
        return "setup keeps the skill off until it's fixed"
    return "setup ignores it"


def advice(said: str, meant: str, fixes: str, otherwise: str = "") -> str:
    """A mistake's line: what's wrong and what setup did, then, when a known word is close, "Did
    you mean" it, with the fixes that may apply after "If not,". Without one, the fixes alone,
    or otherwise, when it's given."""
    if meant:
        return f'{said} Did you mean "{meant}"? If not, {fixes}'
    rest = otherwise or fixes
    return f"{said} {rest[0].upper()}{rest[1:]}"


def unknown_type(kind: str, listed: str) -> str:
    """The mistake for a type the list doesn't take, said with every fix that may apply, since
    the type may be misspelled, come from a newer dev-home-toolkit, or be made up, and with the
    closest type the list takes, if one is close."""
    said = (
        f'"{kind}" in {listed} is a requirement this dev-home-toolkit doesn\'t know, so '
        f"{outcome(listed)}."
    )
    fixes = (
        f'update dev-home-toolkit to a newer version, or remove "{kind}" from {listed} and '
        "describe it in the compatibility: line at the top of the skill's SKILL.md."
    )
    return advice(said, closest(kind, LISTS[listed]), fixes)


def unknown_field(name: str, known: Iterable[str], *, limit: bool = False) -> str:
    """The mistake for a field in a dev-home-skill.json that this copy doesn't know, among the
    fields known in its place: it may be misspelled, or come from a newer dev-home-toolkit. One in
    an entry of supportedOn (limit) keeps the skill off, since it may narrow where the skill goes,
    such as a minimum version; any other is ignored."""
    meant = closest(name, known)
    update = "update dev-home-toolkit to a newer version"
    if limit:
        said = (
            f'"{name}" in {SUPPORTED_ON} is a field this dev-home-toolkit doesn\'t know, so '
            f"{outcome(SUPPORTED_ON)}."
        )
        return advice(said, meant, f'{update}, or remove "{name}".')
    said = f'"{name}" is a field this dev-home-toolkit doesn\'t know, so setup ignores it.'
    return advice(said, meant, f"{update}.", f'check the spelling of "{name}", or {update}.')


def parse_entry(entry: object, number: int, listed: str) -> tuple[Requirement | None, list[str]]:
    """One entry of a list, and a mistake for each part of it this copy can't use, each a
    sentence. An entry of supportedOn that can't be used counts as one with a mistake, which
    keeps the skill off, since its writer meant to limit where the skill goes; one of dependsOn
    is left out, None. A type the list doesn't take is one this copy doesn't know there, even one
    the other list takes."""
    where = f"entry {number} of {listed}"
    limit = listed == SUPPORTED_ON

    def unusable(kind: str, mistakes: list[str]) -> tuple[Requirement | None, list[str]]:
        return (Requirement(kind, mistake=True) if limit else None), mistakes

    if not isinstance(entry, dict) or not isinstance(entry.get("type"), str):
        return unusable("", [f"{where} isn't a JSON object with a type, so {outcome(listed)}."])
    # A type, and a name in anyOf, match in any case, such as "Program" or "Windows": no two this
    # copy knows differ only in case, so none can match the wrong one.
    kind = entry["type"]
    if kind.lower() not in LISTS[listed]:
        return unusable("", [unknown_type(kind, listed)])
    where = f'{where} (type "{kind}")'
    kind = kind.lower()
    unknown = [field for field in entry if field not in FIELDS[kind]]
    mistakes = [unknown_field(field, FIELDS[kind], limit=limit) for field in unknown]

    def wrong(needs: str) -> tuple[Requirement | None, list[str]]:
        return unusable(kind, [*mistakes, f"{where} needs {needs}, so {outcome(listed)}."])

    if kind in ("os", "agent"):
        known = OS_NAMES if kind == "os" else AGENT_NAMES
        needs = f"anyOf: a list of one or more of {quoted(known)}"
        names = entry.get("anyOf")
        if (
            not isinstance(names, list)
            or not names
            or not all(isinstance(name, str) for name in names)
        ):
            return wrong(needs)
        # A name this copy doesn't know is left out, so a misspelling never matches by accident.
        # It can only add a place, never rule out one that's listed, so the rest still apply.
        mistakes += [
            f'{where} names "{name}", which this dev-home-toolkit doesn\'t know: it knows '
            f"{quoted(known)}."
            for name in names
            if name.lower() not in known
        ]
        kept = tuple(dict.fromkeys(name.lower() for name in names if name.lower() in known))
        if not kept:
            return wrong(needs)
        # A field it doesn't know may narrow the limit, so the skill is kept off.
        return Requirement(kind, kept, mistake=bool(unknown)), mistakes
    if kind == "program":
        name = entry.get("name")
        if not isinstance(name, str) or not PROGRAM_NAME.fullmatch(name):
            return wrong('name: the program\'s name alone, such as "gh"')
        used_for = entry.get("usedFor", "")
        if not isinstance(used_for, str):
            mistakes.append(f"{where}: usedFor isn't text, so it was left out.")
            return Requirement(kind, (name,)), mistakes
        return Requirement(kind, (name,), used_for.strip()), mistakes
    at_least = entry.get("atLeast")
    if not isinstance(at_least, str) or not VERSION.fullmatch(at_least):
        return wrong('atLeast: the lowest version it runs on, in quotes, such as "3.13"')
    return Requirement(kind, version=tuple(int(part) for part in at_least.split("."))), mistakes


def parse_list(value: object, listed: str) -> tuple[tuple[Requirement, ...], list[str]]:
    """The requirements in one of a skill's lists, supportedOn or dependsOn, and a mistake for
    each part of it this copy can't use, each a sentence, for a line that names the file (see
    parse_entry)."""
    if not isinstance(value, list):
        mistake = f"{listed} isn't a list, so {outcome(listed)}."
        return ((Requirement("", mistake=True),) if listed == SUPPORTED_ON else ()), [mistake]
    found: list[Requirement] = []
    mistakes: list[str] = []
    for number, entry in enumerate(value, 1):
        requirement, wrong = parse_entry(entry, number, listed)
        if requirement is not None:
            found.append(requirement)
        mistakes += wrong
    return tuple(found), mistakes


def programs_named(requires: Iterable[Requirement]) -> set[str]:
    """Each program the requirements name, to look for once a run (see this_pc)."""
    return {requirement.names[0] for requirement in requires if requirement.kind == "program"}


def warned_about(requires: Iterable[Requirement]) -> tuple[Requirement, ...]:
    """The requirements setup only warns about, those of dependsOn, which /dev-home skills checks
    again where the agent runs."""
    return tuple(
        requirement
        for requirement in requires
        if not requirement.mistake and not RULES[requirement.kind].keeps_off
    )


def is_file(path: Path) -> bool:
    """Whether a file is there, counting one that can't be looked at, such as in a folder this
    user can't read, as not there."""
    try:
        return path.is_file()
    except OSError:
        return False


def path_folders(path: str) -> list[Path]:
    """The folders a PATH names by their full path. Any other entry is the current folder's,
    which may be a project's, as programs.find_program has it."""
    return [
        Path(folder) for folder in path.split(os.pathsep) if folder and Path(folder).is_absolute()
    ]


def saved_path() -> str:
    """Windows' saved PATH, which every program Windows starts gets: the system's part, then the
    user's, with any %NAME% in them filled in. Read from the registry, which starts no process.
    Empty off Windows, or where it can't be read."""
    if sys.platform != "win32":
        return ""
    parts: list[str] = []
    system = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    for root, key in (
        (winreg.HKEY_LOCAL_MACHINE, system),
        (winreg.HKEY_CURRENT_USER, "Environment"),
    ):
        try:
            with winreg.OpenKey(root, key) as opened:
                value, _ = winreg.QueryValueEx(opened, "Path")
        except OSError:
            continue
        if isinstance(value, str):
            parts.append(winreg.ExpandEnvironmentStrings(value))
    return os.pathsep.join(parts)


def on_path(name: str, folders: Sequence[Path]) -> bool:
    """Whether a program is in one of the folders, as a shell finds it: on Windows, with any of
    the extensions in PATHEXT, such as .exe or .cmd."""
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
    """This PC's operating system, by the name a skill's file uses, or Python's own name for one
    that has none."""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    return sys.platform


def this_pc(programs: Iterable[str]) -> ThisPC:
    """This PC's facts, with each of programs looked for once where a newly started shell would
    look: in this run's PATH, and on Windows also in the saved PATH, so a program installed after
    the agents started still counts. None of it starts a process."""
    wanted = set(programs)
    folders = path_folders(os.environ.get("PATH", ""))
    if wanted:
        folders += [folder for folder in path_folders(saved_path()) if folder not in folders]
    return ThisPC(
        operating_system(),
        tuple(sys.version_info[:3]),
        frozenset(name for name in wanted if on_path(name, folders)),
    )


def unmet(requires: Iterable[Requirement], pc: ThisPC, agents: Collection[str]) -> list[Unmet]:
    """Each of a skill's requirements it doesn't meet in a skills folder that agents read, each by
    the name a skill's file gives it, such as codex. Anything under supportedOn with a mistake
    counts as not met."""
    read_by = frozenset(agents)
    found: list[Unmet] = []
    for requirement in requires:
        if requirement.mistake:
            found.append(Unmet(MISTAKE, keeps_off=True, can_act=True, per_folder=False))
            continue
        rule = RULES[requirement.kind]
        if not rule.met(requirement, pc, read_by):
            reason = rule.reason(requirement, pc)
            found.append(Unmet(reason, rule.keeps_off, rule.can_act, rule.per_folder))
    return found
