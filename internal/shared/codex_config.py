"""Codex's config.toml: whether it lets Codex write to dev-home and read long AGENTS.md files, and
planning the change that does both; and the [[skills.config]] entries that hide a skill in that
Codex home, which setup adds and removes. Python can read TOML but not write it, and a rewrite
would lose the person's comments and layout, so each change is made as whole-line insertions,
edits, and removals by a reader that follows only the TOML it needs, and refuses anything else."""

import copy
import json
import re
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import same_path
from .settings_files import Plan, read_settings_file, to_lines

MULTI_LINE_STRING = re.compile(r"'''|\"\"\"")


@dataclass(frozen=True)
class Header:
    name: str
    line: int
    is_array: bool


@dataclass
class Key:
    """A key's table, its name as written, and the lines its value spans."""

    table: str
    name: str
    start: int
    end: int


@dataclass
class Layout:
    headers: list[Header] = field(default_factory=list)
    keys: list[Key] = field(default_factory=list)
    reason: str | None = None


def path_pattern(path: str) -> str:
    """Matches the path inside a TOML string, written with single or doubled slashes of either
    kind, but not a longer path that starts the same way. Use it ignoring case."""
    parts = [re.escape(part) for part in re.split(r"[\\/]+", path) if part]
    return r"[\\/]{1,2}".join(parts) + r"[\\/]{0,2}['\"]"


def masked_line(line: str) -> str | None:
    """A line with the insides of strings replaced by underscores and any comment cut off, so
    brackets, dots, and equals signs in strings can't pass for structure. Positions still match
    the original line. None when a string doesn't close."""
    out: list[str] = []
    quote = ""
    index = 0
    while index < len(line):
        char = line[index]
        if not quote:
            if char == "#":
                break
            if char in "\"'":
                quote = char
            out.append(char)
        elif char == quote:
            quote = ""
            out.append(char)
        elif quote == '"' and char == "\\" and index + 1 < len(line):
            out.append("__")
            index += 1
        else:
            out.append("_")
        index += 1
    return None if quote else "".join(out)


def depth_change(masked: str) -> int:
    """Brackets and braces opened minus closed, in a masked line."""
    return sum(masked.count(c) for c in "[{") - sum(masked.count(c) for c in "]}")


def read_layout(lines: list[str]) -> Layout:
    """The tables and keys, as far as setup needs them: each key's table and the lines its value
    spans. Sets reason instead when the file uses TOML this reader doesn't follow, so setup never
    edits a file it hasn't fully understood."""
    layout = Layout()
    table = ""
    depth = 0
    key: Key | None = None
    for index, line in enumerate(lines):
        masked = masked_line(line)
        if masked is None:
            layout.reason = f"line {index + 1} has a string that does not close on that line"
            return layout
        if depth > 0 and key is not None:
            depth += depth_change(masked)
            key.end = index
            if depth < 0:
                layout.reason = f"line {index + 1} closes more brackets than were opened"
                return layout
            continue
        if not masked.strip():
            continue
        header = re.match(r"\s*(\[\[?)([^\[\]]+)(\]\]?)\s*$", masked)
        if header and len(header.group(1)) == len(header.group(3)):
            table = line[header.start(2) : header.end(2)].strip()
            layout.headers.append(Header(table, index, len(header.group(1)) == 2))
            continue
        assignment = re.match(r"\s*([^=\[\]\{\}]+?)\s*=(.*)$", masked)
        if assignment:
            key = Key(table, line[assignment.start(1) : assignment.end(1)], index, index)
            layout.keys.append(key)
            depth = depth_change(assignment.group(2))
            if depth < 0:
                layout.reason = f"line {index + 1} closes more brackets than it opens"
                return layout
            continue
        layout.reason = f"line {index + 1} is not a table, a key, or a comment"
        return layout
    if depth != 0:
        layout.reason = "a list or inline table does not close"
    return layout


