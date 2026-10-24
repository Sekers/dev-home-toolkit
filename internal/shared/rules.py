"""The end user's rules in dev-home's rules/, and joining them, after the operating rules, into the
one file setup writes for each agent. The design and its reasons are in docs/development/
decisions/, in decision 0065, "Where end users' rules live", and decision 0066, "Notes in rule
files". This module only reads: setup writes each agent's file, and the my-rules.md files it
finds missing (decision 0064, "Each agent's rules file"). It also works out what setup moves into
rules/ from an agent's file: the lines setup didn't write, with the headings they sat under, the
moved file's name and note, and whether a file there already holds the same text.

rules/ has four levels, and an agent's file joins them in this order, each one's mine/ folder,
the end user's own files:

    rules/_all-agents/              every agent, every PC
    rules/<agent>/                  one agent, every PC: claude-code/, codex/
    rules/pcs/<pc>/_all-agents/     every agent, one PC
    rules/pcs/<pc>/<agent>/         one agent, one PC

then rules/pcs/<pc>/<agent>/unanswered/, the lines setup set aside while it couldn't ask where they
go, each only in the rules file it came from, as its note's from field names it. In each folder,
every .md file joins, subfolders included, alphabetically by path.

Each file is read as UTF-8 unless a byte-order mark says otherwise, and joins with: its note, and
every other HTML comment that starts a line outside fenced code, left out, whole lines and all, as
Claude Code leaves out such comments; a code block it leaves open closed at its end; and its blank
lines at either end dropped. A note, at a file's start, may limit it to some operating systems
with os:, and setup reads no other field there.

Matching headings combine: Markdown headings (one to six #, then a space or the line's end, never
in fenced code) of the same level and text, letter case and surrounding spaces aside, under the
same parent. A merged section sits where its heading first appears, and holds its own text first,
from each file in join order, then its subsections, each where it first appears, but a deeper
heading before a shallower one, so text keeps the heading it had. What a file has outside a
top-level heading of its own goes under # My rules, so none of it reads as part of the operating
rules, and a heading with nothing under it is left out. The operating rules come first and never
merge, and nothing is ever deduplicated.

Setup tells its own lines in an agent's file from anyone else's by the copy it keeps of what it
last wrote there. Joining puts the lines someone added back in the same section, by the headings
they keep, and a file that was there before setup moves whole."""

import bisect
import difflib
import hashlib
import os
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .links import is_link
from .paths import real_path
from .requirements import OS_NAMES, advice, closest, quoted

