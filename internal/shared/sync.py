"""Syncs your dev-home with GitHub, commits only the files it's given, and checks dev-home-toolkit
for updates.

Agents run git in dev-home only through this script, so that several sessions can use the
handoff and knowledge skills at once. Every session on this PC shares that folder, so a file this
script isn't given may be another session's work in progress. It never stages, commits, stashes,
resets, or discards such a file. It lists it instead, with how long ago it changed: LEFT, or
STALE once nobody has touched it for 15 minutes.

It finds dev-home through local-settings.json, which setup writes. One run at a time: a run
waits for any other run on the same dev-home to finish. The lock is one the operating system
holds on the file dev-home-sync.lock in dev-home's .git folder, so it goes when the run ends, even
one that stops partway. The file itself stays.

Without --message, it syncs: fetch, then fast-forward, or merge when two PCs both have new
commits, then push. Git refuses a merge that would change an uncommitted file, and a merge that
conflicts is undone at once, so nothing is lost either way. --fetch says when to fetch:

    always     Every time. Without --fetch, this is what it does.
    auto       As dev-home.json in dev-home says: with several active copies, or no answer,
               every time; with one, only when dev-home's last check of GitHub is
               devHome.checkEveryHours old (local-settings.json; 12 by default).

A sync that skips the fetch still merges what an earlier fetch brought in, pushes commits waiting
here, and lists the uncommitted files: it skips only the network call. With one active copy, any
commits a fetch brings in came from another copy, so it says to check the setting.

With --message and paths, it commits exactly those paths, then pushes without fetching first.
Only when GitHub rejects the push, because it has commits this copy lacks, does it fetch, merge,
and push again. A push that fails for any other reason, such as offline, waits for the next sync.

When the paths include knowledge/README.md, the knowledge base's index, it commits nothing while
the index lists a note that's neither committed nor among the paths, such as one another session
is still adding, or lists a note twice. After it brings in commits from GitHub, it reports a note
the index lists twice, which happens when two PCs change the same row.

Then it runs update's quiet check (internal/shared/update.py, the same as its --quiet), which
checks dev-home-toolkit for new commits and makes every decision about them: it pulls them when
updates.installAutomatically is on, as it is unless local-settings.json turns it off, and
otherwise says they're waiting. It
checks GitHub only once updates.checkEveryHours (24 by default) have passed since it last did.

Last, it runs setup's code with --quiet, inside this process, so updated skills, and skills
added on another PC, are set up on this one. Setup runs as a process of its own instead when
the check has just pulled an update, or when another process changed the shared modules while
this sync waited for its lock. That keeps setup from combining old loaded modules with new
files.

A sync that commits usually comes right after a plain one, which just did both of those. So it
skips the update check, and runs setup only when it brought in commits from GitHub.

An error in any step, such as a bug, is a PROBLEM line, and the steps after it still run, so
the update check that could install a fix isn't skipped.

Exits 0 when done, including when GitHub can't be reached, and 1 when the user needs to act.

Options:

    --fetch always|auto          When to fetch, for a sync without --message (see above).
    --message "<area>: <what>"   The commit message for the paths.
    <path> ...                   The files to commit, relative to dev-home. Name both paths of a
                                 renamed file.

Examples, in dev-home-toolkit's folder, with Python 3.12 or later:

    py sync.py

Syncs with GitHub, and lists the files left uncommitted.

    py sync.py --fetch auto

The same, but with one active copy, checks GitHub for dev-home's changes only when that check
is due.

    py sync.py --message "handoff: you/tool" "handoffs/github/you/tool/HANDOFF.md"

Commits that one file, then syncs.

prepare.py runs main([]) inside its own process, so keep main's name and arguments.
"""

import contextlib
import errno
import importlib
import os
import posixpath
import re
import sys
import time
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import IO

from .git import GIT_MISSING, GitResult, last_fetch_age, run_git
from .output import commit_count, describe, first_line, status_line
from .programs import by_hand, find_program, run_setup
from .settings import (
    DEFAULT_HOURS,
    KNOWLEDGE_INDEX,
    SCHEMA_VERSION,
    SETTINGS_PATH,
    get,
    hours_setting,
    layout,
    read_dev_home_settings,
    read_settings,
)

if sys.platform == "win32":
    import msvcrt

    # What locking a byte that another run holds raises.
    BUSY = {errno.EACCES, errno.EDEADLOCK}