def value_text(lines: list[str], key: Key) -> str:
    """A key's lines joined, with any comments cut off, so a commented-out path doesn't count."""
    code: list[str] = []
    for index in range(key.start, key.end + 1):
        masked = masked_line(lines[index]) or ""
        code.append(lines[index][: len(masked)])
    return "\n".join(code)


def is_configured(text: str, writable_root: str, min_doc_bytes: int) -> bool:
    """Whether the text has writable_root in [sandbox_workspace_write] writable_roots, and a
    top-level project_doc_max_bytes of at least min_doc_bytes. Comments and other tables don't
    count. For a file the reader can't follow, it falls back to a plain text search."""
    pattern = path_pattern(writable_root)
    lines = to_lines(text)
    layout = None if MULTI_LINE_STRING.search(text) else read_layout(lines)
    if layout is None or layout.reason:
        roots = re.search(r"writable_roots\s*=\s*\[[^\]]*" + pattern, text, re.IGNORECASE)
        max_bytes = re.search(r"(?m)^\s*project_doc_max_bytes\s*=\s*(\d+)", text)
        return (
            roots is not None and max_bytes is not None and int(max_bytes.group(1)) >= min_doc_bytes
        )
    has_root = False
    has_max_bytes = False
    for key in layout.keys:
        if key.table == "" and key.name == "project_doc_max_bytes":
            number = re.search(r"=\s*([0-9][0-9_]*)\s*$", value_text(lines, key))
            if number and int(number.group(1).replace("_", "")) >= min_doc_bytes:
                has_max_bytes = True
        elif (
            key.table == "sandbox_workspace_write"
            and key.name == "writable_roots"
            and re.search(pattern, value_text(lines, key), re.IGNORECASE)
        ):
            has_root = True
    return has_root and has_max_bytes


def names_key(name: str, key: Key) -> bool:
    """Whether a key is this setting in any form: quoted, in another case, or with a dotted part
    after it, such as writable_roots.x. Only the plain form gets edited; the others are
    refused."""
    return re.match(rf"[\"']?{name}[\"']?\s*(\.|$)", key.name, re.IGNORECASE) is not None


