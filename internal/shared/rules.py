"""The end user's rules in dev-home's rules/, and joining them, after the operating rules, into the
one file setup writes for each agent. The design and its reasons are in docs/development/
decisions/, in decision 0065, "Where end users' rules live", and decision 0066, "Notes in rule
files". This module only reads: setup writes each agent's file (decision 0064, "Each agent's rules
file").

rules/ has four levels, and an agent's file joins them in this order, each one's mine/ folder,
the end user's own files:

    rules/_all-agents/              every agent, every PC
    rules/<agent>/                  one agent, every PC: claude-code/, codex/
    rules/pcs/<pc>/_all-agents/     every agent, one PC
    rules/pcs/<pc>/<agent>/         one agent, one PC

then rules/pcs/<pc>/<agent>/unanswered/, the lines setup set aside while it couldn't ask where they
go. In each folder, every .md file joins, subfolders included, alphabetically by path.

Each file is read as UTF-8 unless a byte-order mark says otherwise, and joins with: its note, and
every other HTML comment that starts a line outside fenced code, left out, whole lines and all, as
Claude Code leaves out such comments; a code block it leaves open closed at its end; and its blank
lines at either end dropped. A note, at a file's start, may limit it to some operating systems
with os:, and setup reads no other field there.

Matching headings combine: Markdown headings (one to six #, then a space or the line's end, never
in fenced code) of the same level and text, letter case and surrounding spaces aside, under the
same parent. A merged section sits where its heading first appears, and holds its own text first,
from each file in join order, then its subsections, each where it first appears, but a deeper
heading before a shallower one, so text keeps the heading it had. Text before a file's first
heading goes first, for the same reason. The
operating rules come first and never merge, and nothing is ever deduplicated."""

import os
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .links import is_link
from .requirements import OS_NAMES, advice, closest, quoted

RULES = "rules"
ALL_AGENTS = "_all-agents"
PCS = "pcs"
MINE = "mine"
UNANSWERED = "unanswered"
MY_RULES = "my-rules.md"
# The longest a name in rules/ may be (decision 0065): a PC's folder, an agent's folder, a
# built-in rule's name, and the name of a file setup moves there, .md included.
PC_NAME_LIMIT = 32
AGENT_NAME_LIMIT = 24
BUILT_IN_NAME_LIMIT = 40
MOVED_NAME_LIMIT = 60
# Windows refuses a longer path by default, and git needs room beyond a file's own path for the
# files it writes beside it.
PATH_LIMIT = 260
PATH_ROOM = 30

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
CLOSING_HASHES = re.compile(r"(?:^|[ \t]+)#+$")
NOTE_START = "<!-- note"
NOTE_FIELD = re.compile(r"([A-Za-z0-9-]+):(.*)")


@dataclass(frozen=True)
class RuleFile:
    """A rule file as it joins: its text, the operating systems its note limits it to, if any,
    and a line for each problem with it, each naming the file."""

    path: Path
    text: str
    systems: tuple[str, ...]
    problems: tuple[str, ...]


@dataclass(frozen=True)
class Joined:
    """An agent's rules on one PC: the operating rules, then the end user's rules joined, and how
    many bytes the end user's part takes as UTF-8, with a line for each problem with their files."""

    text: str
    own_bytes: int
    problems: list[str]


@dataclass
class Section:
    """A heading and what's under it, or with level 0, the whole of a file or of the joined rules.
    chunks are its own text, one list of lines from each file, and children its subsections."""

    heading: str
    level: int
    key: tuple[int, str]
    chunks: list[list[str]] = field(default_factory=list)
    children: list["Section"] = field(default_factory=list)


def pc_folder(computer_name: str) -> str:
    """The folder for a PC under rules/pcs/: its computer name in lowercase, with any other
    character than a letter or a digit as a hyphen, cut to PC_NAME_LIMIT."""
    return re.sub(r"[^a-z0-9]", "-", computer_name.lower())[:PC_NAME_LIMIT]


