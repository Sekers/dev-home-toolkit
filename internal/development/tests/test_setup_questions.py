"""What setup asks a person, and what it does with the answers.

These run setup's code inside this process, from the sandbox's copy, with a small fake for the
person at the console, since a test can't type into a real one; gh is faked too where a test
would reach GitHub. Git and the files stay real. The other tests here run setup.py as a process
with no console, to check that it then never waits for an answer.
"""

import contextlib
import json
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from helpers import (
    Sandbox,
    check_in_sandbox,
    git,
    link_target,
    profile_kept,
    remove_link,
    run_python,
    sandbox_for,
    script_env,
    shared_module,
    write_text,
)

pytestmark = pytest.mark.xdist_group("setup-questions")

# The question about installing updates, whatever Enter gives.
UPDATES = (
    r"^Pull updates automatically\? 'y', 'n', or 'd' for the default \(yes\) "
    r"\[[yY]/[nN]/[dD]\]: $"
)


@pytest.fixture(scope="module")
def box(request: pytest.FixtureRequest) -> Iterator[Sandbox]:
    yield from sandbox_for(request, "setup-questions")


class Person:
    """Answers questions at the console: the answer whose pattern the question matches, the next
    of a list of them, one each time it's asked, or what a function gives, for a person who also
    does something while answering. A question with no answer ends the input, as when a person
    closes the console."""

    def __init__(self, answers: dict[str, str | list[str] | Callable[[str], str]]) -> None:
        self.answers = answers
        self.asked: list[str] = []

    def __call__(self, prompt: str = "") -> str:
        self.asked.append(prompt)
        for pattern, answer in self.answers.items():
            if re.search(pattern, prompt):
                if isinstance(answer, list):
                    if not answer:
                        break
                    return answer.pop(0)
                if callable(answer):
                    return answer(prompt)
                return answer
        raise EOFError


@pytest.fixture
def person(box: Sandbox, monkeypatch: pytest.MonkeyPatch) -> Iterator[Person]:
    """A person at the console, with no answers until a test gives some."""
    someone = Person({})
    monkeypatch.setattr(shared_module(box, "console"), "is_console", lambda: True)
    monkeypatch.setattr("builtins.input", someone)
    yield someone


class FakeGh:
    """gh, signed in, recording each call. A clone copies the sandbox's own dev-home remote, as
    if from GitHub, or clone_from when a test sets it. failing names a command, such as
    ("repo", "create"), that fails instead."""

    def __init__(self, box: Sandbox) -> None:
        self.box = box
        self.calls: list[tuple[str, ...]] = []
        self.failing: tuple[str, ...] = ()
        self.clone_from = box.remote

    def __call__(self, program: str, *args: str) -> tuple[int, list[str]]:
        self.calls.append(args)
        if self.failing and args[: len(self.failing)] == self.failing:
            return 1, [f"gh: {' '.join(self.failing)} failed on purpose"]
        if args[:2] == ("repo", "clone"):
            git("clone", "--quiet", str(self.clone_from), args[3])
        return 0, []


@pytest.fixture
def fake_gh(box: Sandbox, monkeypatch: pytest.MonkeyPatch) -> FakeGh:
    gh = FakeGh(box)
    code = shared_module(box, "setup")
    monkeypatch.setattr(code, "find_program", lambda name: "gh" if name == "gh" else None)
    monkeypatch.setattr(code, "run_tool", gh)
    return gh


@pytest.fixture
def settings(box: Sandbox) -> Iterator[Path]:
    """local-settings.json, put back as it was after the test."""
    path = box.tools / "local-settings.json"
    before = path.read_bytes()
    yield path
    path.write_bytes(before)


def setup_here(box: Sandbox, *args: str) -> int:
    returned: int = shared_module(box, "setup").main(list(args))
    return returned


def test_without_a_console_it_asks_nothing_even_without_quiet(box: Sandbox, settings: Path) -> None:
    # With no dev-home folder saved, setup would ask for one, but input comes from NUL, as an
    # agent's command's does.
    saved = json.loads(settings.read_text(encoding="utf-8"))
    saved["devHome"]["folder"] = ""
    write_text(settings, json.dumps(saved, indent=2) + "\n")
    result = run_python(box, "setup.py")
    assert result.code == 1, str(result)
    assert result.has_line(r"^PROBLEM\s+This PC has no dev-home folder set"), str(result)


