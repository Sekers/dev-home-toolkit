"""What setup asks a person, and what it does with the answers.

These run setup's code inside this process, from the sandbox's copy, with a small fake for the
person at the console, since a test can't type into a real one; gh is faked too where a test
would reach GitHub. Git and the files stay real. The other tests here run setup.py as a process
with no console, to check that it then never waits for an answer.
"""

import json
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from helpers import (
    Sandbox,
    check_in_sandbox,
    git,
    link_target,
    remove_link,
    run_python,
    sandbox_for,
    script_env,
    shared_module,
    write_text,
)

pytestmark = pytest.mark.xdist_group("setup-questions")

# The question about installing updates, whatever Enter gives.
UPDATES = r"^Pull updates automatically\? y, n, or d for the default \(yes\) \[[yY]/[nN]/[dD]\]: $"


@pytest.fixture(scope="module")
def box(request: pytest.FixtureRequest) -> Iterator[Sandbox]:
    yield from sandbox_for(request, "setup-questions")


class Person:
    """Answers questions at the console: the answer whose pattern the question matches, or the
    next of a list of them, one each time it's asked. A question with no answer ends the input,
    as when a person closes the console."""

    def __init__(self, answers: dict[str, str | list[str]]) -> None:
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


def test_a_first_run_asks_about_updates_and_each_claude_folder(
    box: Sandbox,
    settings: Path,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A first run has no local-settings.json yet. Here it must keep testHomeDir, so the run gets
    # settings with no answers instead.
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
    person.answers.update(
        {
            UPDATES: "y",
            r"\.claude-second, for another Claude account\? \[y/N\]: $": "yes",
            r"\.claude-third, for another Claude account\? \[y/N\]: $": "n",
            # A yes to the settings change the new folder needs.
            r"Make this change\? \[y/N\]: $": "y",
        }
    )
    try:
        returned = setup_here(box)
        out = capsys.readouterr().out
        written = json.loads(settings.read_text(encoding="utf-8"))
        allowed = json.loads((second / "settings.json").read_text(encoding="utf-8"))
        linked = link_target(second / "skills" / "handoff")
    finally:
        for folder in (second / "skills", second / "rules"):
            for link in folder.iterdir() if folder.is_dir() else []:
                remove_link(link)
        shutil.rmtree(second)
        shutil.rmtree(third)
    assert returned == 0, out
    assert any(".claude-third, for another Claude account?" in asked for asked in person.asked)
    assert written["updates"]["installAutomatically"] is True
    # The no is kept, so the folder isn't asked about again.
    assert written["claudeCode"]["folders"] == {
        "~/.claude-second": {"setUp": True},
        "~/.claude-third": {"setUp": False},
    }
    assert written["testHomeDir"] == saved["testHomeDir"]
    assert linked == box.generated / "skills" / "handoff"
    assert len(allowed["permissions"]["additionalDirectories"]) == 2
    assert re.search(
        r"^SET\s+Claude Code settings in \.claude-second: changed .* \(new file\)", out, re.M
    ), out


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
    person.answers.update(
        {
            UPDATES: "n",
            r"\.claude-later, for another Claude account\? \[y/N\]: $": "n",
        }
    )
    try:
        returned = setup_here(box)
        written = json.loads(settings.read_text(encoding="utf-8"))
        asked = list(person.asked)
        again = setup_here(box)
        out = capsys.readouterr().out
    finally:
        shutil.rmtree(later)
    assert returned == 0 and again == 0, out
    assert len(asked) == 2, asked
    assert person.asked == asked, person.asked
    assert written["updates"]["installAutomatically"] is False
    assert written["claudeCode"]["folders"] == {"~/.claude-later": {"setUp": False}}


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
    assert ("Type y, n, or d." in out) == isinstance(answer, list), out


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


def test_setup_by_hand_saves_only_once_a_sync_lets_go_of_its_lock(
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
        # A sync runs setup while it holds the lock, so that setup saves without it.
        held = shared_module(box, "setup").main([], sync_holds_lock=True)
    out = capsys.readouterr().out
    saved = json.loads(settings.read_text(encoding="utf-8"))
    assert waited == 1, out
    pattern = r"^PROBLEM\s+This PC's settings weren't saved: a sync, or an update, has been using"
    assert re.search(pattern, out, re.M), out
    assert "installAutomatically" not in unsaved.get("updates", {}), unsaved
    assert held == 0, out
    assert saved["updates"]["installAutomatically"] is True, saved


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
    assert written == {
        "schemaVersion": 1,
        "testHomeDir": saved["testHomeDir"],
        "devHome": {"folder": content},
        "updates": {"installAutomatically": False},
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


# How many copies of dev-home are in active use, asked of a dev-home of the test's own.

ELSEWHERE = r"^Is dev-home in active use anywhere besides this PC, .*\? \[y/n\]: $"
ALONGSIDE = r"^Will another copy stay in use alongside this one, .*\? \[y/n\]: $"
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


def check_copies(box: Sandbox, home: Path, *, cloned: bool = False) -> int:
    """Asks setup's question about copies for one dev-home, and returns setup's exit code."""
    run = shared_module(box, "setup").Setup(quiet=False, what_if=False)
    run.cloned = cloned
    run.check_copies(home)
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
    assert re.search(r"^Type y or n\.$", out, re.M), out
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


@pytest.mark.parametrize(("answer", "several"), [("y", True), ("n", False)])
def test_after_a_clone_set_to_one_copy_asks_whether_another_stays(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str], answer: str, several: bool
) -> None:
    text = '{"schemaVersion": 1, "multiMachine": false, "x": 1}\n'
    home, remote = own_dev_home(box, f"copies-cloned-{answer}", text)
    person.answers.update({ALONGSIDE: answer, SAVE_COPIES: "y"})
    returned = check_copies(box, home, cloned=True)
    out = capsys.readouterr().out
    assert returned == 0, out
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


def test_an_older_dev_home_json_is_asked_again_and_rewritten_in_place(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    # Its old answer is the default, so Enter keeps it, and git has the old file.
    home, remote = own_dev_home(box, "copies-older", '{"multiMachine": false, "x": 1}\n')
    person.answers.update({ELSEWHERE.replace(r"\[y/n\]", r"\[y/N\]"): "", SAVE_COPIES: "y"})
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
    run = shared_module(box, "setup").Setup(quiet=True, what_if=False)
    run.check_copies(home)
    out = capsys.readouterr().out
    assert run.finish() == 1, out
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
    person.answers.update({ALONGSIDE: "y", SAVE_COPIES: "y"})
    with path.open("rb"):
        returned = check_copies(box, home, cloned=True)
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(r"^PROBLEM\s+Could not write .*dev-home\.json\. ", out, re.M), out
    assert path.read_bytes() == before
    assert sorted(entry.name for entry in home.glob("dev-home.json*")) == ["dev-home.json"]
    assert git("-C", str(remote), "log", "-1", "--format=%s") == ["test: dev-home"]


# --configure's menu at a console.

MENU = r"^Number to change, a to go through them all, or Enter to finish: $"
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
    assert "Type a number from 1 to 6, or a, or press Enter to finish." in out, out
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
            ELSEWHERE.replace(r"\[y/n\]", r"\[Y/n\]"): "",
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
    assert "There are no ~/.claude-* folders to set up." in out, out


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
            ELSEWHERE.replace(r"\[y/n\]", r"\[Y/n\]"): "",
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
            MENU: ["6", ""],
            ELSEWHERE.replace(r"\[y/n\]", r"\[Y/n\]"): "n",
            r"^Have all the other copies been retired, .*\? \[y/N\]: $": "n",
        }
    )
    head = git("-C", str(box.remote), "rev-parse", "main")
    returned = setup_here(box, "--configure")
    out = capsys.readouterr().out
    assert returned == 0, out
    assert "dev-home stays set to several copies." in out, out
    assert git("-C", str(box.remote), "rev-parse", "main") == head


def test_a_yes_to_a_settings_change_writes_it_and_keeps_a_backup(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    path = box.profile / ".claude" / "settings.json"
    before = path.read_bytes()
    write_text(path, '{\n  "model": "x"\n}\n')
    person.answers[r"Make this change\? \[y/N\]: $"] = "y"
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
    assert changed["model"] == "x"
    assert len(changed["permissions"]["additionalDirectories"]) == 2
    assert backup_text == '{\n  "model": "x"\n}\n'
    assert re.search(r"^\s+Line \d+:$", out, re.M) and re.search(r"^\s+\+ ", out, re.M), out


def test_a_no_to_a_settings_change_leaves_the_file_and_says_so(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    path = box.profile / ".claude" / "settings.json"
    before = path.read_bytes()
    write_text(path, "{}\n")
    person.answers[r"Make this change\? \[y/N\]: $"] = "n"
    try:
        returned = setup_here(box)
        out = capsys.readouterr().out
        kept = path.read_text(encoding="utf-8")
    finally:
        path.write_bytes(before)
    assert returned == 1, out
    assert kept == "{}\n"
    assert re.search(r"^PROBLEM\s+Claude Code settings in \.claude: left unchanged", out, re.M), out


def test_a_yes_to_a_codex_config_change_writes_its_toml(
    box: Sandbox, person: Person, capsys: pytest.CaptureFixture[str]
) -> None:
    path = box.profile / ".codex" / "config.toml"
    before = path.read_bytes()
    write_text(path, 'model = "x"\n')
    person.answers[r"Make this change\? \[y/N\]: $"] = "y"
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
    assert re.search(r"^SET\s+Codex config: changed .* Backup of the old file: ", out, re.M), out


def test_a_file_that_changes_while_setup_waits_is_left_alone(
    box: Sandbox,
    person: Person,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = box.profile / ".claude" / "settings.json"
    before = path.read_bytes()
    write_text(path, "{}\n")

    def yes_after_an_edit(prompt: str = "") -> str:
        write_text(path, '{"model": "y"}\n')
        return "y"

    monkeypatch.setattr("builtins.input", yes_after_an_edit)
    try:
        returned = setup_here(box)
        out = capsys.readouterr().out
        kept = path.read_text(encoding="utf-8")
        backups = list(path.parent.glob("settings.json.bak-*"))
    finally:
        path.write_bytes(before)
    assert returned == 1, out
    assert kept == '{"model": "y"}\n'
    assert backups == []
    pattern = r"^PROBLEM\s+Claude Code settings in \.claude: could not write .* The file changed"
    assert re.search(pattern, out, re.M), out


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
    returned = setup_here(box, "--content-dir", str(missing))
    out = capsys.readouterr().out
    assert returned == 1, out
    assert re.search(rf"^PROBLEM\s+.*{problem}", out, re.M), out
    assert not (missing / ".git").exists()


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
    copies = (ELSEWHERE, ALONGSIDE)
    assert not any(re.search(p, asked) for p in copies for asked in person.asked), person.asked
    create = ("repo", "create", "my-dev-home", "--private", "--source", str(new_home))
    assert any(call[: len(create)] == create for call in fake_gh.calls), fake_gh.calls
    # The only problems left come from the sandbox's other dev-home: links to it, which setup
    # leaves alone, and settings changes for the new one, which nobody answers here.
    problems = [line for line in out.splitlines() if line.startswith("PROBLEM")]
    assert returned == 1 and problems, out
    assert all(re.search(r"Left alone|left unchanged", line) for line in problems), out
