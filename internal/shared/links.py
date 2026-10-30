"""Links to folders: finding where one points, making one, and removing one without touching what
it points to, by itself or in a folder being deleted."""

import os
import shutil
import stat
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .paths import comparable, long_form, without_long_prefix

if sys.platform == "win32":
    import _winapi


@dataclass(frozen=True)
class LinkInfo:
    """What is at a path: a link, with the comparable path it points to, or something else."""

    is_link: bool
    target: str | None


def is_link(path: Path) -> bool:
    return path.is_symlink() or os.path.isjunction(path)


def link_info(path: Path) -> LinkInfo | None:
    """None when nothing is at the path. A link whose target is gone still counts as a link."""
    if is_link(path):
        target = without_long_prefix(str(path.readlink()))
        if not Path(target).is_absolute():
            target = str(path.parent / target)
        return LinkInfo(True, comparable(target))
    if os.path.lexists(path):
        return LinkInfo(False, None)
    return None


def make_folder_link(link: Path, target: Path) -> str:
    """Makes a link to a folder, and returns its kind: a junction on Windows, which needs no
    Developer Mode, and a symbolic link elsewhere, where any user can make one.
    _winapi.CreateJunction is part of Python on Windows, though not documented for general use;
    Python's own tests make junctions with it."""
    link.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        _winapi.CreateJunction(str(target), str(link))
        return "junction"
    link.symlink_to(target, target_is_directory=True)
    return "symlink"


def remove_folder_link(link: Path) -> None:
    """Removes a link to a folder, never anything in what it points to. A recursive delete would
    follow a junction into its target, so it's never used for a link."""
    try:
        link.unlink()
    except OSError:
        # A junction or a symbolic link to a folder, on Windows.
        link.rmdir()


def remove_folder(folder: Path, last: str = "") -> None:
    """Deletes a folder and everything in it. Each link inside goes first, by itself, so the
    delete never reaches what a link points to, and a folder that is itself a link loses only the
    link. The entry of the folder named last, when there is one, goes after the rest of what's in
    the folder, so a delete that stops partway still leaves it. It works through Windows' long form
    of the path, so it deletes what git checked out past Windows' path limit too. Raises OSError
    when something can't be deleted."""
    if is_link(folder):
        remove_folder_link(folder)
        return
    root = long_form(folder)
    # A list of folders still to look in, rather than recursion, which a deep tree could exhaust.
    links: list[str] = []
    folders = [root]
    while folders:
        with os.scandir(folders.pop()) as entries:
            for entry in entries:
                if entry.is_symlink() or entry.is_junction():
                    links.append(entry.path)
                elif entry.is_dir(follow_symlinks=False):
                    folders.append(entry.path)
    for link in links:
        # unlink takes a link to a file, and rmdir one to a folder.
        remove_folder_link(Path(link))

    def writable(function: Callable[..., object], path: str, _error: BaseException) -> None:
        # Git makes its object files read-only.
        Path(path).chmod(stat.S_IWRITE)
        function(path)

    if last:
        with os.scandir(root) as entries:
            first = [entry for entry in entries if entry.name != last]
        for entry in first:
            if entry.is_dir(follow_symlinks=False):
                shutil.rmtree(entry.path, onexc=writable)
            else:
                Path(entry.path).chmod(stat.S_IWRITE)
                Path(entry.path).unlink()
    shutil.rmtree(root, onexc=writable)