RULES = "rules"
ALL_AGENTS = "_all-agents"
PCS = "pcs"
MINE = "mine"
UNANSWERED = "unanswered"
MY_RULES = "my-rules.md"
# The heading the end user's rules go under, as many an end user's own rules file starts.
MY_RULES_HEADING = "# My rules"
# The first line of the operating rules, which every rules file setup writes starts with, kept
# first (docs/development/skills.md).
OPERATING_HEADING = "# Private repo: dev-home (rules loaded)"
# What the name of each file setup moves into rules/ starts with (see moved_name).
MOVED = "moved"
# The most pairs of lines matched_lines has difflib compare at once, such as 100 lines with 100.
SMALL_COMPARISON = 10_000
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
    and a line for each problem with it, each naming the file. origin is its note's from field,
    the file setup moved it from, or "" for none."""

    path: Path
    text: str
    systems: tuple[str, ...]
    problems: tuple[str, ...]
    origin: str = ""


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
    """The folder for a PC under rules/pcs/: its name (computer.computer_name) in lowercase, with
    any other character than a letter or a digit as a hyphen, cut to PC_NAME_LIMIT. An empty
    name, which would make this PC's levels look like another PC's folders, is pc."""
    return re.sub(r"[^a-z0-9]", "-", computer_name.lower())[:PC_NAME_LIMIT] or "pc"


def copy_name(folder: Path) -> str:
    """The name of the copy setup keeps of a file it last wrote, by where it wrote it: an agent's
    folder, for the rules file there, or a file's own path, for dev-home's AGENTS.md and
    CLAUDE.md. It's that path in lowercase, with each run of other characters than letters and
    digits as one hyphen, and a short hash of the path, so two paths that differ only in such
    characters never share a copy."""
    full = str(folder).lower()
    readable = re.sub(r"[^a-z0-9]+", "-", full).strip("-")[-60:]
    return f"{readable}-{hashlib.sha256(full.encode('utf-8')).hexdigest()[:8]}.md"


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
    fields = note_fields(lines)
    os_field = fields.get("os")
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
    text = "\n".join(trimmed(kept))
    return RuleFile(path, text, systems, tuple(problems), fields.get("from", ""))


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


def under_my_rules(file: Section) -> Section:
    """A file's tree with what it has outside a top-level heading of its own, its text before any
    heading and any deeper heading before its first top-level one, moved under # My rules. Without
    a heading, those rules would follow the operating rules' last line as if they were part of
    them, and wouldn't combine with what other files have under # My rules."""
    text = [chunk for chunk in map(trimmed, file.chunks) if chunk]
    # A deeper heading is only ever outside a top-level one before the file's first top-level one,
    # so # My rules goes first, where those rules were.
    deeper = [child for child in file.children if child.level > 1]
    top = [child for child in file.children if child.level == 1]
    if not text and not deeper:
        return Section(file.heading, 0, file.key, [], top)
    mine = parsed(MY_RULES_HEADING).children[0]
    mine.chunks, mine.children = text, deeper
    return Section(file.heading, 0, file.key, [], [mine, *top])


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
    other way round, from different files. A heading with nothing under it holds no rule, so it's
    left out."""
    children = sorted(section.children, key=lambda child: -child.level)
    blocks = [*section.chunks, *(block for child in children if (block := rendered(child)))]
    if section.level and not blocks:
        return []
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
            merge(root, under_my_rules(parsed(text)))
    return "\n".join(rendered(root))


def joined_rules(
    operating: str, rules_root: Path, pc: str, agent: str, system: str, source: Path | None = None
) -> Joined:
    """An agent's rules on a PC whose operating system is system, by the name a skill's file
    uses: the operating rules' text, then the end user's files in rules_root, joined, for source,
    the agent's rules file setup writes them into. A file in this PC's unanswered/ joins only for
    the rules file its note's from field names, the one setup set it aside from (see came_from):
    until a person says where its lines go, they load only where they were."""
    texts: list[str] = []
    problems: list[str] = []
    waiting = Path(PCS, pc, agent, UNANSWERED)
    for folder in joined_folders(pc, agent):
        for path in markdown_files(rules_root / folder):
            rule = read_rule(path)
            problems += rule.problems
            if folder == waiting and not came_from(rule, source):
                continue
            if not rule.systems or system in rule.systems:
                texts.append(rule.text)
    own = join(texts)
    parts = [operating.strip("\n"), own] if own else [operating.strip("\n")]
    return Joined("\n\n".join(parts) + "\n", len(own.encode("utf-8")), problems)


def already_held(
    text: str,
    rules_root: Path,
    pc: str,
    agent: str,
    system: str,
    source: Path | None,
    skip: Path | None = None,
) -> Path | None:
    """The file that already holds text, rules setup is about to move into rules/ from source, an
    agent's rules file, where it joins for that file on a PC whose operating system is system:
    any level's mine/ for agent on this PC, or a file in this PC's unanswered/ that came from
    source, other than skip (see duplicate_of). Added again, the rules would load twice. One set
    aside from another file loads only there, and one whose note's os field leaves this system
    out doesn't load here, so neither counts. None when no file does."""
    wanted = evened(text)
    waiting = Path(PCS, pc, agent, UNANSWERED)
    for folder in joined_folders(pc, agent):
        for path in markdown_files(rules_root / folder):
            if path == skip or not holds(path, wanted):
                continue
            rule = read_rule(path)
            if rule.systems and system not in rule.systems:
                continue
            if folder != waiting or came_from(rule, source):
                return path
    return None


