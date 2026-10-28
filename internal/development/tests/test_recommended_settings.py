"""The settings dev-home-toolkit recommends for Claude Code (decision 0032): what a sync says while
one waits for an answer, the answers an agent gives through --configure (decision 0038), how
setup writes a yes, and how it checks the answers saved in this PC's settings. The questions at a
console are in test_setup_questions.py.
"""

import json
import re
import shutil
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from helpers import (
    Run,
    Sandbox,
    recommended_values,
    run_python,
    sandbox_for,
    shared_module,
    write_text,
)

pytestmark = pytest.mark.xdist_group("recommended")

# The NEW line a sync prints while ~/.claude has that many recommended settings with no answer.
WAITING = (
    r"^NEW\s+Setup has no answer yet about {count} dev-home-toolkit recommends for Claude Code "
    r"in ~/\.claude, so it leaves {them}\. Answer with /dev-home configure: all recommended, "
    r"none, each, or remind me in N days\. Or run .*setup\.py in a terminal, and it asks\.$"
)


def waiting(count: int) -> str:
    settings = "1 setting" if count == 1 else f"{count} settings"
    them = "it as it is" if count == 1 else "them as they are"
    return WAITING.format(count=settings, them=them)


@pytest.fixture(scope="module")
def box(request: pytest.FixtureRequest) -> Iterator[Sandbox]:
    yield from sandbox_for(request, "recommended")


@pytest.fixture
def claude(box: Sandbox) -> Iterator[Path]:
    """~/.claude's settings.json, with none of the recommended settings in it, so all three wait
    for an answer. It's put back afterwards, with local-settings.json, ~/.claude.json, and their
    backups removed."""
    path = box.profile / ".claude" / "settings.json"
    settings = box.toolkit / "local-settings.json"
    older = box.profile / ".claude.json"
    before = path.read_bytes(), settings.read_bytes()
    data = json.loads(before[0])
    for key in recommended_values():
        data.pop(key)
    write_text(path, json.dumps(data, indent=2) + "\n")
    yield path
    path.write_bytes(before[0])
    settings.write_bytes(before[1])
    older.unlink(missing_ok=True)
    for file in (path, settings):
        for backup in file.parent.glob(file.name + ".bak-*"):
            backup.unlink()


def with_keys(path: Path, **keys: Any) -> None:
    """Sets keys at the top of a settings file, as JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(keys)
    write_text(path, json.dumps(data, indent=2) + "\n")


def settings_of(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def answers(box: Sandbox) -> Any:
    """The answers saved for ~/.claude's recommended settings."""
    saved = settings_of(box.toolkit / "local-settings.json")
    return saved["claudeCode"]["folders"]["~/.claude"].get("recommendedSettings")


def sync(box: Sandbox) -> Run:
    return run_python(box, "setup.py", "--quiet")


def configure(box: Sandbox, *args: str) -> Run:
    return run_python(box, "setup.py", "--configure", *args)


def command(listing: Run, name: str) -> str:
    """The assignment the listing gives for a yes, by its name, such as
    claudeCode.recommendedSettings.attribution-off, or claudeCode.recommendedSettings for all
    that wait."""
    pattern = re.compile(rf"--configure '({re.escape(name)}\+=[^']+)'")
    for line in listing.lines:
        found = pattern.search(line)
        if found:
            return found.group(1)
    raise AssertionError(f"No command for {name}:\n{listing}")


def test_a_sync_names_the_recommended_settings_waiting_and_changes_nothing(
    box: Sandbox, claude: Path
) -> None:
    # Nothing is written without a yes, and the line comes on every sync until they're answered.
    settings = box.toolkit / "local-settings.json"
    before = claude.read_bytes(), settings.read_bytes()
    result = sync(box)
    again = sync(box)
    assert result.code == 0 and result.has_line(waiting(3)), str(result)
    assert again.has_line(waiting(3)), str(again)
    assert (claude.read_bytes(), settings.read_bytes()) == before
    # The one with the recommended value already isn't counted.
    with_keys(claude, attribution=False)
    assert sync(box).has_line(waiting(2))