def test_with_input_from_a_silent_pipe_it_never_waits(box: Sandbox, settings: Path) -> None:
    saved = json.loads(settings.read_text(encoding="utf-8"))
    saved["devHome"]["folder"] = ""
    write_text(settings, json.dumps(saved, indent=2) + "\n")
    argv = [sys.executable, "-I", str(box.tools / "setup.py")]
    check_in_sandbox(argv)
    process = subprocess.Popen(
        argv,
        cwd=box.root,
        env=script_env(box),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # The pipe stays open, with nothing written to it, until setup ends.
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        raise AssertionError("setup waited for input nobody gave") from None
    finally:
        assert process.stdin is not None and process.stdout is not None
        process.stdin.close()
    out = process.stdout.read().decode("utf-8", errors="replace")
    process.stdout.close()
    assert process.returncode == 1, out
    assert re.search(r"^PROBLEM\s+This PC has no dev-home folder set", out, re.M), out


def test_output_to_a_file_is_no_console(box: Sandbox) -> None:
    # Python writes a question to the output, so with output in a file nobody would see it.
    console = shared_module(box, "console")
    with (box.root / "output.txt").open("w", encoding="utf-8") as file:
        assert not console.is_console_stream(file)


# The shared prompt for a list of optional items. Nothing calls it yet, so these call it
# directly.


def items(box: Sandbox, *recommended: bool) -> list[Any]:
    """Optional items named one, two, and so on, each recommended or not, in order."""
    names = ["one", "two", "three"]
    console = shared_module(box, "console")
    return [
        console.ListItem(name, wanted, f"Add {name}?")
        for name, wanted in zip(names, recommended, strict=False)
    ]


def choose_from_list(box: Sandbox, *recommended: bool) -> Any:
    return shared_module(box, "console").choose_from_list(
        "These items are new:", "Add them?", items(box, *recommended)
    )


def test_a_list_all_recommended_offers_all_none_or_each_and_enter_takes_all(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    person.answers[r"^Add them\?"] = ["", "a", "all", "a", "n"]
    enter = choose_from_list(box, True, True)
    assert capsys.readouterr().out == "These items are new:\n  one\n  two\n"
    assert person.asked == ["Add them? 'a' for all, 'n' for none, or 'e' to ask for each [A/n/e]: "]
    assert (enter.choice, enter.answers) == ("recommended", {"one": True, "two": True})
    # a is All recommended here, as Enter is, so the two can never be saved differently.
    assert choose_from_list(box, True, True).choice == "recommended"
    # Only the letters count.
    assert choose_from_list(box, True, True).choice == "recommended"
    assert "Type 'a', 'n', or 'e'." in capsys.readouterr().out
    none = choose_from_list(box, True, True)
    assert (none.choice, none.answers) == ("none", {"one": False, "two": False})


def test_a_mixed_list_marks_each_item_and_enter_takes_the_recommended_ones(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    person.answers[r"^Add them\?"] = ["", "a", "r"]
    enter = choose_from_list(box, True, False, True)
    out = capsys.readouterr().out
    assert out == (
        "These items are new:\n"
        "  one      recommended\n"
        "  two      not recommended\n"
        "  three    recommended\n"
    )
    assert person.asked == [
        "Add them? 'a' for all, 'r' for the recommended ones, 'n' for none, or 'e' to ask for "
        "each [a/R/n/e]: "
    ]
    assert (enter.choice, enter.answers) == (
        "recommended",
        {"one": True, "two": False, "three": True},
    )
    every = choose_from_list(box, True, False, True)
    assert (every.choice, every.answers) == ("all", {"one": True, "two": True, "three": True})
    assert choose_from_list(box, True, False, True).choice == "recommended"


@pytest.mark.parametrize("colored", [True, False], ids=["with color", "without color"])
def test_a_key_to_type_stands_apart_from_the_words_around_it(
    box: Sandbox, monkeypatch: pytest.MonkeyPatch, colored: bool
) -> None:
    # In quotes always, so it still stands apart with NO_COLOR or in copied text, and green too
    # at a console that shows color.
    monkeypatch.setattr(shared_module(box, "output"), "use_color", lambda: colored)
    key = shared_module(box, "console").key("a")
    assert key == ("\x1b[32m'a'\x1b[0m" if colored else "'a'")


def test_a_list_with_nothing_recommended_takes_enter_as_none(box: Sandbox, person: Person) -> None:
    person.answers[r"^Add them\?"] = ["", "n", "a"]
    enter = choose_from_list(box, False, False)
    assert person.asked == ["Add them? 'a' for all, 'n' for none, or 'e' to ask for each [a/N/e]: "]
    assert (enter.choice, enter.answers) == ("recommended", {"one": False, "two": False})
    assert choose_from_list(box, False, False).choice == "recommended"
    every = choose_from_list(box, False, False)
    assert (every.choice, every.answers) == ("all", {"one": True, "two": True})


def test_asking_for_each_item_defaults_to_its_recommendation(box: Sandbox, person: Person) -> None:
    person.answers[r"^Add them\?"] = "e"
    person.answers[r"^Add (one|two|three)\?"] = ["", "", "y"]
    answer = choose_from_list(box, True, False, False)
    assert person.asked[1:] == ["Add one? [Y/n]: ", "Add two? [y/N]: ", "Add three? [y/N]: "]
    assert (answer.choice, answer.answers) == ("each", {"one": True, "two": False, "three": True})


def test_a_list_of_one_asks_only_its_items_question(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    person.answers[r"^Add one\?"] = ["", "n", "y"]
    answer = choose_from_list(box, False)
    assert person.asked == ["Add one? [y/N]: "]
    assert capsys.readouterr().out == ""
    # Its answer is the choice the list's letters would give, so one item is saved as several
    # would be: the recommendation, typed or by Enter, is All recommended.
    assert (answer.choice, answer.answers) == ("recommended", {"one": False})
    assert choose_from_list(box, False).choice == "recommended"
    every = choose_from_list(box, False)
    assert (every.choice, every.answers) == ("all", {"one": True})
    person.answers[r"^Add one\?"] = "n"
    none = choose_from_list(box, True)
    assert (none.choice, none.answers) == ("none", {"one": False})


def test_an_empty_list_asks_nothing(box: Sandbox, person: Person) -> None:
    answer = choose_from_list(box)
    assert person.asked == []
    assert (answer.choice, answer.answers) == ("recommended", {})


def test_a_list_answered_only_partway_gives_no_answer(box: Sandbox, person: Person) -> None:
    person.answers[r"^Add them\?"] = "e"
    person.answers[r"^Add one\?"] = "y"
    # The question about two ends the input, as when a person closes the console.
    assert choose_from_list(box, True, True) is None
    assert person.asked[-1] == "Add two? [Y/n]: "
    person.answers.clear()
    assert choose_from_list(box, True, True) is None


def test_setup_asks_no_list_without_a_console(box: Sandbox, person: Person) -> None:
    run = shared_module(box, "setup").Setup(quiet=True, what_if=False)
    assert run.choose_from_list("These items are new:", "Add them?", items(box, True)) is None
    assert person.asked == []


def test_asks_for_the_dev_home_folder_when_none_is_saved(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    saved = json.loads(settings.read_text(encoding="utf-8"))
    content = saved["devHome"]["folder"]
    saved["devHome"]["folder"] = ""
    write_text(settings, json.dumps(saved, indent=2) + "\n")
    person.answers[r"^Your dev-home folder \[.*\]: $"] = content
    returned = setup_here(box)
    out = capsys.readouterr().out
    assert returned == 0, out
    assert json.loads(settings.read_text(encoding="utf-8"))["devHome"]["folder"] == content
    assert re.search(r"^SET\s+This PC's settings", out, re.MULTILINE), out


# The question about each Claude Code folder, and about all of them at once.
FOLDERS = (
    r"^Set up Claude Code in them with dev-home's skills and rules\? 'a' for all, 'n' for none, "
    r"or 'e' to ask for each \[A/n/e\]: $"
)


def folder_question(folder: Path, hint: str = r"\[Y/n\]") -> str:
    """One folder's question, in a list asked about one at a time, or in the menu."""
    return rf"^Set up Claude Code in {re.escape(str(folder))}\? {hint}: $"


# The question about the only Claude Code folder setup hasn't asked about, after a line naming it.
THIS_FOLDER = r"^Set up Claude Code in this folder\? \[Y/n\]: $"


# The one question for Codex, which covers every Codex home, since they all read the same skills.
CODEX = r"^Set up Codex in every Codex home\? \[Y/n\]: $"


def test_a_first_run_asks_about_updates_each_claude_folder_and_codex(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A first run has no local-settings.json yet. Here it must keep testHomeDir, so the run gets
    # settings with no answers instead. Every Claude Code folder setup finds is in one list,
    # ~/.claude included, each recommended, and Codex gets one question for every Codex home,
    # ~/.codex included. A ~/.codex-* folder counts only with Codex's settings or sign-in in it.
    code = shared_module(box, "setup")
    saved = json.loads(settings.read_text(encoding="utf-8"))
    first_run = shared_module(box, "settings").LocalSettings(
        content_dir=saved["devHome"]["folder"], test_home_dir=saved["testHomeDir"]
    )
    monkeypatch.setattr(code, "load_local_settings", lambda: first_run)
    second = box.profile / ".claude-second"
    third = box.profile / ".claude-third"
    second.mkdir()
    third.mkdir()
    work = box.profile / ".codex-work"
    plain = box.profile / ".codex-plain"
    write_text(work / "auth.json", "{}\n")
    plain.mkdir()
    person.answers.update(
        {
            UPDATES: "y",
            FOLDERS: "e",
            folder_question(box.profile / ".claude"): "",
            folder_question(second): "yes",
            folder_question(third): "n",
            CODEX: "",
        }
    )
    try:
        returned = setup_here(box)
        out = capsys.readouterr().out
        written = json.loads(settings.read_text(encoding="utf-8"))
        allowed = json.loads((second / "settings.json").read_text(encoding="utf-8"))
        linked = link_target(second / "skills" / "handoff")
        work_rules = (work / "AGENTS.md").exists()
        work_config = tomllib.loads((work / "config.toml").read_text(encoding="utf-8"))
    finally:
        for folder in (second / "skills", second / "rules"):
            for link in folder.iterdir() if folder.is_dir() else []:
                remove_link(link)
        for folder in (second, third, work, plain):
            shutil.rmtree(folder)
    assert returned == 0, out
    assert any(re.search(FOLDERS, asked) for asked in person.asked), person.asked
    assert sum(1 for asked in person.asked if re.search(CODEX, asked)) == 1, person.asked
    assert re.search(r"^Claude Code folders setup hasn't asked about yet", out, re.M), out
    homes = f"{box.profile / '.codex'}, {work}"
    pattern = rf"^Codex homes: {re.escape(homes)}$"
    assert re.search(pattern, out, re.M), out
    assert ".codex-plain" not in out, out
    assert written["updates"]["installAutomatically"] is True
    # The no is kept, so the folder isn't asked about again.
    assert written["claudeCode"]["folders"] == {
        "~/.claude": {"setUp": True},
        "~/.claude-second": {"setUp": True},
        "~/.claude-third": {"setUp": False},
    }
    # One answer, so every home gets it, and the rules and the config.toml lines.
    assert written["codex"] == {
        "homes": {"~/.codex": {"setUp": True}, "~/.codex-work": {"setUp": True}}
    }
    assert work_rules, out
    assert work_config["sandbox_workspace_write"]["writable_roots"] == [str(box.content)]
    assert written["testHomeDir"] == saved["testHomeDir"]
    assert linked == box.generated / "skills" / "handoff"
    # Each yes approved the settings change its folder or home needs, and the questions said so
    # first.
    assert len(allowed["permissions"]["additionalDirectories"]) == 2
    pattern = (
        r"^SET\s+Claude Code settings in \.claude-second: added dev-home and dev-home-tools to "
        r"permissions\.additionalDirectories in .*settings\.json \(new file\)$"
    )
    assert re.search(pattern, out, re.M), out
    # The list, then what a yes does, then the question; and for Codex, the homes first.
    words = " ".join(out.split())
    claude = (
        f"{box.profile / '.claude-third'} A 'yes' sets up dev-home's skills and rules in each. "
        "It also adds your dev-home and dev-home-tools folders to "
        "permissions.additionalDirectories in each folder's settings.json, so Claude Code can use "
        "them from any project. A 'no' removes all of that, if it's there. Setup backs up each "
        "file first."
    )
    assert claude in words, out
    codex = (
        f"Codex homes: {homes} Every Codex home reads the same skills, so they share one answer. "
        "A 'yes' sets up dev-home's skills and rules in each home. In each home's config.toml, "
        "it also adds your dev-home folder to writable_roots, so Codex can write there from any "
        "project, and sets project_doc_max_bytes to 65536, so Codex reads all of your rules. "
        "A 'no' removes all of that but project_doc_max_bytes, if it's there. Setup backs up "
        "each file first."
    )
    assert codex in words, out
    assert not any(re.search(r"change\?", asked) for asked in person.asked), person.asked


def test_enter_at_the_list_of_claude_folders_sets_them_all_up(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Each is recommended, so a first setup is still one Enter.
    saved = json.loads(settings.read_text(encoding="utf-8"))
    del saved["claudeCode"]
    write_text(settings, json.dumps(saved, indent=2) + "\n")
    extra = box.profile / ".claude-extra"
    write_text(extra / "settings.json", "{}\n")
    person.answers[FOLDERS] = ""
    try:
        setup_here(box)
        out = capsys.readouterr().out
        written = json.loads(settings.read_text(encoding="utf-8"))
        linked = link_target(extra / "skills" / "handoff")
    finally:
        for folder in (extra / "skills", extra / "rules"):
            for link in folder.iterdir() if folder.is_dir() else []:
                remove_link(link)
        shutil.rmtree(extra)
    assert written["claudeCode"]["folders"] == {
        "~/.claude": {"setUp": True},
        "~/.claude-extra": {"setUp": True},
    }, out
    assert linked == box.generated / "skills" / "handoff", out


def test_asks_each_question_whose_answer_isnt_saved_yet_then_never_again(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Not a first run: the file is there, but automatic updates have no answer yet, and a Claude
    # folder was made after the first run.
    saved = json.loads(settings.read_text(encoding="utf-8"))
    del saved["updates"]["installAutomatically"]
    write_text(settings, json.dumps(saved, indent=2) + "\n")
    later = box.profile / ".claude-later"
    later.mkdir()
    # A list of one names its folder, says what a yes does, and asks only about that folder.
    person.answers.update({UPDATES: "n", THIS_FOLDER: "n"})
    try:
        returned = setup_here(box)
        written = json.loads(settings.read_text(encoding="utf-8"))
        asked = list(person.asked)
        again = setup_here(box)
        out = capsys.readouterr().out
    finally:
        shutil.rmtree(later)
    assert returned == 0 and again == 0, out
    # Every run by hand shows the settings menu too.
    questions = [prompt for prompt in person.asked if not re.search(MENU, prompt)]
    assert len(asked) == 3 and re.search(MENU, asked[-1]), asked
    assert questions == asked[:2], person.asked
    assert re.search(rf"^Claude Code folder: {re.escape(str(later))}$", out, re.M), out
    assert "A 'yes' sets up dev-home's skills and rules there." in out, out
    assert "A 'no' removes all of that, if it's there." in " ".join(out.split()), out
    assert written["updates"]["installAutomatically"] is False
    assert written["claudeCode"]["folders"] == {
        "~/.claude": {"setUp": True},
        "~/.claude-later": {"setUp": False},
    }


def test_enter_at_the_first_updates_question_follows_the_default(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Saved as the default, not as its value, so a later change of default reaches this PC.
    unanswered_updates(settings)
    person.answers[UPDATES] = ""
    returned = setup_here(box)
    out = capsys.readouterr().out
    written = json.loads(settings.read_text(encoding="utf-8"))
    assert returned == 0, out
    assert any(asked.endswith("(yes) [y/n/D]: ") for asked in person.asked), person.asked
    assert written["updates"]["installAutomatically"] == {"$state": "default"}, written


def test_with_no_answer_to_the_updates_question_nothing_is_saved(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # The input ends, as when a person closes the console: the question stays unanswered.
    unanswered_updates(settings)
    returned = setup_here(box)
    out = capsys.readouterr().out
    written = json.loads(settings.read_text(encoding="utf-8"))
    assert returned == 0, out
    assert any(re.search(UPDATES, asked) for asked in person.asked), person.asked
    assert "installAutomatically" not in written.get("updates", {}), written


@pytest.mark.parametrize(
    ("saved", "answer", "hint", "written"),
    [
        (None, "", "[y/n/D]", {"$state": "default"}),
        (True, "", "[Y/n/d]", True),
        (False, "", "[y/N/d]", False),
        ({"$state": "default"}, "", "[y/n/D]", {"$state": "default"}),
        (True, "d", "[Y/n/d]", {"$state": "default"}),
        ({"$state": "default"}, "n", "[y/n/D]", False),
        (False, ["maybe", "yes"], "[y/N/d]", True),
    ],
    ids=[
        "nothing saved, Enter",
        "yes saved, Enter",
        "no saved, Enter",
        "default saved, Enter",
        "yes saved, d",
        "default saved, n",
        "an answer it doesn't take",
    ],
)
def test_the_updates_question_takes_yes_no_or_default_and_enter_keeps_a_saved_answer(
    box: Sandbox,
    backups_removed: Path,
    person: Person,
    capsys: pytest.CaptureFixture[str],
    saved: object,
    answer: str | list[str],
    hint: str,
    written: object,
) -> None:
    # Enter never turns a yes or a no into following the default without the person noticing.
    data = json.loads(backups_removed.read_text(encoding="utf-8"))
    data["updates"].pop("installAutomatically", None)
    if saved is not None:
        data["updates"]["installAutomatically"] = saved
    write_text(backups_removed, json.dumps(data, indent=2) + "\n")
    person.answers.update({MENU: ["2", ""], UPDATES: answer})
    returned = setup_here(box, "--configure")
    out = capsys.readouterr().out
    result = json.loads(backups_removed.read_text(encoding="utf-8"))
    assert returned == 0, out
    asked = [prompt for prompt in person.asked if re.search(UPDATES, prompt)]
    assert asked and all(prompt.endswith(f"(yes) {hint}: ") for prompt in asked), asked
    assert result["updates"]["installAutomatically"] == written, result
    assert ("Type 'y', 'n', or 'd'." in out) == isinstance(answer, list), out


def test_a_yes_replaces_a_value_of_the_wrong_kind_that_equals_it_in_python(
    box: Sandbox, backups_removed: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # In Python, 1 == True, but the file needs true: 1 isn't a value the setting takes.
    data = json.loads(backups_removed.read_text(encoding="utf-8"))
    data["updates"]["installAutomatically"] = 1
    write_text(backups_removed, json.dumps(data, indent=2) + "\n")
    person.answers.update({MENU: ["2", ""], UPDATES: "y"})
    setup_here(box, "--configure")
    out = capsys.readouterr().out
    written = json.loads(backups_removed.read_text(encoding="utf-8"))
    assert written["updates"]["installAutomatically"] is True, out


def unanswered_updates(settings: Path) -> None:
    saved = json.loads(settings.read_text(encoding="utf-8"))
    saved.get("updates", {}).pop("installAutomatically", None)
    write_text(settings, json.dumps(saved, indent=2) + "\n")


def test_a_save_keeps_what_a_sync_wrote_while_a_question_waited(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unanswered_updates(settings)
    code = shared_module(box, "setup")
    asking = code.Setup.ask_auto_update

    def ask_while_a_sync_writes(run: Any, data: dict[str, Any]) -> object:
        meanwhile = json.loads(settings.read_text(encoding="utf-8"))
        meanwhile["devHome"]["checkEveryHours"] = 6
        write_text(settings, json.dumps(meanwhile, indent=2) + "\n")
        answer: object = asking(run, data)
        return answer

    monkeypatch.setattr(code.Setup, "ask_auto_update", ask_while_a_sync_writes)
    person.answers[UPDATES] = "y"
    returned = setup_here(box)
    out = capsys.readouterr().out
    written = json.loads(settings.read_text(encoding="utf-8"))
    assert returned == 0, out
    assert written["updates"]["installAutomatically"] is True, written
    assert written["devHome"]["checkEveryHours"] == 6, written


def test_setup_by_hand_does_its_work_only_once_a_sync_lets_go_of_its_lock(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    unanswered_updates(settings)
    person.answers[UPDATES] = "y"
    sync = shared_module(box, "sync")
    monkeypatch.setattr(sync, "LOCK_WAIT_SECONDS", 0)
    git_dir = box.content / ".git"
    assert git_dir.is_dir()
    with sync.one_run_at_a_time(git_dir) as owned:
        assert owned
        waited = setup_here(box)
        unsaved = json.loads(settings.read_text(encoding="utf-8"))
        # A sync runs setup while it holds the lock, so that setup works without taking it.
        held = shared_module(box, "setup").main([], sync_holds_lock=True)
    out = capsys.readouterr().out
    saved = json.loads(settings.read_text(encoding="utf-8"))
    assert waited == 1, out
    pattern = r"^PROBLEM\s+Setup changed nothing: a sync, or an update, has been using dev-home"
    assert re.search(pattern, out, re.M), out
    assert "installAutomatically" not in unsaved.get("updates", {}), unsaved
    assert held == 0, out
    assert saved["updates"]["installAutomatically"] is True, saved


def test_a_run_by_hand_asks_everything_before_its_work_which_holds_the_sync_lock(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The questions and the menu, in that order, with the lock free, so no sync waits on a person;
    # then the work, holding it, the settings file the folder's yes approved included, since a
    # sync writes it too.
    unanswered_updates(settings)
    path = box.profile / ".claude" / "settings.json"
    before = path.read_bytes()
    write_text(path, "{}\n")
    sync = shared_module(box, "sync")
    code = shared_module(box, "setup")
    monkeypatch.setattr(sync, "LOCK_WAIT_SECONDS", 0)
    events: list[str] = []

    def lock_held() -> bool:
        with sync.one_run_at_a_time(box.content / ".git") as owned:
            return not owned

    def answering(event: str, answer: str) -> Callable[[str], str]:
        def answer_it(prompt: str) -> str:
            events.append(f"{event}, lock held: {lock_held()}")
            return answer

        return answer_it

    making_the_link = code.Setup.sync_python_link

    def python_link(run: Any, *args: Any, **kwargs: Any) -> None:
        events.append(f"work, lock held: {lock_held()}")
        making_the_link(run, *args, **kwargs)

    writing = code.write_settings_file

    def write_file(file: Path, *args: Any, **kwargs: Any) -> str:
        if file == path:
            events.append(f"settings file, lock held: {lock_held()}")
        written: str = writing(file, *args, **kwargs)
        return written

    monkeypatch.setattr(code.Setup, "sync_python_link", python_link)
    monkeypatch.setattr(code, "write_settings_file", write_file)
    person.answers.update(
        {
            UPDATES: answering("updates", "y"),
            MENU: answering("menu", ""),
        }
    )
    try:
        returned = setup_here(box)
        out = capsys.readouterr().out
    finally:
        path.write_bytes(before)
        for backup in path.parent.glob("settings.json.bak-*"):
            backup.unlink()
    assert returned == 0, out
    assert events == [
        "updates, lock held: False",
        "menu, lock held: False",
        "work, lock held: True",
        "settings file, lock held: True",
    ], events
    assert json.loads(settings.read_text(encoding="utf-8"))["updates"]["installAutomatically"]


@pytest.mark.skipif(sys.platform != "win32", reason="only Windows refuses to replace an open file")
def test_an_answer_that_cant_be_saved_leaves_the_old_settings_whole(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Saved by swapping in a new copy, so a save that can't finish, here because another program
    # holds the file open, leaves the old file as it was rather than half written.
    monkeypatch.setattr(shared_module(box, "settings_files"), "REPLACE_WAIT_SECONDS", 0.2)
    saved = json.loads(settings.read_text(encoding="utf-8"))
    saved.get("updates", {}).pop("installAutomatically", None)
    write_text(settings, json.dumps(saved, indent=2) + "\n")
    before = settings.read_bytes()
    person.answers[UPDATES] = "n"
    with settings.open("rb"):
        returned = setup_here(box)
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(r"^PROBLEM\s+Could not save this PC's settings", out, re.M), out
    assert settings.read_bytes() == before
    left = sorted(entry.name for entry in settings.parent.glob("local-settings.json*"))
    assert left == ["local-settings.json"], "no backup and no new file left beside it"


SET_ASIDE = r"^Set it aside and answer the questions again\? \[Y/n\]: $"


def test_at_a_console_settings_in_the_older_layout_are_set_aside_and_asked_again(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Only testHomeDir comes along, so the run still uses the test profile.
    saved = json.loads(settings.read_text(encoding="utf-8"))
    content = saved["devHome"]["folder"]
    old = {"contentDir": content, "autoUpdate": True, "testHomeDir": saved["testHomeDir"]}
    old_text = json.dumps(old, indent=2) + "\n"
    write_text(settings, old_text)
    person.answers.update(
        {
            SET_ASIDE: "",
            r"^Your dev-home folder \[.*\]: $": content,
            UPDATES: "n",
            THIS_FOLDER: "",
            CODEX: "",
        }
    )
    try:
        returned = setup_here(box)
        out = capsys.readouterr().out
        written = json.loads(settings.read_text(encoding="utf-8"))
        backups = list(settings.parent.glob("local-settings.json.bak-*"))
        kept = [backup.read_text(encoding="utf-8") for backup in backups]
    finally:
        for backup in settings.parent.glob("local-settings.json.bak-*"):
            backup.unlink()
    assert returned == 0, out
    assert re.search(r"^SET\s+The old settings, set aside: .*local-settings\.json\.bak-", out, re.M)
    assert kept == [old_text], kept
    # Each skill but dev-home, which is always added, is new to the settings.
    unanswered = {"addedToAgents": {"$state": "unanswered"}}
    assert written == {
        "schemaVersion": 1,
        "testHomeDir": saved["testHomeDir"],
        "devHome": {"folder": content},
        "updates": {"installAutomatically": False},
        "claudeCode": {"folders": {"~/.claude": {"setUp": True}}},
        "codex": {"homes": {"~/.codex": {"setUp": True}}},
        "skills": {"handoff": unanswered, "knowledge": unanswered, "mine": unanswered},
    }, written


def test_at_a_console_a_no_to_setting_the_older_settings_aside_stops(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    saved = json.loads(settings.read_text(encoding="utf-8"))
    old_text = json.dumps({"contentDir": "x", "testHomeDir": saved["testHomeDir"]}) + "\n"
    write_text(settings, old_text)
    person.answers[SET_ASIDE] = "n"
    returned = setup_here(box)
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(r"^PROBLEM\s+Stopped: .*local-settings\.json is in an older layout", out, re.M)
    assert settings.read_text(encoding="utf-8") == old_text
    assert not list(settings.parent.glob("local-settings.json.bak-*"))


NOT_A_DEV_HOME = r"^Your dev-home folder, or Enter to stop: $"


def test_at_a_console_asks_again_for_a_folder_that_isnt_a_dev_home(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    project = box.root / "console-project"
    write_text(project / "README.md", "# a project\n")
    content = json.loads(settings.read_text(encoding="utf-8"))["devHome"]["folder"]
    person.answers[NOT_A_DEV_HOME] = content
    returned = setup_here(box, "--content-dir", str(project))
    out = capsys.readouterr().out
    assert returned == 0, out
    assert re.search(r"console-project doesn't look like a dev-home: it has no ", out), out
    assert json.loads(settings.read_text(encoding="utf-8"))["devHome"]["folder"] == content


def test_at_a_console_enter_stops_at_a_folder_that_isnt_a_dev_home(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    project = box.root / "console-project-too"
    write_text(project / "README.md", "# a project\n")
    before = settings.read_text(encoding="utf-8")
    person.answers[NOT_A_DEV_HOME] = ""
    returned = setup_here(box, "--content-dir", str(project))
    out = capsys.readouterr().out
    assert returned == 1, out
    pattern = r"^PROBLEM\s+Stopped: .*console-project-too doesn't look like a dev-home\."
    assert re.search(pattern, out, re.M), out
    assert settings.read_text(encoding="utf-8") == before


def test_a_folder_chosen_in_the_menu_is_checked_before_anything_is_saved(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    project = box.root / "menu-project"
    write_text(project / "README.md", "# a project\n")
    before = settings.read_text(encoding="utf-8")
    person.answers.update(
        {MENU: ["1", ""], r"^Your dev-home folder \[.*\]: $": str(project), NOT_A_DEV_HOME: ""}
    )
    returned = setup_here(box)
    out = capsys.readouterr().out
    assert returned == 1, out
    pattern = r"^PROBLEM\s+Stopped: .*menu-project doesn't look like a dev-home\."
    assert re.search(pattern, out, re.M), out
    assert settings.read_text(encoding="utf-8") == before


# How many copies of dev-home are in active use, asked of a dev-home of the test's own.

ELSEWHERE = r"^Is dev-home in active use anywhere besides this PC, .*\? \[y/n\]: $"
# The same question, with dev-home.json's answer, several or one, as its default.
ELSEWHERE_YES = ELSEWHERE.replace(r"\[y/n\]", r"\[Y/n\]")
ELSEWHERE_NO = ELSEWHERE.replace(r"\[y/n\]", r"\[y/N\]")
RETIRED = r"^Have all the other copies been retired, .*\? \[y/N\]: $"
SAVE_COPIES = r"Save it, commit it, and push it to GitHub\? \[y/N\]: $"


def own_dev_home(box: Sandbox, name: str, copies: str | None) -> tuple[Path, Path]:
    """A dev-home with a remote of its own, and dev-home.json's text, if any. Returns both."""
    remote = box.root / f"{name}.git"
    home = box.root / name
    git("init", "--quiet", "--bare", "-b", "main", str(remote))
    git("clone", "--quiet", str(remote), str(home))
    git("-C", str(home), "config", "commit.gpgsign", "false")
    write_text(home / "global-rules" / "global-rules.md", "# My rules\n")
    write_text(home / "knowledge" / "README.md", "# Knowledge base\n")
    if copies is not None:
        write_text(home / "dev-home.json", copies)
    git("-C", str(home), "add", "--all")
    git("-C", str(home), "commit", "--quiet", "-m", "test: dev-home")
    git("-C", str(home), "push", "--quiet", "-u", "origin", "main")
    return home, remote


def check_copies(
    box: Sandbox,
    home: Path,
    *,
    quiet: bool = False,
    first_setup: bool = False,
    cloned: bool = False,
    created: bool = False,
) -> int:
    """Asks setup's question about copies for one dev-home, shows the change, and makes it, as
    a run of setup does in its questions, its changes to confirm, and its work. Returns setup's
    exit code."""
    run = shared_module(box, "setup").Setup(quiet=quiet, what_if=False)
    run.cloned = cloned
    run.created = created
    settings = shared_module(box, "settings").LocalSettings(content_dir=str(home))
    run.ask_about_copies(settings, home, first_setup=first_setup)
    run.confirm_copies(home)
    run.write_copies(home)
    returned: int = run.finish()
    return returned


def test_asks_how_many_copies_with_no_default_then_commits_and_pushes_the_answer(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    home, remote = own_dev_home(box, "copies-unanswered", None)
    # Enter has no default, so the question comes again, after saying what to type.
    person.answers.update({ELSEWHERE: ["", "y"], SAVE_COPIES: "y"})
    returned = check_copies(box, home)
    out = capsys.readouterr().out
    assert returned == 0, out
    assert sum(1 for asked in person.asked if re.search(ELSEWHERE, asked)) == 2, person.asked
    assert re.search(r"^Type 'y' or 'n'\.$", out, re.M), out
    assert json.loads((home / "dev-home.json").read_text(encoding="utf-8")) == {
        "schemaVersion": 1,
        "multiMachine": True,
    }
    assert re.search(r'^\s+\+\s+"multiMachine": true', out, re.M), out
    assert git("-C", str(remote), "log", "-1", "--format=%s") == ["dev-home: several active copies"]
    assert re.search(r"On each other copy, run /dev-home sync", out), out


def test_a_no_to_saving_the_copies_answer_leaves_dev_home_as_it_is(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    home, remote = own_dev_home(box, "copies-not-saved", None)
    person.answers.update({ELSEWHERE: "n", SAVE_COPIES: "n"})
    returned = check_copies(box, home)
    out = capsys.readouterr().out
    assert returned == 1, out
    assert not (home / "dev-home.json").exists()
    assert re.search(r"^PROBLEM\s+.*dev-home\.json was left as it is\.", out, re.M), out
    assert git("-C", str(remote), "log", "-1", "--format=%s") == ["test: dev-home"]


@pytest.mark.parametrize(
    ("answer", "several"), [("y", True), ("n", False), ("", False)], ids=["y", "n", "Enter"]
)
def test_after_a_clone_set_to_one_copy_asks_with_one_as_the_default(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str], answer: str, several: bool
) -> None:
    text = '{"schemaVersion": 1, "multiMachine": false, "x": 1}\n'
    home, remote = own_dev_home(box, f"copies-cloned-{answer or 'enter'}", text)
    person.answers.update({ELSEWHERE_NO: answer, SAVE_COPIES: "y"})
    returned = check_copies(box, home, cloned=True)
    out = capsys.readouterr().out
    assert returned == 0, out
    assert any(re.search(ELSEWHERE_NO, asked) for asked in person.asked), person.asked
    saved = json.loads((home / "dev-home.json").read_text(encoding="utf-8"))
    # A key setup doesn't know is kept.
    assert saved == {"schemaVersion": 1, "multiMachine": several, "x": 1}, saved
    subjects = git("-C", str(remote), "log", "--format=%s")
    assert (subjects[0] == "dev-home: several active copies") == several, subjects
    # Without a change, nothing is shown or asked about saving.
    assert any(re.search(SAVE_COPIES, asked) for asked in person.asked) == several


def test_an_answered_dev_home_is_asked_nothing(box: Sandbox, person: Person) -> None:
    home, _ = own_dev_home(box, "copies-answered", '{"schemaVersion": 1, "multiMachine": false}\n')
    assert check_copies(box, home) == 0
    assert person.asked == []


def test_a_first_setup_asks_with_dev_home_jsons_answer_as_the_default(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Adding a PC is when the answer most often changes. Enter keeps several copies.
    text = '{"schemaVersion": 1, "multiMachine": true}\n'
    home, remote = own_dev_home(box, "copies-first-setup", text)
    person.answers[ELSEWHERE_YES] = ""
    returned = check_copies(box, home, first_setup=True)
    out = capsys.readouterr().out
    assert returned == 0, out
    assert any(re.search(ELSEWHERE_YES, asked) for asked in person.asked), person.asked
    assert (home / "dev-home.json").read_text(encoding="utf-8") == text
    assert git("-C", str(remote), "log", "-1", "--format=%s") == ["test: dev-home"]


@pytest.mark.parametrize(("retired", "several"), [("y", False), ("n", True)])
def test_a_first_setup_that_says_one_copy_asks_whether_the_others_are_retired(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str], retired: str, several: bool
) -> None:
    # Such as a new PC that replaces one being retired.
    text = '{"schemaVersion": 1, "multiMachine": true}\n'
    home, remote = own_dev_home(box, f"copies-replacing-{retired}", text)
    person.answers.update({ELSEWHERE_YES: "n", RETIRED: retired, SAVE_COPIES: "y"})
    returned = check_copies(box, home, first_setup=True)
    out = capsys.readouterr().out
    assert returned == 0, out
    saved = json.loads((home / "dev-home.json").read_text(encoding="utf-8"))
    assert saved["multiMachine"] is several, saved
    subjects = git("-C", str(remote), "log", "-1", "--format=%s")
    assert subjects == ["test: dev-home" if several else "dev-home: one active copy"], subjects


def test_a_dev_home_this_run_created_is_asked_nothing_even_on_a_first_setup(
    box: Sandbox, person: Person
) -> None:
    # Nothing else can be using a dev-home that was just created.
    text = '{"schemaVersion": 1, "multiMachine": false}\n'
    home, _ = own_dev_home(box, "copies-created", text)
    assert check_copies(box, home, first_setup=True, created=True) == 0
    assert person.asked == []


def test_a_dev_home_json_that_changes_after_its_change_is_shown_is_left_as_it_is(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Such as a sync bringing in another copy's answer while setup's questions wait.
    home, remote = own_dev_home(box, "copies-changed-meanwhile", None)
    path = home / "dev-home.json"
    meanwhile = '{"schemaVersion": 1, "multiMachine": false}\n'

    def yes_after_a_sync(prompt: str) -> str:
        write_text(path, meanwhile)
        return "y"

    person.answers.update({ELSEWHERE: "y", SAVE_COPIES: yes_after_a_sync})
    returned = check_copies(box, home)
    out = capsys.readouterr().out
    assert returned == 1, out
    pattern = r"^PROBLEM\s+.*dev-home\.json changed after setup showed its change"
    assert re.search(pattern, out, re.M), out
    assert path.read_text(encoding="utf-8") == meanwhile
    assert git("-C", str(remote), "log", "-1", "--format=%s") == ["test: dev-home"]


def test_an_older_dev_home_json_is_asked_again_and_rewritten_in_place(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Its old answer is the default, so Enter keeps it, and git has the old file.
    home, remote = own_dev_home(box, "copies-older", '{"multiMachine": false, "x": 1}\n')
    person.answers.update({ELSEWHERE_NO: "", SAVE_COPIES: "y"})
    returned = check_copies(box, home)
    out = capsys.readouterr().out
    assert returned == 0, out
    saved = json.loads((home / "dev-home.json").read_text(encoding="utf-8"))
    assert saved == {"schemaVersion": 1, "multiMachine": False, "x": 1}, saved
    assert sorted(entry.name for entry in home.glob("dev-home.json*")) == ["dev-home.json"]
    assert git("-C", str(remote), "log", "-1", "--format=%s") == ["dev-home: one active copy"]


@pytest.mark.parametrize(
    ("text", "said"),
    [
        (
            '{"multiMachine": false}\n',
            r"is in an older layout, without a schemaVersion, so each sync checks GitHub every "
            r"time\. Run .*setup\.py in a terminal: it asks its question again",
        ),
        (
            '{"schemaVersion": 2, "multiMachine": false}\n',
            r"has a schemaVersion this dev-home-tools doesn't know, perhaps written by a newer "
            r"one on another copy, so setup left it alone",
        ),
    ],
    ids=["older layout", "newer layout"],
)
def test_a_quiet_run_leaves_a_dev_home_json_in_another_layout_alone(
    box: Sandbox, capsys: pytest.CaptureFixture[str], text: str, said: str
) -> None:
    name = "copies-quiet-" + ("older" if "schemaVersion" not in text else "newer")
    home, _ = own_dev_home(box, name, text)
    returned = check_copies(box, home, quiet=True)
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(rf"^PROBLEM\s+.*{said}", out, re.M), out
    assert (home / "dev-home.json").read_text(encoding="utf-8") == text


@pytest.mark.skipif(sys.platform != "win32", reason="only Windows refuses to replace an open file")
def test_a_copies_answer_that_cant_be_saved_leaves_dev_home_as_it_is(
    box: Sandbox,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(shared_module(box, "settings_files"), "REPLACE_WAIT_SECONDS", 0.2)
    text = '{"schemaVersion": 1, "multiMachine": false}\n'
    home, remote = own_dev_home(box, "copies-held-open", text)
    path = home / "dev-home.json"
    before = path.read_bytes()
    person.answers.update({ELSEWHERE_NO: "y", SAVE_COPIES: "y"})
    with path.open("rb"):
        returned = check_copies(box, home, cloned=True)
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(r"^PROBLEM\s+Could not write .*dev-home\.json\. ", out, re.M), out
    assert path.read_bytes() == before
    assert sorted(entry.name for entry in home.glob("dev-home.json*")) == ["dev-home.json"]
    assert git("-C", str(remote), "log", "-1", "--format=%s") == ["test: dev-home"]


# --configure's menu at a console.

MENU = r"^Number to change, 'a' to go through them all, or Enter to go on: $"
UPDATE_HOURS = r"^Check GitHub for dev-home-tools updates every how many hours .*\[24\]: $"
CONTENT_HOURS = r"^Check GitHub for dev-home's changes every how many hours .*\[12\]: $"


@pytest.fixture
def backups_removed(settings: Path) -> Iterator[Path]:
    yield settings
    for backup in settings.parent.glob("local-settings.json.bak-*"):
        backup.unlink()


def test_the_menu_changes_the_setting_picked_and_keeps_a_backup(
    box: Sandbox, backups_removed: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    person.answers.update({MENU: ["9", "2", ""], UPDATES: "y"})
    returned = setup_here(box, "--configure")
    out = capsys.readouterr().out
    assert returned == 0, out
    assert "dev-home-tools settings" in out and "Shared by every copy of dev-home" in out, out
    assert "Type a number from 1 to 7, or 'a', or press Enter to go on." in out, out
    saved = json.loads(backups_removed.read_text(encoding="utf-8"))
    assert saved["updates"]["installAutomatically"] is True, saved
    assert re.search(r"^SET\s+This PC's settings: .* Backup of the old file: ", out, re.M), out


def test_the_menu_goes_through_every_setting_with_its_answer_as_the_default(
    box: Sandbox, backups_removed: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Enter keeps each answer, except the update check's hours, set to 6.
    content = json.loads(backups_removed.read_text(encoding="utf-8"))["devHome"]["folder"]
    person.answers.update(
        {
            MENU: ["a", ""],
            r"^Your dev-home folder \[.*\]: $": "",
            UPDATES: "",
            UPDATE_HOURS: ["six", "6"],
            CONTENT_HOURS: "",
            folder_question(box.profile / ".claude"): "",
            CODEX: "",
            ELSEWHERE_YES: "",
        }
    )
    returned = setup_here(box, "--configure")
    out = capsys.readouterr().out
    saved = json.loads(backups_removed.read_text(encoding="utf-8"))
    assert returned == 0, out
    assert "Type a whole number of hours: 0 or more." in out, out
    assert saved["updates"]["checkEveryHours"] == 6, saved
    assert "checkEveryHours" not in saved["devHome"], saved
    assert saved["devHome"]["folder"] == content, saved
    assert saved["updates"]["installAutomatically"] is False, saved
    assert saved["claudeCode"]["folders"] == {"~/.claude": {"setUp": True}}, saved
    assert saved["codex"] == {"homes": {"~/.codex": {"setUp": True}}}, saved
    assert any(re.search(folder_question(box.profile / ".claude"), p) for p in person.asked)
    assert any(re.search(CODEX, p) for p in person.asked), person.asked


def test_the_menu_answers_codex_once_for_every_home(
    box: Sandbox, backups_removed: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # A home that's gone is offered for removal first, as a Claude Code folder is.
    gone = box.profile / ".codex-gone"
    with profile_kept(box):
        start = json.loads(backups_removed.read_text(encoding="utf-8"))
        start["codex"]["homes"]["~/.codex-gone"] = {"setUp": True}
        write_text(backups_removed, json.dumps(start, indent=2) + "\n")
        remove = rf"^{re.escape(str(gone))} no longer exists\. Remove it from the settings\? "
        remove += r"\[y/N\]: $"
        person.answers.update({MENU: ["6", ""], remove: "y", CODEX: "n"})
        returned = setup_here(box, "--configure")
        out = capsys.readouterr().out
        saved = json.loads(backups_removed.read_text(encoding="utf-8"))
    assert returned == 0, out
    row = r"^\s+6\s+Codex homes to set up\s+~/\.codex: yes, ~/\.codex-gone: yes \(not found\)$"
    assert re.search(row, out, re.M), out
    asked = [p for p in person.asked if re.search(remove, p) or re.search(CODEX, p)]
    assert len(asked) == 2 and re.search(remove, asked[0]), person.asked
    assert saved["codex"] == {"homes": {"~/.codex": {"setUp": False}}}, saved


def test_no_answer_about_codex_leaves_every_home_as_it_is(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Such as a console closed at the question: nothing is saved, so the next run asks again.
    unanswered = json.loads(settings.read_text(encoding="utf-8"))
    del unanswered["codex"]
    write_text(settings, json.dumps(unanswered, indent=2) + "\n")
    person.answers[MENU] = ""
    returned = setup_here(box)
    out = capsys.readouterr().out
    saved = json.loads(settings.read_text(encoding="utf-8"))
    assert returned == 1, out
    assert any(re.search(CODEX, asked) for asked in person.asked), person.asked
    pattern = (
        r"^PROBLEM\s+No answer came about Codex, so setup left it as it is\. Run setup\.py again "
        r"to answer\.$"
    )
    assert re.search(pattern, out, re.M), out
    assert "codex" not in saved, saved


def test_the_menu_says_when_setup_finds_no_codex_home(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # A profile Codex has never run in, with no home listed, has nothing to ask about.
    profile = box.root / "no-codex-profile"
    profile.mkdir()
    other = json.loads(settings.read_text(encoding="utf-8"))
    del other["codex"]
    other["testHomeDir"] = profile.as_posix()
    write_text(settings, json.dumps(other, indent=2) + "\n")
    person.answers[MENU] = ["6", ""]
    try:
        returned = setup_here(box, "--configure")
        out = capsys.readouterr().out
    finally:
        shutil.rmtree(profile)
    assert returned == 0, out
    assert re.search(r"^\s+6\s+Codex homes to set up\s+none found$", out, re.M), out
    assert re.search(r"^Setup found no Codex homes\.$", out, re.M), out
    assert not any(re.search(CODEX, asked) for asked in person.asked), person.asked


def test_a_no_in_the_menu_replaces_the_answer_a_new_codex_home_got_from_the_main_one(
    box: Sandbox, backups_removed: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # So the line saying the new home was set up to match never shows.
    work = box.profile / ".codex-work"
    write_text(work / "config.toml", (box.profile / ".codex" / "config.toml").read_text("utf-8"))
    person.answers.update({MENU: ["6", ""], CODEX: "n"})
    with profile_kept(box):
        try:
            returned = setup_here(box, "--configure")
            out = capsys.readouterr().out
            saved = json.loads(backups_removed.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(work)
    assert returned == 0, out
    assert "dev-home is now" not in out, out
    assert saved["codex"] == {
        "homes": {"~/.codex": {"setUp": False}, "~/.codex-work": {"setUp": False}}
    }, saved


def test_enter_in_the_menu_keeps_a_setting_that_follows_its_default(
    box: Sandbox, backups_removed: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Pinning the default's value would stop it following a later change of default.
    following = {"$state": "default"}
    saved = json.loads(backups_removed.read_text(encoding="utf-8"))
    saved["updates"] = {"installAutomatically": following, "checkEveryHours": following}
    write_text(backups_removed, json.dumps(saved, indent=2) + "\n")
    person.answers.update(
        {
            MENU: ["a", ""],
            r"^Your dev-home folder \[.*\]: $": "",
            UPDATES: "",
            UPDATE_HOURS: "",
            CONTENT_HOURS: "",
            ELSEWHERE_YES: "",
        }
    )
    returned = setup_here(box, "--configure")
    out = capsys.readouterr().out
    kept = json.loads(backups_removed.read_text(encoding="utf-8"))
    assert returned == 0, out
    assert kept["updates"] == {"installAutomatically": following, "checkEveryHours": following}
    assert "checkEveryHours" not in kept["devHome"], kept


def test_the_menu_keeps_several_copies_unless_the_others_are_retired(
    box: Sandbox, settings: Path, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    person.answers.update(
        {
            MENU: ["7", ""],
            ELSEWHERE_YES: "n",
            RETIRED: "n",
        }
    )
    head = git("-C", str(box.remote), "rev-parse", "main")
    returned = setup_here(box, "--configure")
    out = capsys.readouterr().out
    assert returned == 0, out
    assert "dev-home stays set to several copies." in out, out
    assert git("-C", str(box.remote), "rev-parse", "main") == head


def test_a_run_by_hand_makes_a_folders_settings_change_without_asking(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # The yes to setting up the folder approved it.
    path = box.profile / ".claude" / "settings.json"
    before = path.read_bytes()
    write_text(path, '{\n  "model": "x"\n}\n')
    try:
        returned = setup_here(box)
        out = capsys.readouterr().out
        changed = json.loads(path.read_text(encoding="utf-8"))
        backups = sorted(path.parent.glob("settings.json.bak-*"))
        backup_text = backups[0].read_text(encoding="utf-8") if backups else ""
    finally:
        path.write_bytes(before)
        for backup in path.parent.glob("settings.json.bak-*"):
            backup.unlink()
    assert returned == 0, out
    assert not any(re.search(r"change\?", asked) for asked in person.asked), person.asked
    assert changed["model"] == "x"
    assert len(changed["permissions"]["additionalDirectories"]) == 2
    assert backup_text == '{\n  "model": "x"\n}\n'
    pattern = (
        r"^SET\s+Claude Code settings in \.claude: added dev-home and dev-home-tools to "
        r"permissions\.additionalDirectories in .*settings\.json\. Backup of the old file: "
    )
    assert re.search(pattern, out, re.M), out


def test_a_run_by_hand_makes_a_codex_homes_config_change_in_its_toml(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    path = box.profile / ".codex" / "config.toml"
    before = path.read_bytes()
    write_text(path, 'model = "x"\n')
    try:
        returned = setup_here(box)
        out = capsys.readouterr().out
        changed = path.read_text(encoding="utf-8")
    finally:
        path.write_bytes(before)
        for backup in path.parent.glob("config.toml.bak-*"):
            backup.unlink()
    assert returned == 0, out
    assert changed.startswith('model = "x"\nproject_doc_max_bytes = 65536\n'), changed
    assert f"writable_roots = ['{box.content}']" in changed, changed
    pattern = (
        r"^SET\s+Codex config in \.codex: added dev-home to writable_roots, and "
        r"project_doc_max_bytes, in .*config\.toml\. Backup of the old file: "
    )
    assert re.search(pattern, out, re.M), out


def test_a_file_that_changes_after_its_change_is_planned_is_left_alone(
    box: Sandbox,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Such as Claude Code saving it at that moment: the next run plans the change again.
    path = box.profile / ".claude" / "settings.json"
    before = path.read_bytes()
    write_text(path, "{}\n")
    code = shared_module(box, "setup")
    reading = code.read_settings_file

    def edited_first(file: Path) -> Any:
        write_text(path, '{"model": "z"}\n')
        return reading(file)

    monkeypatch.setattr(code, "read_settings_file", edited_first)
    try:
        returned = setup_here(box)
        out = capsys.readouterr().out
        kept = path.read_text(encoding="utf-8")
        backups = list(path.parent.glob("settings.json.bak-*"))
    finally:
        path.write_bytes(before)
    assert returned == 1, out
    assert kept == '{"model": "z"}\n'
    assert backups == []
    pattern = (
        r"^PROBLEM\s+Claude Code settings in \.claude: could not write .* The file changed while "
        r"setup was planning its change, so it was left alone\. The next run makes the change\.$"
    )
    assert re.search(pattern, out, re.M), out


# Another run saving this PC's settings while this one asks its questions or waits for the lock.

# What setup saves for a skill new to the PC: no answer yet about adding it to the agents.
UNANSWERED = {"addedToAgents": {"$state": "unanswered"}}
# The update check this run's own answer sets, by hand in the menu or through --configure.
OWN_HOURS = 7
WAYS = ("quiet", "by hand", "configure")
# Where setup links the skills in the sandbox's profile: for Claude Code, and for Codex.
SKILLS_FOLDERS = (Path(".claude") / "skills", Path(".agents") / "skills")


def edit(settings: Path, change: Callable[[dict[str, Any]], object]) -> None:
    data = json.loads(settings.read_text(encoding="utf-8"))
    change(data)
    write_text(settings, json.dumps(data, indent=2) + "\n")


def before_the_work(
    box: Sandbox, monkeypatch: pytest.MonkeyPatch, meanwhile: Callable[[], object]
) -> None:
    """Runs meanwhile just before this run takes the sync's lock for its work, as another run, such
    as a sync or --configure in another session, can save this PC's settings while this run asks
    its questions or waits for the lock."""
    code = shared_module(box, "setup")
    taking = code.Setup.work_lock

    @contextlib.contextmanager
    def another_run_first(run: Any, content_root: Path) -> Iterator[bool]:
        meanwhile()
        with taking(run, content_root) as owned:
            yield owned

    monkeypatch.setattr(code.Setup, "work_lock", another_run_first)


def saved_meanwhile(
    box: Sandbox, monkeypatch: pytest.MonkeyPatch, change: Callable[[dict[str, Any]], object]
) -> None:
    """Has another run save this PC's settings with change made (see before_the_work)."""
    before_the_work(box, monkeypatch, lambda: edit(box.tools / "local-settings.json", change))


def run_as(box: Sandbox, person: Person, how: str) -> int:
    """Runs setup in one of the WAYS a run can wait while another saves: quiet, as an agent runs
    it, which takes the sync's lock only for its work, unlike a sync's own setup; by hand at the
    console, changing the update check in the menu; or --configure, changing it, as an agent does.
    The last two set it to OWN_HOURS."""
    if how == "quiet":
        return setup_here(box, "--quiet")
    if how == "configure":
        return setup_here(box, "--configure", f"updates.checkEveryHours={OWN_HOURS}")
    person.answers.update({MENU: ["3", ""], UPDATE_HOURS: str(OWN_HOURS)})
    return setup_here(box)


def own_answer(how: str) -> int | None:
    """The update check a run leaves: OWN_HOURS, unless it's a quiet run, which answers nothing."""
    return None if how == "quiet" else OWN_HOURS


@pytest.mark.parametrize("how", WAYS)
def test_an_answer_saved_meanwhile_stays_and_the_work_follows_it(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    how: str,
) -> None:
    # Such as a no to a skill new to this PC, given through --configure in another session: this
    # run found the skill with no answer, but its mark never replaces the answer, the NEW line
    # doesn't name it, and its links go, as the no says.
    edit(settings, lambda data: data["skills"].pop("mine"))

    def answered(data: dict[str, Any]) -> None:
        data["skills"]["mine"] = {"addedToAgents": False}
        data["devHome"]["checkEveryHours"] = 6

    saved_meanwhile(box, monkeypatch, answered)
    with profile_kept(box):
        returned = run_as(box, person, how)
        out = capsys.readouterr().out
        saved = json.loads(settings.read_text(encoding="utf-8"))
        links = [link_target(box.profile / skills / "mine") for skills in SKILLS_FOLDERS]
    assert returned == 0, out
    assert saved["skills"]["mine"] == {"addedToAgents": False}, saved
    assert saved["devHome"]["checkEveryHours"] == 6, saved
    assert saved["updates"].get("checkEveryHours") == own_answer(how), saved
    assert not re.search(r"^NEW\s.*'mine'", out, re.M), out
    assert links == [None, None], out


@pytest.mark.parametrize("how", WAYS)
def test_a_skill_another_run_named_meanwhile_isnt_named_again(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    how: str,
) -> None:
    # Such as a sync's setup while this run asked its questions: it saved the skill as new to this
    # PC, and its NEW line named it.
    edit(settings, lambda data: data["skills"].pop("mine"))
    saved_meanwhile(box, monkeypatch, lambda data: data["skills"].update(mine=UNANSWERED))
    returned = run_as(box, person, how)
    out = capsys.readouterr().out
    saved = json.loads(settings.read_text(encoding="utf-8"))
    assert returned == 0, out
    assert saved["skills"]["mine"] == UNANSWERED, saved
    assert saved["updates"].get("checkEveryHours") == own_answer(how), saved
    assert not re.search(r"^NEW\s", out, re.M), out


@pytest.mark.parametrize("how", WAYS)
def test_codex_turned_off_meanwhile_turns_off_a_home_found_since(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    how: str,
) -> None:
    # Such as a no to Codex through --configure in another session, while this run gave a home it
    # found the main home's yes: every home gets the no, so they still share one answer, and none
    # is set up.
    second = box.profile / ".codex-second"
    write_text(second / "config.toml", "")
    off = {"homes": {"~/.codex": {"setUp": False}}}
    saved_meanwhile(box, monkeypatch, lambda data: data.update(codex=off))
    with profile_kept(box):
        try:
            returned = run_as(box, person, how)
            out = capsys.readouterr().out
            saved = json.loads(settings.read_text(encoding="utf-8"))
            set_up = (second / "AGENTS.md").exists()
        finally:
            shutil.rmtree(second)
    assert returned == 0, out
    homes = {"~/.codex": {"setUp": False}, "~/.codex-second": {"setUp": False}}
    assert saved["codex"] == {"homes": homes}, saved
    assert saved["updates"].get("checkEveryHours") == own_answer(how), saved
    assert not set_up, out
    pattern = (
        r"^SET\s+dev-home is now turned off for Codex in ~/\.codex-second, to match ~/\.codex\."
    )
    assert re.search(pattern, out, re.M), out


@pytest.mark.parametrize("how", WAYS)
def test_a_rename_another_run_made_meanwhile_keeps_the_answer_it_saved(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    how: str,
) -> None:
    # Such as a skill renamed from former to renamed: this run moved former's no to the new name,
    # and --configure in another session moved it too, then said yes. The yes stays, the skill is
    # added, and the file names it once, by its new name.
    folder = box.content / "skills" / "renamed"
    write_text(folder / "SKILL.md", "---\nname: renamed\ndescription: A test skill.\n---\n")
    write_text(folder / "dev-home-skill.json", json.dumps({"formerNames": ["former"]}) + "\n")
    edit(settings, lambda data: data["skills"].update(former={"addedToAgents": False}))

    def moved_then_yes(data: dict[str, Any]) -> None:
        data["skills"].pop("former")
        data["skills"]["renamed"] = {"addedToAgents": True}

    saved_meanwhile(box, monkeypatch, moved_then_yes)
    try:
        returned = run_as(box, person, how)
        out = capsys.readouterr().out
        saved = json.loads(settings.read_text(encoding="utf-8"))
        links = [link_target(box.profile / skills / "renamed") for skills in SKILLS_FOLDERS]
    finally:
        for skills in SKILLS_FOLDERS:
            if link_target(box.profile / skills / "renamed") is not None:
                remove_link(box.profile / skills / "renamed")
        shutil.rmtree(folder)
    assert returned == 0, out
    assert saved["skills"]["renamed"] == {"addedToAgents": True}, saved
    assert "former" not in saved["skills"], saved
    assert saved["updates"].get("checkEveryHours") == own_answer(how), saved
    assert links == [folder, folder], out
    assert "skills.former" not in out, out
    assert not re.search(r"^NEW\s", out, re.M), out


@pytest.mark.parametrize("how", WAYS)
def test_a_setting_declared_and_answered_meanwhile_stays(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    how: str,
) -> None:
    # Such as a preference a sync brought in a skill's update, which --configure in another
    # session then answered, or a setting of dev-home-tools' own that an update brought: this run
    # read what's declared before, so it doesn't know them, and leaves them to the runs that do.
    declared = box.content / "skills" / "mine" / "dev-home-skill.json"
    preference = {"default": True, "label": "Tidy output"}

    def declared_and_answered() -> None:
        write_text(declared, json.dumps({"preferences": {"tidy": preference}}) + "\n")

        def answered(data: dict[str, Any]) -> None:
            data["skills"]["mine"]["preferences"] = {"tidy": False}
            data["updates"]["fromAnUpdate"] = 5

        edit(settings, answered)

    before_the_work(box, monkeypatch, declared_and_answered)
    try:
        returned = run_as(box, person, how)
        out = capsys.readouterr().out
        saved = json.loads(settings.read_text(encoding="utf-8"))
    finally:
        declared.unlink()
    assert returned == 0, out
    assert saved["skills"]["mine"]["preferences"] == {"tidy": False}, saved
    assert saved["updates"]["fromAnUpdate"] == 5, saved
    assert saved["updates"].get("checkEveryHours") == own_answer(how), saved
    assert "Removed" not in out, out


def test_a_value_of_the_wrong_kind_saved_meanwhile_is_reported(
    box: Sandbox,
    settings: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Such as from a hand edit while this run waited for the lock: the work acts on the file as it
    # is by then, so it says what that value counts as.
    saved_meanwhile(box, monkeypatch, lambda data: data["devHome"].update(checkEveryHours="6"))
    returned = setup_here(box, "--quiet")
    out = capsys.readouterr().out
    assert returned == 1, out
    pattern = (
        r'^PROBLEM\s+devHome\.checkEveryHours in local-settings\.json is "6", which isn\'t a whole '
        r"number of hours, 0 or more, so it counts as every 12 hours\. Fix it there\.$"
    )
    assert len(re.findall(pattern, out, re.M)) == 1, out


@pytest.mark.parametrize(
    ("text", "said"),
    [
        ("{not json\n", "and can't be read now. Fix it, then run setup.py again."),
        ('{"schemaVersion": 99}\n', "to a layout this setup doesn't know. Run setup.py again."),
    ],
)
def test_settings_changed_meanwhile_to_what_setup_cant_read_are_left_as_they_are(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    text: str,
    said: str,
) -> None:
    # Such as a hand edit, or a newer dev-home-tools, while this run waited at a question: its
    # answer isn't saved, and the file stays as it is.
    before_the_work(box, monkeypatch, lambda: write_text(settings, text))
    returned = run_as(box, person, "by hand")
    out = capsys.readouterr().out
    assert returned == 1, out
    pattern = (
        r"^PROBLEM\s+This PC's settings weren't saved: .*local-settings\.json changed while setup "
        rf"ran, {re.escape(said)}$"
    )
    assert re.search(pattern, out, re.M), out
    assert settings.read_text(encoding="utf-8") == text


def test_a_syncs_setup_reads_this_pcs_settings_only_once(
    box: Sandbox,
    settings: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # It holds the sync's lock from its start, so no other run can have saved them since, and a
    # second read would only add time.
    code = shared_module(box, "setup")
    loading = code.load_local_settings
    reads: list[None] = []

    def counted() -> Any:
        reads.append(None)
        return loading()

    edit(settings, lambda data: data["skills"].pop("mine"))
    monkeypatch.setattr(code, "load_local_settings", counted)
    returned = code.main(["--quiet"], sync_holds_lock=True)
    out = capsys.readouterr().out
    saved = json.loads(settings.read_text(encoding="utf-8"))
    assert returned == 0, out
    assert len(reads) == 1, reads
    assert saved["skills"]["mine"] == UNANSWERED, saved
    assert re.search(r"^NEW\s.*'mine'", out, re.M), out


def test_stops_when_it_cant_find_the_home_folder(
    box: Sandbox, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # The sync runs setup inside its own process, so even this must be a line, not an error.
    def no_home() -> Path:
        raise RuntimeError("Could not determine home directory.")

    monkeypatch.setattr(Path, "home", no_home)
    returned = setup_here(box, "--quiet")
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(r"^PROBLEM\s+setup\.py stopped: RuntimeError: Could not", out, re.M), out


def test_never_raises_even_when_its_lines_cant_be_printed(
    box: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    def closed(*args: object) -> None:
        raise OSError("the output is closed")

    monkeypatch.setattr(shared_module(box, "setup"), "status_line", closed)
    assert setup_here(box, "--quiet") == 1


# A missing dev-home folder: clone, create, or stop. gh is faked.

CHOICE = r"create a new private one \(n\), or stop here \(s\)\? \[s\]: $"
REPO_NAME = r"^Your dev-home repo on GitHub: .*\[dev-home\]: $"
NEW_NAME = r"^Name for the new private repo on GitHub \[dev-home\]: $"


@pytest.mark.parametrize(
    "answers",
    [{CHOICE: "s"}, {}, {CHOICE: "c"}, {CHOICE: "n"}],
    ids=["stop", "no answer", "no repo name to clone", "no repo name to create"],
)
def test_stops_without_an_answer_to_go_on(
    box: Sandbox,
    settings: Path,
    person: Person,
    fake_gh: FakeGh,
    capsys: pytest.CaptureFixture[str],
    answers: dict[str, str],
) -> None:
    person.answers.update(answers)
    missing = box.root / "not-yet-dev-home"
    returned = setup_here(box, "--content-dir", str(missing))
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(r"^PROBLEM\s+Stopped: there is no dev-home at ", out, re.M), out
    assert fake_gh.calls == [("auth", "status")], fake_gh.calls
    assert not (missing / ".git").exists()


@pytest.mark.parametrize(
    ("trouble", "problem"),
    [
        ("no gh", r"needs the GitHub CLI \(gh\)"),
        ("signed out", r"the GitHub CLI is not signed in"),
        ("clone fails", r"Could not clone dev-home\. gh: gh: repo clone failed on purpose"),
    ],
)
def test_says_what_stopped_a_clone(
    box: Sandbox,
    settings: Path,
    person: Person,
    fake_gh: FakeGh,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    trouble: str,
    problem: str,
) -> None:
    if trouble == "no gh":
        monkeypatch.setattr(shared_module(box, "setup"), "find_program", lambda name: None)
    elif trouble == "signed out":
        fake_gh.failing = ("auth", "status")
    else:
        fake_gh.failing = ("repo", "clone")
    person.answers.update({CHOICE: "c", REPO_NAME: ""})
    missing = box.root / "not-yet-dev-home"
    before = settings.read_bytes()
    returned = setup_here(box, "--content-dir", str(missing))
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(rf"^PROBLEM\s+.*{problem}", out, re.M), out
    assert not (missing / ".git").exists()
    # Nothing is saved before dev-home is in place, so the next run offers to clone it again.
    assert settings.read_bytes() == before


def test_a_clone_that_isnt_a_dev_home_gets_no_git_config(
    box: Sandbox,
    settings: Path,
    person: Person,
    fake_gh: FakeGh,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Such as a project's repo, named by mistake at the clone question.
    source = box.root / "a-project.git"
    git("init", "--quiet", "--bare", "-b", "main", str(source))
    work = box.root / "a-project-work"
    git("clone", "--quiet", str(source), str(work))
    write_text(work / "README.md", "# a project\n")
    git("-C", str(work), "add", "--all")
    git("-C", str(work), "commit", "--quiet", "-m", "test: project")
    git("-C", str(work), "push", "--quiet", "origin", "main")
    fake_gh.clone_from = source
    person.answers.update({CHOICE: "c", REPO_NAME: "a-project"})
    cloned = box.root / "wrong-clone"
    returned = setup_here(box, "--content-dir", str(cloned))
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(r"^PROBLEM\s+.*wrong-clone doesn't look like a dev-home", out, re.M), out
    assert "gpgsign" not in (cloned / ".git" / "config").read_text(encoding="utf-8")


def test_a_git_step_that_fails_while_creating_says_which(
    box: Sandbox,
    settings: Path,
    person: Person,
    fake_gh: FakeGh,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # git with no name or email to commit with, as on a new PC.
    empty = box.root / "empty-gitconfig"
    write_text(empty, "")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "user.useConfigOnly")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    for name in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("EMAIL", raising=False)
    person.answers.update({CHOICE: "n", NEW_NAME: ""})
    half_made = box.root / "half-made-dev-home"
    returned = setup_here(box, "--content-dir", str(half_made))
    out = capsys.readouterr().out
    assert returned == 1, out
    pattern = r"^PROBLEM\s+Could not set up the repo in .*: git commit failed\. git: \S"
    assert re.search(pattern, out, re.M), out
    assert not any(call[:2] == ("repo", "create") for call in fake_gh.calls), fake_gh.calls
    # Then it says what that left, and how to start over.
    assert re.search(r"^PROBLEM\s+.* is a git repo with no commits", out, re.M), out


# Last in this file: these leave the profile's generated files built from another dev-home.


def test_clones_an_existing_dev_home(
    box: Sandbox,
    settings: Path,
    person: Person,
    fake_gh: FakeGh,
    capsys: pytest.CaptureFixture[str],
) -> None:
    person.answers.update({CHOICE: "c", REPO_NAME: ""})
    cloned = box.root / "cloned-dev-home"
    setup_here(box, "--content-dir", str(cloned))
    out = capsys.readouterr().out
    assert ("repo", "clone", "dev-home", str(cloned)) in fake_gh.calls, fake_gh.calls
    assert re.search(r"^CREATED\s+Cloned dev-home into ", out, re.M), out
    assert (cloned / "skills" / "mine" / "SKILL.md").is_file()


def test_a_new_dev_home_github_refuses_is_kept_with_the_command_to_finish(
    box: Sandbox,
    settings: Path,
    person: Person,
    fake_gh: FakeGh,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_gh.failing = ("repo", "create")
    person.answers.update({CHOICE: "n", NEW_NAME: "taken"})
    new_home = box.root / "not-on-github-dev-home"
    returned = setup_here(box, "--content-dir", str(new_home))
    out = capsys.readouterr().out
    assert returned == 1, out
    pattern = (
        r"^PROBLEM\s+Created dev-home in .*, but not on GitHub\. gh: gh: repo create failed on "
        r"purpose\. Once that is fixed, run: gh repo create taken --private --source "
    )
    assert re.search(pattern, out, re.M), out
    assert git("-C", str(new_home), "log", "-1", "--format=%s") == ["starter: new dev-home"]


def test_creates_a_new_dev_home_from_the_starter(
    box: Sandbox,
    settings: Path,
    person: Person,
    fake_gh: FakeGh,
    capsys: pytest.CaptureFixture[str],
) -> None:
    person.answers.update({CHOICE: "n", NEW_NAME: "my-dev-home"})
    new_home = box.root / "new-dev-home"
    returned = setup_here(box, "--content-dir", str(new_home))
    out = capsys.readouterr().out
    agents = (new_home / "AGENTS.md").read_text(encoding="utf-8")
    subject = git("-C", str(new_home), "log", "-1", "--format=%s")
    signing = git("-C", str(new_home), "config", "--local", "--get", "commit.gpgsign")
    tools = str(box.tools).replace("\\", "/")
    assert re.search(r"^CREATED\s+New private repo my-dev-home on GitHub", out, re.M), out
    assert f"{tools}/sync.py" in agents
    assert subject == ["starter: new dev-home"]
    assert signing == ["false"]
    # A new dev-home starts with one active copy, without a question.
    assert json.loads((new_home / "dev-home.json").read_text(encoding="utf-8")) == {
        "schemaVersion": 1,
        "multiMachine": False,
    }
    copies = (ELSEWHERE, ELSEWHERE_YES, ELSEWHERE_NO)
    assert not any(re.search(p, asked) for p in copies for asked in person.asked), person.asked
    create = ("repo", "create", "my-dev-home", "--private", "--source", str(new_home))
    assert any(call[: len(create)] == create for call in fake_gh.calls), fake_gh.calls
    # The only problems left come from the sandbox's other dev-home: links to it, which setup
    # leaves alone, and settings changes for the new one, which nobody answers here.
    problems = [line for line in out.splitlines() if line.startswith("PROBLEM")]
    assert returned == 1 and problems, out
    assert all(re.search(r"Left alone|left unchanged", line) for line in problems), out
