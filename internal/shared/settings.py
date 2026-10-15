"""This PC's settings, from local-settings.json in dev-home-tools' folder, and dev-home's own, from
dev-home.json in dev-home, which every copy of it shares. setup.py writes both.

Each setting's name is its path in the file, such as devHome.folder. setting-definitions.json,
beside this file, declares the ones with a single value, as SETTINGS, and each skill declares its
preferences in its dev-home-skill.json. A saved value is missing, a state such as
{"$state": "default"}, or a plain value, the person's own answer; read_value says what each counts
as. check_settings checks every value against the declarations and the folders each tool sets up.
docs/development/settings.md has the rules."""

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
# The file that declares dev-home-tools' own settings with a single value.
DEFINITIONS_PATH = Path(__file__).parent / "setting-definitions.json"
# The key of a saved state, such as {"$state": "default"}. No setting's own value uses it.
STATE = "$state"
TYPE_TEXT = {
    "folder": "a folder",
    "yes-no": "true or false",
    "hours": "a whole number of hours, 0 or more",
}
MISSING = object()


@dataclass(frozen=True)
class Setting:
    """A setting with a single value: one of dev-home-tools' own, or a skill's preference. type
    is "folder", "yes-no", or "hours" (a whole number of hours, 0 or more, where 0 means every
    time). has_default says whether default means anything; asked, whether setup asks about it.
    former_names are the names it was saved under before."""

    path: str
    type: str
    default: Any = None
    has_default: bool = False
    asked: bool = False
    label: str = ""
    help: str = ""
    former_names: tuple[str, ...] = ()


def is_valid(kind: str, value: object) -> bool:
    if kind == "folder":
        return isinstance(value, str)
    if kind == "yes-no":
        return isinstance(value, bool)
    # In Python, true and false are numbers too.
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def load_definitions() -> tuple[Setting, ...]:
    """dev-home-tools' own settings, as setting-definitions.json declares them. It comes with the
    code, so one it can't use is a bug, which stops the run; a test reads it."""
    data = json.loads(DEFINITIONS_PATH.read_text(encoding="utf-8"))
    found: list[Setting] = []
    for path, entry in data["settings"].items():
        if entry["type"] not in TYPE_TEXT or (
            "default" in entry and not is_valid(entry["type"], entry["default"])
        ):
            raise ValueError(
                f"{DEFINITIONS_PATH.name}: {path} has a type or default setup can't use."
            )
        found.append(
            Setting(
                path,
                entry["type"],
                entry.get("default"),
                "default" in entry,
                bool(entry.get("asked", False)),
                entry["label"],
                entry["help"],
                tuple(entry.get("formerNames", ())),
            )
        )
    return tuple(found)


SETTINGS = load_definitions()
BY_PATH = {setting.path: setting for setting in SETTINGS}
# How long, in whole hours, a sync goes without checking GitHub, when this PC's settings don't
# say: for dev-home itself, and for dev-home-tools' updates.
DEFAULT_HOURS = {s.path: s.default for s in SETTINGS if s.type == "hours" and s.has_default}
AUTO_UPDATE = "updates.installAutomatically"
# The folders each tool is set up in, each with its own answer, setUp.
CLAUDE_FOLDERS = "claudeCode.folders"
CODEX_HOMES = "codex.homes"


@dataclass(frozen=True)
class Tool:
    """A tool setup sets up in each of its folders answered yes, whose answers are saved at
    setting: Claude Code in each Claude Code folder, and Codex in each Codex home, as each tool's
    docs call one. default is the folder in the profile that the tool makes when it first runs;
    an extra one is named after it, such as ~/.claude-second, one for each account, and counts
    only when it holds one of marks, if the tool has any. variable names the folder a session of
    the tool uses."""

    name: str
    folder: str
    account: str
    setting: str
    default: str
    variable: str
    marks: tuple[str, ...] = ()


CLAUDE_CODE = Tool(
    "Claude Code", "folder", "Claude", CLAUDE_FOLDERS, ".claude", "CLAUDE_CONFIG_DIR"
)
# A ~/.codex-* folder Codex has used holds its settings or its sign-in.
CODEX = Tool(
    "Codex", "home", "Codex", CODEX_HOMES, ".codex", "CODEX_HOME", ("config.toml", "auth.json")
)
TOOLS = (CLAUDE_CODE, CODEX)
FOLDER_SETTINGS = tuple(tool.setting for tool in TOOLS)
# In a Codex home's entry, the SKILL.md path of each [[skills.config]] entry setup wrote there to
# hide one of dev-home's skills, while the home is answered no. It's setup's record of its own
# changes, not an answer, so a skill turned back on through Codex's menu, which deletes the entry,
# isn't hidden again.
HIDDEN_SKILLS = "hiddenSkills"


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