else:
    import fcntl

    BUSY = {errno.EAGAIN, errno.EWOULDBLOCK, errno.EACCES}

# An agent commits right after it writes, so a file nobody has touched for this long is probably
# not another session's edit in progress.
STALE_AFTER_SECONDS = 15 * 60
LOCK_WAIT_SECONDS = 120
LOCK_FILE = "dev-home-sync.lock"
# Git's marker files for an operation left partway, which a sync must not run into.
IN_PROGRESS = {
    "MERGE_HEAD": "A merge",
    "rebase-merge": "A rebase",
    "rebase-apply": "A rebase",
    "CHERRY_PICK_HEAD": "A cherry-pick",
    "REVERT_HEAD": "A revert",
}
# Anything else reported about the commit or the sync means "up to date" isn't printed.
QUIET_STATES = {"OK", "LEFT", "STALE", "UPDATE"}
# The values --fetch takes, the first being what a sync does without it.
FETCH_WHEN = ("always", "auto")
# A row of the knowledge index (see KNOWLEDGE_INDEX) that links to a note.
INDEX_ROW = re.compile(r"\|\s*\[[^\]]*\]\(([^)\s]+)\)")


def notes_in_index(text: str) -> list[str]:
    """The notes the knowledge index's rows link to, as paths relative to dev-home, in the order
    of the rows, so a note in two rows is there twice."""
    folder = posixpath.dirname(KNOWLEDGE_INDEX)
    matches = (INDEX_ROW.match(line) for line in text.splitlines())
    return [posixpath.normpath(posixpath.join(folder, m.group(1))) for m in matches if m]


def listed_twice(notes: list[str]) -> list[str]:
    """Each note that's in the list more than once, named once. On Windows, two spellings that
    differ only in case are one note."""
    seen: set[str] = set()
    repeated: dict[str, str] = {}
    for note in notes:
        key = os.path.normcase(note)
        if key in seen:
            repeated.setdefault(key, note)
        seen.add(key)
    return list(repeated.values())


def one_active_copy(root: Path) -> bool:
    """Whether dev-home.json says dev-home has one active copy. A missing or unreadable file, one
    in a layout the code doesn't know, or no answer in it, counts as several, so a sync fetches
    rather than risk being behind."""
    return read_dev_home_settings(root).several is False


def format_age(seconds: float) -> str:
    if seconds < 60:
        return "under a minute ago"
    if seconds < 60 * 60:
        return f"{int(seconds // 60)} min ago"
    if seconds < 2 * 24 * 60 * 60:
        return f"{int(seconds // (60 * 60))} h ago"
    return f"{int(seconds // (24 * 60 * 60))} days ago"


class LockError(Exception):
    """The lock file can't be opened or locked, for a reason other than another run holding it."""


def try_lock(handle: IO[bytes]) -> bool:
    """Whether this run got the lock. Any failure but another run holding it, such as a file
    system with no locks, raises LockError, so it can't pass for a sync that never finishes."""
    handle.seek(0)
    try:
        if sys.platform == "win32":
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        if error.errno in BUSY:
            return False
        raise LockError(f"{handle.name} could not be locked: {error}") from error
    return True


def unlock(handle: IO[bytes]) -> None:
    handle.seek(0)
    if sys.platform == "win32":
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def one_run_at_a_time(git_dir: Path) -> Iterator[bool]:
    """Holds the lock for one run on this dev-home, and says whether it got it in time."""
    path = git_dir / LOCK_FILE
    try:
        opened = path.open("a+b")
    except OSError as error:
        raise LockError(f"{path} could not be opened: {error}") from error
    with opened as handle:
        deadline = time.monotonic() + LOCK_WAIT_SECONDS
        while not try_lock(handle):
            if time.monotonic() >= deadline:
                yield False
                return
            time.sleep(0.25)
        try:
            yield True
        finally:
            unlock(handle)


