"""The layout lists against what the code writes (see layouts.py). Every run of the scripts in the
tests checks that what it adds to a file is on that file's list; these check the other way, that
everything on a list is something the code still writes, and that the check itself works."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

import layouts
from helpers import REPO_ROOT, LayoutCheck, Sandbox, layout_snapshot, run_python, sandbox_for


@pytest.fixture(scope="module")
def box(request: pytest.FixtureRequest) -> Iterator[Sandbox]:
    yield from sandbox_for(request, "layouts")


def seen(box: Sandbox, found: dict[tuple[str, object], set[str]]) -> None:
    """Adds the key paths now in the sandbox's files to found, by each file's name and the layout
    version it names, and the files in its dev-home's rules/, as rules' list writes them, under
    ("rules", 1)."""
    declared = layouts.declared_settings(box.toolkit)
    for path, data in layout_snapshot(box).items():
        relative = path.relative_to(box.root).parts
        if relative[1] == layouts.RULES_FOLDER:
            found.setdefault((layouts.RULES_FOLDER, 1), set()).add(layouts.rules_key(relative[2:]))
            continue
        part = layouts.part_named(path.name)
        value = layouts.read_data(data)
        assert value is not None, path
        paths = layouts.key_paths(value, part, declared)
        found.setdefault((part.file, value.get("schemaVersion")), set()).update(paths)


def test_each_list_holds_exactly_what_the_code_writes(box: Sandbox) -> None:
    # Each form a key can take, written by the code: a setting and a preference as a plain value
    # and as their default, a skill's answer, a reminder for a Claude Code folder and for Codex,
    # whose homes share one answer, so its answer goes first, and dev-home.json's own setting.
    found: dict[tuple[str, object], set[str]] = {}
    seen(box, found)
    second = box.profile / ".claude-second"
    second.mkdir()
    settings = box.toolkit / "local-settings.json"
    assignments = [
        "updates.checkEveryHours=6",
        "updates.installAutomatically=default",
        "skills.handoff.preferences.includeSecurityBugsInIssueOffers=false",
        "skills.handoff.preferences.includeSecurityBugsInIssueOffers=default",
        "skills.knowledge.addedToAgents=true",
        f"claudeCode.folders?={second.as_posix()}@3",
        "multiMachine=false",
    ]
    for assignment in assignments:
        result = run_python(box, "setup.py", "--configure", assignment)
        assert result.code == 0, f"{assignment}: {result}"
        seen(box, found)
    data = json.loads(settings.read_text(encoding="utf-8"))
    data.pop("codex")
    settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    codex = (box.profile / ".codex").as_posix()
    result = run_python(box, "setup.py", "--configure", f"codex.homes?={codex}@3")
    assert result.code == 0, str(result)
    seen(box, found)

    # Each file kept the layout the code writes now. A key path the code writes but the list
    # lacks fails the run that wrote it, in helpers.py, so only a key path it no longer writes can
    # be left.
    versions = {file: [v for f, v in found if f == file] for file, _ in found}
    assert all(len(seen_versions) == 1 for seen_versions in versions.values()), versions
    parts = {part.file for part in layouts.PARTS} | {layouts.RULES_FOLDER}
    assert {file for file, _ in found} == parts, found
    for (file, version), written in found.items():
        if file == layouts.RULES_FOLDER:
            list_path, listed = layouts.RULES_LIST, layouts.read_list(layouts.RULES_LIST)
        else:
            part = layouts.part_named(file)
            list_path = layouts.list_path(part, version)
            found_list = layouts.listed(part, version)
            assert found_list is not None, list_path
            listed = found_list
        unwritten = sorted(listed - written)
        assert not unwritten, (
            f"{list_path} has key paths no run in this test wrote: {', '.join(unwritten)}. If the "
            "code no longer writes them, take them off the list; otherwise make this test write "
            "them."
        )


BEFORE = {"schemaVersion": 1, "devHome": {"folder": "C:/dev-home"}}
LISTED = {**BEFORE, "claudeCode": {"folders": {"~/.claude": {"setUp": True}}}}
UNLISTED = {**BEFORE, "claudeCode": {"folders": {"~/.claude": {"setUp": True, "rules": True}}}}


@pytest.fixture
def settings(tmp_path: Path) -> Path:
    """A local-settings.json holding BEFORE, in a folder laid out as a sandbox's copy is."""
    shared = tmp_path / "toolkit" / "internal" / "shared"
    shared.mkdir(parents=True)
    definitions = REPO_ROOT / "internal" / "shared" / "setting-definitions.json"
    (shared / "setting-definitions.json").write_bytes(definitions.read_bytes())
    path = tmp_path / "toolkit" / "local-settings.json"
    write(path, BEFORE)
    return path


def write(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def failure(check: LayoutCheck) -> str:
    with pytest.raises(AssertionError) as failed:
        check.finish("a run")
    return str(failed.value)


def test_a_run_that_adds_only_listed_key_paths_passes(tmp_path: Path, settings: Path) -> None:
    check = LayoutCheck(Sandbox(tmp_path))
    write(settings, LISTED)
    check.finish("a run")


def test_a_run_that_adds_a_key_path_the_list_lacks_fails(tmp_path: Path, settings: Path) -> None:
    write(settings, LISTED)
    check = LayoutCheck(Sandbox(tmp_path))
    write(settings, UNLISTED)
    message = failure(check)
    # It names only the key path the run added, and the list to add it to.
    assert "list doesn't have: claudeCode.folders.<folder>.rules. " in message, message
    assert "local-settings-json-1.txt" in message, message


def test_what_the_test_writes_during_a_run_isnt_the_runs(tmp_path: Path, settings: Path) -> None:
    check = LayoutCheck(Sandbox(tmp_path))
    with check.test_writes():
        write(settings, UNLISTED)
    check.finish("a run")


def test_what_a_run_wrote_before_the_test_wrote_is_still_the_runs(
    tmp_path: Path, settings: Path
) -> None:
    check = LayoutCheck(Sandbox(tmp_path))
    write(settings, UNLISTED)
    with check.test_writes():
        write(settings, {**UNLISTED, "updates": {"checkEveryHours": 6}})
    assert "claudeCode.folders.<folder>.rules" in failure(check)


@pytest.mark.parametrize(
    ("version", "said"),
    [(7, "schemaVersion 7, which has no layout list"), ("1", 'schemaVersion "1", which isn\'t')],
)
def test_a_run_that_writes_a_layout_version_with_no_list_fails(
    tmp_path: Path, settings: Path, version: object, said: str
) -> None:
    # Even with no new key path.
    check = LayoutCheck(Sandbox(tmp_path))
    write(settings, {**BEFORE, "schemaVersion": version})
    assert said in failure(check)


def test_key_paths_name_made_up_names_and_declared_settings_by_placeholder() -> None:
    part = layouts.part_named("local-settings.json")
    data = {
        "schemaVersion": 1,
        "devHome": {"folder": "C:/dev-home"},
        "updates": {"installAutomatically": {"$state": "default"}},
        "claudeCode": {"folders": {"~/.claude-x": {"setUp": {"$state": "remind", "on": "x"}}}},
        "skills": {"tidy": {"preferences": {"short": False}, "addedToAgents": True}},
    }
    paths = layouts.key_paths(data, part, {"devHome.folder", "updates.installAutomatically"})
    assert paths == {
        "schemaVersion",
        "<setting>",
        "<setting>.$state",
        "claudeCode.folders.<folder>.setUp.$state",
        "claudeCode.folders.<folder>.setUp.on",
        "skills.<skill>.preferences.<preference>",
        "skills.<skill>.addedToAgents",
    }
