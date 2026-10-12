"""This PC's settings, from local-settings.json in dev-home-tools' folder, and dev-home's own, from
dev-home.json in dev-home, which every copy of it shares. setup.py writes both.

Each setting's name is its path in the file, such as devHome.folder. SETTINGS lists the ones with
a single value, and check_settings checks every value against them, the folders each tool sets
up, and the preferences the skills declare."""

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# dev-home-tools' folder: this file is in internal/shared/, two folders below it.
TOOLS_ROOT = Path(__file__).parent.parent.parent
SETTINGS_PATH = TOOLS_ROOT / "local-settings.json"
# dev-home's own settings, in its root: for now, only multiMachine, whether more than one copy is
# in active use.
DEV_HOME_SETTINGS = "dev-home.json"
# Each file's layout. It goes up only when a setting is renamed or moved.
SCHEMA_VERSION = 1
DEV_HOME_SCHEMA_VERSION = 1
# The file in a skill's folder that declares its preferences.
SKILL_SETTINGS = "dev-home-skill.json"


@dataclass(frozen=True)
class Setting:
    """A setting with a single value. kind is "folder", "yes-no", or "hours" (a whole number of
    hours, 0 or more, where 0 means every time). default is None for one with no default, which
    counts as unanswered until it's set."""

    path: str
    kind: str
    default: int | None


SETTINGS = (
    Setting("devHome.folder", "folder", None),
    Setting("devHome.checkEveryHours", "hours", 12),
    Setting("updates.installAutomatically", "yes-no", None),
    Setting("updates.checkEveryHours", "hours", 24),
)
BY_PATH = {setting.path: setting for setting in SETTINGS}
# How long, in whole hours, a sync goes without checking GitHub, when this PC's settings don't
# say: for dev-home itself, and for dev-home-tools' updates.
DEFAULT_HOURS = {s.path: s.default for s in SETTINGS if s.default is not None}
# The folders each tool is set up in, each with its own answer, setUp, and the one setup sets up
# whenever it exists, unless it's answered no.
CLAUDE_FOLDERS = "claudeCode.folders"
CODEX_HOMES = "codex.homes"
DEFAULT_FOLDERS = {CLAUDE_FOLDERS: "~/.claude", CODEX_HOMES: "~/.codex"}
KIND_TEXT = {
    "folder": "a folder",
    "yes-no": "true or false",
    "hours": "a whole number of hours, 0 or more",
}
MISSING = object()


def get(data: object, path: str, default: object = None) -> Any:
    """The value at a dotted path, or default when any part of it is missing."""
    for part in path.split("."):
        if not isinstance(data, dict) or part not in data:
            return default
        data = data[part]
    return data


def put(data: dict[str, Any], path: str, value: object) -> None:
    """Sets the value at a dotted path, making the groups on the way."""
    *groups, name = path.split(".")
    for group in groups:
        if not isinstance(data.get(group), dict):
            data[group] = {}
        data = data[group]
    data[name] = value


def is_valid(kind: str, value: object) -> bool:
    if kind == "folder":
        return isinstance(value, str)
    if kind == "yes-no":
        return isinstance(value, bool)
    # In Python, true and false are numbers too.
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def hours_text(hours: int) -> str:
    return "every time" if hours == 0 else "every hour" if hours == 1 else f"every {hours} hours"


def read_settings() -> dict[str, Any] | None:
    """This PC's settings as the file has them, or None when the file is missing or isn't a JSON
    object."""
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def layout(data: dict[str, Any], known: int) -> str:
    """Whether a settings file has the layout the code knows: "" when it does, "older" when it
    has no schemaVersion, from before the layout was versioned, and "unknown" for any other
    version, such as one a newer dev-home-tools wrote."""
    if "schemaVersion" not in data:
        return "older"
    version = data["schemaVersion"]
    if isinstance(version, int) and not isinstance(version, bool) and version == known:
        return ""
    return "unknown"