class Sync:
    """One run, on the dev-home at root. fetch_when is one of FETCH_WHEN, and check_hours is
    devHome.checkEveryHours, how long dev-home goes without checking GitHub with one active copy
    (0: never).
    Without then, it skips the update check and setup that otherwise follow, for a run setup
    itself starts."""

    def __init__(
        self,
        root: Path,
        git_dir: Path,
        fetch_when: str = FETCH_WHEN[0],
        check_hours: int = DEFAULT_HOURS["devHome.checkEveryHours"],
        *,
        then: bool = True,
    ) -> None:
        self.root = root
        self.git_dir = git_dir
        self.fetch_when = fetch_when
        self.check_hours = check_hours
        self.then = then
        # Read once this run holds the lock, and again after a merge, which can change it.
        self.one_copy = False
        self.problems = 0
        # Set once anything about the commit or the sync is reported, so "up to date" is printed
        # only when nothing else was.
        self.reported = False
        self.stopped = False
        # Set once commits from GitHub are merged in, since they may bring skills that setup must
        # link.
        self.brought_in = False
        # Set once the update check installs new dev-home-toolkit commits, whose code setup must
        # load fresh.
        self.updated = False

    def status(self, state: str, message: str) -> None:
        if state == "PROBLEM":
            self.problems += 1
        if state not in QUIET_STATES:
            self.reported = True
        status_line(state, message)

    def git(self, *args: str) -> GitResult:
        return run_git(self.root, *args)

    def busy(self, result: GitResult) -> None:
        self.status(
            "PROBLEM",
            f"Another git process kept dev-home locked through {result.tries} tries, so this step "
            "was skipped. If no git is running, one that stopped partway left a lock file behind; "
            f"ask the user before deleting it. git: {first_line(result.err)}",
        )

    def ahead_behind(self) -> tuple[int, int] | None:
        counts = self.git("rev-list", "--left-right", "--count", "HEAD...@{upstream}")
        parts = counts.text.split()
        if counts.code != 0 or len(parts) != 2:
            return None
        return int(parts[0]), int(parts[1])

    def read_index(self) -> str | None:
        """The knowledge index as it is on disk, or None when there isn't one."""
        try:
            return (self.root / KNOWLEDGE_INDEX).read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def index_is_ready(self, paths: list[str]) -> bool:
        """Whether the knowledge index can be committed with paths. Git commits the whole file,
        so it would take in a row that another session has added for a note it hasn't committed
        yet. So every note the index lists has to be committed already, or among paths and still
        there, and none may be listed twice; otherwise this says why, and returns False. One git
        call, for the notes already committed."""
        text = self.read_index()
        if text is None:
            return True
        notes = notes_in_index(text)
        twice = listed_twice(notes)
        if twice:
            self.status(
                "PROBLEM",
                f"{KNOWLEDGE_INDEX} lists {', '.join(twice)} more than once, so nothing was "
                "committed. Keep one row for each, then commit again.",
            )
            return False
        folder = posixpath.dirname(KNOWLEDGE_INDEX) + "/"
        tree = self.git("ls-tree", "-r", "-z", "--name-only", "HEAD", "--", folder)
        if tree.code != 0:
            if tree.locked:
                self.busy(tree)
            else:
                self.status(
                    "PROBLEM",
                    f"Could not see which notes {KNOWLEDGE_INDEX} lists are committed, so nothing "
                    f"was committed. git: {first_line(tree.err)}",
                )
            return False
        committed = {os.path.normcase(name) for name in tree.text.split("\0") if name}
        given = {os.path.normcase(path) for path in paths}

        def included(note: str) -> bool:
            key = os.path.normcase(note)
            if key in given:
                return (self.root / note).is_file()
            return key in committed

        missing = [note for note in notes if not included(note)]
        if missing:
            self.status(
                "PROBLEM",
                f"{KNOWLEDGE_INDEX} lists notes that wouldn't be committed with it: "
                f"{', '.join(missing)}. Nothing was committed. Another session may still be "
                "adding them: commit again once they're committed, or name them too if they're "
                "this session's.",
            )
            return False
        return True

    def report_index_listed_twice(self) -> None:
        """After commits came in: dev-home's .gitattributes merges the knowledge index line by
        line, so when two PCs change the same row, both versions stay, with no conflict."""
        text = self.read_index()
        twice = listed_twice(notes_in_index(text)) if text else []
        if twice:
            self.status(
                "PROBLEM",
                f"After the commits from GitHub, {KNOWLEDGE_INDEX} lists {', '.join(twice)} more "
                "than once, as when two PCs change the same row. Ask the user which row to keep "
                "for each, then commit the index.",
            )

    def commit(self, paths: list[str], message: str) -> None:
        index = os.path.normcase(KNOWLEDGE_INDEX)
        if any(os.path.normcase(path) == index for path in paths) and not self.index_is_ready(
            paths
        ):
            self.stopped = True
            return
        listed = ", ".join(paths)
        add = self.git("--literal-pathspecs", "add", "--", *paths)
        if add.code != 0:
            self.stopped = True
            if add.locked:
                self.busy(add)
                return
            self.status(
                "PROBLEM",
                f"Could not stage {listed}, so nothing was committed. git: {first_line(add.err)}",
            )
            return
        staged = self.git("--literal-pathspecs", "diff", "--cached", "--quiet", "--", *paths)
        if staged.code == 0:
            self.status("OK", f"Nothing to commit: {listed} already match the last commit.")
            return
        # With paths, git commits only those paths, and anything another session staged stays out.
        commit = self.git("--literal-pathspecs", "commit", "--quiet", "-m", message, "--", *paths)
        if commit.code != 0:
            self.stopped = True
            # git add staged the paths, and a merge refuses while anything is staged. This puts
            # only their index entries back to the last commit; the files keep their changes.
            unstage = self.git("--literal-pathspecs", "restore", "--staged", "--", *paths)
            if commit.locked:
                self.busy(commit)
            else:
                self.status(
                    "PROBLEM",
                    f"Could not commit {listed}. git: {first_line(commit.err + commit.out)}",
                )
            if unstage.code != 0:
                self.status(
                    "PROBLEM",
                    f"{listed} stayed staged, and git refuses to merge while anything is staged. "
                    f"Ask the user. git: {first_line(unstage.err)}",
                )
            return
        self.status("COMMITTED", f'"{message}" ({listed})')

    def merge_upstream(self, ahead: int, behind: int) -> None:
        if ahead == 0:
            merge = self.git("merge", "--ff-only", "--quiet", "@{upstream}")
            if merge.code == 0:
                self.brought_in = True
                self.status("PULLED", f"{commit_count(behind)} from GitHub.")
                self.report_index_listed_twice()
                return
        else:
            merge = self.git(
                "merge",
                "--no-edit",
                "--quiet",
                "-m",
                "sync: merge another PC's commits",
                "@{upstream}",
            )
            if merge.code == 0:
                self.brought_in = True
                self.status(
                    "MERGED",
                    f"{commit_count(behind)} from GitHub, with a merge commit, because two PCs had "
                    "new commits.",
                )
                self.report_index_listed_twice()
                return
        self.stopped = True
        if merge.locked:
            self.busy(merge)
            return
        if (self.git_dir / "MERGE_HEAD").exists():
            conflicts = ", ".join(self.git("diff", "--name-only", "--diff-filter=U").out)
            abort = self.git("merge", "--abort")
            if abort.code == 0:
                self.status(
                    "PROBLEM",
                    f"Two PCs changed {conflicts}. The merge was undone, and this PC's commits are "
                    "safe. Ask the user how to combine the two versions.",
                )
            else:
                self.status(
                    "PROBLEM",
                    f"Two PCs changed {conflicts}, and undoing the merge failed, so a merge is "
                    f"still in progress in dev-home. Ask the user. git: {first_line(abort.err)}",
                )
            return
        # Git lists the files that stopped it on indented lines.
        files = [line.strip() for line in merge.err + merge.out if re.match(r"\s+\S", line)]
        if files:
            self.status(
                "PROBLEM",
                "Git won't bring in the commits from GitHub while these files have uncommitted "
                f"changes here: {', '.join(files)}. Nothing was changed. Once they are committed, "
                "sync again.",
            )
        else:
            self.status(
                "PROBLEM",
                "Could not bring in the commits from GitHub. Nothing was changed. "
                f"git: {first_line(merge.err + merge.out)}",
            )

    def pending(self, ahead: int, err: list[str] | None = None) -> None:
        """Commits made here that GitHub doesn't have yet. "Synced" fits both uses: GitHub's copy
        is the backup, and how other copies get the changes."""
        them = "it" if ahead == 1 else "them"
        detail = f" git: {first_line(err)}" if err else ""
        self.status(
            "PENDING",
            f"{commit_count(ahead)} saved on this PC, not synced to GitHub yet. The next sync "
            f"sends {them}.{detail}",
        )

    def fetch_is_due(self, age: float | None) -> bool:
        """Whether a sync without --message fetches, given how long ago the last fetch was."""
        if self.fetch_when == "always" or not self.one_copy:
            return True
        return age is None or self.check_hours == 0 or age >= self.check_hours * 60 * 60

    def fetch(self) -> bool:
        """Fetches from GitHub, and says so when it can't."""
        fetch = self.git("fetch", "--quiet")
        if fetch.code == 0:
            return True
        if fetch.locked:
            self.busy(fetch)
            return False
        if self.one_copy:
            self.status(
                "OFFLINE",
                "Could not reach GitHub for dev-home's check. It's set to one active copy, so "
                f"nothing should be missing here. git: {first_line(fetch.err)}",
            )
        else:
            self.status(
                "OFFLINE",
                f"Could not reach GitHub, so dev-home may be behind. git: {first_line(fetch.err)}",
            )
        counts = self.ahead_behind()
        if counts is not None and counts[0] > 0:
            self.pending(counts[0])
        return False

    def sync_remote(self, fetch_first: bool) -> None:
        """Fetches when fetch_first, brings in what GitHub has, and pushes what's waiting here. A
        push GitHub rejects because it has commits this copy lacks gets one more round of fetch,
        merge, and push; any other failure leaves the commits waiting, with no second try."""
        fetch = fetch_first
        for round_number in (1, 2):
            if fetch and not self.fetch():
                return
            counts = self.ahead_behind()
            if counts is None:
                self.status(
                    "PROBLEM",
                    "Could not compare with GitHub, because this branch has no upstream branch.",
                )
                return
            ahead, behind = counts
            if behind > 0:
                self.merge_upstream(ahead, behind)
                if self.stopped:
                    if ahead > 0:
                        self.pending(ahead)
                    return
                # Another copy may have just switched dev-home to several copies, as it should.
                self.one_copy = one_active_copy(self.root)
                if self.one_copy:
                    self.status(
                        "SETTING",
                        f"dev-home brought in {commit_count(behind)} from another copy, but it's "
                        "set to one active copy. If another copy is in use, run /dev-home "
                        "configure.",
                    )
                counts = self.ahead_behind()
                if counts is None:
                    return
                ahead = counts[0]
            if ahead == 0:
                return
            push = self.git("push", "--quiet")
            if push.code == 0:
                self.status("PUSHED", f"{commit_count(ahead)} to GitHub.")
                return
            rejected = re.search(r"rejected|fetch first|non-fast-forward", "\n".join(push.err))
            if round_number == 1 and rejected:
                fetch = True
                continue
            self.pending(ahead, push.err)
            return

    def age_of(self, file: str) -> float | None:
        """How long ago a file changed. A deleted file has no time of its own, so this uses the
        nearest folder above it that still exists, whose time changes when an entry in it is
        removed. That may be dev-home itself, when the file's folders went with it."""
        relative = file
        while True:
            candidate = self.root / relative if relative else self.root
            try:
                return time.time() - candidate.lstat().st_mtime
            except OSError:
                pass
            if not relative:
                return None
            # Git writes paths with forward slashes.
            relative = relative.rpartition("/")[0]

    def write_uncommitted(self) -> None:
        status = self.git("status", "--porcelain=v1", "-z", "--untracked-files=all")
        if status.code != 0:
            self.status(
                "PROBLEM", f"Could not list uncommitted files. git: {first_line(status.err)}"
            )
            return
        fields = [field for field in status.text.split("\0") if field]
        index = 0
        while index < len(fields):
            entry = fields[index]
            index += 1
            if len(entry) < 4:
                continue
            x, y, file = entry[0], entry[1], entry[3:]
            kind = "changed"
            if x == "?":
                kind = "new file"
            elif x in ("R", "C") or y in ("R", "C"):
                # A rename is followed by the name it had before.
                before = fields[index] if index < len(fields) else "?"
                index += 1
                kind = "renamed from " + before
            elif x == "D" or y == "D":
                kind = "deleted"
            elif x == "A":
                kind = "new file"
            if x not in (" ", "?"):
                kind += ", staged"
            age = self.age_of(file)
            # Without a time, nothing shows that nobody is working on it.
            if age is None:
                self.status("LEFT", f"{file} ({kind}, age unknown)")
            elif age >= STALE_AFTER_SECONDS:
                self.status("STALE", f"{file} ({kind}, {format_age(age)})")
            else:
                self.status("LEFT", f"{file} ({kind}, {format_age(age)})")

    def update_toolkit(self) -> None:
        """Runs update's check, which decides what to do about new dev-home-toolkit commits, so what
        the user is told and what gets installed come from the same code. It's loaded only now,
        so an error in it, even one that stops it loading, is reported and can't stop the rest
        of this sync."""
        try:
            update = importlib.import_module(f"{__package__}.update")
            code, self.updated = update.quiet_check()
            if code != 0:
                self.problems += 1
        except Exception as error:
            self.status("PROBLEM", f"update.py stopped: {describe(error)}")

    def setup(self) -> None:
        # Setup runs while this sync holds its lock, which setup's save would otherwise take.
        if not run_setup(fresh=self.updated, sync_holds_lock=True):
            self.problems += 1

    def step(self, what: str, action: Callable[[], None]) -> None:
        """Runs one step. An error in it, such as a bug, becomes a PROBLEM line, and the steps
        after it still run: the update check most of all, since an update is how a fix
        arrives. Costs nothing measurable when the step finishes."""
        try:
            action()
        except Exception as error:
            self.stopped = True
            self.status("PROBLEM", f"{what} stopped partway: {describe(error)}")

    def run(self, paths: list[str], message: str) -> None:
        for marker, what in IN_PROGRESS.items():
            if (self.git_dir / marker).exists():
                self.status(
                    "PROBLEM",
                    f"{what} is in progress in dev-home, perhaps left by a git command that "
                    "stopped partway. Nothing was changed. Ask the user to finish or abort it.",
                )
                return
        self.one_copy = one_active_copy(self.root)
        # A commit pushes first. Without one, the fetch waits for its time when it can.
        age = last_fetch_age(self.git_dir)
        fetch_first = not paths and self.fetch_is_due(age)
        if paths:
            self.step("The commit", lambda: self.commit(paths, message))
            if self.stopped:
                return
        self.step("Syncing with GitHub", lambda: self.sync_remote(fetch_first))
        # A commit with nothing to commit has said so, and reached no GitHub to compare with.
        if not self.reported and not paths:
            if fetch_first or age is None:
                self.status("OK", "dev-home is up to date with GitHub.")
            else:
                # Only a sync with one active copy skips the fetch.
                self.status(
                    "OK",
                    "dev-home is up to date: it's the only active copy, and it last checked "
                    f"GitHub {format_age(age)}.",
                )
        self.step("Listing the uncommitted files", self.write_uncommitted)
        # A sync that commits usually comes right after a plain one, which just checked for
        # updates and ran setup. So it skips the check, and runs setup only for commits it
        # brought in. A run setup started does neither: setup is already running.
        if not self.then:
            return
        plain = not paths
        if plain:
            self.update_toolkit()
        if plain or self.brought_in:
            self.step("Running setup", self.setup)


