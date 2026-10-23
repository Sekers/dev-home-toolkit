"""Codex's config.toml: whether it lets Codex write to dev-home and read long AGENTS.md files,
planning the change that does both, and planning the one that takes dev-home back out. Python can
read TOML but not write it, and a rewrite would lose the person's comments and layout, so each
change is made as whole-line insertions, edits, and removals by a reader that follows only the
TOML it needs, and refuses anything else."""

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .settings_files import Plan, read_settings_file, to_lines

MULTI_LINE_STRING = re.compile(r"'''|\"\"\"")
# A string in a masked line, whose insides masked_line has turned to underscores.
MASKED_STRING = re.compile(r"'[^']*'|\"[^\"]*\"")
SANDBOX = "sandbox_workspace_write"
# How much of the AGENTS.md files Codex reads with no project_doc_max_bytes in config.toml. Setup
# only ever raises what Codex reads, so it adds the setting only to ask for more than this.
CODEX_DEFAULT_DOC_BYTES = 32 * 1024
# The largest whole number TOML holds. Python's reader takes bigger ones, but Codex's doesn't, so a
# bigger project_doc_max_bytes would leave Codex unable to read its config.toml.
TOML_MAX_INTEGER = 2**63 - 1


def reads_enough(max_bytes: int | None, min_doc_bytes: int) -> bool:
    """Whether Codex reads at least min_doc_bytes, given its project_doc_max_bytes, or None when
    config.toml doesn't set it."""
    return (CODEX_DEFAULT_DOC_BYTES if max_bytes is None else max_bytes) >= min_doc_bytes


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
    """Whether the text has both settings (see configured_parts)."""
    return all(configured_parts(text, writable_root, min_doc_bytes))


def configured_parts(text: str, writable_root: str, min_doc_bytes: int) -> tuple[bool, bool]:
    """Whether the text has writable_root in [sandbox_workspace_write] writable_roots, and
    whether Codex reads at least min_doc_bytes: a top-level project_doc_max_bytes that big, or
    none, when min_doc_bytes is no more than Codex reads by default. Comments and other tables
    don't count. For a file the reader can't follow, it falls back to a plain text search."""
    pattern = path_pattern(writable_root)
    lines = to_lines(text)
    layout = None if MULTI_LINE_STRING.search(text) else read_layout(lines)
    if layout is None or layout.reason:
        roots = re.search(r"writable_roots\s*=\s*\[[^\]]*" + pattern, text, re.IGNORECASE)
        found = re.search(r"(?m)^\s*project_doc_max_bytes\s*=\s*(\d+)", text)
        max_bytes = int(found.group(1)) if found else None
        return roots is not None, reads_enough(max_bytes, min_doc_bytes)
    has_root = False
    max_bytes = None
    set_somehow = False
    for key in layout.keys:
        if key.table == "" and names_key("project_doc_max_bytes", key):
            set_somehow = True
            number = re.search(r"=\s*([0-9][0-9_]*)\s*$", value_text(lines, key))
            if key.name == "project_doc_max_bytes" and number:
                max_bytes = int(number.group(1).replace("_", ""))
        elif (
            key.table == "sandbox_workspace_write"
            and key.name == "writable_roots"
            and re.search(pattern, value_text(lines, key), re.IGNORECASE)
        ):
            has_root = True
    # A value this reader can't follow counts as too small, so setup plans a change, which says
    # why it can't make it.
    if set_somehow and max_bytes is None:
        return has_root, False
    return has_root, reads_enough(max_bytes, min_doc_bytes)


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
    """Plans the change that adds writable_root to writable_roots and makes Codex read at least
    min_doc_bytes, raising project_doc_max_bytes, or adding it when Codex's default is less, as
    whole-line insertions and edits, leaving every other line as it was. The new text is read
    again to confirm it's still TOML this reader follows, with each setting defined once and set
    as needed."""
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
    elif not reads_enough(None, min_doc_bytes):
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
        or len(top_max) > 1
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