def test_a_folder_whose_settings_setup_cant_rewrite_is_offered_nothing(
    box: Sandbox, claude: Path
) -> None:
    # A yes couldn't be written there, so nothing is offered, and an answer in chat is refused,
    # with why.
    text = claude.read_text(encoding="utf-8")
    write_text(claude, text.replace("{", "{\n  // mine", 1))
    result = sync(box)
    assert result.code == 0 and not result.has_line(r"^NEW\s"), str(result)
    refused = configure(box, "claudeCode.recommendedSettings.attribution-off+=~/.claude@0123")
    pattern = r"^PROBLEM\s+Setup won't change .*settings\.json: it is not plain JSON"
    assert refused.code == 1 and refused.has_line(pattern), str(refused)


def test_configure_alone_lists_the_recommended_settings_waiting_with_their_commands(
    box: Sandbox, claude: Path
) -> None:
    with_keys(claude, attribution={"commit": "", "pr": ""}, remoteControlAtStartup=False)
    result = configure(box)
    lines = result.lines
    assert result.code == 0, str(result)
    assert lines[lines.index("Waiting for your answer") + 1] == "", str(result)
    start = lines.index("Recommended settings for Claude Code in ~/.claude")
    shown = "\n".join(lines[start : lines.index("dev-home-toolkit settings")])
    # Each as setup's question shows it, in columns, marked where only some are recommended.
    name = "Leave Claude Code's name out of your commits and pull requests"
    assert re.search(rf"^  {re.escape(name)}\s+recommended$", shown, re.M), shown
    remote = "Connect Remote Control when each Claude Code session starts"
    mark = "your own value, which all recommended keeps"
    assert re.search(rf"^  {re.escape(remote)}\s+{mark}$", shown, re.M), shown
    assert '      Now:          {"commit": "", "pr": ""}, an older form\n' in shown, shown
    assert "      Setting:      feedbackSurveyRate, in settings.json\n" in shown, shown
    assert "      Now:          not set\n" in shown and "      Recommended:  0\n" in shown, shown
    assert "      Now:          false\n" in shown, shown
    for setting_id in ("attribution-off", "feedback-survey-off", "remote-control-at-startup"):
        pattern = (
            rf"^      Yes:\s+--configure 'claudeCode\.recommendedSettings\.{setting_id}\+="
            r"~/\.claude@[0-9a-f]{12}'$"
        )
        assert re.search(pattern, shown, re.M), shown
    # All is a yes to each, which differs from all recommended where only some are recommended.
    assert re.search(r"^    all\s+each Yes command above, one after another$", shown, re.M), shown
    pattern = (
        r"^    all recommended\s+--configure 'claudeCode\.recommendedSettings\+=~/\.claude@"
        r"[0-9a-f]{12}' \(yes to each marked recommended, and no to the others\)$"
    )
    assert re.search(pattern, shown, re.M), shown
    assert "--configure 'claudeCode.recommendedSettings-=~/.claude'" in shown, shown
    assert "--configure 'claudeCode.recommendedSettings?=~/.claude@<days>'" in shown, shown
    # The settings show the count, and the list for an agent sends it to the section above.
    row = r"^\s+9\s+Recommended Claude Code settings\s+~/\.claude: 3 not answered yet$"
    assert result.has_line(row), str(result)
    pattern = r"^  ~/\.claude, attribution-off: not answered yet \(see Waiting for your answer\)\.$"
    assert result.has_line(pattern), str(result)
    # With every one recommended, all is all recommended, so it isn't offered twice.
    with_keys(claude, remoteControlAtStartup=True)
    again = configure(box)
    assert not again.has_line(r"^    all\s+each Yes"), str(again)


def test_the_settings_row_puts_each_folder_on_a_line_of_its_own(box: Sandbox, claude: Path) -> None:
    second = box.profile / ".claude-second"
    write_text(second / "settings.json", '{"attribution": false}\n')
    path = box.toolkit / "local-settings.json"
    saved = settings_of(path)
    saved["claudeCode"]["folders"]["~/.claude-second"] = {"setUp": True}
    write_text(path, json.dumps(saved, indent=2) + "\n")
    try:
        result = configure(box)
    finally:
        shutil.rmtree(second)
    first = "  9  Recommended Claude Code settings   "
    index = next(i for i, line in enumerate(result.lines) if line.startswith(first.rstrip()))
    row = result.lines[index : index + 2]
    column = row[0].index("~/.claude:")
    assert row[0].endswith("~/.claude: 3 not answered yet;"), str(result)
    assert row[1] == " " * column + "~/.claude-second: 2 not answered yet, 1 already set", str(
        result
    )


