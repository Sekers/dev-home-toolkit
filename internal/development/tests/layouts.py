"""The layout lists: what dev-home-toolkit's code writes into each file another version of it may
read, so a change to a file's layout never slips in unnoticed (decision 0068, "Versions and layouts
in dev-home"). docs/development/testing.md says when a list changes.

Each list is a file in layout-lists/, one for each file and layout version, such as
local-settings-json-1.txt for local-settings.json with schemaVersion 1. It holds one key path to a
line, from the file's top, joined with dots, with each made-up name as a placeholder: <folder> for
an agent's folder, <recommended> for the id of a recommended setting answered for one, <skill> and
<preference> for a skill and its preferences, and <setting> for a
setting declared in internal/shared/setting-definitions.json, whose whole path it stands for. A
declared setting is left out by name because its declaration, and formerNames, already handle one
being added, renamed, or removed. A saved state, such as {"$state": "remind", "on": "2030-01-15"},
adds each of its keys after its setting's path. Lines starting with # are comments.

dev-home's rules/ has a list too, rules-1.txt: the path of each file the code creates there, from
dev-home's folder, with <pc> for a PC's folder, <agent> for an agent's, and <moved> for the name of
a file setup moves there, which starts with moved-. rules/ has no layout version of its own yet,
so its layout is 1.

So does handoffs/, handoffs-1.txt: the path of each handoff facts.py names, from dev-home's
folder, with a placeholder for each folder below the service's, such as <owner> and <repo>, <host>
and <path> for other's computer and the one or more folders after it, and <pc> and
<folder>-<hash> for a PC's handoffs, and the sections of the handoff skill's template, which the
skill and facts.py read by name, each as section: and the line that starts it. A folder cut to
fit the path budget is written as the path it was cut from, since decision 0088's rule cuts any
of them the same way. handoffs/ has no layout version of its own yet either.

helpers.py checks every run of the scripts in a test: each key path the run adds to one of these
files must be on that file's list for the layout its schemaVersion names, each file it creates in
rules/ on rules' list, and each handoff path it prints, as facts.py's handoff topic does, on
handoffs' list. test_layouts.py checks that the code still writes everything on each list."""

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LISTS = Path(__file__).resolve().with_name("layout-lists")
# The key of a saved state, as internal/shared/settings.py writes it.
STATE = "$state"
SETTING = "<setting>"
RULES_FOLDER = "rules"
RULES_LIST = LISTS / "rules-1.txt"
HANDOFFS_FOLDER = "handoffs"
HANDOFFS_LIST = LISTS / "handoffs-1.txt"
# What starts a template section's line on handoffs' list.
SECTION = "section: "
# The folders below each service's own, as facts.py names them. GitLab's subgroups, when it has
# any, come between its two as one <subgroups>, and other's <path> stands for one or more folders.
HANDOFF_FOLDERS = {
    "github": ("<owner>", "<repo>"),
    "bitbucket": ("<owner>", "<repo>"),
    "gitlab": ("<group>", "<project>"),
    "azure-devops": ("<organization>", "<project>", "<repo>"),
    "other": ("<host>", "<path>"),
    "pcs": ("<pc>", "<folder>-<hash>"),
}
# How a folder cut to fit the path budget ends: a hyphen and 8 hexadecimal characters, or those
# alone. facts.py cuts only a handoff's folder that, with the room beside it, passes the budget
# (decision 0088).
CUT = re.compile(r"(?:.*-)?[0-9a-f]{8}")
PATH_BUDGET = 139
HANDOFF_ROOM = 60


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
            ("claudeCode", "folders", "<folder>", "recommendedSettings"): "<recommended>",
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


def read_list(path: Path) -> set[str]:
    """A list's lines, without its comments."""
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return {line for line in lines if line and not line.startswith("#")}


def listed(part: Part, version: object) -> set[str] | None:
    """The key paths on a part's list for that layout version, or None when it has no list."""
    if not is_version(version):
        return None
    path = list_path(part, version)
    return read_list(path) if path.is_file() else None


def rules_key(relative: Sequence[str]) -> str:
    """A file's path in rules/, given its parts after rules/, as rules' list writes it: rules/,
    then the parts, with <pc> for a PC's folder, <agent> for an agent's, and <moved> for the name
    of a file setup moved there."""
    parts = list(relative)
    agent = 0
    if len(parts) > 1 and parts[0] == "pcs":
        parts[1] = "<pc>"
        agent = 2
    if len(parts) > agent + 1 and parts[agent] != "_all-agents":
        parts[agent] = "<agent>"
    if parts and parts[-1].startswith("moved-"):
        parts[-1] = "<moved>"
    return "/".join([RULES_FOLDER, *parts])


