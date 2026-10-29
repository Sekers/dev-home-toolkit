"""The settings dev-home-toolkit recommends for the agents, which setup offers in each folder set
up, from templates/recommended-settings/recommended-settings.json (decision 0032, "Recommended
settings").

Each entry, by an id that's never reused, has a summary, one line saying what it does, and, for
each agent that has such a setting, that agent's block, by the agent's group in
local-settings.json, such as claudeCode. A block names the key, at the top of the agent's settings
file, and the recommended value, with the older forms of it that the recommended value replaces,
and the file older versions of the agent kept it in, if any. Its texts say what the setting means
for the person with the recommended value, without the setting, with an older form, and with each
other value the agent's docs explain, and what the setting needs to work, for the offer, which
shows the value the file has and what it means. It can also name the kind of value a person
writes for themselves, a custom value. Any other value is unknown, with no text: setup can't know
what it means, or whether the agent accepts it."""

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
ENTRY_FIELDS = ("summary",)
# Each agent that can have a recommended setting, by its group in local-settings.json.
AGENT_GROUPS = ("claudeCode",)
AGENT_FIELDS = (
    "key",
    "value",
    "olderForms",
    "olderPlace",
    "whenRecommended",
    "whenMissing",
    "whenOlderForm",
    "otherValues",
    "customValues",
    "needs",
)
# The kinds of value a person can write for themselves in a setting, which an offer calls a
# custom value (see CustomValues).
CUSTOM_KINDS = ("number", "string", "object", "array")
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
class KnownValue:
    """Another value a setting takes, besides the recommended one and its older forms, whose
    meaning the agent's docs give, with the text saying what it means for the person."""

    value: Any
    when: str


@dataclass(frozen=True)
class CustomValues:
    """The kind of value a person writes for themselves in a setting, such as a number or an
    object, which an offer calls a custom value: for a number, only from minimum to maximum, each
    when given; with the text saying what any such value means, where the agent's docs give it, or
    "" where they don't."""

    kind: str
    minimum: float | None = None
    maximum: float | None = None
    when: str = ""


@dataclass(frozen=True)
class AgentSetting:
    """One agent's form of a recommended setting: the key at the top of its settings file, the
    recommended value, the older forms it replaces, the file older versions kept it in ("" for
    none), and the texts for the offer: what the setting means for the person with the recommended
    value, without it, and with an older form ("" with none); the other values whose meaning is
    known; the kind of value that's a person's own, if any; and what it needs to work ("" when
    nothing). Any other value is unknown, with no text: setup can't know what it means, or whether
    the agent accepts it."""

    key: str
    value: Any
    older_forms: tuple[Any, ...] = ()
    older_place: str = ""
    when_recommended: str = ""
    when_missing: str = ""
    when_older_form: str = ""
    other_values: tuple[KnownValue, ...] = ()
    custom_values: CustomValues | None = None
    needs: str = ""


@dataclass(frozen=True)
class RecommendedSetting:
    """An entry in the list: its id, summary, and each agent's form, by the agent's group."""

    id: str
    summary: str
    agents: dict[str, AgentSetting]


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


