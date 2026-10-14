"""Finds the programs the scripts start, and runs setup."""

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .settings import TOOLS_ROOT

SHARED_ROOT = Path(__file__).parent
# Set in the environment of a setup that a sync runs in a process of its own, while the sync holds
# its lock.
SYNC_HOLDS_LOCK = "DEV_HOME_SYNC_HOLDS_LOCK"


def _shared_file_times() -> dict[str, int] | None:
    """Each shared file's modification time, or None when they can't all be read: the Python
    files, and the data they load with them, such as setting-definitions.json."""
    try:
        with os.scandir(SHARED_ROOT) as entries:
            return {
                entry.name: entry.stat().st_mtime_ns
                for entry in entries
                if entry.name.endswith((".py", ".json")) and entry.is_file()
            }
    except OSError:
        return None


_LOADED_SHARED_FILE_TIMES = _shared_file_times()


def _shared_code_changed() -> bool:
    """Whether internal/shared changed since this module loaded. An unreadable scan counts as
    changed, because a fresh process is the safe way to run setup then."""
    current = _shared_file_times()
    return (
        _LOADED_SHARED_FILE_TIMES is None or current is None or current != _LOADED_SHARED_FILE_TIMES
    )


def find_program(name: str) -> str | None:
    """A program's full path, from the folders in PATH. On Windows, a search would look in the
    current folder first, which may be a project's: a program of the same name there must never
    run, so only full paths in PATH count."""
    if sys.platform != "win32":
        return shutil.which(name)
    for folder in os.environ.get("PATH", "").split(os.pathsep):
        if folder and Path(folder).is_absolute():
            candidate = Path(folder) / f"{name}.exe"
            if candidate.is_file():
                return str(candidate)
    return None


def run_setup(
    *, fresh: bool = False, sync_holds_lock: bool = False, at_console: bool = False
) -> bool:
    """Runs setup, which prints its own lines, PROBLEM lines included, and returns whether it
    had no problem. It runs with --quiet, inside this process unless fresh, or another process
    changed the shared modules since this one loaded them. Setup then runs as a Python process
    of its own, which loads one consistent version of the code. A sync that holds its lock says
    so, and setup's save doesn't wait for the lock it would otherwise take. at_console runs it
    as a person runs it by hand instead: without --quiet, in a process of its own, with this
    one's input, so at a console it asks about anything not answered yet."""
    if at_console or fresh or _shared_code_changed():
        # Setup writes to the same output, so this process's lines go out first.
        sys.stdout.flush()
        # Only the new process's environment changes, never this one's.
        environment = os.environ | {SYNC_HOLDS_LOCK: "1"} if sync_holds_lock else None
        options = [] if at_console else ["--quiet"]
        done = subprocess.run(
            [sys.executable, "-I", str(TOOLS_ROOT / "setup.py"), *options],
            stdin=None if at_console else subprocess.DEVNULL,
            env=environment,
            check=False,
        )
        return done.returncode == 0
    setup = importlib.import_module(f"{__package__}.setup")
    return bool(setup.main(["--quiet"], sync_holds_lock=sync_holds_lock) == 0)


def by_hand(script: str) -> str:
    """The command a person types to run one of the scripts in the root."""
    launcher = "py" if sys.platform == "win32" else "python3"
    return f"{launcher} {(TOOLS_ROOT / script).as_posix()}"
