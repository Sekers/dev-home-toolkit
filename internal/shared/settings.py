"""This PC's settings, from local-settings.json in dev-home-toolkit's folder, and dev-home's own,
from dev-home.json in dev-home, which every copy of it shares. setup.py writes both.

Each setting's name is its path in the file, such as devHome.folder. setting-definitions.json,
beside this file, declares the ones with a single value, as SETTINGS, and each skill declares its
preferences in its dev-home-skill.json, which skill_declarations reads whole, with what the skill
needs to run (see requirements.py). A saved value is missing, a state such as
{"$state": "default"}, or a plain value, the person's own answer; read_value says what each counts
as. check_settings checks every value against the declarations and each agent's folders.
docs/development/settings.md has the rules."""

import copy
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Any

from .paths import comparable, resolve_home, same_path
from .requirements import LISTS, Requirement, parse_list, unknown_field

# dev-home-toolkit's folder: this file is in internal/shared/, two folders below it.
TOOLKIT_ROOT = Path(__file__).parent.parent.parent
SETTINGS_PATH = TOOLKIT_ROOT / "local-settings.json"
# dev-home's own settings, in its root: for now, only multiMachine, whether more than one copy is
# in active use.
DEV_HOME_SETTINGS = "dev-home.json"
# The knowledge base's index in dev-home, the end user's own: a table with one row per note, whose
# first cell links to the note, relative to the index's folder.
KNOWLEDGE_INDEX = "knowledge/README.md"
# Each file's layout version. "Changing a setting later" in docs/development/settings.md says when
# it goes up.
SCHEMA_VERSION = 1
DEV_HOME_SCHEMA_VERSION = 1
# The file in a skill's folder that declares its preferences, and what it needs to run, with the
# fields it takes, and those each preference takes. requirements.py has the fields of the entries
# in supportedOn and dependsOn.
SKILL_SETTINGS = "dev-home-skill.json"
SKILL_FIELDS = (
    "recommended",
    "alwaysAddedToAgents",
    *LISTS,
    "preferences",
    "formerNames",
)
PREFERENCE_FIELDS = ("default", "label", "help", "formerNames")
# Each skill's answer to whether this PC adds it to the agents, at skills.<skill>.addedToAgents.
ADDED_TO_AGENTS = "addedToAgents"
# The rule for a skill's name (see name_problem): the Agent Skills standard's longest name; the
# words claude.ai and Anthropic's API keep out of a skill's name; and the two names Claude Code
# keeps for the skills it downloads from claude.ai, and skips. It saves them in a skills folder
# named synced, in any case, so setup never adds a skill of that name: a link there would take
# those downloads into the skill's own folder.
NAME_LIMIT = 64
RESERVED_WORDS = ("anthropic", "claude")
CLAUDE_DOWNLOADS_FOLDER = "synced"
CLAUDE_DOWNLOADS_NAME = "anthropic-skills"
KEPT_OFF_FOR_NAME = "has a name Claude Code keeps for the skills it downloads from claude.ai"
# The file that declares dev-home-toolkit's own settings with a single value.
DEFINITIONS_PATH = Path(__file__).parent / "setting-definitions.json"
# The key of a saved state, such as {"$state": "default"}. No setting's own value uses it.
STATE = "$state"
TYPE_TEXT = {
    "folder": "a folder",
    "yes-no": "true or false",
    "hours": "a whole number of hours, 0 or more",
    "kib": "a whole number of KiB, 0 or more",
}
# The unit of each kind of setting that holds a whole number, 0 or more.
UNITS = {"hours": "hours", "kib": "KiB"}
MISSING = object()
# A value's path in the settings as its keys, for where a key can hold a dot, as a folder's name
# can.
KeyPath = tuple[str, ...]