def came_from(rule: RuleFile, source: Path | None) -> bool:
    """Whether a rule file's note names source, an agent's rules file, as the file setup moved it
    from, following links, since two folders can lead to one file through a junction."""
    return bool(source and rule.origin) and real_path(rule.origin) == real_path(str(source))


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


# What setup moves into rules/ from an agent's file


@dataclass(frozen=True)
class ToMove:
    """What setup moves into rules/ from an agent's rules file: text, as a file of its own, or ""
    when there's nothing to move; and whole, set when that's the whole file, one that was there
    before setup wrote its own."""

    text: str
    whole: bool = False


@dataclass(frozen=True)
class Context:
    """Where a line of a file sits: the headings it's under, outermost first, the one open at each
    level, and fence, the line that opened the code block it's in, or "" outside one."""

    headings: tuple[str, ...]
    fence: str


def to_move(current: str, kept: str | None, new: str, operating: str) -> ToMove:
    """What setup moves into rules/ from an agent's rules file, current, before it writes new there
    (decision 0064, "Each agent's rules file"): the lines that aren't in kept, the copy of what it
    last wrote there. With no copy, a file that doesn't start with the operating rules' heading
    isn't setup's, so it moves whole. One that does is setup's own, from another PC or from before
    its copy was lost, so the lines that aren't in new move, though they may be setup's own older
    text. Nothing moves from a file of blank lines alone. operating is the operating rules as setup
    writes them now (see added_text)."""
    if not current.strip():
        return ToMove("")
    if kept is not None:
        return ToMove(added_text(current, kept, operating))
    if not current.startswith(OPERATING_HEADING):
        return ToMove("\n".join(trimmed(current.split("\n"))), whole=True)
    return ToMove(added_text(current, new, operating))


def added_text(current: str, before: str, operating: str) -> str:
    """The lines in current that aren't in before, as the text of a file of their own, or "" when
    only blank lines were added. Each run of added lines keeps the headings it sat under, so
    joining puts it back in the same section, and runs under the same heading share it. A line
    under one of the top-level headings in operating, the operating rules, keeps none, since those
    aren't the end user's headings, and goes under # My rules, as joining puts any line outside a
    heading. A run that starts or ends inside a code block gets that block's fence, so it stays
    code. Lines are compared without the spaces at their ends, so an editor that trims them adds
    nothing (see matched_lines)."""
    lines = current.split("\n")
    matched = matched_lines(
        [line.rstrip() for line in before.split("\n")], [*map(str.rstrip, lines)]
    )
    runs: list[tuple[int, int]] = []
    start = -1
    for index in range(len(lines) + 1):
        if index < len(lines) and index not in matched:
            start = index if start < 0 else start
            continue
        if start >= 0 and any(line.strip() for line in lines[start:index]):
            runs.append((start, index))
        start = -1
    contexts = contexts_at(lines, [start for start, _ in runs], top_level_keys(operating))
    return join(run_text(lines[start:end], contexts[start]) for start, end in runs)


def matched_lines(before: Sequence[str], after: Sequence[str]) -> set[int]:
    """The lines of after, by index, that match lines of before in the same order, found as
    patience diff finds them (git diff --patience): the lines both share at either end match,
    then the lines that occur once on each side, in the longest run in the same order in both,
    anchor the rest, and the lines between two anchors are compared the same way. Where no line
    between them occurs once on each side, difflib compares them when they're few, and none match
    when they're many. difflib alone takes minutes on a large file whose lines repeat, such as
    blank lines and code fences, since it tries every pair of them."""
    matched: set[int] = set()
    pending = [(0, len(before), 0, len(after))]
    while pending:
        low, high, after_low, after_high = pending.pop()
        while low < high and after_low < after_high and before[low] == after[after_low]:
            matched.add(after_low)
            low, after_low = low + 1, after_low + 1
        while low < high and after_low < after_high and before[high - 1] == after[after_high - 1]:
            high, after_high = high - 1, after_high - 1
            matched.add(after_high)
        if low == high or after_low == after_high:
            continue
        anchors = unique_anchors(before, after, (low, high), (after_low, after_high))
        if anchors:
            for index, after_index in anchors:
                matched.add(after_index)
                pending.append((low, index, after_low, after_index))
                low, after_low = index + 1, after_index + 1
            pending.append((low, high, after_low, after_high))
        elif (high - low) * (after_high - after_low) <= SMALL_COMPARISON:
            blocks = difflib.SequenceMatcher(
                None, before[low:high], after[after_low:after_high], autojunk=False
            ).get_matching_blocks()
            for block in blocks:
                matched.update(range(after_low + block.b, after_low + block.b + block.size))
    return matched