def hours_text(hours: int) -> str:
    return "every time" if hours == 0 else "every hour" if hours == 1 else f"every {hours} hours"


def accepted_states(setting: Setting) -> list[str]:
    """The states a setting can be saved in, besides missing and a plain value: default for one
    with a default, and unanswered too when setup asks about it."""
    if not setting.has_default:
        return []
    return ["default", "unanswered"] if setting.asked else ["default"]


def read_value(value: object, setting: Setting) -> tuple[Any, bool, bool]:
    """What a saved value counts as, whether it's an answer, and whether it could be used. Missing,
    unanswered, and default count as the setting's default, or None with none; so does a value the
    setting can't use, such as a state it doesn't accept."""
    fallback = setting.default if setting.has_default else None
    if value is MISSING:
        return fallback, False, True
    if isinstance(value, dict) and STATE in value:
        if value[STATE] in accepted_states(setting):
            return fallback, value[STATE] == "default", True
        return fallback, False, False
    if is_valid(setting.type, value):
        return value, True, True
    return fallback, False, False


def saved_answer(answer: bool | str) -> object:
    """How the answer to a yes-or-no question about a setting with a default is saved: yes or
    no as the plain value, and "default" as the default state, so it follows the default."""
    return {STATE: "default"} if answer == "default" else answer


def setting_value(data: dict[str, Any], path: str) -> tuple[Any, bool, bool]:
    """read_value for one of dev-home-tools' own settings, from the file's data."""
    return read_value(get(data, path, MISSING), BY_PATH[path])


def value_text(setting: Setting, value: Any) -> str:
    """A setting's value in words, such as "every 12 hours" or "yes"."""
    if setting.type == "hours":
        return hours_text(int(value))
    if setting.type == "yes-no":
        return "yes" if value else "no"
    return str(value)


def counts_as_text(setting: Setting) -> str:
    """What a value a setting can't use counts as, for a PROBLEM line."""
    if not setting.has_default:
        return "not answered yet" if setting.asked else "not set"
    if setting.type == "hours":
        return hours_text(int(setting.default))
    return f"{json.dumps(setting.default)}, its default"


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
    """A check interval from the settings, and whether the file's value could be used. Missing,
    the default state, and a value it can't use all mean the default."""
    hours, _, usable = setting_value(data, path)
    return int(hours), usable


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
    """A yes-or-no preference a skill declares in its dev-home-skill.json, saved at
    skills.<skill>.preferences.<name>."""

    skill: str
    name: str
    default: bool
    label: str
    help: str
    former_names: tuple[str, ...] = ()

    @property
    def setting(self) -> Setting:
        """The preference as a setting with a default, which setup asks about."""
        return Setting(
            f"skills.{self.skill}.preferences.{self.name}",
            "yes-no",
            self.default,
            True,
            True,
            self.label,
            self.help,
            self.former_names,
        )


@dataclass
class SkillDeclarations:
    """What the skills declare. preferences has every skill there is, by name, with the
    preferences it declares by name, none for a skill without a dev-home-skill.json. unread
    names, in lowercase, each skill whose file couldn't be read, so what it declares isn't known.
    complete says whether every skills folder could be listed, so a skill in neither is gone.
    problems has one for each file, or each preference in one, that can't be used."""

    preferences: dict[str, dict[str, Preference]] = field(default_factory=dict)
    unread: set[str] = field(default_factory=set)
    complete: bool = True
    problems: list[str] = field(default_factory=list)

    def is_gone(self, skill: str) -> bool:
        """Whether a skill is in no skills folder, so its saved answers can go. Never while a
        folder couldn't be listed, or for a skill whose file couldn't be read."""
        return (
            self.complete
            and find_skill(self.preferences, skill) is None
            and skill.lower() not in self.unread
        )