@dataclass(frozen=True)
class Setting:
    """A setting with a single value: one of dev-home-toolkit's own, or a skill's preference. type
    is "folder", "yes-no", "hours" (a whole number of hours, 0 or more, where 0 means every time),
    or "kib" (a whole number of KiB, 0 or more, whose help says what 0 means). has_default says
    whether default means anything; asked, whether setup asks about it. former_names are the names
    it was saved under before."""

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
    """dev-home-toolkit's own settings, as setting-definitions.json declares them. It comes with the
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
# say: for dev-home itself, and for dev-home-toolkit's updates.
DEFAULT_HOURS = {s.path: s.default for s in SETTINGS if s.type == "hours" and s.has_default}
AUTO_UPDATE = "updates.installAutomatically"
# The size of the end user's rules for one agent on this PC past which a sync warns, and the least
# each Codex home's project_doc_max_bytes is set to, each in KiB (decision 0065).
RULES_WARN_ABOVE = "rules.warnAboveKiB"
CODEX_INSTRUCTIONS_MAX = "codex.instructionsMaxKiB"
# Each agent's folders setup knows of, an entry for each with its answer, setUp, in the same shape
# for both agents, such as {"~/.claude": {"setUp": true}}.
CLAUDE_FOLDERS = "claudeCode.folders"
CODEX_HOMES = "codex.homes"


@dataclass(frozen=True)
class Agent:
    """An agent setup sets up in each of its folders, as each agent's docs call one, answered yes in
    its entry at setting. default is the folder in the profile that the agent makes when it first
    runs; an extra one is named after it, such as ~/.claude-second, one for each account, and
    counts only when it holds one of marks, if the agent has any. variable names the folder a
    session of the agent uses.

    shared says every folder reads the same skills, as every Codex home reads ~/.agents/skills,
    so every folder's entry holds the same answer: the main folder's (see folder_rank). Only
    setup's code knows this, so once an agent reads skills per folder, nothing saved changes."""

    name: str
    folder: str
    account: str
    setting: str
    default: str
    variable: str
    marks: tuple[str, ...] = ()
    shared: bool = False

    @property
    def group(self) -> str:
        """The agent's group in local-settings.json, such as claudeCode, which names it in the
        list of recommended settings too."""
        return self.setting.split(".")[0]


CLAUDE_CODE = Agent(
    "Claude Code", "folder", "Claude", CLAUDE_FOLDERS, ".claude", "CLAUDE_CONFIG_DIR"
)
# A ~/.codex-* folder Codex has used holds its settings or its sign-in.
CODEX = Agent(
    "Codex",
    "home",
    "Codex",
    CODEX_HOMES,
    ".codex",
    "CODEX_HOME",
    ("config.toml", "auth.json"),
    shared=True,
)
# Adding an agent: if it reads a skills folder another agent here reads too, such as
# ~/.agents/skills, see AGENTS_SKILLS in setup.py first.
AGENTS = (CLAUDE_CODE, CODEX)
# Each agent's folders, which setting-definitions.json can't declare, since a folder's name can hold
# a dot.
FOLDER_SETTINGS = tuple(agent.setting for agent in AGENTS)
FOLDERS_FOR = {agent.setting: agent for agent in AGENTS}


def folder_rank(agent: Agent, folder: str | Path, home: Path) -> tuple[int, str]:
    """Where a folder of a shared agent comes, in its entries and in choosing the main one: the
    default one, such as ~/.codex, first, then each other one in the profile named after it, by
    name, then every other folder, by its full path. folder may start with ~."""
    full = comparable(resolve_home(str(folder), home))
    name = Path(full).name.lower()
    if same_path(Path(full).parent, home):
        if name == agent.default:
            return 0, ""
        if name.startswith(agent.default + "-"):
            return 1, name
    return 2, os.path.normcase(full)


def order_folders(data: dict[str, Any], home: Path) -> bool:
    """Puts each shared agent's entries in data in order (see folder_rank), and returns whether
    their order changed."""
    moved = False
    for agent in AGENTS:
        entries = get(data, agent.setting)
        if not agent.shared or not isinstance(entries, dict):
            continue
        ordered = sorted(entries, key=lambda entry: folder_rank(agent, entry, home))
        if ordered != list(entries):
            put(data, agent.setting, {entry: entries[entry] for entry in ordered})
            moved = True
    return moved


def get(data: object, path: str, default: object = None) -> Any:
    """The value at a dotted path, or default when any part of it is missing."""
    for part in path.split("."):
        if not isinstance(data, dict) or part not in data:
            return default
        data = data[part]
    return data


def value_at(data: object, keys: KeyPath) -> Any:
    """The value at a path of keys, or MISSING when any part of it is missing."""
    for key in keys:
        if not isinstance(data, dict) or key not in data:
            return MISSING
        data = data[key]
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
    """read_value for one of dev-home-toolkit's own settings, from the file's data."""
    return read_value(get(data, path, MISSING), BY_PATH[path])


