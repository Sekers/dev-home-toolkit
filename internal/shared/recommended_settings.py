"""The settings dev-home-toolkit recommends for the agents, which setup offers in each folder set
up, from templates/recommended-settings/recommended-settings.json (decision 0032, "Recommended
settings").

Each entry, by an id that's never reused, has a summary, one line saying what it does; why, the
reason it's recommended; and, for each agent that has such a setting, that agent's block, by the
agent's group in local-settings.json, such as claudeCode. A block names the key, at the top of the
agent's settings file, and the recommended value, with the older forms of it that the recommended
value replaces, and the file older versions of the agent kept it in, if any. Its texts say what the
agent does without the setting, what an older form does, and what the setting needs to work, for
the offer, which fits its words to what the file has."""

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
AGENT_FIELDS = ("key", "value", "olderForms", "olderPlace", "whenMissing", "whenOlderForm", "needs")
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
    none), and the texts for the offer: what the agent does without it, what an older form does
    ("" with none), and what it needs to work ("" when nothing)."""

    key: str
    value: Any
    older_forms: tuple[Any, ...] = ()
    older_place: str = ""
    when_missing: str = ""
    when_older_form: str = ""
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
