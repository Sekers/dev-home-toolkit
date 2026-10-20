"""Finding a Python 3.12 or later for the skills' scripts, which setup links internal/.python to."""

import json
import os
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

from .paths import same_path

if sys.platform == "win32":
    import winreg

MINIMUM = (3, 12)
# Where each Windows hive keeps the runtimes it knows (PEP 514).
REGISTRY_ROOTS = (r"Software\Python", r"Software\WOW6432Node\Python")
# A test release's full version: an alpha, beta, release candidate, or development build, such as
# 3.16.0a1, the form the Python install manager writes in the registry's Version value.
TEST_RELEASE = re.compile(r"\d+(\.\d+)*\s*(a|b|rc|dev)\d*", re.IGNORECASE)
# How long a Python may take to answer setup's check. Antivirus software can take many seconds to
# scan a Python new to the PC, on a slow PC more.
CHECK_SECONDS = 60


def parse_version(text: object) -> tuple[int, ...] | None:
    if not isinstance(text, str) or not re.fullmatch(r"\d+(\.\d+){1,3}", text.strip()):
        return None
    return tuple(int(part) for part in text.strip().split("."))


def release_version(version: str, sys_version: str) -> tuple[int, ...] | None:
    """A registered runtime's version, or None for a test release, which setup never picks.
    Version holds the full version, such as 3.14.8, and SysVersion only its first two parts, such
    as 3.14, so SysVersion stands in when Version is missing or in a form of its own."""
    if TEST_RELEASE.fullmatch(version.strip()):
        return None
    return parse_version(version) or parse_version(sys_version)


def subkeys(key: "winreg.HKEYType") -> list[str]:
    names: list[str] = []
    index = 0
    while True:
        try:
            names.append(winreg.EnumKey(key, index))
        except OSError:
            return names
        index += 1


def value(key: "winreg.HKEYType", name: str) -> str:
    try:
        found = winreg.QueryValueEx(key, name)[0]
    except OSError:
        return ""
    return found if isinstance(found, str) else ""


def registered_python(
    company_key: "winreg.HKEYType", tag: str
) -> tuple[tuple[int, ...], Path] | None:
    """One runtime's version and folder, from its key under a company, or None when it's a test
    release, older than 3.12, can't be read, or can't be run from its folder."""
    try:
        with winreg.OpenKey(company_key, tag) as tag_key:
            version = release_version(value(tag_key, "Version"), value(tag_key, "SysVersion"))
            if version is None or version < MINIMUM:
                return None
            with winreg.OpenKey(tag_key, "InstallPath") as install:
                exe = value(install, "ExecutablePath")
                if not exe:
                    exe = str(Path(value(install, "")) / "python.exe")
    except OSError:
        return None
    # A Microsoft Store Python runs only through its own alias, never from its folder.
    if not re.search(r"[\\/]python\.exe$", exe, re.IGNORECASE):
        return None
    if re.search(r"[\\/]WindowsApps[\\/]", exe, re.IGNORECASE):
        return None
    return version, Path(exe).parent


def registry_pythons() -> list[tuple[tuple[int, ...], Path]]:
    """The version and folder of each runtime in the registry, newest first, which covers both
    the traditional installer and the Python install manager."""
    if sys.platform != "win32":
        return []
    found: list[tuple[tuple[int, ...], Path]] = []
    roots = [(winreg.HKEY_CURRENT_USER, REGISTRY_ROOTS[0])]
    roots += [(winreg.HKEY_LOCAL_MACHINE, root) for root in REGISTRY_ROOTS]
    for hive, root_path in roots:
        try:
            root = winreg.OpenKey(hive, root_path)
        except OSError:
            continue
        with root:
            for company in subkeys(root):
                # PyLauncher registers the py launcher, not a Python.
                if company == "PyLauncher":
                    continue
                try:
                    with winreg.OpenKey(root, company) as company_key:
                        for tag in subkeys(company_key):
                            runtime = registered_python(company_key, tag)
                            if runtime is not None:
                                found.append(runtime)
                except OSError:
                    # A key this user can't open is skipped, as any other runtime that can't be
                    # used.
                    continue
    found.sort(key=lambda pair: pair[0], reverse=True)
    runtimes: list[tuple[tuple[int, ...], Path]] = []
    for version, folder in found:
        if all(folder != listed for _, listed in runtimes):
            runtimes.append((version, folder))
    return runtimes


def registered_version(folder: Path) -> str | None:
    """The version the registry gives the runtime in a folder, such as 3.14.8, or None when it
    lists no runtime there."""
    for version, runtime in registry_pythons():
        if same_path(runtime, folder):
            return ".".join(str(part) for part in version)
    return None


def candidates(local_app_data: Path, *, skip_registry: bool) -> Iterator[Path]:
    """Folders that may hold a Python 3.12 or later as python.exe, best first. First the Python
    install manager's folder for its commands, whose python.exe runs its default Python: the
    newest stable one installed, unless the person picked another. Then the stable runtimes in
    the registry, newest first, read only when the first won't do. With skip_registry, as for a
    test profile, only the first, since tests can't add registry entries."""
    yield local_app_data / "Python" / "bin"
    if not skip_registry:
        for _, folder in registry_pythons():
            yield folder


def python_version(folder: Path) -> str | None:
    """The version of the python.exe in a folder, such as 3.14.8, when it runs and is 3.12 or
    later, or None. This starts that Python, so setup asks only about one it would link to."""
    exe = folder / "python.exe"
    if not exe.is_file():
        return None
    check = f"import sys; v = sys.version_info; print(v >= {MINIMUM!r}, '%d.%d.%d' % v[:3])"
    try:
        done = subprocess.run(
            [str(exe), "-I", "-c", check],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=CHECK_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    words = done.stdout.split()
    if done.returncode == 0 and len(words) >= 2 and words[-2] == "True":
        return words[-1]
    return None


def fingerprint(folder: Path) -> list[int] | None:
    """What tells setup that the python.exe in a folder has changed since it last checked it,
    such as by an update: its size and the time it was last changed. None when it can't be
    read."""
    try:
        info = (folder / "python.exe").stat()
    except OSError:
        return None
    return [info.st_size, info.st_mtime_ns]


def failure_key(folder: Path) -> str:
    """How the note of failed checks names a folder, the same whatever its case."""
    return os.path.normcase(str(folder))


def read_failures(path: Path) -> dict[str, list[int]]:
    """The Pythons that didn't run when setup last checked them, each by its folder (see
    failure_key), with its python.exe's fingerprint at the time. A note that's missing or can't
    be read counts as none."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        folder: found
        for folder, found in data.items()
        if isinstance(found, list) and all(type(part) is int for part in found)
    }