def unique_anchors(
    before: Sequence[str],
    after: Sequence[str],
    span: tuple[int, int],
    after_span: tuple[int, int],
) -> list[tuple[int, int]]:
    """The lines that occur once in before's span and once in after's, as pairs of their indexes,
    the longest run of them in the same order in both, found by patience sorting."""

    def once(lines: Sequence[str], low: int, high: int) -> dict[str, int]:
        found: dict[str, int] = {}
        for index in range(low, high):
            found[lines[index]] = -1 if lines[index] in found else index
        return found

    in_after = once(after, *after_span)
    pairs = sorted(
        (
            (index, in_after[line])
            for line, index in once(before, *span).items()
            if index >= 0 and in_after.get(line, -1) >= 0
        ),
        key=lambda pair: pair[1],
    )
    # Patience sorting: tops holds, for each length of run so far, the smallest index in before
    # that ends one, and ends which pair that is; back links each pair to the one before it.
    tops: list[int] = []
    ends: list[int] = []
    back: list[int] = []
    for number, (index, _) in enumerate(pairs):
        place = bisect.bisect_left(tops, index)
        back.append(ends[place - 1] if place else -1)
        if place == len(tops):
            tops.append(index)
            ends.append(number)
        else:
            tops[place], ends[place] = index, number
    run: list[tuple[int, int]] = []
    number = ends[-1] if ends else -1
    while number >= 0:
        run.append(pairs[number])
        number = back[number]
    return run[::-1]


def top_level_keys(operating: str) -> set[tuple[int, str]]:
    """What the operating rules' top-level headings match others by (see heading_key): those in
    operating, outside fenced code, and always OPERATING_HEADING."""
    keys = {section.key for section in parsed(operating).children if section.level == 1}
    return keys | {heading_key(1, OPERATING_HEADING[2:])}


def contexts_at(
    lines: Sequence[str], starts: Sequence[int], operating: set[tuple[int, str]]
) -> dict[int, Context]:
    """Where each line in starts sits in lines (see Context), in one pass. A line whose outermost
    heading is one of operating's keys sits under no headings."""
    wanted = set(starts)
    found: dict[int, Context] = {}
    open_headings: list[tuple[int, tuple[int, str], str]] = []
    fence = fence_line = ""
    for index, line in enumerate(lines[: max(starts, default=-1) + 1]):
        if index in wanted:
            mine = not open_headings or open_headings[0][1] not in operating
            headings = tuple(heading for _, _, heading in open_headings) if mine else ()
            found[index] = Context(headings, fence_line)
        if fence:
            if closes(fence, line):
                fence = fence_line = ""
            continue
        if opened := FENCE.match(line):
            fence, fence_line = opened.group(1), line
            continue
        heading = HEADING.match(line)
        if heading is None:
            continue
        level = len(heading.group(1))
        while open_headings and open_headings[-1][0] >= level:
            open_headings.pop()
        open_headings.append((level, heading_key(level, heading.group(2) or ""), line))
    return found


def run_text(run: Sequence[str], context: Context) -> str:
    """A run of added lines as it moves, without blank lines at either end: after the headings it
    sat under, and inside the fence of the code block it starts in, if any, with a code block it
    leaves open closed right after its last line."""
    run = trimmed(run)
    fence = ""
    if context.fence:
        opened = FENCE.match(context.fence)
        fence = opened.group(1) if opened else ""
    for line in run:
        if fence:
            if closes(fence, line):
                fence = ""
        elif opened := FENCE.match(line):
            fence = opened.group(1)
    fenced = [context.fence] if context.fence else []
    closing = [fence] if fence else []
    return "\n".join([*context.headings, *fenced, *run, *closing])