def test_a_yes_in_chat_writes_the_setting_with_a_backup_then_saves_the_answer(
    box: Sandbox, claude: Path
) -> None:
    before = claude.read_text(encoding="utf-8")
    yes = command(configure(box), "claudeCode.recommendedSettings.attribution-off")
    result = configure(box, yes)
    assert result.code == 0, str(result)
    pattern = (
        r"^SET\s+Claude Code settings in \.claude: set attribution to false in .*settings\.json\. "
        r"Backup of the old file: "
    )
    assert result.has_line(pattern), str(result)
    pattern = (
        r"^SET\s+This PC's settings: .*local-settings\.json, with your yes to attribution-off\. "
        r"Backup of the old file: "
    )
    assert result.has_line(pattern), str(result)
    assert settings_of(claude)["attribution"] is False
    backup = next(claude.parent.glob(claude.name + ".bak-*"))
    assert backup.read_text(encoding="utf-8") == before
    assert answers(box) == {"attribution-off": True}
    # It isn't offered again, and the answer stays once it's done.
    again = sync(box)
    assert again.has_line(waiting(2)) and not again.has_line(r"^SET\s"), str(again)


def test_a_yes_to_a_setting_written_twice_sets_it_once_and_says_only_that(
    box: Sandbox, claude: Path
) -> None:
    # The offer judges the last copy, the one Claude Code uses, and a yes leaves one copy.
    text = claude.read_text(encoding="utf-8").rstrip().removesuffix("}").rstrip()
    keys = '  "attribution": {"commit": ""},\n  "attribution": {"commit": "", "pr": ""}'
    write_text(claude, f"{text},\n{keys}\n}}\n")
    listing = configure(box)
    assert listing.has_line(r'^      Now:\s+\{"commit": "", "pr": ""\}, an older form$'), str(
        listing
    )
    result = configure(box, command(listing, "claudeCode.recommendedSettings.attribution-off"))
    pattern = r"^SET\s+Claude Code settings in \.claude: set attribution to false in .*\. Backup"
    assert result.code == 0 and result.has_line(pattern), str(result)
    written = claude.read_text(encoding="utf-8")
    assert written.count('"attribution"') == 1 and settings_of(claude)["attribution"] is False


def test_the_listing_marks_each_setting_even_when_every_one_is_recommended(
    box: Sandbox, claude: Path
) -> None:
    # All recommended says it's a yes to each marked recommended, so each has its mark.
    listing = configure(box)
    for name in (
        "Leave Claude Code's name out of your commits and pull requests",
        "Turn off Claude Code's session quality survey",
        "Connect Remote Control when each Claude Code session starts",
    ):
        assert listing.has_line(rf"^  {re.escape(name)}\s+recommended$"), str(listing)


def test_a_yes_folder_typed_in_another_case_is_the_same_folder(box: Sandbox, claude: Path) -> None:
    # The same run's NEW line doesn't count that setting as waiting any more.
    yes = command(configure(box), "claudeCode.recommendedSettings.attribution-off")
    result = configure(box, yes.replace("~/.claude@", "~/.CLAUDE@"))
    assert result.code == 0 and result.has_line(waiting(2)), str(result)
    assert answers(box) == {"attribution-off": True}


def test_a_yes_that_cant_be_written_saves_no_answer_and_comes_back(
    box: Sandbox, claude: Path
) -> None:
    # Such as a folder's lines that setup can't add, which share the one write.
    with_keys(claude, permissions=5)
    yes = command(configure(box), "claudeCode.recommendedSettings.feedback-survey-off")
    result = configure(box, yes)
    pattern = (
        r"^NEW\s+Claude Code settings in \.claude: left feedbackSurveyRate as it is in "
        r".*settings\.json, since setup couldn't write the file\. Setup asks again\.$"
    )
    assert result.code == 1 and result.has_line(r"^PROBLEM\s+Claude Code settings in"), str(result)
    assert result.has_line(pattern), str(result)
    assert answers(box) is None and settings_of(claude)["permissions"] == 5