def value_text(setting: Setting, value: Any) -> str:
    """A setting's value in words, such as "every 12 hours", "32 KiB", or "yes"."""
    if setting.type == "hours":
        return hours_text(int(value))
    if setting.type == "kib":
        return f"{value} KiB"
    if setting.type == "yes-no":
        return "yes" if value else "no"
    return str(value)


def counts_as_text(setting: Setting) -> str:
    """What a value a setting can't use counts as, for a PROBLEM line."""
    if not setting.has_default:
        return "not answered yet" if setting.asked else "not set"
    if setting.type == "hours":
        return hours_text(int(setting.default))
    if setting.type == "kib":
        return f"{setting.default} KiB, its default"
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
    version, such as one a newer dev-home-toolkit wrote."""
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
    """Each folder in an agent's folders that has an answer, as written, with that answer."""
    if not isinstance(value, dict):
        return {}
    return {
        folder: entry["setUp"]
        for folder, entry in value.items()
        if folder.strip() and isinstance(entry, dict) and isinstance(entry.get("setUp"), bool)
    }


def listed_entries(value: object) -> list[str]:
    """Each folder with an entry in an agent's folders, as written, with an answer or not."""
    if not isinstance(value, dict):
        return []
    return [folder for folder, entry in value.items() if folder.strip() and isinstance(entry, dict)]


# A reminder's date, as written: YYYY-MM-DD, which date.fromisoformat alone would widen.
REMINDER_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class Reminder:
    """An answer to an offer, such as a folder setup hasn't set up, to ask again later: on that
    date, or with none, the next time it would be asked. Saved as {"$state": "remind"}, with the
    date as "on"."""

    on: date | None

    def due(self, today: date) -> bool:
        """Whether it's time to ask again."""
        return self.on is None or self.on <= today

    @property
    def saved(self) -> dict[str, str]:
        """The reminder as the settings file holds it."""
        return {STATE: "remind", **({"on": self.on.isoformat()} if self.on else {})}


def read_reminder(value: object) -> Reminder | None:
    """The reminder a saved value holds, or None when it holds none setup can use."""
    if not isinstance(value, dict) or value.get(STATE) != "remind" or set(value) - {STATE, "on"}:
        return None
    on = value.get("on")
    if on is None and "on" not in value:
        return Reminder(None)
    if not isinstance(on, str) or not REMINDER_DATE.fullmatch(on):
        return None
    try:
        return Reminder(date.fromisoformat(on))
    except ValueError:
        return None


def folder_reminders(value: object) -> dict[str, Reminder]:
    """Each folder in an agent's folders whose answer is a reminder, as written, with it."""
    if not isinstance(value, dict):
        return {}
    found: dict[str, Reminder] = {}
    for folder, entry in value.items():
        if folder.strip() and isinstance(entry, dict):
            reminder = read_reminder(entry.get("setUp"))
            if reminder is not None:
                found[folder] = reminder
    return found


def put_folder_state(
    data: dict[str, Any], path: str, entry: str, state: dict[str, str] | None
) -> None:
    """Saves the answer of one of an agent's folders, by its entry as written, as a state, such as
    a reminder; or with None, takes the state back out, and the entry once nothing is left in it.
    A yes or a no goes in LocalSettings.folders instead, which a save writes over any state."""
    current = get(data, path)
    folders = dict(current) if isinstance(current, dict) else {}
    found = folders.get(entry)
    if state is None and not (isinstance(found, dict) and "setUp" in found):
        return
    kept = dict(found) if isinstance(found, dict) else {}
    if state is not None:
        kept["setUp"] = state
    else:
        kept.pop("setUp", None)
    if kept:
        folders[entry] = kept
    else:
        folders.pop(entry, None)
    put(data, path, folders)


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


@dataclass(frozen=True)
class Skill:
    """What a skill declares in its dev-home-skill.json, or the defaults for a skill without
    one. own says it's the person's own, from dev-home's skills/, rather than dev-home-toolkit's.
    recommended says whether it's added to the agents unless a PC's answer says otherwise, and
    always_added that it's added on every PC, which only dev-home-toolkit's own skills can declare.
    requires is what it needs to run, from its supportedOn and dependsOn (see requirements.py),
    preferences are its preferences, by name, and former_names the names it had before, whose
    answers setup moves to this one. kept_off says why setup never adds it, whatever its answer,
    said to follow "which", or is empty: only for a name Claude Code keeps (see name_problem)."""

    name: str
    own: bool
    recommended: bool = True
    always_added: bool = False
    requires: tuple[Requirement, ...] = ()
    preferences: dict[str, Preference] = field(default_factory=dict)
    former_names: tuple[str, ...] = ()
    kept_off: str = ""

    @property
    def added_setting(self) -> Setting | None:
        """Whether this PC adds the skill to its agents, as a setting with the skill's default,
        which setup asks about; None for a skill that's always added, which has no answer."""
        if self.always_added:
            return None
        return Setting(
            f"skills.{self.name}.{ADDED_TO_AGENTS}",
            "yes-no",
            self.recommended,
            True,
            True,
            f"Add the {self.name} skill to your agents",
            "Whether setup adds the skill to each Claude Code folder and Codex home it sets up on "
            "this PC.",
        )