def leading_space(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


@dataclass(frozen=True)
class Insert:
    """Lines to add before line at."""

    at: int
    lines: list[str]


def plan(path: Path, writable_root: str, min_doc_bytes: int) -> Plan:
    """Plans the change that adds writable_root to writable_roots and raises
    project_doc_max_bytes to at least min_doc_bytes, as whole-line insertions and edits, leaving
    every other line as it was. The new text is read again to confirm it's still TOML this reader
    follows, with each setting defined once and set as needed."""
    pattern = path_pattern(writable_root)
    file = read_settings_file(path)
    result = Plan(file, reason=file.reason)
    if result.reason:
        return result
    if MULTI_LINE_STRING.search(file.text):
        result.reason = "it has multi-line strings, which setup does not edit"
        return result
    lines = to_lines(file.text)
    layout = read_layout(lines)
    if layout.reason:
        result.reason = layout.reason
        return result

    entry = f"'{writable_root}'"
    inserts: list[Insert] = []
    changes: dict[int, str] = {}

    # project_doc_max_bytes: a top-level key, so it goes above the first table.
    max_keys = [
        key for key in layout.keys if key.table == "" and names_key("project_doc_max_bytes", key)
    ]
    if len(max_keys) > 1:
        result.reason = "it sets project_doc_max_bytes more than once"
        return result
    if max_keys:
        key = max_keys[0]
        number = re.search(r"=\s*([0-9][0-9_]*)\s*$", masked_line(lines[key.start]) or "")
        if key.name != "project_doc_max_bytes" or key.end != key.start or number is None:
            result.reason = "its project_doc_max_bytes line is in a form setup does not edit"
            return result
        if int(number.group(1).replace("_", "")) < min_doc_bytes:
            line = lines[key.start]
            changes[key.start] = (
                line[: number.start(1)] + str(min_doc_bytes) + line[number.end(1) :]
            )
    else:
        new_line = f"project_doc_max_bytes = {min_doc_bytes}"
        top_keys = [key for key in layout.keys if key.table == ""]
        if top_keys:
            inserts.append(Insert(top_keys[-1].end + 1, [new_line]))
        elif layout.headers:
            # Above the first table, and above any comment sitting right on top of it.
            at = layout.headers[0].line
            while at > 0 and lines[at - 1].lstrip().startswith("#"):
                at -= 1
            inserts.append(Insert(at, [new_line, ""]))
        else:
            inserts.append(Insert(len(lines), [new_line]))

    # writable_roots, in the [sandbox_workspace_write] table.
    def sandbox_named(name: str) -> bool:
        return re.match(r"[\"']?sandbox_workspace_write", name, re.IGNORECASE) is not None

    other_forms = [
        header
        for header in layout.headers
        if sandbox_named(header.name)
        and (header.name != "sandbox_workspace_write" or header.is_array)
    ]
    other_keys = [key for key in layout.keys if key.table == "" and sandbox_named(key.name)]
    if other_forms or other_keys:
        result.reason = "it sets sandbox_workspace_write in a form setup does not edit"
        return result
    tables = [header for header in layout.headers if header.name == "sandbox_workspace_write"]
    if len(tables) > 1:
        result.reason = "it has [sandbox_workspace_write] more than once"
        return result
    if not tables:
        inserts.append(
            Insert(len(lines), ["[sandbox_workspace_write]", f"writable_roots = [{entry}]"])
        )
    else:
        roots = [
            key
            for key in layout.keys
            if key.table == "sandbox_workspace_write" and names_key("writable_roots", key)
        ]
        if len(roots) > 1 or (len(roots) == 1 and roots[0].name != "writable_roots"):
            result.reason = "its writable_roots line is in a form setup does not edit"
            return result
        if not roots:
            inserts.append(Insert(tables[0].line + 1, [f"writable_roots = [{entry}]"]))
        elif not re.search(pattern, value_text(lines, roots[0]), re.IGNORECASE):
            key = roots[0]
            if key.start == key.end:
                # One line: add the entry before the closing bracket.
                found = re.search(r"=\s*\[(.*)\]\s*$", masked_line(lines[key.start]) or "")
                if found is None:
                    result.reason = "its writable_roots is not a list"
                    return result
                line = lines[key.start]
                head = line[: found.end(1)].rstrip()
                tail = line[found.end(1) :]
                if not found.group(1).strip():
                    separator = ""
                elif head.endswith(","):
                    separator = " "
                else:
                    separator = ", "
                changes[key.start] = head + separator + entry + tail
            else:
                # Several lines: add a line above the closing bracket, with a comma after the
                # entry before it if that has none.
                if (masked_line(lines[key.end]) or "").strip() != "]":
                    result.reason = (
                        "its writable_roots spans several lines in a form setup does not edit"
                    )
                    return result
                last = key.end - 1
                while last > key.start and not (masked_line(lines[last]) or "").strip():
                    last -= 1
                last_code = (masked_line(lines[last]) or "").rstrip()
                if last > key.start:
                    indent = leading_space(lines[last])
                else:
                    indent = leading_space(lines[key.end]) + "    "
                new_entry = indent + entry
                if last_code.endswith(","):
                    new_entry += ","
                elif not last_code.endswith("["):
                    line = lines[last]
                    changes[last] = line[: len(last_code)] + "," + line[len(last_code) :]
                inserts.append(Insert(key.end, [new_entry]))

    # Build the new text. Each original line keeps its own line break, so unchanged lines stay
    # byte for byte as they were. New lines use the break the file mostly uses.
    breaks = re.findall(r"\r?\n", file.text)
    out: list[str] = []
    previous = ""
    # The last line written has no line break after it.
    open_line = False
    for index in range(len(lines) + 1):
        for insert in inserts:
            if insert.at != index:
                continue
            for line in insert.lines:
                if open_line:
                    out.append(file.newline)
                    open_line = False
                # A new table gets a blank line above it, unless it starts the file.
                if line.startswith("[") and out and previous.strip() != "":
                    out.append(file.newline)
                out.append(line + file.newline)
                previous = line
        if index < len(lines):
            line = changes.get(index, lines[index])
            line_break = breaks[index] if index < len(breaks) else ""
            out.append(line + line_break)
            previous = line
            open_line = line_break == ""
    new_text = "".join(out)

    # Check: the new text must read cleanly, pass the same test setup runs, and define each
    # table and setting once.
    after = read_layout(to_lines(new_text))
    names = [header.name for header in after.headers if not header.is_array]
    top_max = [k for k in after.keys if k.table == "" and k.name == "project_doc_max_bytes"]
    sandbox_roots = [
        k for k in after.keys if k.table == "sandbox_workspace_write" and k.name == "writable_roots"
    ]
    if (
        after.reason
        or not is_configured(new_text, writable_root, min_doc_bytes)
        or len(set(names)) != len(names)
        or len(top_max) != 1
        or len(sandbox_roots) != 1
    ):
        result.reason = "a check of the planned change failed"
        return result
    try:
        tomllib.loads(file.text)
    except tomllib.TOMLDecodeError as error:
        result.reason = f"it is not valid TOML ({error})"
        return result
    if not same_apart_from_change(file.text, new_text, writable_root, min_doc_bytes):
        result.reason = "a check of the planned change failed (read as TOML)"
        return result
    result.new_text = new_text
    return result


def same_apart_from_change(
    old_text: str, new_text: str, writable_root: str, min_doc_bytes: int
) -> bool:
    """Reads both versions with Python's own TOML reader: the new one must set both settings as
    planned, and hold everything else exactly as the old one did."""
    try:
        old = tomllib.loads(old_text)
        new = tomllib.loads(new_text)
    except tomllib.TOMLDecodeError:
        return False
    new_max = new.pop("project_doc_max_bytes", None)
    old_max = old.pop("project_doc_max_bytes", None)
    if not isinstance(new_max, int) or new_max < min_doc_bytes:
        return False
    if old_max is not None and (
        not isinstance(old_max, int) or new_max != max(old_max, min_doc_bytes)
    ):
        return False
    old_sandbox = old.get("sandbox_workspace_write", {})
    new_sandbox = new.get("sandbox_workspace_write")
    if not isinstance(old_sandbox, dict) or not isinstance(new_sandbox, dict):
        return False
    old_roots = old_sandbox.pop("writable_roots", [])
    new_roots = new_sandbox.pop("writable_roots", None)
    if not isinstance(new_roots, list) or new_roots[: len(old_roots)] != old_roots:
        return False
    if new_roots[len(old_roots) :] not in ([], [writable_root]):
        return False
    # A table setup added, now empty, wasn't there before.
    if not new_sandbox and "sandbox_workspace_write" not in old:
        del new["sandbox_workspace_write"]
    return old == new


# [[skills.config]]: each entry names a skill by its SKILL.md path, or by its name, and turns it on
# or off in this Codex home. Codex's own /skills menu adds one with enabled = false to turn a skill
# off, and deletes it to turn the skill back on (Codex's source, rust-v0.162.1). It matches a path
# after resolving links, so a skill reached through a junction is named by any path to its file.
SKILLS_CONFIG = "skills.config"


def skill_entry_paths(text: str) -> list[str] | None:
    """The path each [[skills.config]] entry names, in order, leaving out any that names a skill
    by its name instead, or None when the text isn't TOML that names them in a form setup reads."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return None
    entries = config_entries(data)
    if entries is None:
        return None
    return [entry["path"] for entry in entries if isinstance(entry.get("path"), str)]


def config_entries(data: dict[str, Any]) -> list[dict[str, Any]] | None:
    """The [[skills.config]] entries as TOML reads them, none when there are none, or None when
    skills or its config isn't in the form Codex reads."""
    skills = data.get("skills", {})
    if not isinstance(skills, dict):
        return None
    entries = skills.get("config", [])
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        return None
    return entries


def without_empty_skills(data: dict[str, Any]) -> dict[str, Any]:
    """The settings without an empty skills.config, or a skills table it leaves empty, which mean
    the same to Codex as none."""
    skills = data.get("skills")
    if isinstance(skills, dict):
        if skills.get("config") == []:
            del skills["config"]
        if not skills:
            del data["skills"]
    return data


def edit_skills(
    text: str, newline: str, hide: Sequence[str], unhide: Sequence[str]
) -> tuple[str | None, str]:
    """The text with a [[skills.config]] entry that hides each SKILL.md in hide added at the end,
    and every entry whose path is one in unhide removed, with the blank line above it, leaving every
    other line as it was. Returns the new text and "", or None and why setup won't make the change.
    The new text is read again to confirm that it holds the same settings as before, apart from
    exactly those entries."""
    if MULTI_LINE_STRING.search(text):
        return None, "it has multi-line strings, which setup does not edit"
    try:
        before = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        return None, f"it is not valid TOML ({error})"
    lines = to_lines(text)
    layout = read_layout(lines)
    if layout.reason:
        return None, layout.reason
    entries = config_entries(before)
    if entries is None:
        return None, "it sets skills or skills.config in a form setup does not edit"

    # Each entry in the form Codex writes, one [[skills.config]] table each, and nothing else that
    # sets skills.config, so the tables and the entries TOML reads match one for one, in order.
    def spelled_as_config(name: str) -> bool:
        plain = re.sub(r"[\s\"']", "", name).lower()
        return plain == SKILLS_CONFIG or plain.startswith(SKILLS_CONFIG + ".")

    tables = [h for h in layout.headers if h.is_array and h.name == SKILLS_CONFIG]
    other_tables = [h for h in layout.headers if spelled_as_config(h.name) and h not in tables]
    other_keys = [
        key
        for key in layout.keys
        if (key.table == "" and names_key("skills", key))
        or (key.table == "skills" and names_key("config", key))
    ]
    if other_tables or other_keys or len(tables) != len(entries):
        return None, "it sets skills.config in a form setup does not edit"

    removed: set[int] = set()
    gone: list[int] = []
    for index, (header, entry) in enumerate(zip(tables, entries, strict=True)):
        path = entry.get("path")
        if not (isinstance(path, str) and any(same_path(path, p) for p in unhide)):
            continue
        gone.append(index)
        after_header = [h.line for h in layout.headers if h.line > header.line]
        next_line = min(after_header, default=len(lines))
        ends = [k.end for k in layout.keys if header.line < k.start < next_line]
        start, end = header.line, max(ends, default=header.line)
        removed.update(range(start, end + 1))
        if start > 0 and not lines[start - 1].strip():
            removed.add(start - 1)
        elif start == 0 and end + 1 < len(lines) and not lines[end + 1].strip():
            removed.add(end + 1)

    # Each line kept keeps its own line break, so it stays byte for byte as it was.
    breaks = re.findall(r"\r?\n", text)
    out: list[str] = []
    last = ""
    for index, line in enumerate(lines):
        if index in removed:
            continue
        out.append(line + (breaks[index] if index < len(breaks) else ""))
        last = line
    for path in hide:
        if out and not out[-1].endswith("\n"):
            out.append(newline)
        if out and last.strip():
            out.append(newline)
        block = ["[[skills.config]]", f"path = {json.dumps(path)}", "enabled = false"]
        out.extend(line + newline for line in block)
        last = block[-1]
    new_text = "".join(out)

    # Check: the new text must read as the old one did, with those entries gone and the new ones
    # last.
    expected = copy.deepcopy(before)
    kept = [entry for index, entry in enumerate(entries) if index not in gone]
    kept += [{"path": path, "enabled": False} for path in hide]
    expected.setdefault("skills", {})["config"] = kept
    try:
        after = tomllib.loads(new_text)
    except tomllib.TOMLDecodeError:
        return None, "a check of the planned change failed"
    if without_empty_skills(after) != without_empty_skills(expected):
        return None, "a check of the planned change failed (read as TOML)"
    return new_text, ""