def has_comment(line: str) -> bool:
    """Whether a line ends in a comment. masked_line cuts it off and keeps every other position,
    so the masked line is shorter."""
    return len((masked_line(line) or "").rstrip()) != len(line.rstrip())


def is_root(text: str, writable_root: str) -> bool:
    """Whether a TOML string, quotes included, is writable_root, written with single or doubled
    slashes of either kind. path_pattern leaves out the slashes a path starts with, such as
    /home/you/dev-home's, so they're matched here."""
    pattern = r"['\"][\\/]{0,2}" + path_pattern(writable_root)
    return re.fullmatch(pattern, text, re.IGNORECASE) is not None


def mentions_root(text: str, writable_root: str) -> bool:
    """Whether a writable_roots anywhere in the text holds writable_root, in whatever form or
    table, a form setup won't edit included, so a removal can say so rather than miss it.
    Comments don't count, unless the reader can't follow the file, when it falls back to a plain
    text search."""
    pattern = path_pattern(writable_root)
    lines = to_lines(text)
    layout = None if MULTI_LINE_STRING.search(text) else read_layout(lines)
    if layout is None or layout.reason:
        found = re.search(r"writable_roots\s*=\s*\[[^\]]*" + pattern, text, re.IGNORECASE)
        return found is not None
    return any(
        re.search(rf"writable_roots|{SANDBOX}", key.name, re.IGNORECASE)
        and re.search(pattern, value_text(lines, key), re.IGNORECASE)
        for key in layout.keys
    )


def list_items(line: str, masked: str, start: int, end: int) -> list[str] | None:
    """The strings between start and end in a line, quotes included, or None when anything else
    is there but commas and spaces."""
    part = masked[start:end]
    items: list[str] = []
    rest: list[str] = []
    position = 0
    for match in MASKED_STRING.finditer(part):
        rest.append(part[position : match.start()])
        items.append(line[start + match.start() : start + match.end()])
        position = match.end()
    rest.append(part[position:])
    if re.search(r"[^\s,]", "".join(rest)):
        return None
    return items