def test_a_yes_whose_value_changed_since_the_listing_is_refused(box: Sandbox, claude: Path) -> None:
    yes = command(configure(box), "claudeCode.recommendedSettings.attribution-off")
    with_keys(claude, attribution={"commit": "Mine"})
    before = claude.read_bytes()
    result = configure(box, yes)
    pattern = (
        r"^PROBLEM\s+That setting in ~/\.claude changed since the listing showed it, so nothing "
        r"was changed\. Run --configure again to see it as it is now\."
    )
    assert result.code == 1 and result.has_line(pattern), str(result)
    assert not result.has_line(r"^To change one setting"), str(result)
    assert claude.read_bytes() == before and answers(box) is None


def test_all_recommended_in_chat_takes_the_recommended_ones_and_keeps_a_value_someone_chose(
    box: Sandbox, claude: Path
) -> None:
    # As Enter at a console: yes to each recommended there, in one write, and no to the others.
    with_keys(claude, attribution={"commit": "", "pr": ""}, remoteControlAtStartup=False)
    every = command(configure(box), "claudeCode.recommendedSettings")
    result = configure(box, every)
    assert result.code == 0, str(result)
    pattern = (
        r"^SET\s+Claude Code settings in \.claude: set attribution to false and "
        r"feedbackSurveyRate to 0 in "
    )
    assert result.has_line(pattern), str(result)
    assert len(list(claude.parent.glob(claude.name + ".bak-*"))) == 1
    written = settings_of(claude)
    assert written["attribution"] is False and written["feedbackSurveyRate"] == 0, written
    assert written["remoteControlAtStartup"] is False, written
    assert answers(box) == {
        "attribution-off": True,
        "feedback-survey-off": True,
        "remote-control-at-startup": False,
    }
    # This PC's settings got one backup, for the no and the yeses together.
    settings = box.toolkit / "local-settings.json"
    assert len(list(settings.parent.glob(settings.name + ".bak-*"))) == 1
    assert not sync(box).has_line(r"^NEW\s")


def test_a_stale_answer_for_all_of_them_is_refused(box: Sandbox, claude: Path) -> None:
    # Its fingerprint covers which ones wait, so one answered meanwhile changes it.
    every = command(configure(box), "claudeCode.recommendedSettings")
    assert configure(box, "claudeCode.recommendedSettings.attribution-off-=~/.claude").code == 0
    result = configure(box, every)
    pattern = r"^PROBLEM\s+What waits in ~/\.claude changed since the listing showed it"
    assert result.code == 1 and result.has_line(pattern), str(result)
    assert "feedbackSurveyRate" not in settings_of(claude)


def test_a_no_or_a_reminder_in_chat_is_saved_and_a_reminder_never_replaces_an_answer(
    box: Sandbox, claude: Path
) -> None:
    name = "claudeCode.recommendedSettings"
    no = configure(box, f"{name}.attribution-off-=~/.claude")
    assert no.code == 0 and no.has_line(r'^\s+\+\s+"attribution-off": false'), str(no)
    later = configure(box, f"{name}.feedback-survey-off?=~/.claude@7")
    assert later.code == 0, str(later)
    on = (date.today() + timedelta(days=7)).isoformat()
    assert answers(box) == {
        "attribution-off": False,
        "feedback-survey-off": {"$state": "remind", "on": on},
    }
    assert sync(box).has_line(waiting(1))
    refused = configure(box, f"{name}.attribution-off?=~/.claude@3")
    pattern = r"^PROBLEM\s+attribution-off in ~/\.claude already has an answer, no, and a reminder"
    assert refused.code == 1 and refused.has_line(pattern), str(refused)
    # None, for every one that waits: the no stays, and the reminder before its date isn't one.
    none = configure(box, f"{name}-=~/.claude")
    assert none.code == 0, str(none)
    assert answers(box)["remote-control-at-startup"] is False
    assert answers(box)["feedback-survey-off"] == {"$state": "remind", "on": on}
    assert "attribution" not in settings_of(claude)
    assert not sync(box).has_line(r"^NEW\s")


