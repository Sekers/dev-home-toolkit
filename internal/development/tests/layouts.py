"""The layout lists: what dev-home-toolkit's code writes into each file another version of it may
read, so a change to a file's layout never slips in unnoticed (decision 0068, "Versions and layouts
in dev-home"). docs/development/testing.md says when a list changes.

Each list is a file in layout-lists/, one for each file and layout version, such as
local-settings-json-1.txt for local-settings.json with schemaVersion 1. It holds one key path to a
line, from the file's top, joined with dots, with each made-up name as a placeholder: <folder> for
an agent's folder, <skill> and <preference> for a skill and its preferences, and <setting> for a
setting declared in internal/shared/setting-definitions.json, whose whole path it stands for. A
declared setting is left out by name because its declaration, and formerNames, already handle one
being added, renamed, or removed. A saved state, such as {"$state": "remind", "on": "2030-01-15"},
adds each of its keys after its setting's path. Lines starting with # are comments.

helpers.py checks every run of the scripts in a test: each key path the run adds to one of these
files must be on that file's list for the layout its schemaVersion names. test_layouts.py checks
that the code still writes everything on each list."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LISTS = Path(__file__).resolve().with_name("layout-lists")
# The key of a saved state, as internal/shared/settings.py writes it.
STATE = "$state"
SETTING = "<setting>"


@dataclass(frozen=True)
class Part:
    """A file another version of dev-home-toolkit may read: its name, the start of its lists'
    names, and where its keys are made-up names, by the key path above them, placeholders
    included, with the placeholder each one gets."""

    file: str
    list_name: str
    named: dict[tuple[str, ...], str]


PARTS = (
    Part(
        "local-settings.json",
        "local-settings-json",
        {
            ("claudeCode", "folders"): "<folder>",
            ("codex", "homes"): "<folder>",
            ("skills",): "<skill>",
            ("skills", "<skill>", "preferences"): "<preference>",
        },
    ),
    Part("dev-home.json", "dev-home-json", {}),
)


def part_named(file: str) -> Part:
    return next(part for part in PARTS if part.file == file)


def list_path(part: Part, version: object) -> Path:
    return LISTS / f"{part.list_name}-{version}.txt"


def is_version(version: object) -> bool:
    """Whether a schemaVersion is a whole number, as the code always writes it."""
    return isinstance(version, int) and not isinstance(version, bool)


def listed(part: Part, version: object) -> set[str] | None:
    """The key paths on a part's list for that layout version, or None when it has no list."""
    if not is_version(version):
        return None
    path = list_path(part, version)
    if not path.is_file():
        return None
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return {line for line in lines if line and not line.startswith("#")}


def declared_settings(toolkit: Path) -> set[str]:
    """The path of every setting setting-definitions.json declares, in a copy of the repo."""
    path = toolkit / "internal" / "shared" / "setting-definitions.json"
    return set(json.loads(path.read_text(encoding="utf-8"))["settings"])


def key_paths(data: dict[str, Any], part: Part, declared: set[str]) -> set[str]:
    """Every key path in a file's data, as its list writes them: the path to each value that isn't
    a JSON object, or is an empty one, and each key of a saved state."""
    paths: set[str] = set()

    def walk(value: dict[str, Any], shown: tuple[str, ...], real: tuple[str, ...]) -> None:
        for key, inner in value.items():
            if shown in part.named:
                path = (*shown, part.named[shown])
            elif ".".join((*real, key)) in declared:
                path = (SETTING,)
            else:
                path = (*shown, key)
            if not isinstance(inner, dict) or not inner:
                paths.add(".".join(path))
            elif STATE in inner:
                paths.update(".".join((*path, state_key)) for state_key in inner)
            else:
                walk(inner, path, (*real, key))

    walk(data, (), ())
    return paths


def read_data(data: bytes | None) -> dict[str, Any] | None:
    """A file's JSON object, or None when it isn't one, such as a file a test broke on purpose."""
    if data is None:
        return None
    try:
        value = json.loads(data.decode("utf-8-sig"))
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def problems(path: Path, before: list[bytes], after: bytes, toolkit: Path) -> list[str]:
    """What's wrong with what a run wrote to one of the files a list covers, given its bytes
    after the run, and before it and after each write the test made during it: a layout version
    the run wrote that has no list, and each key path it added that its layout's list doesn't
    have. A file that isn't a JSON object isn't checked: the code never writes one."""
    part = part_named(path.name)
    data = read_data(after)
    if data is None:
        return []
    declared = declared_settings(toolkit)
    added = key_paths(data, part, declared)
    versions = set()
    for earlier in before:
        old = read_data(earlier)
        if old is not None:
            added -= key_paths(old, part, declared)
            versions.add(json.dumps(old.get("schemaVersion")))
    version = data.get("schemaVersion")
    if not added and json.dumps(version) in versions:
        return []
    if not is_version(version):
        return [f"{path} has schemaVersion {json.dumps(version)}, which isn't a whole number."]
    known = listed(part, version)
    if known is None:
        return [
            f"{path} has schemaVersion {json.dumps(version)}, which has no layout list. Save "
            f"one as {list_path(part, version)} (see docs/development/testing.md)."
        ]
    missing = sorted(added - known)
    if not missing:
        return []
    return [
        f"{path} gained key paths that layout {version}'s list doesn't have: "
        f"{', '.join(missing)}. A change to what the code writes there is a layout change: "
        f"before 1.0.0, add them to {list_path(part, version)}; from 1.0.0, raise the file's "
        "schemaVersion, save a list for the new layout, and add a conversion step (see "
        "docs/development/testing.md)."
    ]
