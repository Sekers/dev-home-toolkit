"""Claude Code's settings.json: which folders it lets Claude Code use, which instruction files its
sessions skip, and which keys it has more than once, and planning the change that adds dev-home
and dev-home-toolkit to the first and setup's patterns to the second, or takes them back out.
Every change keeps only the last copy of a key written more than once, the one Claude Code
uses."""

import copy
import json
from pathlib import Path
from typing import Any

from .settings_files import Plan, SettingsFile, read_settings_file

# Where each list setup changes is in the settings.
FOLDERS = ("permissions", "additionalDirectories")
EXCLUDES = ("claudeMdExcludes",)
# A key the settings don't have, as plan keeps each value it replaces.
ABSENT = object()


def without_comments(text: str) -> str:
    """JSON text with // and /* */ comments taken out, outside strings."""
    out: list[str] = []
    index = 0
    in_string = False
    while index < len(text):
        char = text[index]
        if in_string:
            out.append(char)
            if char == "\\" and index + 1 < len(text):
                out.append(text[index + 1])
                index += 1
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
            out.append(char)
        elif text.startswith("//", index):
            while index < len(text) and text[index] != "\n":
                index += 1
            continue
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = len(text) if end < 0 else end + 2
            continue
        else:
            out.append(char)
        index += 1
    return "".join(out)


def listed(text: str, keys: tuple[str, ...]) -> list[str] | None:
    """The strings in the list at keys, such as FOLDERS, or None when the text isn't JSON even
    with comments taken out. Comments don't stop this check, though setup won't edit a file
    that has them. An empty file has none."""
    if not text.strip():
        return []
    try:
        value = json.loads(without_comments(text))
    except ValueError:
        return None
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def folders_allowed(text: str) -> list[str] | None:
    """The folders in permissions.additionalDirectories (see listed)."""
    return listed(text, FOLDERS)


class RewrittenError(ValueError):
    """A number that writing the file back would change, such as 1e5, which would become
    100000.0."""


class Pairs(list[tuple[str, Any]]):
    """An object's keys and values as read, in order, a key written more than once included."""


def objects_in(value: Any, path: tuple[str, ...], repeated: list[str]) -> Any:
    """The value read with Pairs, with each object made a dict that keeps the last copy of a key
    written more than once, in the place of its first, as Claude Code reads it. Adds the path of
    each such key to repeated, once, joined with dots."""
    if isinstance(value, Pairs):
        found: dict[str, Any] = {}
        for key, inner in value:
            if key in found:
                name = ".".join((*path, key))
                if name not in repeated:
                    repeated.append(name)
            found[key] = objects_in(inner, (*path, key), repeated)
        return found
    if isinstance(value, list):
        return [objects_in(item, path, repeated) for item in value]
    return value


def repeated_keys(text: str) -> list[str] | None:
    """The path of each key written more than once in one object, joined with dots, or None when
    the text isn't JSON even with comments taken out (see listed)."""
    if not text.strip():
        return []
    try:
        parsed = json.loads(without_comments(text), object_pairs_hook=Pairs)
    except ValueError:
        return None
    repeated: list[str] = []
    objects_in(parsed, (), repeated)
    return repeated


def exact_float(text: str) -> float:
    number = float(text)
    if json.dumps(number) != text:
        raise RewrittenError(text)
    return number


def exact_int(text: str) -> int:
    number = int(text)
    if str(number) != text:
        raise RewrittenError(text)
    return number


def not_a_number(text: str) -> float:
    """NaN and Infinity aren't JSON, though Python reads them."""
    raise ValueError(f"{text} is not JSON")


def read_json(text: str) -> tuple[Any, list[str]]:
    """Plain JSON only, read so that writing it back changes nothing but layout, apart from a key
    written more than once in one object, which keeps only its last copy, the one Claude Code
    uses. Also returns the path of each such key (see objects_in)."""
    parsed = json.loads(
        text,
        object_pairs_hook=Pairs,
        parse_float=exact_float,
        parse_int=exact_int,
        parse_constant=not_a_number,
    )
    repeated: list[str] = []
    return objects_in(parsed, (), repeated), repeated