def rules_problems(path: Path, relative: Sequence[str], before: list[bytes]) -> list[str]:
    """What's wrong with a file a run created in rules/: one rules' list doesn't have. A file that
    was there before the run isn't the run's to answer for."""
    key = rules_key(relative)
    if before or key in read_list(RULES_LIST):
        return []
    return [
        f"{path} is a file the run created in rules/ that rules' list doesn't have: {key}. A "
        f"change to what the code writes there is a layout change: before 1.0.0, add it to "
        f"{RULES_LIST}; from 1.0.0, raise rules/'s layout version, save a list for the new layout, "
        "and add a conversion step (see docs/development/testing.md)."
    ]


def handoffs_key(service: str, name: str, handoff: str) -> str:
    """The handoff path facts.py names, by its service, name, and handoff lines, as handoffs'
    list writes it (see the description above). A path that's neither the service and name
    whole, nor a cut of them, is written as it is, which no list line matches."""
    parts = name.split("/")
    whole = [HANDOFFS_FOLDER, service, *parts]
    folders = handoff.split("/")[:-1]
    # Counted as Windows counts it, in UTF-16 units.
    whole_length = len(("/".join(whole) + "/").encode("utf-16-le", "surrogatepass")) // 2
    cut = (
        whole_length + HANDOFF_ROOM > PATH_BUDGET
        and len(folders) > 2
        and folders[:-1] == whole[: len(folders) - 1]
        and CUT.fullmatch(folders[-1])
    )
    if (folders != whole and not cut) or service not in HANDOFF_FOLDERS:
        return handoff
    placeholders = list(HANDOFF_FOLDERS[service])
    if service == "gitlab" and len(parts) > 2:
        placeholders.insert(1, "<subgroups>")
    # <subgroups> and other's <path> may each stand for several folders.
    if service in ("gitlab", "other"):
        shaped = len(parts) >= len(placeholders)
    else:
        shaped = len(parts) == len(placeholders)
    # A PC's handoff folder always ends with its path's hash, as a cut one does.
    if not shaped or (service == "pcs" and not CUT.fullmatch(parts[-1])):
        return handoff
    return "/".join([HANDOFFS_FOLDER, service, *placeholders, "HANDOFF.md"])


def handoffs_problems(facts: Mapping[str, str]) -> list[str]:
    """What's wrong with the handoff path a run printed, by the key: value lines it printed, when
    it printed one, as facts.py's handoff topic does: one handoffs' list doesn't have."""
    if "handoff" not in facts:
        return []
    key = handoffs_key(facts.get("service", ""), facts.get("name", ""), facts["handoff"])
    if key in read_list(HANDOFFS_LIST):
        return []
    return [
        f"The run named the handoff {facts['handoff']}, which handoffs' list doesn't have: {key}. "
        f"A change to where facts.py files handoffs is a layout change: before 1.0.0, add it to "
        f"{HANDOFFS_LIST}; from 1.0.0, raise handoffs/'s layout version, save a list for the new "
        "layout, and add a conversion step (see docs/development/testing.md)."
    ]


def handoff_sections(template: str) -> set[str]:
    """The lines of the handoff skill's template that the skill and facts.py read by name, as
    handoffs' list writes them: each heading below the title, and the State line's start."""
    sections = set()
    for line in template.splitlines():
        if line.startswith("## "):
            sections.add(SECTION + line)
        elif line.startswith("**State as of"):
            sections.add(SECTION + "**State as of")
    return sections


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


def problems(path: Path, before: list[bytes], after: bytes, toolkit: Path, root: Path) -> list[str]:
    """What's wrong with what a run wrote to one of the files a list covers, in the sandbox at
    root, given its bytes after the run, and before it and after each write the test made during
    it: for a file in a dev-home's rules/, see rules_problems; for another, a layout version the
    run wrote that has no list, and each key path it added that its layout's list doesn't have.
    A file that isn't a JSON object isn't checked: the code never writes one."""
    relative = path.relative_to(root).parts
    if len(relative) > 2 and relative[1] == RULES_FOLDER:
        return rules_problems(path, relative[2:], before)
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