@dataclass
class SkillDeclarations:
    """What the skills declare. skills has every skill there is, by name, apart from those in
    unread, which names, in lowercase, each skill whose file couldn't be read, so what it declares
    isn't known. complete says whether every skills folder could be listed, so a skill in neither
    is gone. problems has one for each file, or each part of one, that can't be used."""

    skills: dict[str, Skill] = field(default_factory=dict)
    unread: set[str] = field(default_factory=set)
    complete: bool = True
    problems: list[str] = field(default_factory=list)

    @property
    def preferences(self) -> dict[str, dict[str, Preference]]:
        """The preferences each skill declares, by skill and by name."""
        return {name: skill.preferences for name, skill in self.skills.items()}

    def is_gone(self, skill: str) -> bool:
        """Whether a skill is in no skills folder, so its saved answers can go. Never while a
        folder couldn't be listed, or for a skill whose file couldn't be read."""
        return (
            self.complete
            and find_skill(self.skills, skill) is None
            and skill.lower() not in self.unread
        )


def read_skill_file(folder: Path, *, own: bool) -> tuple[Skill | None, list[str]]:
    """What the dev-home-skill.json in a skill's folder declares (see Skill), and a problem for
    each part of it that can't be used, which counts as left out. None, with its problem, when the
    file can't be read as a JSON object, or its preferences aren't one, so what it declares isn't
    known. A field it doesn't know is a problem too, though it changes nothing: it may be
    misspelled, or come from a newer dev-home-toolkit. A problem said twice, such as one field
    misspelled in two places, is listed once."""
    path = folder / SKILL_SETTINGS
    if not path.is_file():
        return Skill(folder.name, own), []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        return None, [f"{path} could not be read as JSON, so it was skipped. {error}"]
    if not isinstance(data, dict):
        return None, [f"{path} isn't a JSON object, so it was skipped."]
    declared = data.get("preferences", {})
    if not isinstance(declared, dict):
        return None, [f"{path}: preferences isn't a JSON object, so it was skipped."]
    problems = [
        f"{path}: {unknown_field(key, SKILL_FIELDS)}" for key in data if key not in SKILL_FIELDS
    ]
    recommended = data.get("recommended", True)
    if not isinstance(recommended, bool):
        problems.append(f"{path}: recommended isn't true or false, so it counts as true.")
        recommended = True
    always = data.get("alwaysAddedToAgents", False)
    if not isinstance(always, bool):
        problems.append(f"{path}: alwaysAddedToAgents isn't true or false, so it counts as false.")
        always = False
    elif always and own:
        problems.append(
            f"{path}: alwaysAddedToAgents is only for dev-home-toolkit's own skills, so it counts "
            "as false."
        )
        always = False
    requires: tuple[Requirement, ...] = ()
    for listed in LISTS:
        if listed in data:
            found, mistakes = parse_list(data[listed], listed)
            requires += found
            problems += [f"{path}: {mistake}" for mistake in mistakes]
    former_names = data.get("formerNames", [])
    if not isinstance(former_names, list) or not all(
        isinstance(name, str) and name.strip() for name in former_names
    ):
        problems.append(f"{path}: formerNames isn't a list of names, so it was left out.")
        former_names = []
    preferences: dict[str, Preference] = {}
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
            problems.append(
                f"{path}: the preference {key} needs a name with no dots, a default of true or "
                "false, a label, and formerNames, if any, as a list of names, so it was skipped."
            )
            continue
        problems += [
            f"{path}: {unknown_field(name, PREFERENCE_FIELDS)}"
            for name in entry
            if name not in PREFERENCE_FIELDS
        ]
        preferences[key] = Preference(
            folder.name,
            key,
            entry["default"],
            entry["label"],
            entry.get("help", ""),
            tuple(former or ()),
        )
    skill = Skill(folder.name, own, recommended, always, requires, preferences, tuple(former_names))
    return skill, list(dict.fromkeys(problems))