def dump(data: object) -> str:
    """Two-space JSON, as Claude Code writes it."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def read_object(result: Plan) -> dict[str, Any] | None:
    """The file's settings, read so that writing them back changes nothing but layout and the
    earlier copies of a key written more than once, which result.repeated names, or None with
    result.reason saying why setup won't rewrite it. An empty file has none."""
    file = result.file
    try:
        data, result.repeated = read_json(file.text) if file.text.strip() else ({}, [])
    except RewrittenError as error:
        result.reason = f"rewriting it would change how its number {error} is written"
        return None
    except ValueError:
        result.reason = (
            "it is not plain JSON (it may have comments), and rewriting it would lose that"
        )
        return None
    if not isinstance(data, dict):
        result.reason = "its top level is not a JSON object"
        return None
    return data


def read_file(path: Path) -> SettingsFile:
    """A settings file as read_settings_file reads it, with why it can't be read, if so."""
    try:
        return read_settings_file(path)
    except OSError as error:
        return SettingsFile(reason=f"it can't be read ({error.strerror or error})")


def settings_object(file: SettingsFile) -> tuple[dict[str, Any] | None, str]:
    """The settings in a settings.json, as read (see read_file), as Claude Code reads them, with
    the last copy of a key written more than once, or None with why setup won't rewrite the file
    (see read_object). A file that isn't there has none."""
    result = Plan(file, reason=file.reason)
    data = None if result.reason else read_object(result)
    return data, result.reason or ""


def new_text_for(result: Plan, data: dict[str, Any]) -> str | None:
    """The settings as Claude Code writes them, with the file's line breaks, or None with
    result.reason saying why they can't be written back."""
    file = result.file
    new_text = dump(data).replace("\n", file.newline)
    if file.final_newline:
        new_text += file.newline
    try:
        new_text.encode("utf-8")
    except UnicodeEncodeError:
        result.reason = (
            "it has a \\u escape for half a character (an unpaired surrogate), which can't be "
            "written back as UTF-8"
        )
        return None
    return new_text


def note_layout(result: Plan, original_indented: str) -> None:
    """Says so when the rewrite changes other lines' layout, though not their settings."""
    text = result.file.text
    if text.strip() and original_indented != text.replace("\r\n", "\n").rstrip("\n"):
        result.note = (
            "Some other lines change only in layout (spacing or escaping). "
            "The settings in them stay the same."
        )


def list_to_extend(
    result: Plan, data: dict[str, Any], keys: tuple[str, ...], made: list[tuple[str, ...]]
) -> list[Any] | None:
    """The list at keys in data, made, with any object it goes in, when it isn't there, and the
    outermost key made added to made. None with result.reason saying why setup won't add to it."""
    parent = data
    making = False
    for depth, key in enumerate(keys):
        last = depth == len(keys) - 1
        if key not in parent:
            parent[key] = [] if last else {}
            if not making:
                made.append(keys[: depth + 1])
                making = True
        value = parent[key]
        if value is None:
            result.reason = f'its "{key}" is null'
            return None
        if last:
            if not isinstance(value, list):
                result.reason = f'its "{key}" is not a list'
                return None
            return value
        if not isinstance(value, dict):
            result.reason = f'its "{key}" is not a JSON object'
            return None
        parent = value
    return None


