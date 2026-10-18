"""Shows the dev-home-toolkit commits waiting on GitHub, and pulls them after a yes.

Lists each waiting commit and the files it changes, and points to the command that shows every
changed line. On a yes, it pulls them (fast-forward only), holding the sync's lock on dev-home
so a sync in another session waits for the pull, then runs setup as a person runs it by hand,
so the updated skills and rules take effect on this PC, and at a console setup asks about
anything new. When the pull changes the default of a setting this PC follows, one it hasn't
chosen a value for, it says so, once, then and there.

Everything about dev-home-toolkit updates happens here: a sync runs its quiet check, the same as
--quiet, and a person runs it without. So what the user is told and what gets installed come
from the same code.

Options:

    --quiet   What a sync runs, as quiet_check() inside its own process. Never asks. Checks
              GitHub once updates.checkEveryHours (in local-settings.json; 24 by default, and 0
              for every time) have passed since the last fetch, and otherwise uses what that
              fetch found. Then prints at most one line, in the sync's format: OFFLINE when
              GitHub can't be reached, UPDATE while commits are waiting, or PULLED once it has
              pulled them, which it does only when updates.installAutomatically is on, as it is
              unless local-settings.json turns it off. Leaves setup to the sync, which runs it
              next.

Run without --quiet, it always checks GitHub.

Example, with Python 3.12 or later:

    py C:/Users/you/dev-home-toolkit/update.py

A sync loads this module only when it gets to the update check, and an error in it is reported
and can't stop the rest of the sync: an update is how fixes arrive.
"""

import contextlib
import json
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .git import GIT_MISSING, last_fetch_age, run_git
from .output import CYAN, GREEN, RED, color, commit_count, first_line, status_line
from .paths import comparable
from .programs import by_hand, find_program, run_setup
from .settings import (
    AUTO_UPDATE,
    DEFINITIONS_PATH,
    MISSING,
    STATE,
    TOOLKIT_ROOT,
    get,
    hours_setting,
    hours_text,
    read_settings,
    read_skill_file,
    setting_value,
)
from .sync import LOCK_WAIT_SECONDS, LockError, one_run_at_a_time


def stop(quiet: bool, text: str) -> int:
    """With --quiet, a PROBLEM line, which the sync reports like its own."""
    if quiet:
        status_line("PROBLEM", text)
    else:
        print(color(text, RED), flush=True)
    return 1


def main(argv: Sequence[str]) -> int:
    quiet = False
    for word in argv:
        if word == "--quiet":
            quiet = True
        elif word in ("--help", "-h"):
            print(__doc__)
            return 0
        else:
            return stop(quiet, f"No such option: {word}. The only option is --quiet.")
    return quiet_check()[0] if quiet else ask_and_install()


def quiet_check() -> tuple[int, bool]:
    """What a sync runs: checks GitHub, never asks, and installs waiting commits only when
    updates.installAutomatically is on. Returns the exit code, and whether it installed commits,
    since the sync's setup then needs the new code."""
    return check(quiet=True)


def ask_and_install() -> int:
    """What a person runs: shows the waiting commits, and installs them after a yes."""
    return check(quiet=False)[0]


def check_is_due() -> bool:
    """Whether a quiet check fetches: once updates.checkEveryHours have passed since the last
    successful fetch. A clone whose .git isn't a folder, such as a worktree, fetches every time."""
    hours = hours_setting(read_settings() or {}, "updates.checkEveryHours")[0]
    git_dir = TOOLKIT_ROOT / ".git"
    if hours == 0 or not git_dir.is_dir():
        return True
    age = last_fetch_age(git_dir)
    return age is None or age >= hours * 60 * 60