def problem(text: str) -> int:
    status_line("PROBLEM", text)
    return 1


def parse_arguments(argv: Sequence[str]) -> tuple[str, list[str], str] | str:
    """The commit message, the paths, and when to fetch, or why the arguments can't be used."""
    message = ""
    paths: list[str] = []
    fetch_when = ""
    rest = list(argv)
    while rest:
        word = rest.pop(0)
        if word == "--message":
            if not rest:
                return "--message needs the commit message after it."
            message = rest.pop(0)
        elif word == "--fetch":
            if not rest or rest[0] not in FETCH_WHEN:
                return f"--fetch needs one of these after it: {', '.join(FETCH_WHEN)}."
            fetch_when = rest.pop(0)
        elif word == "--":
            paths.extend(rest)
            rest = []
        elif word.startswith("-"):
            return f"No such option: {word}. The options are --message and --fetch."
        else:
            paths.append(word)
    if fetch_when and (message or paths):
        return "--fetch is for a sync without --message: a commit pushes without fetching first."
    return message, paths, fetch_when or FETCH_WHEN[0]


def main(argv: Sequence[str]) -> int:
    if any(word in ("--help", "-h") for word in argv):
        print(__doc__)
        return 0
    try:
        return sync(argv)
    except Exception as error:
        return problem(f"sync.py stopped: {describe(error)}")