def test_configure_refuses_a_recommended_setting_it_cant_take(box: Sandbox, claude: Path) -> None:
    name = "claudeCode.recommendedSettings"
    cases = [
        (f"{name}.thing-on+=~/.claude@0123", "There is no recommended setting named thing-on"),
        (f"{name}.attribution-off=true", "takes +=<folder>@<fingerprint> for yes"),
        (f"{name}.attribution-off+=~/.claude", "takes a folder and the fingerprint"),
        (f"{name}.attribution-off-=~/.claude-none", "isn't a Claude Code folder set up"),
        (f"{name}.attribution-off?=~/.claude", "takes a folder and a whole number of days"),
    ]
    for assignment, fault in cases:
        result = configure(box, assignment)
        assert result.code == 1 and result.has_line(re.escape(fault)), str(result)
    assert answers(box) is None


def test_a_value_in_claude_json_counts_where_settings_json_has_none(
    box: Sandbox, claude: Path
) -> None:
    # Claude Code uses the value older versions left in ~/.claude.json only then, so a true there
    # needs nothing, and a false there is a value someone chose.
    older = box.profile / ".claude.json"
    write_text(older, json.dumps({"remoteControlAtStartup": True, "projects": {}}) + "\n")
    assert sync(box).has_line(waiting(2))
    write_text(older, json.dumps({"remoteControlAtStartup": False}) + "\n")
    listing = configure(box)
    pattern = (
        r"^      Now:\s+false, in \.claude\.json, which counts while settings\.json sets none$"
    )
    assert listing.has_line(pattern), str(listing)
    # All recommended keeps it, as a no; a yes writes settings.json alone, which then wins.
    every = configure(box, command(listing, "claudeCode.recommendedSettings"))
    assert every.code == 0 and answers(box)["remote-control-at-startup"] is False, str(every)
    assert "remoteControlAtStartup" not in settings_of(claude)
    yes = command(configure(box), "claudeCode.recommendedSettings.remote-control-at-startup")
    assert configure(box, yes).code == 0
    assert settings_of(claude)["remoteControlAtStartup"] is True
    assert settings_of(older) == {"remoteControlAtStartup": False}


def test_a_yes_whose_value_changed_later_is_shown_and_can_be_set_again(
    box: Sandbox, claude: Path
) -> None:
    # Setup never changes it back by itself, nor asks again: the menu and the list show the
    # value, and a yes there writes it again.
    yes = command(configure(box), "claudeCode.recommendedSettings.attribution-off")
    assert configure(box, yes).code == 0
    with_keys(claude, attribution={"commit": "Mine"})
    result = sync(box)
    assert result.has_line(waiting(2)) and not result.has_line(r"^SET\s"), str(result)
    assert settings_of(claude)["attribution"] == {"commit": "Mine"}
    listing = configure(box)
    pattern = (
        r"^  ~/\.claude, attribution-off: yes, but the value changed since: settings\.json has "
        r'\{"commit": "Mine"\} now, which setup leaves as it is\. For yes: --configure .*\. For '
        r"no: --configure "
        r"'claudeCode\.recommendedSettings\.attribution-off-=~/\.claude'\.$"
    )
    assert listing.has_line(pattern), str(listing)
    row = r"^\s+9\s+Recommended Claude Code settings\s+~/\.claude: 1 yes \(1 changed since\), "
    assert listing.has_line(row + r"2 not answered yet$"), str(listing)
    again = configure(box, command(listing, "claudeCode.recommendedSettings.attribution-off"))
    assert again.code == 0 and settings_of(claude)["attribution"] is False, str(again)
    # Taken out, as /config's default does, it's named as missing, not as a value.
    data = settings_of(claude)
    del data["attribution"]
    write_text(claude, json.dumps(data, indent=2) + "\n")
    pattern = (
        r"^  ~/\.claude, attribution-off: yes, but the value changed since: settings\.json "
        r"doesn't set it now, which setup leaves as it is\. "
    )
    assert configure(box).has_line(pattern)
    # And where only .claude.json has it, it's named there.
    yes = command(configure(box), "claudeCode.recommendedSettings.remote-control-at-startup")
    assert configure(box, yes).code == 0
    data = settings_of(claude)
    del data["remoteControlAtStartup"]
    write_text(claude, json.dumps(data, indent=2) + "\n")
    write_text(box.profile / ".claude.json", '{"remoteControlAtStartup": false}\n')
    pattern = (
        r"^  ~/\.claude, remote-control-at-startup: yes, but the value changed since: "
        r"settings\.json doesn't set it, and \.claude\.json has false now, which setup leaves "
    )
    assert configure(box).has_line(pattern)