def check(*, quiet: bool) -> tuple[int, bool]:
    # Git would otherwise use any repo this folder sits in, such as a zip download unpacked inside
    # another project, and offer to update that repo instead.
    if not (TOOLKIT_ROOT / ".git").exists():
        if quiet:
            return 0, False
        return stop(
            quiet,
            f"{TOOLKIT_ROOT} is not a git clone of dev-home-toolkit, so it can't update itself. "
            "Clone dev-home-toolkit as the README shows, and use that copy instead.",
        ), False

    if find_program("git") is None:
        return stop(quiet, f"dev-home-toolkit was not checked for updates. {GIT_MISSING}"), False

    # A clone with no upstream branch, such as a new local copy, has nothing to update from.
    if run_git(TOOLKIT_ROOT, "rev-parse", "--verify", "--quiet", "@{upstream}").code != 0:
        if quiet:
            return 0, False
        return stop(quiet, "This clone has no upstream branch to update from."), False

    # Between checks, a quiet check uses what the last fetch found.
    fetch = run_git(TOOLKIT_ROOT, "fetch", "--quiet") if not quiet or check_is_due() else None
    if fetch is not None and fetch.code != 0:
        if quiet:
            status_line(
                "OFFLINE",
                f"Could not check dev-home-toolkit for updates. git: {first_line(fetch.err)}",
            )
            return 0, False
        problem = f"Could not reach GitHub. git: {first_line(fetch.err + fetch.out)}"
        return stop(quiet, problem), False

    # Everything below uses this exact commit, not @{upstream}: a sync in another session can
    # fetch newer commits while the question waits, and a yes pulls only what was shown.
    target = run_git(TOOLKIT_ROOT, "rev-parse", "--verify", "--quiet", "@{upstream}")
    if target.code != 0:
        return stop(
            quiet,
            "Could not read what GitHub has for dev-home-toolkit. "
            f"git: {first_line(target.err + target.out)}",
        ), False
    commit = target.text.strip()

    counts = run_git(TOOLKIT_ROOT, "rev-list", "--left-right", "--count", f"HEAD...{commit}")
    parts = counts.text.split()
    if counts.code != 0 or len(parts) != 2:
        return stop(
            quiet,
            "Could not compare dev-home-toolkit with GitHub. "
            f"git: {first_line(counts.err + counts.out)}",
        ), False
    ahead, behind = int(parts[0]), int(parts[1])
    if behind == 0:
        if not quiet:
            print(color("dev-home-toolkit is up to date.", GREEN), flush=True)
        return 0, False
    waiting = commit_count(behind)
    if ahead > 0:
        if quiet:
            status_line(
                "UPDATE",
                f"{waiting} waiting in dev-home-toolkit, not installed, because this clone has "
                f"{commit_count(ahead)} of its own. The user can merge them by hand.",
            )
            return 0, False
        return stop(
            quiet,
            f"This clone has {commit_count(ahead)} of its own, so it can't simply move forward to "
            f"the {waiting} on GitHub. Merge them by hand.",
        ), False

    if quiet:
        # Only the setting turned on, by an answer or its default, installs anything unasked. A
        # file that can't be read installs nothing, whatever the default: something has gone wrong
        # on this PC. (A sync stops before this when it can't read the file either.)
        settings = read_settings()
        if settings is None or setting_value(settings, AUTO_UPDATE)[0] is not True:
            status_line(
                "UPDATE",
                f"{waiting} waiting in dev-home-toolkit. To see them and install them, the user "
                f"runs: {by_hand('update.py')}",
            )
            return 0, False
        before = declared_defaults()
        merge = run_git(TOOLKIT_ROOT, "merge", "--ff-only", "--quiet", commit)
        if merge.code != 0:
            status_line(
                "UPDATE",
                f"{waiting} waiting in dev-home-toolkit, not installed. "
                f"git: {first_line(merge.err + merge.out)}",
            )
            return 0, False
        notice = changed_defaults_notice(before, declared_defaults(), settings)
        status_line("PULLED", f"{waiting} to dev-home-toolkit.{notice}")
        return 0, True

    print(f"{waiting} waiting in dev-home-toolkit:")
    print()
    log = run_git(TOOLKIT_ROOT, "log", "--format=  %h %ad  %s", "--date=short", f"HEAD..{commit}")
    for line in log.out:
        print(line)
    print()
    print("Files they change:")
    for line in run_git(TOOLKIT_ROOT, "diff", "--stat", "HEAD", commit).out:
        print("  " + line)
    print()
    print(f"To see every changed line first: git -C {TOOLKIT_ROOT.as_posix()} diff HEAD {commit}")
    print(flush=True)

    try:
        answer = input("Pull them now? [y/N] ")
    except EOFError:
        no_answer = "No answer came, so nothing was pulled. Run it in a terminal to answer."
        return stop(quiet, no_answer), False
    if answer.strip().lower() not in ("y", "yes"):
        print("Nothing was pulled.")
        return 0, False

    with sync_lock() as owned:
        if not owned:
            return stop(
                quiet,
                f"Nothing was pulled: a sync, or another update, has been using dev-home for "
                f"{LOCK_WAIT_SECONDS // 60} minutes. Run {by_hand('update.py')} again shortly.",
            ), False
        before = declared_defaults()
        merge = run_git(TOOLKIT_ROOT, "merge", "--ff-only", "--quiet", commit)
    if merge.code != 0:
        problem = f"Could not pull them. git: {first_line(merge.err + merge.out)}"
        return stop(quiet, problem), False
    notice = changed_defaults_notice(before, declared_defaults(), read_settings())
    print(color(f"Pulled {waiting}.{notice}", CYAN))
    print(color("Running setup so they take effect:", CYAN), flush=True)
    # Setup runs as a person runs it by hand, so at a console it asks about anything new, such as
    # a skill the update brings, and it loads the code just pulled.
    if not run_setup(at_console=True):
        return 1, True
    print(color("Done.", GREEN))
    return 0, True