def hours_setting(data: dict[str, Any], path: str) -> tuple[int, bool]:
    """A check interval from the settings, and whether the file's value could be used. A missing
    value, or one that isn't a whole number of 0 or more, means the default."""
    default = DEFAULT_HOURS[path]
    value = get(data, path, MISSING)
    if value is MISSING:
        return default, True
    if is_valid("hours", value):
        return int(value), True
    return default, False


def folder_answers(value: object) -> dict[str, bool]:
    """Each folder in a tool's folders that has an answer, as written, with that answer."""
    if not isinstance(value, dict):
        return {}
    return {
        folder: entry["setUp"]
        for folder, entry in value.items()
        if folder.strip() and isinstance(entry, dict) and isinstance(entry.get("setUp"), bool)
    }


@dataclass(frozen=True)
class Preference:
    """A yes-or-no preference a skill declares in its dev-home-skill.json."""

    skill: str
    name: str
    default: bool
    label: str
    help: str


def skill_preferences(content_dir: str) -> tuple[dict[str, dict[str, Preference]], list[str]]:
    """Every preference the skills declare, by skill and then name: dev-home-tools' skills, then
    the person's own in dev-home, where one with the same name as a dev-home-tools skill isn't
    set up, so its file is skipped. Also a problem for each file, or each preference in one, that
    can't be used."""
    found: dict[str, dict[str, Preference]] = {}
    problems: list[str] = []
    folders = [TOOLS_ROOT / "templates" / "skills"]
    if content_dir:
        folders.append(Path(content_dir) / "skills")
    for folder in folders:
        try:
            skills = sorted(f for f in folder.iterdir() if (f / "SKILL.md").is_file())
        except OSError:
            continue
        for skill in skills:
            path = skill / SKILL_SETTINGS
            taken = any(skill.name.lower() == known.lower() for known in found)
            if taken or not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError) as error:
                problems.append(f"{path} could not be read as JSON, so it was skipped. {error}")
                continue
            declared = data.get("preferences", {}) if isinstance(data, dict) else None
            if not isinstance(declared, dict):
                problems.append(f"{path}: preferences isn't a JSON object, so it was skipped.")
                continue
            found[skill.name] = {}
            for key, entry in declared.items():
                usable = (
                    isinstance(entry, dict)
                    and isinstance(entry.get("default"), bool)
                    and isinstance(entry.get("label"), str)
                    and entry["label"].strip() != ""
                    and isinstance(entry.get("help", ""), str)
                )
                if not usable or "." in key or not key.strip():
                    problems.append(
                        f"{path}: the preference {key} needs a name with no dots, a default of "
                        "true or false, and a label, so it was skipped."
                    )
                    continue
                found[skill.name][key] = Preference(
                    skill.name, key, entry["default"], entry["label"], entry.get("help", "")
                )
    return found, problems


def find_skill(preferences: dict[str, dict[str, Preference]], skill: str) -> str | None:
    """The name a skill declares its preferences under, matched without case, as Windows matches
    its folder."""
    return next((name for name in preferences if name.lower() == skill.lower()), None)