def normalized(text: str) -> str:
    """Text after Unicode's NFKC normalizing, as skills-ref compares names. It never changes ASCII
    text, so the module that does it, which takes a millisecond or two to load, is loaded only
    for text with other characters."""
    if text.isascii():
        return text
    import unicodedata

    return unicodedata.normalize("NFKC", text)


def standard_faults(name: str) -> list[str]:
    """What the Agent Skills standard's rule for a name asks that a name doesn't do, each said as
    advice, as its reference validator, skills-ref, checks it: after Unicode's NFKC normalizing,
    lowercase letters from any alphabet, digits, and hyphens; no hyphen at the start or the end,
    and no two in a row; and at most NAME_LIMIT characters."""
    normal = normalized(name)
    faults: list[str] = []
    if normal != normal.lower() or not all(c.isalnum() or c == "-" for c in normal):
        faults.append("use lowercase letters, digits, and hyphens")
    if normal.startswith("-") or normal.endswith("-") or "--" in normal:
        faults.append("start and end it with a letter or a digit, with no two hyphens in a row")
    if len(normal) > NAME_LIMIT:
        faults.append(f"use at most {NAME_LIMIT} characters")
    return faults


def reserved_words(name: str) -> list[str]:
    """The words claude.ai and Anthropic's API keep out of a skill's name that a name has in it,
    in any case."""
    folded = name.casefold()
    return [word for word in RESERVED_WORDS if word in folded]


def suggested_name(name: str) -> str:
    """A name close to one that breaks the rule, that the rule allows, such as "my-notes" for
    "My_Notes", or "" when there's none to suggest, such as for one with a reserved word."""
    lowered = normalized(name).lower()
    hyphened = re.sub(r"-{2,}", "-", re.sub(r"[\W_]", "-", lowered)).strip("-")
    suggestion = hyphened[:NAME_LIMIT].rstrip("-")
    if not suggestion or standard_faults(suggestion) or reserved_words(suggestion):
        return ""
    return suggestion


def frontmatter_name(text: str) -> str | None:
    """The first name: line's value in a SKILL.md's frontmatter, without quotes or a comment, or
    None when there's no frontmatter, it has no closing --- line, or it has no name: line."""
    lines = text.replace("\r\n", "\n").split("\n")
    if lines[0].strip() != "---":
        return None
    found: str | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            return found
        match = re.match(r"name:(.*)$", line)
        if match and found is None:
            value = match.group(1).strip()
            quoted = re.match(r"([\"'])(.*?)\1(\s+#.*)?$", value)
            found = quoted.group(2) if quoted else re.sub(r"\s+#.*$", "", value)
    return None


def name_problem(folder: Path) -> str:
    """The PROBLEM line for a skill whose name breaks the rule for names, or "" for one that
    follows it: the Agent Skills standard's rule (see standard_faults), with no word claude.ai
    and Anthropic's API keep out, not a name Claude Code keeps, and a name: line in its SKILL.md
    that matches its folder. Setup checks the end user's own skills, and a test
    dev-home-toolkit's. The design is in docs/development/decisions/, in decision 0072, "Fields in
    skill and rule files"."""
    name = folder.name
    dotted = "." in name
    fix = "Rename its folder and the name: line in its SKILL.md"
    if not dotted:
        # A setting's name is its path, with dots between its parts, so a dotted one has none.
        fix += (
            f', and add "{name}" to formerNames in its dev-home-skill.json so your answers move '
            "with it"
        )
    if name.casefold() == CLAUDE_DOWNLOADS_FOLDER:
        kept_off = f"The skill {name} {KEPT_OFF_FOR_NAME}, so setup doesn't add it to your agents."
        return f"{kept_off} {fix}."
    said: list[str] = []
    faults = standard_faults(name)
    if faults:
        suggestion = suggested_name(name)
        such_as = f', such as "{suggestion}"' if suggestion else ""
        said.append(
            f"The skill {name} has a name the Agent Skills standard doesn't allow: "
            f"{'; '.join(faults)}{such_as}."
        )
    words = reserved_words(name)
    if words:
        quoted = " and ".join(f'"{word}"' for word in words)
        whose = "Its name also has" if said else f"The skill {name} has"
        skips = (
            ", and Claude Code skips a skill with this name"
            if name.casefold() == CLAUDE_DOWNLOADS_NAME
            else ""
        )
        said.append(
            f"{whose} {quoted} in it, which claude.ai and Anthropic's API don't allow in a "
            f"skill's name{skips}."
        )
    if said:
        if dotted:
            said.append(
                "Until it's renamed, setup can't save whether to add it to your agents, so it "
                "follows its default."
            )
        return f"{' '.join(said)} {fix}."
    try:
        text = (folder / "SKILL.md").read_bytes().decode("utf-8-sig", errors="replace")
    except OSError:
        return ""
    written = frontmatter_name(text)
    if written is not None and normalized(written) == normalized(name):
        return ""
    needs = "but the Agent Skills standard needs one that matches the skill's folder"
    if written is None:
        return (
            f"The skill {name}'s SKILL.md has no name: line in its frontmatter, {needs}. Add "
            f'"name: {name}" to the frontmatter at the top of the file, between two --- lines.'
        )
    if not written:
        return (
            f"The skill {name}'s SKILL.md has an empty name: line, {needs}. Change it to "
            f'"name: {name}".'
        )
    return (
        f'The skill {name}\'s SKILL.md says "name: {written}", but the Agent Skills standard needs '
        f'its name: line to match the skill\'s folder. Change it to "name: {name}", or rename the '
        f'folder to match and add "{name}" to formerNames in its dev-home-skill.json so your '
        "answers move with it."
    )