def slug(text: str) -> str:
    """text in lowercase, with each run of other characters than letters and digits as one hyphen,
    and none at either end."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def moved_name(pc: str, folder: Path, path: Path, taken: Iterable[str]) -> str:
    """The name of a file setup moves into a mine/ or unanswered/ folder (decision 0066, "Notes in
    rule files"): moved-<pc>-<folder>-<path>.md, where <pc> is this PC's folder under pcs/ (see
    pc_folder), <folder> the agent folder's name, such as codex for ~/.codex, and <path> the
    file's path inside it, path, without .md, each as slug writes it. The whole name, .md
    included, is cut to MOVED_NAME_LIMIT. A name in taken, the names already in that folder, in
    any letter case, gets the first free -2, -3, and so on before .md, still within the limit, so a
    file already there is never overwritten."""
    inner = path.as_posix()
    if inner.lower().endswith(".md"):
        inner = inner[: -len(".md")]
    stem = "-".join(part for part in (MOVED, slug(pc), slug(folder.name), slug(inner)) if part)
    return free_name(stem, taken)


def free_name(stem: str, taken: Iterable[str]) -> str:
    """stem.md, cut to MOVED_NAME_LIMIT, .md included, or when a name in taken is that, in any
    letter case, the first free stem-2.md, stem-3.md, and so on, still within the limit."""
    used = {name.lower() for name in taken}
    number = 1
    while True:
        suffix = f"-{number}" if number > 1 else ""
        name = stem[: MOVED_NAME_LIMIT - len(".md") - len(suffix)].rstrip("-") + suffix + ".md"
        if name.lower() not in used:
            return name
        number += 1


def moved_file(text: str, *, when: datetime, pc: str, source: Path, about: str) -> str:
    """A file setup moves into rules/, as it writes it: a note saying who moved it, when, on which
    PC, and from where, with about, a sentence on what it holds, then text (decision 0066). when
    carries its offset from UTC, as datetime.now().astimezone() gives it, and pc is the PC's
    folder under pcs/."""
    note = [
        NOTE_START,
        "by: setup",
        f"when: {when.isoformat(sep=' ', timespec='seconds')}",
        f"pc: {pc}",
        f"from: {source}",
        "",
        about,
        "-->",
    ]
    return "\n".join([*note, "", text.strip("\n"), ""])


def duplicate_of(text: str, folder: Path, skip: Path | None = None) -> Path | None:
    """The file in folder, subfolders included, that already holds text, a file setup is about to
    move there, so setup doesn't add it twice (decision 0066): the same text, each without its
    note, and with line endings and blank lines at either end evened out. None when none does,
    other than skip, the file the text comes from."""
    wanted = evened(text)
    return next(
        (path for path in markdown_files(folder) if path != skip and holds(path, wanted)), None
    )


def holds(path: Path, wanted: str) -> bool:
    """Whether a file holds wanted, a text as evened gives it."""
    try:
        data = path.read_bytes()
    except OSError:
        return False
    return evened(decode(path, data)[0]) == wanted


def evened(text: str) -> str:
    """text without the note it starts with, if any, with LF line breaks and no blank lines at
    either end, as duplicate_of compares files."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(trimmed(without_note(lines)))


def without_note(lines: Sequence[str]) -> list[str]:
    """lines without the note they start with, if they start with one: through the line where it
    ends, or all of them, when it never ends."""
    start = next((index for index, line in enumerate(lines) if line.strip()), len(lines))
    if start == len(lines) or lines[start].strip() != NOTE_START:
        return list(lines)
    end = next((index for index in range(start + 1, len(lines)) if "-->" in lines[index]), None)
    return [] if end is None else list(lines[end + 1 :])


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