def skill_preferences(content_dir: str) -> SkillDeclarations:
    """Every skill and the preferences it declares: dev-home-tools' skills, then the person's
    own in dev-home, where one with the same name as a dev-home-tools skill isn't set up, so its
    file is skipped (see SkillDeclarations). The list is complete only when dev-home's folder is a
    git repo, so a PC whose dev-home isn't cloned yet, even into a folder already made for it, or
    is on a drive that's unplugged, loses no answers."""
    found = SkillDeclarations()
    folders = [TOOLS_ROOT / "templates" / "skills"]
    if content_dir and (Path(content_dir) / ".git").exists():
        folders.append(Path(content_dir) / "skills")
    else:
        found.complete = False
    for folder in folders:
        try:
            skills = sorted(f for f in folder.iterdir() if (f / "SKILL.md").is_file())
        except FileNotFoundError:
            # A dev-home with no skills of its own yet.
            continue
        except OSError:
            found.complete = False
            continue
        for skill in skills:
            path = skill / SKILL_SETTINGS
            if find_skill(found.preferences, skill.name) is not None:
                continue
            if not path.is_file():
                found.preferences[skill.name] = {}
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError) as error:
                found.problems.append(
                    f"{path} could not be read as JSON, so it was skipped. {error}"
                )
                found.unread.add(skill.name.lower())
                continue
            declared = data.get("preferences", {}) if isinstance(data, dict) else None
            if not isinstance(declared, dict):
                found.problems.append(
                    f"{path}: preferences isn't a JSON object, so it was skipped."
                )
                found.unread.add(skill.name.lower())
                continue
            found.preferences[skill.name] = {}
            for key, entry in declared.items():
                former = entry.get("formerNames", []) if isinstance(entry, dict) else None
                usable = (
                    isinstance(entry, dict)
                    and isinstance(entry.get("default"), bool)
                    and isinstance(entry.get("label"), str)
                    and entry["label"].strip() != ""
                    and isinstance(entry.get("help", ""), str)
                    and isinstance(former, list)
                    and all(isinstance(name, str) and name.strip() for name in former)
                )
                if not usable or "." in key or not key.strip():
                    found.problems.append(
                        f"{path}: the preference {key} needs a name with no dots, a default of "
                        "true or false, a label, and formerNames, if any, as a list of names, so "
                        "it was skipped."
                    )
                    continue
                found.preferences[skill.name][key] = Preference(
                    skill.name,
                    key,
                    entry["default"],
                    entry["label"],
                    entry.get("help", ""),
                    tuple(former or ()),
                )
    return found


def find_skill(preferences: dict[str, dict[str, Preference]], skill: str) -> str | None:
    """The name a skill declares its preferences under, matched without case, as Windows matches
    its folder."""
    return next((name for name in preferences if name.lower() == skill.lower()), None)


def remove_path(data: dict[str, Any], path: str) -> None:
    """Removes the value at a dotted path, and each group it leaves empty."""
    *groups, name = path.split(".")
    chain = [data]
    for group in groups:
        inner = chain[-1].get(group)
        if not isinstance(inner, dict):
            return
        chain.append(inner)
    chain[-1].pop(name, None)
    for container, group in zip(reversed(chain[:-1]), reversed(groups), strict=True):
        if container[group]:
            break
        del container[group]


@dataclass
class Checked:
    """What check_settings found: the settings with each answer under a former name moved to the
    setting's name, and each setting nothing declares removed; a problem for each value of the
    wrong kind; and what was moved and removed, for the line that says so."""

    data: dict[str, Any]
    problems: list[str] = field(default_factory=list)
    moved: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