def test_what_if_shows_a_yes_to_a_recommended_setting_and_changes_nothing(
    box: Sandbox, claude: Path
) -> None:
    settings = box.toolkit / "local-settings.json"
    before = claude.read_bytes(), settings.read_bytes()
    yes = command(configure(box), "claudeCode.recommendedSettings.feedback-survey-off")
    result = configure(box, yes, "--what-if")
    assert result.code == 0, str(result)
    assert result.has_line(r'^\s+\+\s+"feedbackSurveyRate": 0$'), str(result)
    assert result.has_line(r"^What if: Save the yes to feedback-survey-off: "), str(result)
    assert (claude.read_bytes(), settings.read_bytes()) == before


def test_answers_to_recommended_settings_are_checked_with_this_pcs_settings(
    box: Sandbox, claude: Path
) -> None:
    # An id the list doesn't have any more is removed, like a setting nothing declares, and so
    # are answers in a Codex home, which has no recommended settings; a value of the wrong kind
    # is a problem, and counts as no answer.
    path = box.toolkit / "local-settings.json"
    saved = settings_of(path)
    saved["claudeCode"]["folders"]["~/.claude"]["recommendedSettings"] = {
        "attribution-off": True,
        "gone-now": False,
        "feedback-survey-off": "yes",
    }
    saved["codex"]["homes"]["~/.codex"]["recommendedSettings"] = {"attribution-off": True}
    write_text(path, json.dumps(saved, indent=2) + "\n")
    result = sync(box)
    removed = (
        r"^SET\s+This PC's settings: .*Removed claudeCode\.folders ~/\.claude: "
        r"recommendedSettings\.gone-now, codex\.homes ~/\.codex: recommendedSettings: nothing "
        r"declares them any more\. Backup of the old file: "
    )
    assert result.has_line(removed), str(result)
    problem = (
        r"^PROBLEM\s+claudeCode\.folders ~/\.claude: recommendedSettings\.feedback-survey-off in "
        r'local-settings\.json is "yes", which isn\'t true, false, or a reminder, .* so it counts '
        r"as not answered yet\. Fix it there\.$"
    )
    assert result.code == 1 and result.has_line(problem), str(result)
    assert result.has_line(waiting(2)), str(result)
    kept = settings_of(path)
    assert kept["claudeCode"]["folders"]["~/.claude"]["recommendedSettings"] == {
        "attribution-off": True,
        "feedback-survey-off": "yes",
    }
    assert kept["codex"]["homes"]["~/.codex"] == {"setUp": True}