def levels(pc: str, agent: str) -> list[Path]:
    """The four levels for an agent on a PC, in the order they join, relative to rules/."""
    return [Path(ALL_AGENTS), Path(agent), Path(PCS, pc, ALL_AGENTS), Path(PCS, pc, agent)]


def joined_folders(pc: str, agent: str) -> list[Path]:
    """The folders whose files join for an agent on a PC, in order, relative to rules/."""
    return [*(level / MINE for level in levels(pc, agent)), Path(PCS, pc, agent, UNANSWERED)]


def markdown_files(folder: Path) -> list[Path]:
    """Every .md file in folder and its subfolders, alphabetically by its path there, in any
    letter case first. A linked folder isn't followed, so a link can't loop."""
    found: list[Path] = []

    def walk(current: Path) -> None:
        try:
            entries = list(os.scandir(current))
        except OSError:
            return
        for entry in entries:
            path = Path(entry.path)
            if entry.is_dir():
                if not is_link(path):
                    walk(path)
            elif entry.is_file() and path.suffix.lower() == ".md":
                found.append(path)

    walk(folder)

    def by_path(path: Path) -> tuple[str, str]:
        relative = path.relative_to(folder).as_posix()
        return relative.casefold(), relative

    return sorted(found, key=by_path)


def decode(path: Path, data: bytes) -> tuple[str, list[str]]:
    """A file's text, with LF line breaks, and a line for each way its bytes aren't clean UTF-8.
    A byte-order mark decides between UTF-8 and UTF-16; anything else is read as UTF-8, with the
    replacement character for each byte that isn't, and NUL bytes left out. Setup never rewrites
    the file: the end user saves it as UTF-8."""
    problems: list[str] = []
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = data.decode("utf-16", errors="replace")
        problems.append(
            f"{path} is saved as UTF-16, which git counts as binary, so a sync can't merge it: "
            "save it as UTF-8."
        )
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("utf-8-sig", errors="replace")
            problems.append(
                f"{path} isn't saved as UTF-8, so setup reads each byte that isn't as the "
                "replacement character: save it as UTF-8."
            )
    if "\x00" in text:
        text = text.replace("\x00", "")
        problems.append(
            f"{path} has NUL bytes, which setup leaves out, and which make git count it as "
            "binary: save it as UTF-8 without them."
        )
    return text.replace("\r\n", "\n").replace("\r", "\n"), problems


def note_fields(lines: Sequence[str]) -> dict[str, str]:
    """The fields of the note a file starts with, if it has one: an HTML comment whose first line
    is only "note", then a field to a line, "name: value", until the first line that isn't one.
    Names are read in any case, a value is the rest of its line, with one pair of quotes around
    it forgiven, and a field written twice counts its last value."""
    first = next((line for line in lines if line.strip()), "")
    if first.strip() != NOTE_START:
        return {}
    fields: dict[str, str] = {}
    for line in lines[lines.index(first) + 1 :]:
        text, ends, _ = line.partition("-->")
        found = NOTE_FIELD.fullmatch(text.strip())
        if found is None:
            break
        value = found.group(2).strip()
        if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        fields[found.group(1).lower()] = value
        if ends:
            break
    return fields


def closes(fence: str, line: str) -> bool:
    """Whether line closes a code block that fence, such as ```, opened."""
    stripped = line.strip()
    return (
        len(line) - len(line.lstrip(" ")) <= 3
        and len(stripped) >= len(fence)
        and set(stripped) == {fence[0]}
    )


def without_comments(lines: Sequence[str]) -> tuple[list[str], bool, str]:
    """lines without each HTML comment that starts a line outside fenced code, whole lines and
    all, with a code block left open closed at the end. Also whether a comment never ended, and
    so went to the end, and the fence of a code block that never closed, or ""."""
    kept: list[str] = []
    fence = ""
    in_comment = False
    for line in lines:
        if in_comment:
            in_comment = "-->" not in line
            continue
        if fence:
            kept.append(line)
            if closes(fence, line):
                fence = ""
            continue
        opened = FENCE.match(line)
        if opened:
            fence = opened.group(1)
            kept.append(line)
            continue
        stripped = line.lstrip(" ")
        if len(line) - len(stripped) <= 3 and stripped.startswith("<!--"):
            # From the second character, so <!--> and <!---> end where they start, as in Markdown.
            in_comment = "-->" not in stripped[2:]
            continue
        kept.append(line)
    if fence:
        # Right after the last line that isn't blank, since the blank lines after it are the
        # file's own end, which joining drops.
        kept = trimmed(kept)
        kept.append(fence)
    return kept, in_comment, fence