def check_settings(
    data: dict[str, Any], declared: SkillDeclarations, *, remove_gone_skills: bool
) -> Checked:
    """Checks this PC's settings against the declarations: an answer saved under a setting's
    former name moves to its name, a setting nothing declares is removed, and a value of the wrong
    kind is a problem, saying what it counts as instead. A skill whose file can't be read keeps
    its answers. So does a skill that's gone, unless remove_gone_skills: only a run that holds the
    sync's lock passes it, since a sync or an update may be replacing a skill's files at that
    moment, and the skill would only look gone. The settings passed in aren't changed."""
    preferences = declared.preferences
    checked = Checked(copy.deepcopy(data))
    data = checked.data
    problems = checked.problems
    file = SETTINGS_PATH.name

    def remove(container: dict[str, Any], key: str, path: str) -> None:
        del container[key]
        checked.removed.append(path)

    for setting in SETTINGS:
        if get(data, setting.path, MISSING) is not MISSING:
            continue
        for old in setting.former_names:
            value = get(data, old, MISSING)
            if value is not MISSING:
                remove_path(data, old)
                put(data, setting.path, value)
                checked.moved.append(f"{old} to {setting.path}")
                break

    def wrong(path: str, value: object, wanted: str, counts_as: str) -> None:
        problems.append(
            f"{path} in {file} is {json.dumps(value)}, which isn't {wanted}, so it counts as "
            f"{counts_as}. Fix it there."
        )

    def check_value(path: str, value: object, setting: Setting) -> None:
        if not read_value(value, setting)[2]:
            wrong(path, value, TYPE_TEXT[setting.type], counts_as_text(setting))

    def check_group(key: str, value: dict[str, Any]) -> None:
        for name, inner in list(value.items()):
            path = f"{key}.{name}"
            setting = BY_PATH.get(path)
            if setting is None:
                remove(value, name, path)
            else:
                check_value(path, inner, setting)

    def check_folders(key: str, value: dict[str, Any]) -> None:
        for name, inner in list(value.items()):
            path = f"{key}.{name}"
            if path not in FOLDER_SETTINGS:
                remove(value, name, path)
                continue
            if not isinstance(inner, dict):
                wrong(path, inner, "a JSON object of folders", "none answered")
                continue
            for folder, entry in inner.items():
                where = f"{path} {folder}"
                if not isinstance(entry, dict):
                    wrong(where, entry, "a JSON object", "not answered yet")
                    continue
                for entry_key, answer in list(entry.items()):
                    if entry_key == HIDDEN_SKILLS and path == CODEX_HOMES:
                        if not is_path_list(answer):
                            wrong(f"{where}: {entry_key}", answer, "a list of paths", "none")
                    elif entry_key != "setUp":
                        remove(entry, entry_key, f"{where}: {entry_key}")
                    elif not isinstance(answer, bool):
                        wrong(f"{where}: setUp", answer, "true or false", "not answered yet")

    def check_skills(value: dict[str, Any]) -> None:
        for skill, inner in list(value.items()):
            name = find_skill(preferences, skill)
            if name is None:
                if remove_gone_skills and declared.is_gone(skill):
                    remove(value, skill, f"skills.{skill}")
                continue
            if not isinstance(inner, dict):
                wrong(f"skills.{skill}", inner, "a JSON object", "the defaults")
                continue
            for group, saved in list(inner.items()):
                where = f"skills.{skill}.{group}"
                if group != "preferences":
                    remove(inner, group, where)
                elif not isinstance(saved, dict):
                    wrong(where, saved, "a JSON object of preferences", "the defaults")
                else:
                    for preference in preferences[name].values():
                        if preference.name in saved:
                            continue
                        old = next((n for n in preference.former_names if n in saved), None)
                        if old is not None:
                            saved[preference.name] = saved.pop(old)
                            checked.moved.append(f"{where}.{old} to {where}.{preference.name}")
                    for key, answer in list(saved.items()):
                        known = preferences[name].get(key)
                        if known is None:
                            remove(saved, key, f"{where}.{key}")
                        else:
                            check_value(f"{where}.{key}", answer, known.setting)

    groups = {path.split(".")[0] for path in BY_PATH}
    for key, value in list(data.items()):
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
            # A group left empty goes too, or the save would write it back.
            if isinstance(value, dict) and not value:
                del data[key]
        else:
            remove(data, key, key)
    return checked


@dataclass
class LocalSettings:
    """The settings setup asks for, with defaults for anything missing. folders holds, for each
    tool's folders (CLAUDE_FOLDERS and CODEX_HOMES), each folder with an answer, as written, so
    setup asks about it only once. data holds everything the file had, so a save keeps the keys
    setup doesn't know, and each setting in the form it was saved in: setting_value reads one, such
    as whether automatic updates are answered yet. found says the file had settings in it.
    test_home_dir is only ever in a test sandbox's file, which the tests write; setup never adds
    it."""

    content_dir: str = ""
    folders: dict[str, dict[str, bool]] = field(
        default_factory=lambda: {path: {} for path in FOLDER_SETTINGS}
    )
    test_home_dir: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    found: bool = False


def answered(folders: dict[str, bool], answer: bool) -> list[str]:
    """The folders with that answer, as written."""
    return [folder for folder, setup in folders.items() if setup is answer]