def skill_declarations(content_dir: str) -> SkillDeclarations:
    """Every skill and what it declares: dev-home-toolkit's skills, then the person's own in
    dev-home, where one with the same name as a dev-home-toolkit skill isn't added, so its file is
    skipped (see SkillDeclarations). Each of the person's own whose name breaks the rule for names
    is a problem, and one with a name Claude Code keeps is never added (see name_problem). The
    list is complete only when dev-home's folder is a git repo, so a PC whose dev-home isn't
    cloned yet, even into a folder already made for it, or is on a drive that's unplugged, loses
    no answers."""
    found = SkillDeclarations()
    folders = [(TOOLKIT_ROOT / "templates" / "skills", False)]
    if content_dir and (Path(content_dir) / ".git").exists():
        folders.append((Path(content_dir) / "skills", True))
    else:
        found.complete = False
    for folder, own in folders:
        try:
            skills = sorted(f for f in folder.iterdir() if (f / "SKILL.md").is_file())
        except FileNotFoundError:
            # A dev-home with no skills of its own yet.
            continue
        except OSError:
            found.complete = False
            continue
        for skill in skills:
            if find_skill(found.skills, skill.name) is not None:
                continue
            declared, problems = read_skill_file(skill, own=own)
            found.problems += problems
            if own:
                named = name_problem(skill)
                if named:
                    found.problems.append(named)
                if declared is not None and skill.name.casefold() == CLAUDE_DOWNLOADS_FOLDER:
                    declared = replace(declared, kept_off=KEPT_OFF_FOR_NAME)
            if declared is None:
                found.unread.add(skill.name.lower())
            else:
                found.skills[skill.name] = declared
    return found


def find_skill(skills: Mapping[str, object], skill: str) -> str | None:
    """The name a skill is listed under, matched without case, as Windows matches its folder."""
    return next((name for name in skills if name.lower() == skill.lower()), None)


def unanswered_only(entry: object) -> bool:
    """Whether a skill's saved entry holds nothing but marks that nothing is answered yet, such as
    the one setup writes for a skill new to this PC: no answer of the end user's."""
    return (
        isinstance(entry, dict)
        and bool(entry)
        and all(value == {STATE: "unanswered"} for value in entry.values())
    )