def sync(argv: Sequence[str]) -> int:
    parsed = parse_arguments(argv)
    if isinstance(parsed, str):
        return problem(parsed)
    message, values, fetch_when = parsed

    setup = by_hand("setup.py")
    if not SETTINGS_PATH.exists():
        return problem(
            f"dev-home-toolkit is not set up on this PC yet. The user runs {setup} once in a "
            "terminal."
        )
    settings = read_settings()
    if settings is None:
        return problem(
            f"{SETTINGS_PATH} could not be read as a JSON object of settings. The user fixes it, "
            f"or deletes it and runs {setup} in a terminal to answer its questions again."
        )
    found = layout(settings, SCHEMA_VERSION)
    if found == "older":
        return problem(
            f"{SETTINGS_PATH} is in an older layout, from before its settings were grouped, so "
            f"the sync can't find dev-home. The user runs {setup} in a terminal: it offers to set "
            "the file aside and ask its questions again."
        )
    if found == "unknown":
        return problem(
            f"{SETTINGS_PATH} has a schemaVersion this dev-home-toolkit doesn't know, perhaps "
            f"written by a newer one, so the sync left dev-home alone. The user runs "
            f"{by_hand('update.py')}, or sets the file aside and runs {setup} in a terminal."
        )
    content_dir = get(settings, "devHome.folder")
    if not isinstance(content_dir, str) or not content_dir:
        return problem(
            f"{SETTINGS_PATH} has no dev-home folder. The user runs {setup} once in a terminal."
        )
    root = Path(os.path.abspath(content_dir))

    problems = 0
    paths: list[str] = []
    # On Windows, two spellings of a path that differ only in case are the same file.
    seen: set[str] = set()
    for value in values:
        if not value.strip():
            continue
        full = Path(os.path.abspath(root / value))
        if root not in full.parents:
            problems += problem(f"{value} is not inside dev-home ({root}).")
            continue
        # A folder would take in every file under it, including another session's new files.
        if full.is_dir():
            problems += problem(f"{value} is a folder. Name each file to commit.")
            continue
        relative = full.relative_to(root).as_posix()
        if os.path.normcase(relative) not in seen:
            seen.add(os.path.normcase(relative))
            paths.append(relative)
    if problems == 0:
        if message and not paths:
            problems += problem("Name the files to commit after --message.")
        elif not message and paths:
            problems += problem('Give a commit message with --message "<area>: <what>".')
        elif message and not re.match(r"[^\s:]+: \S", message):
            problems += problem(
                'Commit messages read "<area>: <what>", for example "handoff: my-project". '
                f"Got: {message}"
            )
    if problems:
        return 1

    check_hours = hours_setting(settings, "devHome.checkEveryHours")[0]
    return sync_root(root, paths, message, fetch_when, check_hours)