def json_kind(value: Any) -> str:
    """A JSON value's kind: boolean, number, string, object, array, or null."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int | float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    return "array" if isinstance(value, list) else "null"


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
    if any(form is None or json_equal(form, value) for form in older):
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
        when_recommended=text_field(where, block, "whenRecommended", required=True),
        when_missing=text_field(where, block, "whenMissing", required=True),
        when_older_form=when_older,
        other_values=read_other_values(where, block, [value, *older]),
        custom_values=read_custom_values(where, block),
        needs=text_field(where, block, "needs", required=False),
    )


def read_other_values(
    where: str, block: dict[str, Any], taken: list[Any]
) -> tuple[KnownValue, ...]:
    """otherValues: a list of one or more, each a value and the text saying what it means, none of
    them the recommended value, an older form, or a value already listed."""
    if "otherValues" not in block:
        return ()
    items = block["otherValues"]
    if not isinstance(items, list) or not items:
        raise ValueError(f"{where}: otherValues isn't a list of one or more values.")
    known: list[KnownValue] = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"value", "when"}:
            raise ValueError(
                f"{where}: each of otherValues has a value and a when, and nothing else."
            )
        if any(json_equal(item["value"], other) for other in [*taken, *(k.value for k in known)]):
            raise ValueError(
                f"{where}: otherValues holds the recommended value, an older form, or a value "
                "twice."
            )
        known.append(
            KnownValue(
                item["value"], text_field(f"{where}: otherValues", item, "when", required=True)
            )
        )
    return tuple(known)


def read_custom_values(where: str, block: dict[str, Any]) -> CustomValues | None:
    """customValues: the kind, one of CUSTOM_KINDS; for a number, a min and a max, each optional;
    and the text saying what any such value means, optional."""
    if "customValues" not in block:
        return None
    found = block["customValues"]
    if not isinstance(found, dict) or set(found) - {"kind", "min", "max", "when"}:
        raise ValueError(f"{where}: customValues isn't a JSON object of kind, min, max, and when.")
    kind = found.get("kind")
    if kind not in CUSTOM_KINDS:
        raise ValueError(f"{where}: customValues' kind isn't one of {', '.join(CUSTOM_KINDS)}.")
    bounds = {name: found[name] for name in ("min", "max") if name in found}
    if bounds and kind != "number":
        raise ValueError(f"{where}: customValues has a min or a max, but its kind isn't number.")
    if any(json_kind(bound) != "number" for bound in bounds.values()):
        raise ValueError(f"{where}: customValues' min or max isn't a number.")
    if len(bounds) == 2 and bounds["min"] > bounds["max"]:
        raise ValueError(f"{where}: customValues' min is more than its max.")
    when = text_field(f"{where}: customValues", found, "when", required=False)
    return CustomValues(kind, bounds.get("min"), bounds.get("max"), when)


def not_json(word: str) -> Any:
    """Refuses NaN and Infinity, which Python's reader takes but JSON doesn't have."""
    raise ValueError(f"The list holds {word}, which isn't JSON.")


def load_recommended(path: Path = CATALOG_PATH) -> tuple[RecommendedSetting, ...]:
    """The recommended settings, as the list declares them. It comes with the code, so one setup
    can't use is a bug, which stops the run; a test reads it."""
    data = json.loads(path.read_text(encoding="utf-8"), parse_constant=not_json)
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
        found.append(RecommendedSetting(name, summary, agents))
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
# an older form of it, or any other value, known, custom, or unknown (see other_meaning).
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


def other_meaning(setting: AgentSetting, value: Any) -> tuple[str, tuple[str, ...]]:
    """What an offer says about a value that's neither the recommended one nor an older form, as a
    note after the value and the text under it: for a value the list knows, no note, and what it
    means; for one of the kind a person writes for themselves (see CustomValues), "a custom
    value", and what such a value means, where the list says; and for any other, "an unknown
    value", and nothing more, since setup can't know what it means, or whether the agent accepts
    it."""
    for known in setting.other_values:
        if json_equal(value, known.value):
            return "", (known.when,)
    custom = setting.custom_values
    if custom is not None and json_kind(value) == custom.kind:
        low, high = custom.minimum, custom.maximum
        if custom.kind != "number" or (
            (low is None or value >= low) and (high is None or value <= high)
        ):
            return ", a custom value", (custom.when,) if custom.when else ()
    return ", an unknown value", ()


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
    and what it means, where setup knows (see other_meaning); and the recommended value, with
    what it means for the person, then what it needs to work, if anything. Where the folder has the
    recommended value already, the value says so, with no recommendation after it."""
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
    else:
        note, meaning = other_meaning(setting, current.value)
        if current.place != file:
            meaning = (f"In {current.place}, which counts while {file} sets none.", *meaning)
        rows.append(("Now:", f"{value}{note}", meaning))
    needs = (setting.needs,) if setting.needs else ()
    rows.append(("Recommended:", shown(setting.value), (setting.when_recommended, *needs)))
    return rows