def saved_skill_path(data: dict[str, Any], skill: str, rest: str) -> str:
    """Where a skill's setting is in this PC's settings, such as skills.handoff.addedToAgents,
    with the skill's name as the file has it, matched without case, or as given when the file
    has no entry for it."""
    saved = data.get("skills")
    if not isinstance(saved, dict) or skill in saved:
        return f"skills.{skill}.{rest}"
    return f"skills.{find_skill(saved, skill) or skill}.{rest}"


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
    data: dict[str, Any],
    declared: SkillDeclarations,
    *,
    remove_gone_skills: bool,
    seen: dict[str, Any] | None = None,
) -> Checked:
    """Checks this PC's settings against the declarations: an answer saved under a setting's
    former name moves to its name, a setting nothing declares is removed, and a value of the wrong
    kind is a problem, saying what it counts as instead. A skill whose file can't be read keeps
    its answers. So does a skill that's gone, unless remove_gone_skills: only a run that holds the
    sync's lock passes it, since a sync or an update may be replacing a skill's files at that
    moment, and the skill would only look gone. With seen, the file as a run first read it, only
    what that held is removed: another run saved the rest since, and it may know a declaration
    that this run, which read its own earlier, doesn't, such as one an update brought. The
    settings passed in aren't changed."""
    preferences = declared.preferences
    checked = Checked(copy.deepcopy(data))
    data = checked.data
    problems = checked.problems
    file = SETTINGS_PATH.name

    def remove(container: dict[str, Any], key: str, path: str, keys: KeyPath) -> None:
        if seen is not None and value_at(seen, keys) is MISSING:
            return
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
            agent = FOLDERS_FOR.get(path)
            if setting is not None:
                check_value(path, inner, setting)
            elif agent is not None:
                check_folders(path, inner, agent)
            else:
                remove(value, name, path, (key, name))

    def check_folders(path: str, value: object, agent: Agent) -> None:
        """An agent's folders, each with an entry, which holds its answer, setUp: yes, no, or a
        reminder."""
        unset = "not answered yet"
        if not isinstance(value, dict):
            wrong(path, value, f"a JSON object of {agent.folder}s", "none")
            return
        for folder, entry in value.items():
            where = f"{path} {folder}"
            if not isinstance(entry, dict):
                wrong(where, entry, "a JSON object", unset)
                continue
            for entry_key, answer in list(entry.items()):
                if entry_key != "setUp":
                    keys = (*path.split("."), folder, entry_key)
                    remove(entry, entry_key, f"{where}: {entry_key}", keys)
                elif not isinstance(answer, bool) and read_reminder(answer) is None:
                    wanted = 'true, false, or a reminder, {"$state": "remind", "on": "YYYY-MM-DD"}'
                    wrong(f"{where}: setUp", answer, wanted, unset)

    def move_renamed_skills(value: dict[str, Any]) -> None:
        """Moves a skill's answers to its name as its folder spells it now: from the same name in
        another case, such as after a folder renamed from Tidy to tidy, so every reader finds them
        under one name; or from a name it had before, in its formerNames, unless it has answers
        under its name already, or a skill still has the old name. The mark that nothing is
        answered yet, which setup writes for a skill new to this PC, holds no answer, so the old
        answers replace it, such as when the old and the new folder were both there for a while."""
        for name, skill in declared.skills.items():
            if name in value and not unanswered_only(value[name]):
                continue
            other_case = next(
                (key for key in value if key != name and key.lower() == name.lower()), None
            )
            if other_case is not None:
                value[name] = value.pop(other_case)
                checked.moved.append(f"skills.{other_case} to skills.{name}")
                continue
            former = {old.lower() for old in skill.former_names}
            old = next(
                (
                    key
                    for key in value
                    if key.lower() in former
                    and find_skill(declared.skills, key) is None
                    and key.lower() not in declared.unread
                ),
                None,
            )
            if old is not None:
                value[name] = value.pop(old)
                checked.moved.append(f"skills.{old} to skills.{name}")

    def check_skills(value: dict[str, Any]) -> None:
        move_renamed_skills(value)
        for skill, inner in list(value.items()):
            name = find_skill(preferences, skill)
            if name is None:
                if remove_gone_skills and declared.is_gone(skill):
                    remove(value, skill, f"skills.{skill}", ("skills", skill))
                continue
            if not isinstance(inner, dict):
                wrong(f"skills.{skill}", inner, "a JSON object", "the defaults")
                continue
            for group, saved in list(inner.items()):
                where = f"skills.{skill}.{group}"
                added = declared.skills[name].added_setting
                if group == ADDED_TO_AGENTS and added is not None:
                    check_value(where, saved, added)
                elif group != "preferences":
                    remove(inner, group, where, ("skills", skill, group))
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
                            keys = ("skills", skill, "preferences", key)
                            remove(saved, key, f"{where}.{key}", keys)
                        else:
                            check_value(f"{where}.{key}", answer, known.setting)

    groups = {path.split(".")[0] for path in (*BY_PATH, *FOLDER_SETTINGS)}
    for key, value in list(data.items()):
        if key == "schemaVersion":
            continue
        if key == "testHomeDir":
            if not isinstance(value, str):
                wrong(key, value, "a folder", "not set")
        elif key in groups | {"skills"}:
            if not isinstance(value, dict):
                wrong(key, value, "a JSON object of settings", "none set")
            elif key == "skills":
                check_skills(value)
            else:
                check_group(key, value)
            # A group left empty goes too, or the save would write it back.
            if isinstance(value, dict) and not value:
                del data[key]
        else:
            remove(data, key, key, (key,))
    return checked