def is_path_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(p, str) and p.strip() for p in value)


def home_entry(data: dict[str, Any], entry: str) -> dict[str, Any] | None:
    """A Codex home's entry in codex.homes, by its name as written, which may hold a dot."""
    homes = get(data, CODEX_HOMES)
    found = homes.get(entry) if isinstance(homes, dict) else None
    return found if isinstance(found, dict) else None


def hidden_skills(data: dict[str, Any], entry: str) -> list[str]:
    """The SKILL.md paths of the [[skills.config]] entries setup wrote in a Codex home, as its entry
    records them, or none when it records none it can use."""
    found = home_entry(data, entry)
    paths = found.get(HIDDEN_SKILLS) if found is not None else None
    return list(paths) if isinstance(paths, list) and is_path_list(paths) else []


def set_hidden_skills(data: dict[str, Any], entry: str, paths: list[str]) -> None:
    """Records the SKILL.md paths of the [[skills.config]] entries setup wrote in a Codex home, in
    its entry, which is made when it's missing. With none, the record goes, and so does an entry
    or group it leaves empty."""
    found = home_entry(data, entry)
    if found is None:
        if not paths:
            return
        homes = get(data, CODEX_HOMES)
        if not isinstance(homes, dict):
            put(data, CODEX_HOMES, {})
            homes = get(data, CODEX_HOMES)
        found = homes[entry] = {}
    if paths:
        found[HIDDEN_SKILLS] = list(paths)
        return
    found.pop(HIDDEN_SKILLS, None)
    if not found:
        homes = get(data, CODEX_HOMES)
        del homes[entry]
        if not homes:
            remove_path(data, CODEX_HOMES)


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
    settings.folders = {path: folder_answers(get(data, path)) for path in FOLDER_SETTINGS}
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


def local_settings_data(settings: LocalSettings) -> dict[str, Any]:
    """What the file holds for the settings, with schemaVersion first, keeping every other key the
    file had where it was. testHomeDir is kept when the file has it, and never added."""
    data = copy.deepcopy(settings.data)
    data.pop("schemaVersion", None)
    if settings.content_dir:
        put(data, "devHome.folder", settings.content_dir)
    for path in FOLDER_SETTINGS:
        merge_answers(data, path, settings.folders[path])
    if settings.test_home_dir:
        data["testHomeDir"] = settings.test_home_dir
    return {"schemaVersion": SCHEMA_VERSION, **data}


def settings_text(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def local_settings_text(settings: LocalSettings) -> str:
    """The file's text for the settings (see local_settings_data)."""
    return settings_text(local_settings_data(settings))


KeyPath = tuple[str, ...]


def leaves(data: dict[str, Any], prefix: KeyPath = ()) -> dict[KeyPath, Any]:
    """Each value in the settings by its path of keys. A state, such as {"$state": "default"}, and
    an empty group are values of their own. Keys go in a tuple, since a folder's name can hold a
    dot."""
    found: dict[KeyPath, Any] = {}
    for key, value in data.items():
        path = (*prefix, key)
        if isinstance(value, dict) and value and STATE not in value:
            found.update(leaves(value, path))
        else:
            found[path] = value
    return found


def apply_changes(data: dict[str, Any], before: dict[str, Any], after: dict[str, Any]) -> None:
    """Makes in data the changes that turned before into after, value by value, and nothing else,
    so whatever else data has, such as another run's answer saved in the meantime, stays."""
    old, new = leaves(before), leaves(after)
    for path in old:
        # A group this run filled, such as an empty one it added answers to, isn't removed: its
        # new values go in below, beside whatever else the group holds by now.
        filled = any(len(other) > len(path) and other[: len(path)] == path for other in new)
        if path not in new and not filled:
            chain = [data]
            for key in path[:-1]:
                inner = chain[-1].get(key)
                if not isinstance(inner, dict):
                    break
                chain.append(inner)
            else:
                chain[-1].pop(path[-1], None)
                # A group left empty goes, as merge_answers drops one.
                for container, key in zip(reversed(chain[:-1]), reversed(path[:-1]), strict=True):
                    if container[key]:
                        break
                    del container[key]
    for path, value in new.items():
        if path in old and old[path] == value:
            continue
        target = data
        for key in path[:-1]:
            if not isinstance(target.get(key), dict):
                target[key] = {}
            target = target[key]
        target[path[-1]] = copy.deepcopy(value)


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
