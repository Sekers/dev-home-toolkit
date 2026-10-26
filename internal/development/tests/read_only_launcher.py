"""Runs a script that should only report, such as facts.py, with Python's audit hooks watching
what it does, for the tests. The test helpers run every direct run of such a script through it:

    python -I read_only_launcher.py <script> <its arguments>

Every kind of audit event is sorted into one of three groups:

- harmless: HARMLESS, kinds that can't change anything or reach the network
- checked by its arguments, such as open, which may read but not write, and subprocess.Popen,
  which may start only the programs PROGRAMS allows the script, doing only what they may
- forbidden: CHANGES, ENVIRONMENT_CHANGES, PROGRAM_STARTS, and NETWORK

The run stops at once, with a line starting FAILED and exit code EXIT_CODE, at a forbidden event,
a checked one whose arguments aren't allowed, or a kind that isn't sorted yet, such as one a new
Python version or another operating system raises. Sorting a new kind as harmless is a safety
change: say so in the commit. Python's own writes to __pycache__ are allowed. Watching stops when
the script ends, so what runs after it, such as coverage saving its data, is never checked. The
tests' reading of the code (find_changes_or_network_use in helpers.py) is the other layer.

It imports only the standard library, since it runs in the watched process.
"""

import os
import re
import runpy
import sys
from pathlib import PurePath

# What git may be asked to do: the first word, or first two, of a git command that only reads.
GIT_READS = {"rev-parse", "rev-list", "cat-file", "merge-base", "remote get-url"}
# The programs each script may start, by its file name. Only these scripts can be watched.
PROGRAMS: dict[str, set[str]] = {"facts.py": {"git"}, "issue_status.py": {"git", "gh"}}
# The Windows DLLs a script may load, and the functions it may call from them: none today.
DLLS: set[str] = set()
DLL_CALLS: set[str] = set()
# What ctypes looks up in a DLL for itself.
CTYPES_OWN_LOOKUPS = {"GetLastError"}
FAILED = "FAILED: read-only check:"
EXIT_CODE = 97
UNSORTED = (
    "raises a kind of audit event read_only_launcher.py hasn't sorted. If it can't change "
    "anything or reach the network, add it to HARMLESS there, and say in the commit that it's a "
    "safety change; if it can, add it to the forbidden events"
)

# Kinds that can't change anything or reach the network, each seen in a normal run.
HARMLESS = {
    # Python running code: compiling, importing, and loading compiled modules, or preparing one
    # to save, which open, checked below, then saves.
    "compile",
    "exec",
    "import",
    "marshal.dumps",
    "marshal.loads",
    # Reading Python's own state, such as coverage looking at the code it measures.
    "builtins.id",
    "object.__setattr__",
    "sys._getframe",
    "sys._getframemodulename",
    # Listing a folder.
    "os.listdir",
    "os.scandir",
    # subprocess reading a program's output: a pipe, wrapped as a file, read on a thread.
    "_thread.start_joinable_thread",
    "_winapi.CreatePipe",
    "msvcrt.open_osfhandle",
    # Reading the computer's host name, which sends nothing over the network.
    "socket.gethostname",
}

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
# What a Windows file handle asks for that can change the file: GENERIC_WRITE, GENERIC_ALL,
# MAXIMUM_ALLOWED, DELETE, WRITE_DAC, WRITE_OWNER, FILE_WRITE_DATA, FILE_APPEND_DATA,
# FILE_WRITE_EA, and FILE_WRITE_ATTRIBUTES; and FILE_FLAG_DELETE_ON_CLOSE. Any way of opening it
# other than OPEN_EXISTING may create or empty it.
WINDOWS_WRITE_ACCESS = 0x40000000 | 0x10000000 | 0x02000000 | 0x000D0000 | 0x00000116
WINDOWS_DELETE_ON_CLOSE = 0x04000000
WINDOWS_OPEN_EXISTING = 3
# Kinds that change a file, a folder, the registry, or another process. Python may save its
# compiled modules with some of them, which only_pycache allows.
CHANGES = {
    "mmap.__new__",
    "os.chflags",
    "os.chmod",
    "os.chown",
    "os.kill",
    "os.killpg",
    "os.lchflags",
    "os.link",
    "os.mkdir",
    "os.remove",
    "os.removexattr",
    "os.rename",
    "os.rmdir",
    "os.setxattr",
    "os.symlink",
    "os.truncate",
    "os.utime",
    "shutil.chown",
    "shutil.copyfile",
    "shutil.copymode",
    "shutil.copystat",
    "shutil.copytree",
    "shutil.make_archive",
    "shutil.move",
    "shutil.rmtree",
    "shutil.unpack_archive",
    "_winapi.CopyFile2",
    "_winapi.CreateJunction",
    "_winapi.TerminateProcess",
    "winreg.CreateKey",
    "winreg.DeleteKey",
    "winreg.DeleteValue",
    "winreg.LoadKey",
    "winreg.SaveKey",
    "winreg.SetValue",
}
ENVIRONMENT_CHANGES = {"os.putenv", "os.unsetenv"}
# Kinds that start a program other than through subprocess, whose commands are checked.
PROGRAM_STARTS = {
    "os.exec",
    "os.fork",
    "os.forkpty",
    "os.spawn",
    "os.startfile",
    "os.system",
    "pty.spawn",
}
NETWORK = (
    "ftplib.",
    "http.client.",
    "imaplib.",
    "nntplib.",
    "poplib.",
    "smtplib.",
    "socket.",
    "telnetlib.",
    "urllib.",
    "webbrowser.",
)
# Where subprocess starts the program its subprocess.Popen event was just about, by system.
PROCESS_STARTS = {"_winapi.CreateProcess", "os.posix_spawn", "_posixsubprocess.fork_exec"}