def check_settings(
    data: dict[str, Any], preferences: dict[str, dict[str, Preference]]
) -> list[str]:
    """A problem for each value in this PC's settings that's of the wrong kind, saying what it
    counts as instead, and for each key setup doesn't know, which is kept as it is."""
    problems: list[str] = []
    file = SETTINGS_PATH.name

    def unknown(path: str) -> None:
        problems.append(
            f"{file} has {path}, which setup doesn't know, so it's ignored and kept as it is. "
            "Remove it, or fix its name."
        )

    def wrong(path: str, value: object, wanted: str, counts_as: str) -> None:
        problems.append(
            f"{path} in {file} is {json.dumps(value)}, which isn't {wanted}, so it counts as "
            f"{counts_as}. Fix it there."
        )

    def check_group(key: str, value: dict[str, Any]) -> None:
        for name, inner in value.items():
            path = f"{key}.{name}"
            setting = BY_PATH.get(path)
            if setting is None:
                unknown(path)
            elif not is_valid(setting.kind, inner):
                if setting.default is not None:
                    counts_as = hours_text(setting.default)
                else:
                    counts_as = "not answered yet" if setting.kind == "yes-no" else "not set"
                wrong(path, inner, KIND_TEXT[setting.kind], counts_as)

    def check_folders(key: str, value: dict[str, Any]) -> None:
        for name, inner in value.items():
            path = f"{key}.{name}"
            if path not in (CLAUDE_FOLDERS, CODEX_HOMES):
                unknown(path)
                continue
            if not isinstance(inner, dict):
                wrong(path, inner, "a JSON object of folders", "none answered")
                continue
            for folder, entry in inner.items():
                where = f"{path} {folder}"
                if not isinstance(entry, dict):
                    wrong(where, entry, "a JSON object", "not answered yet")
                    continue
                for entry_key, answer in entry.items():
                    if entry_key != "setUp":
                        unknown(f"{where}: {entry_key}")
                    elif not isinstance(answer, bool):
                        wrong(f"{where}: setUp", answer, "true or false", "not answered yet")
                if path == CODEX_HOMES and folder != DEFAULT_FOLDERS[CODEX_HOMES]:
                    problems.append(
                        f"{file} has {where}, but setup sets up only "
                        f"{DEFAULT_FOLDERS[CODEX_HOMES]} for now, so it's left alone."
                    )

    def check_skills(value: dict[str, Any]) -> None:
        for skill, inner in value.items():
            name = find_skill(preferences, skill)
            if name is None:
                unknown(f"skills.{skill}, a skill that declares no preferences,")
                continue
            if not isinstance(inner, dict):
                wrong(f"skills.{skill}", inner, "a JSON object of preferences", "the defaults")
                continue
            for key, answer in inner.items():
                preference = preferences[name].get(key)
                if preference is None:
                    unknown(f"skills.{skill}.{key}")
                elif not isinstance(answer, bool):
                    default = json.dumps(preference.default)
                    wrong(
                        f"skills.{skill}.{key}", answer, "true or false", f"{default}, its default"
                    )

    groups = {path.split(".")[0] for path in BY_PATH}
    for key, value in data.items():
        if key == "schemaVersion":
            continue
        if key == "testHomeDir":
            if not isinstance(value, str):
                wrong(key, value, "a folder", "not set")
        elif key in groups | {"claudeCode", "codex", "skills"}:
            if not isinstance(value, dict):
                wrong(key, value, "a JSON object of settings", "none set")
            elif key in groups:
                check_group(key, value)
            elif key == "skills":
                check_skills(value)
            else:
                check_folders(key, value)
        else:
            unknown(key)
    return problems


@dataclass
class LocalSettings:
    """The settings setup asks for, with defaults for anything missing. auto_update is None until
    a person answers its question, and a sync treats that as off. claude_folders and codex_homes
    hold each folder with an answer, as written, so setup asks about it only once. data holds
    everything the file had, so a save keeps the keys setup doesn't know. found says the file
    had settings in it. test_home_dir is only ever in a test sandbox's file, which the tests
    write; setup never adds it."""

    content_dir: str = ""
    auto_update: bool | None = None
    claude_folders: dict[str, bool] = field(default_factory=dict)
    codex_homes: dict[str, bool] = field(default_factory=dict)
    test_home_dir: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    found: bool = False


def answered(folders: dict[str, bool], answer: bool) -> list[str]:
    """The folders with that answer, as written."""
    return [folder for folder, setup in folders.items() if setup is answer]


def load_local_settings() -> LocalSettings | None:
    """The settings, or None when the file is there but can't be read as a JSON object. A file
    in another layout loads too, so the caller checks layout() first."""
    settings = LocalSettings()
    if not SETTINGS_PATH.exists():
        return settings
    try:
        text = SETTINGS_PATH.read_text(encoding="utf-8-sig")
        # An empty file holds no answers yet, so it counts as no file.
        if not text.strip():
            return settings
        data = json.loads(text)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    settings.data = data
    settings.found = True
    folder = get(data, "devHome.folder")
    if isinstance(folder, str):
        settings.content_dir = folder
    auto_update = get(data, "updates.installAutomatically")
    if isinstance(auto_update, bool):
        settings.auto_update = auto_update
    settings.claude_folders = folder_answers(get(data, CLAUDE_FOLDERS))
    settings.codex_homes = folder_answers(get(data, CODEX_HOMES))
    if isinstance(data.get("testHomeDir"), str):
        settings.test_home_dir = data["testHomeDir"]
    return settings