def trimmed(lines: Sequence[str]) -> list[str]:
    """lines without the blank ones at either end."""
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return list(lines[start:end])


def systems_in(path: Path, value: str) -> tuple[tuple[str, ...], list[str]]:
    """The operating systems a note's os field names, or () for every system, when it names none,
    or one this dev-home-toolkit doesn't know, since dropping a needed rule costs more than loading
    an extra one. With a line for each name it doesn't know."""
    names = [name.strip() for name in value.split(",") if name.strip()]
    unknown = [name for name in names if name.lower() not in OS_NAMES]
    problems = []
    for name in unknown:
        said = (
            f"{path} names \"{name}\" in its note's os: field, which this dev-home-toolkit doesn't "
            "know, so the rule loads on every system."
        )
        fixes = f"name one or more of {quoted(OS_NAMES)}, separated by commas."
        problems.append(advice(said, closest(name, OS_NAMES), fixes))
    if unknown or not names:
        return (), problems
    return tuple(dict.fromkeys(name.lower() for name in names)), problems


def read_rule(path: Path) -> RuleFile:
    """A rule file as it joins (see the description above)."""
    try:
        data = path.read_bytes()
    except OSError as error:
        return RuleFile(path, "", (), (f"{path} couldn't be read, so it's left out: {error}",))
    text, problems = decode(path, data)
    lines = text.split("\n")
    systems: tuple[str, ...] = ()
    os_field = note_fields(lines).get("os")
    if os_field is not None:
        systems, found = systems_in(path, os_field)
        problems += found
    kept, unended, fence = without_comments(lines)
    if unended:
        problems.append(
            f"{path} has a comment, <!--, that never ends with -->, so setup leaves out "
            "everything from there to the file's end: end the comment."
        )
    if fence:
        problems.append(
            f"{path} opens a code block with {fence} that never closes, so setup closes it at the "
            "file's end: close it where it should end."
        )
    return RuleFile(path, "\n".join(trimmed(kept)), systems, tuple(problems))


def heading_key(level: int, text: str) -> tuple[int, str]:
    """What a heading matches others by: its level, and its text, without a closing run of #,
    surrounding spaces, or letter case."""
    return level, CLOSING_HASHES.sub("", text).strip().casefold()


def parsed(text: str) -> Section:
    """A file's text as a tree of its headings."""
    root = Section("", 0, (0, ""), [[]])
    open_sections = [root]
    fence = ""
    for line in text.split("\n"):
        heading = None if fence else HEADING.match(line)
        if fence:
            if closes(fence, line):
                fence = ""
        elif opened := FENCE.match(line):
            fence = opened.group(1)
        if heading is None:
            open_sections[-1].chunks[0].append(line)
            continue
        level = len(heading.group(1))
        while open_sections[-1].level >= level:
            open_sections.pop()
        section = Section(line, level, heading_key(level, heading.group(2) or ""), [[]])
        open_sections[-1].children.append(section)
        open_sections.append(section)
    return root


def merge(into: Section, part: Section) -> None:
    """Adds part, a section of one file, to into, its match in the joined rules."""
    into.chunks += [chunk for chunk in map(trimmed, part.chunks) if chunk]
    for child in part.children:
        match = next((section for section in into.children if section.key == child.key), None)
        if match is None:
            match = Section(child.heading, child.level, child.key)
            into.children.append(match)
        merge(match, child)