def split_command_line(line: str) -> list[str]:
    """A Windows command line's words, undoing subprocess.list2cmdline: quotes group words, and
    backslashes count as escapes only before a quote."""
    words: list[str] = []
    word: list[str] = []
    quoted = started = False
    slashes = 0
    for c in line:
        if c == "\\":
            slashes += 1
            continue
        if c == '"':
            word.append("\\" * (slashes // 2))
            if slashes % 2:
                word.append('"')
            else:
                quoted, started = not quoted, True
            slashes = 0
            continue
        word.append("\\" * slashes)
        slashes = 0
        if c in " \t" and not quoted:
            # Spaces end a word; "" is an empty word.
            if "".join(word) or started:
                words.append("".join(word))
            word, started = [], False
            continue
        word.append(c)
    word.append("\\" * slashes)
    if "".join(word) or started:
        words.append("".join(word))
    return words


def words_of(args: object) -> list[str]:
    """A command's words as text. subprocess passes the event a list of words, except on
    Windows, where it passes the command line it builds from them."""
    if isinstance(args, str):
        return split_command_line(args) if sys.platform == "win32" else []
    if not isinstance(args, (list, tuple)):
        return []
    return [os.fsdecode(w) if isinstance(w, (str, bytes, os.PathLike)) else "" for w in args]


def allowed_command(args: object, programs: set[str], executable: object = None) -> bool:
    """Whether a command is a program the script may start, doing only what it may ask: git with
    a command in GIT_READS, or gh sending GitHub a GraphQL query that only reads, given in the
    command itself, as gh api graphql -f query=<the query>. executable is the program to start,
    when it isn't the command's first word."""
    words = words_of(args)
    if len(words) < 2:
        return False
    name = PurePath(words[0]).stem.lower()
    if name not in programs:
        return False
    if executable is not None and PurePath(words_of([executable])[0]).stem.lower() != name:
        return False
    if name == "git":
        return words[1] in GIT_READS or " ".join(words[1:3]) in GIT_READS
    if name == "gh":
        if len(words) != 5 or words[1:4] != ["api", "graphql", "-f"]:
            return False
        query = words[4].removeprefix("query=")
        return words[4].startswith("query=query") and not re.search(r"\bmutation\b", query)
    return False


def in_pycache(value: object) -> bool:
    return (
        isinstance(value, (str, bytes, os.PathLike))
        and "__pycache__" in PurePath(os.fsdecode(value)).parts
    )


def only_pycache(args: tuple[object, ...]) -> bool:
    """Whether every path an event names is inside a __pycache__ folder, where Python saves the
    modules it has compiled."""
    paths = [a for a in args if isinstance(a, (str, bytes, os.PathLike))]
    return bool(paths) and all(in_pycache(p) for p in paths)


def opens_for_writing(args: tuple[object, ...]) -> bool:
    """Whether an open event opens a file for writing. A number in place of a path is a
    descriptor already open, such as a pipe to a program: opening one on disk raises its own
    event."""
    path, mode, flags = (*args, None, None, None)[:3]
    if isinstance(path, int):
        return False
    if isinstance(flags, int):
        return bool(flags & WRITE_FLAGS)
    return isinstance(mode, str) and any(c in mode for c in "wax+")


def creates_a_writable_handle(args: tuple[object, ...]) -> bool:
    """Whether a Windows CreateFile event asks for a handle that can change the file, or may
    create or empty it. Its arguments are the path, the access asked for, the sharing, how to
    open it, and the flags."""
    _path, access, _share, disposition, flags = (*args, 0, 0, 0, 0, 0)[:5]
    return (
        not isinstance(access, int)
        or not isinstance(flags, int)
        or bool(access & WINDOWS_WRITE_ACCESS)
        or bool(flags & WINDOWS_DELETE_ON_CLOSE)
        or disposition != WINDOWS_OPEN_EXISTING
    )


class Watch:
    """The audit hook, and what it remembers between events."""

    def __init__(self, programs: set[str]) -> None:
        self.programs = programs
        self.on = True
        # subprocess raises a second event as it starts the program it was allowed to.
        self.process_allowed = False

    def problem(self, event: str, args: tuple[object, ...]) -> str:
        """What's wrong with the event for a read-only script, or empty text."""
        if event in HARMLESS:
            return ""
        # Checked by their arguments.
        if event == "open":
            return "" if not opens_for_writing(args) or only_pycache(args) else "opens a file"
        if event == "_winapi.CreateFile":
            return "opens a file" if creates_a_writable_handle(args) else ""
        if event == "sqlite3.connect":
            # Connecting to a database file creates it when it's missing.
            return "" if args[:1] == (":memory:",) else "opens a database"
        if event == "ctypes.dlopen":
            return "" if args[:1] in {(dll,) for dll in DLLS} else "loads a DLL"
        if event == "ctypes.dlsym":
            name = args[1] if len(args) > 1 else None
            allowed = name in DLL_CALLS or name in CTYPES_OWN_LOOKUPS
            return "" if allowed else "looks up a DLL function"
        if event == "subprocess.Popen":
            executable, command = (*args, None, None)[:2]
            self.process_allowed = allowed_command(command, self.programs, executable)
            return "" if self.process_allowed else "starts a program"
        if event in PROCESS_STARTS:
            allowed, self.process_allowed = self.process_allowed, False
            return "" if allowed else "starts a program"
        if event in CHANGES:
            return "" if only_pycache(args) else "changes a file, a folder, or a process"
        # Forbidden.
        if event in ENVIRONMENT_CHANGES:
            return "changes an environment variable"
        if event in PROGRAM_STARTS:
            return "starts a program"
        if event.startswith(NETWORK):
            return "reaches the network"
        return UNSORTED

    def __call__(self, event: str, args: tuple[object, ...]) -> None:
        if not self.on:
            return
        problem = self.problem(event, args)
        if problem:
            # Only the first two arguments: the path or the command, never an environment.
            sys.stderr.write(f"{FAILED} {problem}: {event} {args[:2]!r:.500}\n")
            sys.stderr.flush()
            os._exit(EXIT_CODE)


def main(argv: list[str]) -> None:
    script = argv[0]
    programs = PROGRAMS.get(PurePath(script).name)
    if programs is None:
        sys.exit(f"read_only_launcher.py watches only {', '.join(sorted(PROGRAMS))}: {script}")
    watch = Watch(programs)
    sys.argv = list(argv)
    sys.addaudithook(watch)
    try:
        runpy.run_path(script, run_name="__main__")
    finally:
        watch.on = False


if __name__ == "__main__":
    main(sys.argv[1:])