def value_at(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        data = data[key]
    return data


def plan(
    path: Path,
    folders: list[str],
    excludes: list[str] | None = None,
    values: dict[str, Any] | None = None,
    file: SettingsFile | None = None,
) -> Plan:
    """Plans adding folders to permissions.additionalDirectories, and patterns to
    claudeMdExcludes, and setting each key in values, at the top of the settings, to its value:
    in its place when it's there, and otherwise last. With none of them, it plans rewriting the
    file alone, which keeps only the last copy of a key written more than once (see
    read_object). It plans on file, the file as already read, if given, so a check of what the
    file had is of what the write replaces. As a check, the new text is parsed again with the
    additions and values taken back out, and has to match the original exactly, as Claude Code
    reads it."""
    additions = [(FOLDERS, folders), (EXCLUDES, excludes or [])]
    values = values or {}
    file = read_settings_file(path) if file is None else file
    result = Plan(file, reason=file.reason)
    if result.reason:
        return result
    data = read_object(result)
    if data is None:
        return result

    original = json.dumps(data)
    original_indented = dump(data)
    made: list[tuple[str, ...]] = []
    for keys, entries in additions:
        if entries:
            target = list_to_extend(result, data, keys, made)
            if target is None:
                return result
            target.extend(entries)
    # Each key's value before, or ABSENT for one the file doesn't have.
    before = {name: data.get(name, ABSENT) for name in values}
    for name, value in values.items():
        data[name] = copy.deepcopy(value)

    new_text = new_text_for(result, data)
    if new_text is None:
        return result

    # Check: read the new text back, confirm the new entries and values, take them out again, and
    # compare what's left with the original.
    check = json.loads(new_text)
    for name, value in values.items():
        if name not in check or json.dumps(check[name]) != json.dumps(value):
            result.reason = "a check of the planned change failed (a new value did not read back)"
            return result
        if before[name] is ABSENT:
            del check[name]
        else:
            check[name] = before[name]
    for keys, entries in additions:
        if not entries:
            continue
        check_list = value_at(check, keys)
        if check_list[len(check_list) - len(entries) :] != entries:
            result.reason = "a check of the planned change failed (a new entry did not read back)"
            return result
        if not any(keys[: len(key)] == key for key in made):
            del check_list[len(check_list) - len(entries) :]
    for key in made:
        del value_at(check, key[:-1])[key[-1]]
    if json.dumps(check) != original:
        result.reason = "a check of the planned change failed (the rest did not read back the same)"
        return result

    result.new_text = new_text
    note_layout(result, original_indented)
    return result


def take_list(data: dict[str, Any], keys: tuple[str, ...]) -> list[Any] | None:
    """Takes the list at keys out of data, then each object it was in that's left empty, and
    returns it. None, changing nothing, when it isn't a list there."""
    parents = [data]
    for key in keys[:-1]:
        child = parents[-1].get(key)
        if not isinstance(child, dict):
            return None
        parents.append(child)
    found = parents[-1].get(keys[-1])
    if not isinstance(found, list):
        return None
    del parents[-1][keys[-1]]
    for depth in range(len(parents) - 1, 0, -1):
        if not parents[depth]:
            del parents[depth - 1][keys[depth - 1]]
    return found


def plan_removal(path: Path, folders: list[str], excludes: list[str] | None = None) -> Plan:
    """Plans taking folders out of permissions.additionalDirectories, and patterns out of
    claudeMdExcludes, each exactly as written, after a no to the folder whose settings these are,
    then each list once it's empty, and "permissions" once that's empty, as they were before setup
    added them. As a check, both versions are read again: each new list has to be the old one
    without those entries, and everything else has to read the same."""
    removals = [
        (keys, entries)
        for keys, entries in ((FOLDERS, folders), (EXCLUDES, excludes or []))
        if entries
    ]
    file = read_settings_file(path)
    result = Plan(file, reason=file.reason)
    if result.reason:
        return result
    data = read_object(result)
    if data is None:
        return result
    original_indented = dump(data)
    for keys, entries in removals:
        parent: Any = data
        for key in keys[:-1]:
            parent = parent.get(key) if isinstance(parent, dict) else None
        current = parent.get(keys[-1]) if isinstance(parent, dict) else None
        if not isinstance(parent, dict) or not isinstance(current, list):
            result.reason = f'its "{keys[-1]}" is not a list'
            return result
        kept = [entry for entry in current if entry not in entries]
        if len(kept) == len(current):
            result.reason = "a check of the planned change failed (no entry to take out)"
            return result
        if kept:
            parent[keys[-1]] = kept
        else:
            take_list(data, keys)

    new_text = new_text_for(result, data)
    if new_text is None:
        return result

    old = json.loads(file.text)
    new = json.loads(new_text)
    for keys, entries in removals:
        old_list = take_list(old, keys) or []
        new_list = take_list(new, keys) or []
        if new_list != [entry for entry in old_list if entry not in entries]:
            result.reason = (
                "a check of the planned change failed (the rest did not read back the same)"
            )
            return result
    if json.dumps(new) != json.dumps(old):
        result.reason = "a check of the planned change failed (the rest did not read back the same)"
        return result

    result.new_text = new_text
    note_layout(result, original_indented)
    return result