def plan_removal(path: Path, writable_root: str) -> Plan:
    """Plans taking writable_root out of [sandbox_workspace_write] writable_roots, after a no to
    Codex, as whole-line edits and removals, leaving every other line as it was. Every comment
    stays: the writable_roots line goes once its list is empty, and the table once nothing else
    is in it, on it, or right above it, not even a comment. Python's own TOML reader then checks
    that nothing else changed."""
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
    tables = [header for header in layout.headers if header.name == SANDBOX]
    roots = [
        key for key in layout.keys if key.table == SANDBOX and names_key("writable_roots", key)
    ]
    if (
        len(tables) != 1
        or tables[0].is_array
        or len(roots) != 1
        or roots[0].name != "writable_roots"
    ):
        result.reason = "its writable_roots line is in a form setup does not edit"
        return result
    key = roots[0]
    changes: dict[int, str] = {}
    removed: set[int] = set()

    if key.start == key.end:
        # One line: keep the other entries, or remove the line when none is left.
        masked = masked_line(lines[key.start]) or ""
        found = re.search(r"=\s*\[(.*)\]\s*$", masked)
        items = None if found is None else list_items(lines[key.start], masked, *found.span(1))
        if found is None or items is None:
            result.reason = "its writable_roots is not a list of paths"
            return result
        kept = [item for item in items if not is_root(item, writable_root)]
        if len(kept) == len(items):
            result.reason = "a check of the planned change failed (dev-home is not in it)"
            return result
        line = lines[key.start]
        # A line with a comment stays, as an empty list, so the comment does too.
        if kept or has_comment(line):
            changes[key.start] = line[: found.start(1)] + ", ".join(kept) + line[found.end(1) :]
        else:
            removed.add(key.start)
    else:
        # Several lines: one entry on each, between "writable_roots = [" and "]".
        start_code = masked_line(lines[key.start]) or ""
        end_code = (masked_line(lines[key.end]) or "").strip()
        if not re.search(r"=\s*\[\s*$", start_code) or end_code != "]":
            result.reason = "its writable_roots spans several lines in a form setup does not edit"
            return result
        left = 0
        commented = False
        for index in range(key.start + 1, key.end):
            masked = masked_line(lines[index]) or ""
            if not masked.strip():
                commented = commented or bool(lines[index].strip())
                continue
            items = list_items(lines[index], masked, 0, len(masked))
            if items is None or len(items) != 1:
                result.reason = (
                    "its writable_roots spans several lines in a form setup does not edit"
                )
                return result
            if not is_root(items[0], writable_root):
                left += 1
            elif has_comment(lines[index]):
                # The comment stays, on a line of its own, as it would on one line.
                line = lines[index]
                changes[index] = leading_space(line) + line[len(masked) :].strip()
                commented = True
            else:
                removed.add(index)
        if not removed and not changes:
            result.reason = "a check of the planned change failed (dev-home is not in it)"
            return result
        ends = (lines[key.start], lines[key.end])
        if left == 0 and not commented and not any(has_comment(line) for line in ends):
            removed.update(range(key.start, key.end + 1))

    # The table goes too once nothing is left in it, with the blank lines in it, and with the
    # blank lines above it when it ends the file. A comment on its header, or right above it,
    # keeps it, as one in it does.
    table = tables[0]
    following = [header.line for header in layout.headers if header.line > table.line]
    table_end = following[0] if following else len(lines)
    others = [k for k in layout.keys if k.table == SANDBOX and k is not key]
    body = [i for i in range(table.line + 1, table_end) if i not in removed]
    noted_above = table.line > 0 and lines[table.line - 1].lstrip().startswith("#")
    if (
        key.start in removed
        and not others
        and not has_comment(lines[table.line])
        and not noted_above
        and not any(lines[i].strip() for i in body)
    ):
        removed.add(table.line)
        removed.update(body)
        if not following:
            above = table.line - 1
            while above >= 0 and not lines[above].strip():
                removed.add(above)
                above -= 1

    # Build the new text. Each line kept keeps its own line break, so it stays byte for byte as
    # it was.
    breaks = re.findall(r"\r?\n", file.text)
    out: list[str] = []
    for index, line in enumerate(lines):
        if index in removed:
            continue
        line_break = breaks[index] if index < len(breaks) else ""
        out.append(changes.get(index, line) + line_break)
    new_text = "".join(out)

    after = read_layout(to_lines(new_text))
    if after.reason or not same_apart_from_removal(file.text, new_text, writable_root):
        result.reason = "a check of the planned change failed (read as TOML)"
        return result
    result.new_text = new_text
    return result


def same_apart_from_removal(old_text: str, new_text: str, writable_root: str) -> bool:
    """Reads both versions with Python's own TOML reader: the new one must hold writable_roots
    without writable_root, or none once nothing is left, and everything else exactly as the old
    one did."""
    try:
        old = tomllib.loads(old_text)
        new = tomllib.loads(new_text)
    except tomllib.TOMLDecodeError:
        return False
    old_sandbox = old.get(SANDBOX)
    new_sandbox = new.get(SANDBOX, {})
    if not isinstance(old_sandbox, dict) or not isinstance(new_sandbox, dict):
        return False
    old_roots = old_sandbox.pop("writable_roots", None)
    new_roots = new_sandbox.pop("writable_roots", [])
    if not isinstance(old_roots, list):
        return False
    kept = [
        root
        for root in old_roots
        if not (isinstance(root, str) and is_root(f"'{root}'", writable_root))
    ]
    if len(kept) == len(old_roots) or new_roots != kept:
        return False
    for data in (old, new):
        if data.get(SANDBOX) == {}:
            del data[SANDBOX]
    return old == new


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
    if old_max is not None and not isinstance(old_max, int):
        return False
    # What Codex read before stays when it's enough, and otherwise becomes min_doc_bytes.
    if new_max != (old_max if reads_enough(old_max, min_doc_bytes) else min_doc_bytes):
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
