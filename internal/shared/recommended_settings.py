"""The settings dev-home-toolkit recommends for the agents, which setup offers in each folder set
up, from templates/recommended-settings/recommended-settings.json (decision 0032, "Recommended
settings").

Each entry, by an id that's never reused, has a summary, one line saying what it does; why, the
reason it's recommended; and, for each agent that has such a setting, that agent's block, by the
agent's group in local-settings.json, such as claudeCode. A block names the key, at the top of the
agent's settings file, and the recommended value, with the older forms of it that the recommended
value replaces, and the file older versions of the agent kept it in, if any. Its texts say what the
agent does without the setting, with an older form, and with any other value, which someone chose,
and what the setting needs to work, for the offer, which shows the value the file has and what it
means."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CATALOG_PATH = (
    Path(__file__).parent.parent.parent
    / "templates"
    / "recommended-settings"
    / "recommended-settings.json"
)
ENTRY_FIELDS = ("summary", "why")
# Each agent that can have a recommended setting, by its group in local-settings.json.
AGENT_GROUPS = ("claudeCode",)
AGENT_FIELDS = (
    "key",
    "value",
    "olderForms",
    "olderPlace",
    "whenMissing",
    "whenOlderForm",
    "whenOther",
    "needs",
)
# The files an agent's older versions kept a setting in, which it still reads where its settings
# files have none: for Claude Code, .claude.json (~/.claude.json for ~/.claude, and the one inside
# any other folder).
OLDER_PLACES = (".claude.json",)
# An id, as the Agent Skills standard writes a name: lowercase letters, digits, and hyphens, with no
# hyphen at either end, and none twice in a row.
ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
# A summary's longest length, as a built-in skill's (decision 0072).
SUMMARY_LIMIT = 80


@dataclass(frozen=True)
class AgentSetting:
    """One agent's form of a recommended setting: the key at the top of its settings file, the
    recommended value, the older forms it replaces, the file older versions kept it in ("" for
    none), and the texts for the offer: what the agent does without it, with an older form ("" with
    none), and with any other value, and what it needs to work ("" when nothing)."""

    key: str
    value: Any
    older_forms: tuple[Any, ...] = ()
    older_place: str = ""
    when_missing: str = ""
    when_older_form: str = ""
    when_other: str = ""
    needs: str = ""


@dataclass(frozen=True)
class RecommendedSetting:
    """An entry in the list: its id, summary, why, and each agent's form, by the agent's group."""

    id: str
    summary: str
    why: str
    agents: dict[str, AgentSetting]


def text_field(where: str, entry: dict[str, Any], name: str, *, required: bool) -> str:
    """A field holding one line of plain text, or "" when it's optional and left out."""
    if name not in entry:
        if required:
            raise ValueError(f"{where} has no {name}.")
        return ""
    value = entry[name]
    if not isinstance(value, str) or not value.strip() or "\n" in value:
        raise ValueError(f"{where}: {name} isn't one line of text.")
    return value


def read_agent_setting(where: str, block: object) -> AgentSetting:
    if not isinstance(block, dict):
        raise ValueError(f"{where} isn't a JSON object.")
    unknown = [name for name in block if name not in AGENT_FIELDS]
    if unknown:
        raise ValueError(f"{where} has fields setup doesn't know: {', '.join(unknown)}.")
    key = block.get("key")
    if not isinstance(key, str) or not key or "." in key:
        raise ValueError(f"{where}: key isn't a key at the top of the settings file.")
    if "value" not in block or block["value"] is None:
        raise ValueError(f"{where} has no value.")
    value = block["value"]
    older = block.get("olderForms", [])
    if not isinstance(older, list) or ("olderForms" in block and not older):
        raise ValueError(f"{where}: olderForms isn't a list of one or more values.")
    if any(form is None or form == value for form in older):
        raise ValueError(f"{where}: olderForms holds null, or the recommended value.")
    place = block.get("olderPlace", "")
    if place not in ("", *OLDER_PLACES):
        raise ValueError(f"{where}: olderPlace isn't one of {', '.join(OLDER_PLACES)}.")
    when_older = text_field(where, block, "whenOlderForm", required=bool(older))
    if when_older and not older:
        raise ValueError(f"{where} has whenOlderForm, but no olderForms.")
    return AgentSetting(
        key,
        value,
        tuple(older),
        place,
        text_field(where, block, "whenMissing", required=True),
        when_older,
        text_field(where, block, "whenOther", required=True),
        text_field(where, block, "needs", required=False),
    )