@dataclass
class LocalSettings:
    """The settings setup asks for, with defaults for anything missing. folders holds, for each
    agent, each folder answered yes or no, as written, so setup asks about it only once; a folder
    whose answer is a reminder has it in data instead (see folder_reminders). data holds
    everything the file had, so a save keeps the keys setup doesn't know, and each setting in the
    form it was saved in: setting_value reads one, such as whether automatic updates are answered
    yet. found says the file had settings in it. test_home_dir is only ever in a test sandbox's
    file, which the tests write; setup never adds it."""

    content_dir: str = ""
    folders: dict[str, dict[str, bool]] = field(
        default_factory=lambda: {path: {} for path in FOLDER_SETTINGS}
    )
    test_home_dir: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    found: bool = False

    @property
    def home(self) -> Path:
        """The profile folder setup sets up: yours, unless testHomeDir names another."""
        return Path(comparable(self.test_home_dir)) if self.test_home_dir else Path.home()


def answered(folders: dict[str, bool], answer: bool) -> list[str]:
    """The folders with that answer, as written."""
    return [folder for folder, setup in folders.items() if setup is answer]


def load_local_settings() -> LocalSettings | None:
    """The settings, or None when the file is there but can't be read as a JSON object. A file
    in another layout loads too, so the caller checks layout() first."""
    if not SETTINGS_PATH.exists():
        return LocalSettings()
    try:
        text = SETTINGS_PATH.read_text(encoding="utf-8-sig")
        # An empty file holds no answers yet, so it counts as no file.
        if not text.strip():
            return LocalSettings()
        data = json.loads(text)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return settings_in(data)


def settings_in(data: dict[str, Any]) -> LocalSettings:
    """The settings a file's data holds, as load_local_settings reads them, keeping data itself."""
    settings = LocalSettings(data=data, found=True)
    folder = get(data, "devHome.folder")
    if isinstance(folder, str):
        settings.content_dir = folder
    settings.folders = {path: folder_answers(get(data, path)) for path in FOLDER_SETTINGS}
    if isinstance(data.get("testHomeDir"), str):
        settings.test_home_dir = data["testHomeDir"]
    return settings


def merge_answers(data: dict[str, Any], path: str, answers: dict[str, bool]) -> None:
    """Writes an agent's folder answers into data, keeping each entry's other keys. A folder whose
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
    file had where it was, apart from a shared agent's folders, which go in order (see
    order_folders). testHomeDir is kept when the file has it, and never added."""
    data = copy.deepcopy(settings.data)
    data.pop("schemaVersion", None)
    if settings.content_dir:
        put(data, "devHome.folder", settings.content_dir)
    for path in FOLDER_SETTINGS:
        merge_answers(data, path, settings.folders[path])
    order_folders(data, settings.home)
    if settings.test_home_dir:
        data["testHomeDir"] = settings.test_home_dir
    return {"schemaVersion": SCHEMA_VERSION, **data}


def settings_text(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def same_apart_from_order(old_text: str, new_text: str) -> bool:
    """Whether two settings files hold the same keys and values, whatever their order, counting
    a key written twice, which reading the file would drop, as a difference."""

    def unordered(pairs: list[tuple[str, Any]]) -> list[tuple[str, str]]:
        return sorted((key, json.dumps(value, sort_keys=True)) for key, value in pairs)

    try:
        old = json.loads(old_text, object_pairs_hook=unordered)
        new = json.loads(new_text, object_pairs_hook=unordered)
    except ValueError:
        return False
    return bool(old == new)


def local_settings_text(settings: LocalSettings) -> str:
    """The file's text for the settings (see local_settings_data)."""
    return settings_text(local_settings_data(settings))


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


def written_alike(first: object, second: object) -> bool:
    """Whether two values are written the same in a settings file, whatever the order of their
    keys. true and 1 differ, though Python counts them as equal."""
    return json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


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
        if path in old and written_alike(old[path], value):
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