def test_the_menu_removes_a_gone_folders_answers_to_its_recommended_settings(
    box: Sandbox, claude: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = box.toolkit / "local-settings.json"
    saved = settings_of(path)
    saved["claudeCode"]["folders"]["~/.claude-gone"] = {
        "setUp": True,
        "recommendedSettings": {"attribution-off": True},
    }
    write_text(path, json.dumps(saved, indent=2) + "\n")
    run = shared_module(box, "setup").Setup(quiet=False, what_if=False)
    run.can_ask = True
    settings, _ = run.read_settings()
    # Yes to removing the gone folder, and Enter, which keeps its answer, for the other.
    monkeypatch.setattr(
        run,
        "choose",
        lambda question, default=None: True if "no longer exists" in question else default,
    )
    configure_module = shared_module(box, "configure")
    assert configure_module.change_claude_folders(run, settings) is True
    assert "~/.claude-gone" not in settings.data["claudeCode"]["folders"], settings.data


def test_a_sync_reads_claude_json_only_for_a_setting_that_can_wait(
    box: Sandbox, claude: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Remote Control is answered, so only attribution is judged, which never needs .claude.json.
    path = box.toolkit / "local-settings.json"
    saved = settings_of(path)
    saved["claudeCode"]["folders"]["~/.claude"]["recommendedSettings"] = {
        "feedback-survey-off": True,
        "remote-control-at-startup": False,
    }
    write_text(path, json.dumps(saved, indent=2) + "\n")
    code = shared_module(box, "setup")
    run = code.Setup(quiet=True, what_if=False)
    settings, _ = run.read_settings()

    def no_reads(place: Path) -> Any:
        raise AssertionError(f"read {place}")

    monkeypatch.setattr(code, "read_json_object", no_reads)
    found = run.recommended_offers(settings)
    assert [offer.setting.id for _, _, offers in found for offer in offers] == ["attribution-off"]


def test_a_yes_is_judged_on_the_read_the_write_plans_on(box: Sandbox, claude: Path) -> None:
    # So a change between two reads can't slip past the check: the work plans on that read too,
    # and leaves the file alone when it changes after it.
    code = shared_module(box, "setup")
    run = code.Setup(quiet=True, what_if=False)
    run.read_settings()
    current = shared_module(box, "recommended_settings").Current
    run.recommended_yes[(code.yes_key(claude.parent), "attribution-off")] = current()
    seen = shared_module(box, "settings_files").SettingsFile(text='{"attribution": true}\n')
    values, ids, already, left, reason = run.recommended_to_write(claude.parent, seen)
    assert (values, ids, already, left, reason) == ({}, [], [], ["attribution-off"], "")


def test_names_the_yeses_saved_with_their_folders_when_there_are_several(box: Sandbox) -> None:
    names = shared_module(box, "setup").yes_names
    assert names([("~/.claude", "a"), ("~/.claude", "b")]) == "a and b"
    pairs = [("~/.claude", "a"), ("~/.claude-second", "a"), ("~/.claude-second", "b")]
    assert names(pairs) == "a in ~/.claude and a and b in ~/.claude-second"


def test_a_folder_with_every_recommended_setting_answered_costs_a_sync_no_reads(
    box: Sandbox, claude: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A yes or a no, or a reminder before its date, leaves nothing to ask there, so setup doesn't
    # read the folder's settings.json or .claude.json to find out.
    path = box.toolkit / "local-settings.json"
    saved = settings_of(path)
    on = (date.today() + timedelta(days=3)).isoformat()
    saved["claudeCode"]["folders"]["~/.claude"]["recommendedSettings"] = {
        "attribution-off": True,
        "feedback-survey-off": False,
        "remote-control-at-startup": {"$state": "remind", "on": on},
    }
    write_text(path, json.dumps(saved, indent=2) + "\n")
    run = shared_module(box, "setup").Setup(quiet=True, what_if=False)
    settings, _ = run.read_settings()

    def no_reads(folder: Path) -> Any:
        raise AssertionError(f"read {folder}")

    monkeypatch.setattr(run, "current_values", no_reads)
    assert run.recommended_offers(settings) == []


def test_a_recommended_settings_plan_sets_each_value_in_its_place_or_last(box: Sandbox) -> None:
    claude_settings = shared_module(box, "claude_settings")
    path = box.root / "plans" / "settings.json"
    text = '{\n  "attribution": {"commit": ""},\n  "model": "a",\n  "attribution": true\n}\n'
    write_text(path, text)
    plan = claude_settings.plan(path, [], [], {"attribution": False, "feedbackSurveyRate": 0})
    assert plan.reason is None, plan.reason
    # A key written twice keeps its first place, with the last copy's value replaced.
    assert plan.new_text == (
        '{\n  "attribution": false,\n  "model": "a",\n  "feedbackSurveyRate": 0\n}\n'
    )
    assert plan.repeated == ["attribution"]


def test_a_recommended_value_is_judged_as_claude_code_reads_it(box: Sandbox) -> None:
    module = shared_module(box, "recommended_settings")
    survey = module.AgentSetting("feedbackSurveyRate", 0, when_missing="On.", when_other="On.")
    assert module.state_of(survey, module.Current()) == module.MISSING
    assert module.state_of(survey, module.Current("settings.json", 0.0)) == module.DONE
    assert module.state_of(survey, module.Current("settings.json", False)) == module.OTHER
    assert module.json_equal({"a": [1, True]}, {"a": [1.0, True]})
    assert not module.json_equal({"a": 1}, {"a": True}) and not module.json_equal(1, "1")
    attribution = module.AgentSetting(
        "attribution",
        False,
        older_forms=({"commit": "", "pr": ""},),
        when_missing="On.",
        when_older_form="Partly.",
        when_other="Yours.",
    )
    older = module.Current("settings.json", {"pr": "", "commit": ""})
    assert module.state_of(attribution, older) == module.OLDER