def load_recommended(path: Path = CATALOG_PATH) -> tuple[RecommendedSetting, ...]:
    """The recommended settings, as the list declares them. It comes with the code, so one setup
    can't use is a bug, which stops the run; a test reads it."""
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("recommendedSettings") if isinstance(data, dict) else None
    if not isinstance(entries, dict) or set(data) != {"recommendedSettings"}:
        raise ValueError(f"{path.name} isn't a JSON object of recommendedSettings alone.")
    found: list[RecommendedSetting] = []
    keys: dict[tuple[str, str], str] = {}
    for name, entry in entries.items():
        where = f"{path.name}: {name}"
        if not ID.fullmatch(name):
            raise ValueError(f"{where}: the id isn't lowercase words joined by hyphens.")
        if not isinstance(entry, dict):
            raise ValueError(f"{where} isn't a JSON object.")
        unknown = [field for field in entry if field not in (*ENTRY_FIELDS, *AGENT_GROUPS)]
        if unknown:
            raise ValueError(f"{where} has fields setup doesn't know: {', '.join(unknown)}.")
        summary = text_field(where, entry, "summary", required=True)
        if len(summary) > SUMMARY_LIMIT:
            raise ValueError(f"{where}: summary is longer than {SUMMARY_LIMIT} characters.")
        # A list at a console names its items by their summaries.
        same = next((other.id for other in found if other.summary == summary), None)
        if same is not None:
            raise ValueError(f"{where}: {same} has the same summary.")
        agents = {
            group: read_agent_setting(f"{where}.{group}", entry[group])
            for group in AGENT_GROUPS
            if group in entry
        }
        if not agents:
            raise ValueError(f"{where} has no agent's setting.")
        for group, setting in agents.items():
            other = keys.setdefault((group, setting.key), name)
            if other != name:
                raise ValueError(f"{where}: {other} has the same {group} key, {setting.key}.")
        found.append(
            RecommendedSetting(
                name, summary, text_field(where, entry, "why", required=True), agents
            )
        )
    return tuple(found)


RECOMMENDED = load_recommended()


def keys_for(group: str) -> list[str]:
    """The keys of every recommended setting an agent has, by the agent's group, in the list's
    order."""
    return [entry.agents[group].key for entry in RECOMMENDED if group in entry.agents]


def for_agent(group: str) -> list[RecommendedSetting]:
    """Every recommended setting an agent has, by the agent's group, in the list's order."""
    return [entry for entry in RECOMMENDED if group in entry.agents]


def ids_for(group: str) -> list[str]:
    """The id of every recommended setting an agent has, by the agent's group."""
    return [entry.id for entry in for_agent(group)]


def json_equal(first: Any, second: Any) -> bool:
    """Whether two JSON values mean the same to an agent that reads them as JavaScript does: true
    and 1 differ, while 0 and 0.0 are the same number."""
    if isinstance(first, bool) or isinstance(second, bool):
        return isinstance(first, bool) and isinstance(second, bool) and first == second
    if isinstance(first, int | float) and isinstance(second, int | float):
        return bool(first == second)
    if isinstance(first, dict) and isinstance(second, dict):
        return first.keys() == second.keys() and all(
            json_equal(first[key], second[key]) for key in first
        )
    if isinstance(first, list) and isinstance(second, list):
        return len(first) == len(second) and all(
            json_equal(a, b) for a, b in zip(first, second, strict=True)
        )
    return type(first) is type(second) and bool(first == second)


@dataclass(frozen=True)
class Current:
    """A recommended setting as one of an agent's folders has it now: place, the file its value
    comes from, "settings.json" or the setting's older place, or "" when neither has one; and
    value, the value there."""

    place: str = ""
    value: Any = None

    @property
    def described(self) -> str:
        """The value an offer describes, as the work compares it: where it comes from, and its
        JSON, or "" for none."""
        if not self.place:
            return ""
        return f"{self.place}:{json.dumps(self.value, sort_keys=True, ensure_ascii=False)}"


# What a folder's value is, for a recommended setting: the recommended value already, missing,
# an older form of it, or another value, which someone chose.
DONE = "done"
MISSING = "missing"
OLDER = "older"
OTHER = "other"


def state_of(setting: AgentSetting, current: Current) -> str:
    """What a folder's value is, for a recommended setting (see DONE and the rest)."""
    if not current.place:
        return MISSING
    if json_equal(current.value, setting.value):
        return DONE
    if any(json_equal(current.value, form) for form in setting.older_forms):
        return OLDER
    return OTHER


def shown(value: Any) -> str:
    """A value as an offer shows it: its JSON, on one line."""
    return json.dumps(value, ensure_ascii=False)


# What an offer says about a recommended setting: rows, each a label, the value beside it, and
# paragraphs under the value.
OfferRows = list[tuple[str, str, tuple[str, ...]]]


def offer_text(entry: RecommendedSetting, group: str, current: Current, file: str) -> OfferRows:
    """What an offer says about one recommended setting in one of an agent's folders, by the
    agent's group, in plain words (decision 0032), as rows: the setting, by its key in file, the
    settings file a yes writes; the value the folder has now, with where when it's another file,
    and what it means; and the recommended value, with what it does and why, then what it needs to
    work, if anything. Where the folder has the recommended value already, the value says so, with
    no recommendation after it."""
    setting = entry.agents[group]
    state = state_of(setting, current)
    value = shown(current.value)
    rows: OfferRows = [("Setting:", f"{setting.key}, in {file}", ())]
    if state == DONE:
        where = "" if current.place == file else f", in {current.place}"
        return [*rows, ("Now:", f"{value}{where}, as recommended", ())]
    if state == MISSING:
        rows.append(("Now:", "not set", (setting.when_missing,)))
    elif state == OLDER:
        rows.append(("Now:", f"{value}, an older form", (setting.when_older_form,)))
    elif current.place == file:
        rows.append(("Now:", value, (setting.when_other,)))
    else:
        rows.append(
            (
                "Now:",
                f"{value}, in {current.place}, which counts while {file} sets none",
                (setting.when_other,),
            )
        )
    needs = (setting.needs,) if setting.needs else ()
    rows.append(("Recommended:", shown(setting.value), (entry.why, *needs)))
    return rows