def commit_for_setup(
    root: Path, paths: list[str], message: str, *, holds_lock: bool = False
) -> int:
    """Commits files in the dev-home at root, each named relative to it, and syncs, as
    sync.py --message does. Setup runs this, so it skips the update check and setup, which a sync
    that brings in commits otherwise runs: setup would start again inside itself. Setup says
    when it holds the lock already, which this sync would otherwise wait for. Returns 0, or 1
    when the user needs to act, and never raises."""
    try:
        return sync_root(root, paths, message, FETCH_WHEN[0], 0, then=False, holds_lock=holds_lock)
    except Exception as error:
        return problem(f"The commit of {', '.join(paths)} stopped: {describe(error)}")


def sync_root(
    root: Path,
    paths: list[str],
    message: str,
    fetch_when: str,
    check_hours: int,
    *,
    then: bool = True,
    holds_lock: bool = False,
) -> int:
    """One run on the dev-home at root, once the arguments are checked. With holds_lock, the
    caller holds the lock already."""
    if find_program("git") is None:
        return problem(f"dev-home was not synced. {GIT_MISSING}")
    found = run_git(root, "rev-parse", "--absolute-git-dir")
    if found.code != 0:
        return problem(f"{root} is not a git repo. git: {first_line(found.err)}")
    git_dir = Path(first_line(found.out))

    run = Sync(root, git_dir, fetch_when, check_hours, then=then)
    if holds_lock:
        run.run(paths, message)
        return 1 if run.problems else 0
    try:
        with one_run_at_a_time(git_dir) as owned:
            if owned:
                run.run(paths, message)
            else:
                run.status(
                    "PROBLEM",
                    f"Another sync, or an update, has been using dev-home for "
                    f"{LOCK_WAIT_SECONDS // 60} minutes. Try again shortly, and if it keeps "
                    "happening, ask the user.",
                )
    except LockError as error:
        return problem(
            "Nothing was synced: each sync holds a lock on a file in dev-home's .git folder, so "
            f"only one runs at a time, and {error}. Ask the user."
        )
    return 1 if run.problems else 0