def rendered(section: Section) -> list[str]:
    """A joined section's lines: its heading, then each chunk of its own text and each
    subsection, with a blank line between them. A subsection with a deeper heading goes before
    one with a shallower heading, which would otherwise take it in: only merging puts them the
    other way round, from different files."""
    children = sorted(section.children, key=lambda child: -child.level)
    blocks = [*section.chunks, *(rendered(child) for child in children)]
    lines = [section.heading] if section.level else []
    for block in blocks:
        if lines:
            lines.append("")
        lines += block
    return lines


def join(texts: Iterable[str]) -> str:
    """The end user's rule files' texts, in join order, joined, with their headings combined."""
    root = Section("", 0, (0, ""))
    for text in texts:
        if text:
            merge(root, parsed(text))
    return "\n".join(rendered(root))


def joined_rules(operating: str, rules_root: Path, pc: str, agent: str, system: str) -> Joined:
    """An agent's rules on a PC whose operating system is system, by the name a skill's file
    uses: the operating rules' text, then the end user's files in rules_root, joined."""
    texts: list[str] = []
    problems: list[str] = []
    for folder in joined_folders(pc, agent):
        for path in markdown_files(rules_root / folder):
            rule = read_rule(path)
            problems += rule.problems
            if not rule.systems or system in rule.systems:
                texts.append(rule.text)
    own = join(texts)
    parts = [operating.strip("\n"), own] if own else [operating.strip("\n")]
    return Joined("\n\n".join(parts) + "\n", len(own.encode("utf-8")), problems)


def stray_files(rules_root: Path, pc: str, agents: Iterable[str]) -> list[Path]:
    """Each .md file directly in a level folder, for the agents set up on this PC, which never
    joins: the end user's files go in mine/. Any other file there, such as one Windows keeps a
    folder's settings in, is left alone."""
    folders = dict.fromkeys(level for agent in agents for level in levels(pc, agent))
    found: list[Path] = []
    for folder in folders:
        try:
            entries = sorted(os.scandir(rules_root / folder), key=lambda entry: entry.name)
        except OSError:
            continue
        found += [
            Path(entry.path)
            for entry in entries
            if entry.is_file() and Path(entry.name).suffix.lower() == ".md"
        ]
    return found


def stray_file_problem(rules_root: Path, path: Path) -> str:
    level = path.parent.relative_to(rules_root.parent).as_posix()
    return (
        f"{path} is directly in {level}/, where setup doesn't read rules, so no agent loads it: "
        f"move it into {level}/{MINE}/."
    )


def missing_my_rules(rules_root: Path, pc: str, agents: Iterable[str]) -> list[Path]:
    """Each my-rules.md setup makes sure is there, empty when it makes it, for every agent and for
    each agent set up on this PC, at both the every-PC and this PC's levels, that's missing, in any
    letter case. Setup never touches another file in mine/."""
    folders = dict.fromkeys(level / MINE for agent in agents for level in levels(pc, agent))
    missing: list[Path] = []
    for folder in folders:
        try:
            names = {entry.name.lower() for entry in os.scandir(rules_root / folder)}
        except OSError:
            names = set()
        if MY_RULES not in names:
            missing.append(rules_root / folder / MY_RULES)
    return missing


def longest_rules_path() -> int:
    """The longest path in rules/ that the caps allow, from dev-home's folder: a file setup moves
    into a PC's unanswered/ folder for an agent."""
    parts = (RULES, PCS, "p" * PC_NAME_LIMIT, "a" * AGENT_NAME_LIMIT, UNANSWERED)
    return len("/".join(parts)) + 1 + MOVED_NAME_LIMIT


def path_problem(dev_home: Path) -> str:
    """A line when dev-home's folder is too long for the longest path in rules/, with room for git,
    to stay under Windows' limit, or "" when it fits."""
    allowed = PATH_LIMIT - PATH_ROOM - longest_rules_path() - 2
    if len(str(dev_home)) <= allowed:
        return ""
    return (
        f"dev-home's folder, {dev_home}, is {len(str(dev_home))} characters long, and the longest "
        f"path setup may make in it would pass Windows' limit of {PATH_LIMIT} characters. Move "
        f"dev-home to a folder of {allowed} characters or fewer, such as C:\\Programming\\dev-home."
    )