def merge_answers(data: dict[str, Any], path: str, answers: dict[str, bool]) -> None:
    """Writes a tool's folder answers into data, keeping each entry's other keys. A folder whose
    answer was taken back loses its setUp, and goes once nothing is left in its entry. A setUp
    that isn't true or false was never an answer, so it's kept as it is."""
    current = get(data, path)
    folders = dict(current) if isinstance(current, dict) else {}
    for folder, entry in list(folders.items()):
        if folder in answers or not isinstance(entry, dict):
            continue
        if isinstance(entry.get("setUp"), bool):
            rest = {key: value for key, value in entry.items() if key != "setUp"}
            if rest:
                folders[folder] = rest
            else:
                del folders[folder]
    for folder, answer in answers.items():
        entry = folders.get(folder)
        if isinstance(entry, dict):
            folders[folder] = {**entry, "setUp": answer}
        else:
            folders[folder] = {"setUp": answer}
    if folders:
        put(data, path, folders)
    elif isinstance(current, dict):
        group, name = path.split(".")
        del data[group][name]
        if not data[group]:
            del data[group]


def local_settings_text(settings: LocalSettings) -> str:
    """The file's text for the settings, with schemaVersion first, keeping every other key the
    file had where it was. A setting is written only once it's answered. testHomeDir is kept when
    the file has it, and never added."""
    data = copy.deepcopy(settings.data)
    data.pop("schemaVersion", None)
    if settings.content_dir:
        put(data, "devHome.folder", settings.content_dir)
    if settings.auto_update is not None:
        put(data, "updates.installAutomatically", settings.auto_update)
    merge_answers(data, CLAUDE_FOLDERS, settings.claude_folders)
    merge_answers(data, CODEX_HOMES, settings.codex_homes)
    if settings.test_home_dir:
        data["testHomeDir"] = settings.test_home_dir
    text = json.dumps({"schemaVersion": SCHEMA_VERSION, **data}, indent=2, ensure_ascii=False)
    return text + "\n"


@dataclass
class DevHomeSettings:
    """dev-home.json as read: its keys ({} when it's missing or unreadable), its text, its layout
    ("" when it's the one the code knows, "missing", "unreadable", "older", or "unknown"; see
    layout()), and why it couldn't be read."""

    data: dict[str, Any]
    text: str
    layout: str
    error: str = ""

    @property
    def answer(self) -> bool | None:
        """Its answer to whether more than one copy is in active use, whatever its layout."""
        answer = self.data.get("multiMachine")
        return answer if isinstance(answer, bool) else None

    @property
    def several(self) -> bool | None:
        """Its answer, only when it's in the layout the code knows."""
        return self.answer if self.layout == "" else None


def read_dev_home_settings(root: Path) -> DevHomeSettings:
    path = root / DEV_HOME_SETTINGS
    if not path.exists():
        return DevHomeSettings({}, "", "missing")
    try:
        text = path.read_text(encoding="utf-8-sig")
        data = json.loads(text)
    except (OSError, ValueError) as error:
        return DevHomeSettings({}, "", "unreadable", str(error))
    if not isinstance(data, dict):
        return DevHomeSettings({}, text, "unreadable", "not a JSON object")
    return DevHomeSettings(data, text, layout(data, DEV_HOME_SCHEMA_VERSION))


def dev_home_text(data: dict[str, Any], several: bool) -> str:
    """dev-home.json's text with that answer, schemaVersion first, keeping every other key where
    it was."""
    rest = {key: value for key, value in data.items() if key != "schemaVersion"}
    rest["multiMachine"] = several
    return json.dumps({"schemaVersion": DEV_HOME_SCHEMA_VERSION, **rest}, indent=2) + "\n"
