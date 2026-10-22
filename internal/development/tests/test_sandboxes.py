"""The tests' own sandboxes: a run that passes removes the ones earlier runs kept."""

import os
import time
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import conftest
import helpers
from helpers import (
    SANDBOX_ROOT,
    Sandbox,
    make_junction,
    remove_kept_sandboxes,
    remove_sandbox,
    write_text,
)


def test_kept_sandboxes_untouched_for_an_hour_go_and_newer_ones_stay() -> None:
    # A folder of its own stands in for the sandboxes' folder, so real ones, kept by an earlier
    # run or in use by another, are left alone.
    here = SANDBOX_ROOT / f"py-kept-{uuid.uuid4().hex[:8]}"
    root = here / "sandboxes"
    outside = here / "python"
    write_text(outside / "python.exe", "not really\n")
    old, new = root / "py-old", root / "py-new"
    for box in (old, new):
        write_text(box / "toolkit" / "README.md", "copy\n")
        make_junction(box / "profile" / "AppData" / "Local" / "Python" / "bin", outside)
    two_hours_ago = time.time() - 2 * 60 * 60
    os.utime(old, (two_hours_ago, two_hours_ago))
    try:
        assert remove_kept_sandboxes(root) == (1, [])
        assert not old.exists()
        assert (new / "toolkit" / "README.md").is_file()
        # The kept sandbox's link to a Python install went without following it.
        assert (outside / "python.exe").is_file()
        # Nothing left that old, so a second pass removes nothing.
        assert remove_kept_sandboxes(root) == (0, [])
    finally:
        remove_sandbox(Sandbox(here))


def test_no_kept_sandboxes_folder_is_nothing_to_do(tmp_path: Path) -> None:
    assert remove_kept_sandboxes(tmp_path / "none") == (0, [])


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        # Another run that passed at the same moment removed it first.
        (FileNotFoundError("gone"), []),
        # Such as a terminal with it open: a line, and the next passing run tries again.
        (PermissionError("in use"), ["py-old: in use"]),
    ],
    ids=["already gone", "can't be removed"],
)
def test_a_kept_sandbox_that_cant_be_removed_is_reported_unless_its_gone(
    monkeypatch: pytest.MonkeyPatch, error: OSError, expected: list[str]
) -> None:
    here = SANDBOX_ROOT / f"py-kept-{uuid.uuid4().hex[:8]}"
    old = here / "py-old"
    write_text(old / "toolkit" / "README.md", "copy\n")
    two_hours_ago = time.time() - 2 * 60 * 60
    os.utime(old, (two_hours_ago, two_hours_ago))

    def fail(box: Sandbox) -> None:
        raise error

    try:
        monkeypatch.setattr(helpers, "remove_sandbox", fail)
        removed, problems = remove_kept_sandboxes(here)
        assert removed == 0
        assert [line.replace(f"{here}{os.sep}", "") for line in problems] == expected
    finally:
        monkeypatch.undo()
        remove_sandbox(Sandbox(here))


class Reporter:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def write_line(self, line: str) -> None:
        self.lines.append(line)


def finish(
    monkeypatch: pytest.MonkeyPatch, status: pytest.ExitCode, *, worker: bool
) -> tuple[int, list[str]]:
    """Ends a stand-in session and prints its summary as pytest would, with a stand-in for
    removing kept sandboxes, and returns how often it ran and the lines the summary printed."""
    calls: list[None] = []

    def remove() -> tuple[int, list[str]]:
        calls.append(None)
        return 2, ["a-sandbox: in use"]

    monkeypatch.setattr(conftest, "remove_kept_sandboxes", remove)
    config = SimpleNamespace(stash=pytest.Stash(), **({"workerinput": {}} if worker else {}))
    conftest.pytest_sessionfinish(cast(pytest.Session, SimpleNamespace(config=config)), status)
    reporter = Reporter()
    conftest.pytest_terminal_summary(
        cast(pytest.TerminalReporter, reporter), status, cast(pytest.Config, config)
    )
    return len(calls), reporter.lines


def test_only_a_passing_run_removes_kept_sandboxes_and_only_its_main_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert finish(monkeypatch, pytest.ExitCode.OK, worker=False) == (
        1,
        [
            "Removed 2 test sandboxes that earlier runs kept.",
            "Could not remove a test sandbox an earlier run kept: a-sandbox: in use",
        ],
    )
    # A failing run keeps them for a look.
    assert finish(monkeypatch, pytest.ExitCode.TESTS_FAILED, worker=False) == (0, [])
    # Each xdist worker's session ends too, before the run's result is known.
    assert finish(monkeypatch, pytest.ExitCode.OK, worker=True) == (0, [])