@dataclass(frozen=True)
class Default:
    """A default dev-home-toolkit declares: the setting's label, its type, and the value."""

    label: str
    type: str
    value: object


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def declared_defaults() -> dict[str, Default]:
    """Every default dev-home-toolkit declares, by the setting's name, as its files say right now:
    its own settings in setting-definitions.json, and for each of its skills, whether it's added
    to the agents and its preferences, as setup reads them. Read from the files each time, since
    an update changes them; one that can't be read declares nothing. A person's own skills don't
    come with updates, so they're left out."""
    found: dict[str, Default] = {}
    definitions = read_json(DEFINITIONS_PATH)
    settings = definitions.get("settings") if isinstance(definitions, dict) else None
    for path, entry in settings.items() if isinstance(settings, dict) else ():
        if isinstance(entry, dict) and "default" in entry:
            label = str(entry.get("label") or path)
            found[path] = Default(label, str(entry.get("type", "")), entry["default"])
    try:
        skills = sorted((TOOLKIT_ROOT / "templates" / "skills").iterdir())
    except OSError:
        # A notice that can't be worked out is left out, never the pull it would follow.
        skills = []
    for skill in skills:
        declared, _ = read_skill_file(skill, own=False)
        if declared is None:
            continue
        added = declared.added_setting
        if added is not None:
            found[added.path] = Default(added.label, "yes-no", added.default)
        for preference in declared.preferences.values():
            found[preference.setting.path] = Default(preference.label, "yes-no", preference.default)
    return found


def default_text(default: Default) -> str:
    if default.type == "hours" and isinstance(default.value, int):
        return hours_text(default.value)
    if isinstance(default.value, bool):
        return "yes" if default.value else "no"
    return str(default.value)


def changed_defaults_notice(
    before: dict[str, Default], after: dict[str, Default], settings: dict[str, Any] | None
) -> str:
    """The sentence an update adds when it changes the default of a setting this PC follows:
    one it hasn't saved, or saved as unanswered or as the default. A saved value of its own never
    changes, so it isn't named. Empty when there's none, or this PC's settings can't be read."""
    if settings is None:
        return ""
    changes: list[str] = []
    for path, new in after.items():
        old = before.get(path)
        if old is None or (old.value == new.value and type(old.value) is type(new.value)):
            continue
        saved = get(settings, path, MISSING)
        follows = saved is MISSING or (
            isinstance(saved, dict) and saved.get(STATE) in ("default", "unanswered")
        )
        if follows:
            changes.append(f"{new.label} is now {default_text(new)}")
    if not changes:
        return ""
    which = "a setting" if len(changes) == 1 else "settings"
    return (
        f" It changed the default of {which} this PC follows: {'; '.join(changes)}. To choose "
        "your own value: /dev-home configure."
    )


@contextlib.contextmanager
def sync_lock() -> Iterator[bool]:
    """The sync's lock on dev-home, which a person's update holds for its pull, as a sync holds
    it for its own. Otherwise a sync in another session could run setup while git replaces the
    skills' files, and see a skill missing for a moment, or generate files from half-updated
    templates. Neither the question before it nor the setup after it holds the lock, since setup
    may ask questions too, and a sync never waits on a person; setup takes the lock itself for
    its work, after its questions. Yields whether this run holds it, or True when there's no lock
    to take: no dev-home folder set yet, one whose .git isn't a folder, or a lock file that can't
    be opened, which nothing else can hold either."""
    folder = get(read_settings() or {}, "devHome.folder")
    git_dir = Path(comparable(folder)) / ".git" if isinstance(folder, str) and folder else None
    with contextlib.ExitStack() as held:
        owned = True
        if git_dir is not None and git_dir.is_dir():
            with contextlib.suppress(LockError):
                owned = held.enter_context(one_run_at_a_time(git_dir))
        yield owned
