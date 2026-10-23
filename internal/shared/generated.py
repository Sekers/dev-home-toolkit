"""Filling in templates: the placeholders, and each skill's stamp. No generated file carries a
note saying not to edit it (decision 0064, "Each agent's rules file")."""

import hashlib
import os
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from .links import is_link

# Files whose placeholders setup fills in. Any other file is copied as it is.
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".toml", ".yml", ".yaml", ".ps1", ".py", ".sh"}

PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")


@dataclass(frozen=True)
class Rendered:
    """A file's bytes, filled in, with the placeholders left that setup doesn't know."""

    data: bytes
    unknown: list[str]


def read_text(path: Path) -> str:
    """A text file's text, with LF line breaks."""
    return path.read_bytes().decode("utf-8-sig", errors="replace").replace("\r\n", "\n")


def fill(text: str, values: Mapping[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def render(path: Path, values: Mapping[str, str]) -> Rendered:
    """A file's bytes, with the placeholders filled in for the file types in TEXT_EXTENSIONS,
    whose line breaks become LF."""
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return Rendered(path.read_bytes(), [])
    text = fill(read_text(path), values)
    unknown = [f"{path} ({match.group(0)})" for match in PLACEHOLDER.finditer(text)]
    return Rendered(text.encode("utf-8"), unknown)


def skill_stamp(path: Path, values: Mapping[str, str]) -> str:
    """A skill's stamp: the start of a SHA-256 of its SKILL.md with this PC's paths filled in, so
    it changes whenever the text an agent loads does. The skill's commands carry it, and the
    skill scripts compare it with the stamp in the SKILL.md on disk (see facts.py). The stamp is
    hashed as its placeholder, so it can't change its own value."""
    return hashlib.sha256(fill(read_text(path), values).encode("utf-8")).hexdigest()[:12]


def generated_items(
    folder: Path, *, directories: bool = False, with_cache: bool = False
) -> Iterator[Path]:
    """Every file under folder that setup may write or remove, or with directories every folder.
    It never looks inside a link, which may point anywhere, such as at a Python install. Without
    with_cache it also leaves out Python's bytecode cache folders (__pycache__), which Python
    writes beside the scripts when they run, so they aren't removed and rebuilt on every run."""
    with os.scandir(folder) as entries:
        found = sorted(entries, key=lambda entry: entry.name)
    for entry in found:
        if is_link(Path(entry.path)):
            continue
        if not entry.is_dir():
            if not directories:
                yield Path(entry.path)
            continue
        if entry.name == "__pycache__" and not with_cache:
            continue
        if directories:
            yield Path(entry.path)
        yield from generated_items(Path(entry.path), directories=directories, with_cache=with_cache)
