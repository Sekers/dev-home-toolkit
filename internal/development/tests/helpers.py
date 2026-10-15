"""What the tests share: sandboxes, running scripts as agents run them, and reading scripts' code.

A test never runs the scripts in this repo. It builds a sandbox under
internal/development/.test-sandbox/, which git ignores: a copy of this repo's working tree
(uncommitted changes included, development tools left out), a scratch profile, a
dev-home with some content, and local bare repos standing in for GitHub. The copy's
local-settings.json sets testHomeDir before anything in the copy runs, so every setup run from
it, including the ones sync.py and update.py start, uses the scratch profile instead of the
real one. run refuses a script outside a sandbox. Nothing here uses the network or GitHub.

The skills' commands are taken word for word from the sandbox's generated skills. They start
with internal/.python/python.exe, a junction setup makes. A virtual environment's python.exe
can't run through a junction, so the tests start each command with this environment's own
Python instead, by its real path, which lets coverage measure the scripts. One test runs a
command unchanged.
"""

import ast
import contextlib
import importlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import uuid
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import pytest

from read_only_launcher import DLL_CALLS, FAILED, GIT_READS, PROGRAMS

# This file is in internal/development/tests/, three folders below the repo's root.
REPO_ROOT = Path(__file__).resolve().parents[3]
SANDBOX_ROOT = REPO_ROOT / "internal" / "development" / ".test-sandbox"
# Runs a script that should only report with Python's audit hooks watching it.
LAUNCHER = Path(__file__).resolve().with_name("read_only_launcher.py")

# What a sandbox's copy leaves out, by its path in the repo: what belongs to this PC (including
# the Python link, which would copy the Python install), and everything for development, the
# sandboxes among it. Python's __pycache__ folders are left out wherever they are, and so is
# everything in the root whose name starts with SETTINGS_FILES: this PC's settings, their dated
# backups, and the new copy a save leaves beside them.
NOT_COPIED = {
    ".git",
    "internal/.generated",
    "internal/.python",
    "internal/development",
}
SETTINGS_FILES = "local-settings.json"


@dataclass(frozen=True)
class Sandbox:
    """A sandbox's folders. tools is the copy of this repo, and content its dev-home."""

    root: Path

    @property
    def tools(self) -> Path:
        return self.root / "tools"

    @property
    def profile(self) -> Path:
        return self.root / "profile"

    @property
    def content(self) -> Path:
        return self.root / "dev-home"

    @property
    def remote(self) -> Path:
        return self.root / "dev-home-remote.git"

    @property
    def tools_remote(self) -> Path:
        return self.root / "tools-remote.git"

    @property
    def upstream(self) -> Path:
        """A second clone of tools_remote, standing in for the developer pushing updates."""
        return self.root / "tools-upstream"

    @property
    def generated(self) -> Path:
        return self.tools / "internal" / ".generated"

    @property
    def python(self) -> Path:
        """The Python link's python.exe, which every skill command starts with."""
        return self.tools / "internal" / ".python" / "python.exe"

    @property
    def python_bin(self) -> Path:
        """Where setup looks for the Python install manager's shortcuts in this profile."""
        return self.profile / "AppData" / "Local" / "Python" / "bin"


@dataclass(frozen=True)
class Run:
    """A finished run: its exit code, and its output and errors as lines, read as UTF-8."""

    code: int
    lines: list[str]
    facts: dict[str, str] = field(init=False)
    keys: list[str] = field(init=False)

    def __post_init__(self) -> None:
        # Each "key: value" line. A key printed more than once keeps its last value.
        facts: dict[str, str] = {}
        keys: list[str] = []
        for line in self.lines:
            match = re.fullmatch(r"([\w-]+): (.*)", line)
            if match:
                facts[match.group(1)] = match.group(2)
                keys.append(match.group(1))
        object.__setattr__(self, "facts", facts)
        object.__setattr__(self, "keys", keys)

    def has_line(self, pattern: str) -> bool:
        return any(re.search(pattern, line) for line in self.lines)

    def __str__(self) -> str:
        return f"exit code {self.code}:\n" + "\n".join(self.lines)


def make_junction(link: Path, target: Path) -> None:
    """A directory junction, which needs no Developer Mode."""
    link.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


def link_target(path: Path) -> Path | None:
    """Where a link points, without the \\\\?\\ that Windows puts before a junction's target, or
    None when path isn't a link."""
    try:
        target = str(path.readlink())
    except OSError:
        return None
    return Path(target.removeprefix("\\\\?\\"))


def shared_module(box: "Sandbox", name: str) -> ModuleType:
    """A module of the sandbox copy's internal/shared/, loaded into this process, under a
    package name of the sandbox's own, for a test that has to change something inside it, such
    as a fake for the person at the console."""
    folder = box.tools / "internal" / "shared"
    package = "shared_" + box.root.name.replace("-", "_")
    if package not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            package, folder / "__init__.py", submodule_search_locations=[str(folder)]
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[package] = module
        spec.loader.exec_module(module)
    return importlib.import_module(f"{package}.{name}")


def remove_link(link: Path) -> None:
    """Removes a link without touching what it points to."""
    if os.path.isjunction(link):
        link.rmdir()
    elif link.is_symlink():
        try:
            link.unlink()
        except OSError:
            # A symbolic link to a folder, on Windows.
            link.rmdir()


def script_env(sandbox: Sandbox, changes: Mapping[str, str | None] | None = None) -> dict[str, str]:
    """The environment a sandbox's scripts run in. Git stops looking for a repo at the sandbox,
    which is inside this one. CLAUDE_CODE_ENTRYPOINT and CLAUDE_CONFIG_DIR, which the session
    running the tests may have set, are left out: a test that wants a Claude folder from
    CLAUDE_CONFIG_DIR passes one in changes."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CONFIG_DIR")
    }
    env["GIT_CEILING_DIRECTORIES"] = sandbox.root.as_posix()
    for key, value in (changes or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def git(*args: str, cwd: Path | None = None, env: Mapping[str, str] | None = None) -> list[str]:
    """Runs git for building and checking sandboxes, and fails the test when git fails."""
    done = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false", *args],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if done.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {done.stdout}{done.stderr}")
    return done.stdout.splitlines()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def new_sandbox(name: str, *, tools_repo: bool = False) -> Sandbox:
    """Builds a sandbox. The copy's local-settings.json, with testHomeDir, is written before
    anything in the copy can run. With tools_repo, the copy is also a git repo with a remote,
    as a clone of dev-home-tools is, and upstream is a second clone of that remote. The
    profile's Python install manager folder is a junction to this environment's base Python,
    which setup links the copy's internal/.python to."""
    box = Sandbox(SANDBOX_ROOT / f"py-{name}-{uuid.uuid4().hex[:8]}")
    box.root.mkdir(parents=True)

    def leave_out(folder: str, names: list[str]) -> set[str]:
        here = Path(folder).relative_to(REPO_ROOT)
        return {
            n
            for n in names
            if n == "__pycache__"
            or (here / n).as_posix() in NOT_COPIED
            or (here == Path() and n.startswith(SETTINGS_FILES))
        }

    shutil.copytree(REPO_ROOT, box.tools, ignore=leave_out)
    settings = {
        "schemaVersion": 1,
        "devHome": {"folder": box.content.as_posix()},
        "updates": {"installAutomatically": False},
        "claudeCode": {"folders": {"~/.claude": {"setUp": True}}},
        "testHomeDir": box.profile.as_posix(),
    }
    write_text(box.tools / "local-settings.json", json.dumps(settings, indent=2) + "\n")

    # A scratch profile whose settings already have what setup checks for, so a clean run
    # exits 0.
    claude = {"permissions": {"additionalDirectories": [str(box.content), str(box.tools)]}}
    write_text(box.profile / ".claude" / "settings.json", json.dumps(claude, indent=2) + "\n")
    write_text(
        box.profile / ".codex" / "config.toml",
        "project_doc_max_bytes = 65536\n\n[sandbox_workspace_write]\n"
        f"writable_roots = ['{box.content}']\n",
    )
    make_junction(box.python_bin, Path(sys.base_prefix))

    # dev-home, with a remote and some content.
    git("init", "--quiet", "--bare", "-b", "main", str(box.remote))
    git("clone", "--quiet", str(box.remote), str(box.content))
    # Several active copies, so a sync fetches every time unless a test says otherwise.
    files = {
        "dev-home.json": '{\n  "schemaVersion": 1,\n  "multiMachine": true\n}\n',
        "global-rules/global-rules.md": "# My rules\n\n- Personal rule one.\n",
        "knowledge/README.md": "# Knowledge base\n",
        "handoffs/demo/HANDOFF.md": "# demo handoff\n",
        "skills/mine/SKILL.md": "---\nname: mine\ndescription: A personal test skill.\n---\n",
    }
    for relative, text in files.items():
        write_text(box.content / relative, text)
    git("-C", str(box.content), "add", "--", *files)
    git("-C", str(box.content), "commit", "--quiet", "-m", "test: content")
    git("-C", str(box.content), "push", "--quiet", "-u", "origin", "main")

    if tools_repo:
        git("-C", str(box.tools), "init", "--quiet", "-b", "main")
        git("-C", str(box.tools), "add", "-A")
        git("-C", str(box.tools), "commit", "--quiet", "-m", "test: tools")
        git("init", "--quiet", "--bare", "-b", "main", str(box.tools_remote))
        git("-C", str(box.tools), "remote", "add", "origin", str(box.tools_remote))
        git("-C", str(box.tools), "push", "--quiet", "-u", "origin", "main")
        git("clone", "--quiet", str(box.tools_remote), str(box.upstream))
    return box


def sandbox_for(
    request: pytest.FixtureRequest, name: str, *, tools_repo: bool = False
) -> Iterator[Sandbox]:
    """A sandbox for a module's tests, after one setup run, which must exit 0. It's deleted
    afterwards when they all pass, and kept for a look when one fails."""
    box = new_sandbox(name, tools_repo=tools_repo)
    failed = request.session.testsfailed
    setup = run_python(box, "setup.py", "--quiet")
    assert setup.code == 0, str(setup)
    yield box
    if request.session.testsfailed > failed:
        print(f"Sandbox kept: {box.root}")
    else:
        remove_sandbox(box)


def remove_sandbox(box: Sandbox) -> None:
    """Deletes a sandbox. Links go first, one by one and without following them, so deleting
    the rest can't reach anything a link points to, such as a Python install."""
    root = box.root.resolve()
    if SANDBOX_ROOT.resolve() not in root.parents:
        raise AssertionError(f"Refusing to delete {root}, which is not in {SANDBOX_ROOT}.")

    def links(folder: Path) -> Iterator[Path]:
        for entry in os.scandir(folder):
            path = Path(entry.path)
            if entry.is_symlink() or os.path.isjunction(path):
                yield path
            elif entry.is_dir():
                yield from links(path)

    for link in list(links(root)):
        remove_link(link)

    def make_writable(function: Callable[..., object], path: str, _error: BaseException) -> None:
        # Git makes its object files read-only.
        Path(path).chmod(stat.S_IWRITE)
        function(path)

    shutil.rmtree(root, onexc=make_writable)
    # Other tests may be running at the same time, and one may have just made its sandbox here.
    with contextlib.suppress(OSError):
        SANDBOX_ROOT.rmdir()


def check_in_sandbox(argv: list[str]) -> None:
    """Refuses to run a script outside a sandbox, other than the tests' own launcher."""
    for word in argv:
        if word.endswith(".py"):
            path = Path(word).resolve()
            if path != LAUNCHER and SANDBOX_ROOT.resolve() not in path.parents:
                raise AssertionError(f"Refusing to run {path}, which is not in a sandbox.")


def run(
    box: Sandbox,
    argv: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str | None] | None = None,
    answer: str | None = None,
) -> Run:
    """Runs a command as an agent's shell tool does: input from nowhere, so a script can never
    wait for an answer, and its output and errors together, read as UTF-8. With answer, that's
    its input instead, as a person typing it."""
    check_in_sandbox(argv)
    done = subprocess.run(
        argv,
        cwd=cwd,
        env=script_env(box, env),
        input=None if answer is None else (answer + "\n").encode("utf-8"),
        stdin=subprocess.DEVNULL if answer is None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return Run(done.returncode, done.stdout.decode("utf-8", errors="replace").splitlines())


def run_python(
    box: Sandbox,
    script: str,
    *args: str,
    cwd: Path | None = None,
    env: Mapping[str, str | None] | None = None,
    answer: str | None = None,
) -> Run:
    """Runs one of the sandbox copy's Python scripts in its root, such as sync.py, as the skills
    do, with this environment's Python (see the description above)."""
    argv = [sys.executable, "-I", str(box.tools / script), *args]
    return run(box, argv, cwd=cwd or box.root, env=env, answer=answer)


def start_python(box: Sandbox, script: str, *args: str) -> subprocess.Popen[bytes]:
    """Starts one of the sandbox copy's Python scripts in its root without waiting for it, as
    run_python runs it, with its output and errors together."""
    argv = [sys.executable, "-I", str(box.tools / script), *args]
    check_in_sandbox(argv)
    return subprocess.Popen(
        argv,
        cwd=box.root,
        env=script_env(box),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def finish(process: subprocess.Popen[bytes]) -> Run:
    """Waits for a process start_python started, and returns how it ended."""
    out, _ = process.communicate(timeout=120)
    return Run(process.returncode, out.decode("utf-8", errors="replace").splitlines())


def run_while_asking(
    box: Sandbox, script: str, *, prompt: str, answer: str, meanwhile: Callable[[], None]
) -> Run:
    """Runs one of the sandbox copy's Python scripts, waits for the output line that matches
    prompt, which comes just before its question, calls meanwhile, then answers."""
    argv = [sys.executable, "-I", str(box.tools / script)]
    check_in_sandbox(argv)
    process = subprocess.Popen(
        argv,
        cwd=box.root,
        env=script_env(box),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert process.stdin is not None and process.stdout is not None
    lines: list[str] = []
    try:
        while True:
            raw = process.stdout.readline()
            if not raw:
                raise AssertionError(
                    f"never reached a line matching {prompt}:\n" + "\n".join(lines)
                )
            lines.append(raw.decode("utf-8", errors="replace").rstrip("\r\n"))
            if re.search(prompt, lines[-1]):
                break
        meanwhile()
        rest, _ = process.communicate((answer + "\n").encode("utf-8"), timeout=120)
    finally:
        if process.poll() is None:
            process.kill()
    lines.extend(rest.decode("utf-8", errors="replace").splitlines())
    return Run(process.returncode, lines)


def skill_command(box: Sandbox, skill: str, script: str, *, containing: str = "") -> str:
    """The command a sandbox's generated skill gives for a script, word for word: one of the
    shared scripts, or one in the skill's own folder. A skill may give the same command more than
    once, but only one that contains the text given, such as the knowledge skill's
    "--fetch auto"."""
    text = (box.generated / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    python = box.python.as_posix()
    folders = (box.generated / "shared-skill-scripts", box.generated / "skills" / skill)
    paths = "|".join(re.escape((folder / script).as_posix()) for folder in folders)
    pattern = rf"`({re.escape(python)} -I (?:{paths})[^`]*)`"
    commands: set[str] = {
        match.group(1) for match in re.finditer(pattern, text) if containing in match.group(1)
    }
    assert len(commands) == 1, f"{skill} gives {len(commands)} commands for {script}: {commands}"
    return commands.pop()


def run_command(
    box: Sandbox,
    command: str,
    *,
    cwd: Path,
    env: Mapping[str, str | None] | None = None,
    through_link: bool = False,
) -> Run:
    """Runs a skill's command. Its paths have no spaces, so it splits on them. Unless
    through_link, it starts with this environment's Python, by its real path, in place of the
    sandbox's internal/.python/python.exe (see the description above), and a script that should
    only report, such as facts.py, runs through the launcher that watches it, failing the test
    at anything it changes."""
    words = command.split(" ")
    assert words[0] == box.python.as_posix() and words[1] == "-I", command
    if through_link:
        return run(box, words, cwd=cwd, env=env)
    watched = Path(words[2]).name in PROGRAMS
    words[:2] = [sys.executable, "-I", *([str(LAUNCHER)] if watched else [])]
    result = run(box, words, cwd=cwd, env=env)
    if any(line.startswith(FAILED) for line in result.lines):
        raise AssertionError(str(result))
    return result


def new_repo(
    box: Sandbox, name: str, *, origin: str | None = None, commits: tuple[str, ...] = ("first",)
) -> Path:
    """A project repo in the sandbox, beside its dev-home, with empty commits."""
    repo = box.root / name
    git("init", "--quiet", "-b", "main", str(repo))
    for message in commits:
        git("-C", str(repo), "commit", "--quiet", "--allow-empty", "-m", f"test: {message}")
    if origin is not None:
        git("-C", str(repo), "remote", "add", "origin", origin)
    return repo


# ---------------------------------------------------------------------------------------------
# Reading scripts' code without running it


def call_name(node: ast.Call) -> str:
    """A call's dotted name, such as os.environ.get, or empty text when it has none."""
    parts: list[str] = []
    target: ast.expr = node.func
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
        return ".".join(reversed(parts))
    return ""


def main_block_nodes(tree: ast.Module) -> set[ast.AST]:
    """Every node inside the module's if __name__ == "__main__": block."""
    inside: set[ast.AST] = set()
    for statement in tree.body:
        if isinstance(statement, ast.If) and "__name__" in ast.unparse(statement.test):
            for node in statement.body:
                inside.update(ast.walk(node))
    return inside


# What a script that only reports may import, and the names it may use from each module, in
# module.name or from module import name. Any other use of these modules, such as passing one
# around, counts as a change, and so does sys.modules or ctypes.WinDLL anywhere but the one place
# allowed_in_place allows it. Adding a name is a safety change: say so in the commit. Calls are
# also checked one by one, below.
REPORTING_NAMES = {
    "__future__": {"annotations"},
    "collections.abc": {"Callable", "Sequence"},
    "ctypes": {"create_unicode_buffer", "c_ulong", "byref", "WinDLL"},
    "dataclasses": {"dataclass"},
    "functools": {"cache"},
    "importlib.util": {"spec_from_file_location", "module_from_spec"},
    "io": {"TextIOWrapper"},
    "json": {"loads", "dumps"},
    "os": {"environ", "path", "pathsep", "sep", "getcwd", "uname", "fspath"},
    "pathlib": {"Path"},
    "re": {"IGNORECASE", "Match", "compile", "escape", "fullmatch", "match", "search", "sub"},
    "shutil": {"which"},
    "subprocess": {"run", "DEVNULL", "TimeoutExpired"},
    "sys": {"argv", "exit", "modules", "platform", "stderr", "stdout"},
    "types": {"ModuleType"},
    "typing": {"Any"},
    "urllib.parse": {"quote", "unquote"},
}
# The methods a script that only reports may call on an object, as obj.name(...); any other
# method fails. Calls on a module are checked against REPORTING_NAMES instead. A name means the
# same whatever the object, so each must be safe on any object that has it. replace counts only
# with two arguments or more, the form str.replace takes: Path.replace takes one, and moves a
# file. Adding a name is a safety change: say so in the commit.
REPORTING_METHODS = {
    # Text.
    "endswith",
    "isspace",
    "join",
    "lower",
    "replace",
    "rstrip",
    "split",
    "splitlines",
    "startswith",
    "strip",
    # The script's own lists, dicts, and sets, in memory.
    "add",
    "append",
    "extend",
    "fromkeys",
    "get",
    "index",
    "insert",
    "items",
    "pop",
    "setdefault",
    "values",
    # Regular expressions and their matches.
    "end",
    "finditer",
    "group",
    "match",
    "search",
    "start",
    # Paths, read only.
    "cwd",
    "is_absolute",
    "is_dir",
    "is_file",
    "iterdir",
    "read_text",
    # The output streams, given a new encoding.
    "reconfigure",
    # issue_status.py loading facts.py, which this check reads too, and calling its functions.
    "exec_module",
    "find_handoff_place",
    "find_program",
}
# The data attributes a script that only reports may read from Python's own objects, such as a
# finished program's returncode. An attribute read without a call must be one of these, a method
# in REPORTING_METHODS, or a name the script defines itself, such as a field of its own
# dataclass (see defined_names). Adding a name is a safety change: say so in the commit.
REPORTING_ATTRIBUTES = {
    # A finished program: its exit code and output.
    "returncode",
    "stderr",
    "stdout",
    # A path's folder.
    "parent",
    # A class's name, such as an error's.
    "__name__",
    # The computer's name from os.uname(), and the text a DLL function wrote to a buffer.
    "nodename",
    "value",
    # What loads a module from its file, and the module's name, for issue_status.py loading
    # facts.py.
    "loader",
    "name",
}
# Built-ins that write, run code, or reach a method or a name by text, past both lists, and
# __builtins__, which hands out all of them. Any mention fails, not only a call, so none can be
# given another name first.
CHANGING_BUILTINS = {
    "__builtins__",
    "open",
    "exec",
    "eval",
    "compile",
    "__import__",
    "breakpoint",
    "getattr",
    "setattr",
    "delattr",
    "vars",
    "globals",
    "locals",
}
ENVIRON_CHANGES = {"update", "pop", "popitem", "setdefault", "clear", "__setitem__", "__delitem__"}
# The one function that may start each program. run_git's callers must name a command in
# GIT_READS; run_gh may only send a GraphQL request, and the tests that fake gh check that each
# query only reads.
PROGRAM_RUNNERS = {"run_git", "run_gh"}


def runs_gh_graphql(node: ast.Call) -> bool:
    """Whether a call inside run_gh starts gh as gh api graphql -f query=<text>: the query in
    the command, where the launcher and the tests that fake gh can check it, never in a file."""
    command = node.args[0] if node.args else None
    if not isinstance(command, ast.List) or len(command.elts) != 5:
        return False
    words = [e.value if isinstance(e, ast.Constant) else None for e in command.elts[1:4]]
    query = command.elts[4]
    if isinstance(query, ast.JoinedStr) and query.values:
        query = query.values[0]
    return (
        words == ["api", "graphql", "-f"]
        and isinstance(query, ast.Constant)
        and str(query.value).startswith("query=")
    )


def is_changing_call(node: ast.Call, runner: str | None, modules: Collection[str]) -> bool:
    """Whether a call may change something or reach the network (see the function below).
    runner is the program runner the call is inside, if any, and modules the names that stand
    for modules (see module_names)."""
    name = call_name(node)
    func = node.func
    method = func.attr if isinstance(func, ast.Attribute) else ""
    owner = func.value if isinstance(func, ast.Attribute) else None
    if isinstance(owner, ast.Call) and call_name(owner) == "ctypes.WinDLL":
        # A function from a Windows DLL, such as ctypes.WinDLL("kernel32").Function().
        return method not in DLL_CALLS
    if name.startswith("subprocess."):
        return not (runner == "run_git" or (runner == "run_gh" and runs_gh_graphql(node)))
    if name == "run_git":
        words = [str(a.value) for a in node.args[:2] if isinstance(a, ast.Constant)]
        return not ({words[0] if words else "", " ".join(words)} & GIT_READS)
    if name.startswith("importlib") and not name.startswith("importlib.util."):
        # What importlib.util offers is checked against REPORTING_NAMES.
        return True
    if name.startswith("os.environ.") and method in ENVIRON_CHANGES:
        return True
    if not method or name.split(".")[0] in modules:
        # A function by its own name, or one of a module's, which REPORTING_NAMES checks.
        return False
    if method == "replace":
        return len(node.args) < 2
    return method not in REPORTING_METHODS


def module_names(tree: ast.Module) -> dict[str, list[str]]:
    """Each name in the script that stands for a module REPORTING_NAMES lists, with the modules
    it may stand for: each module's first word, such as os or importlib for importlib.util, and
    the name an import gives a module with as."""
    names: dict[str, list[str]] = {}
    for module in REPORTING_NAMES:
        names.setdefault(module.split(".")[0], []).append(module)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname and alias.name in REPORTING_NAMES:
                    names[alias.asname] = [alias.name]
    return names


def allowed_in_place(module: str, name: str, use: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """Whether an allowed name is used where it's allowed. sys.modules can hand out any module,
    ctypes.WinDLL any function of a DLL, and os.environ a way to change the environment once
    it's given another name, so each is allowed only where it can't: sys.modules[name] = module;
    ctypes.WinDLL(dll).Function(...) with a function in DLL_CALLS, the functions the launcher
    allows too; and os.environ read in place, as os.environ.get(...), os.environ[name],
    name in os.environ, or os.environ | other."""
    parent = parents.get(use)
    if (module, name) == ("sys", "modules"):
        return isinstance(parent, ast.Subscript) and isinstance(parent.ctx, ast.Store)
    if (module, name) == ("os", "environ"):
        if isinstance(parent, ast.Attribute):
            return parent.attr == "get" and isinstance(parents.get(parent), ast.Call)
        if isinstance(parent, ast.Subscript):
            return isinstance(parent.ctx, ast.Load)
        return isinstance(parent, ast.Compare) or (
            isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.BitOr)
        )
    if (module, name) == ("ctypes", "WinDLL"):
        method = parents.get(parent) if isinstance(parent, ast.Call) else None
        return (
            isinstance(method, ast.Attribute)
            and method.attr in DLL_CALLS
            and isinstance(parents.get(method), ast.Call)
        )
    return True


def find_disallowed_module_uses(tree: ast.Module) -> list[ast.AST]:
    """Each use of a module REPORTING_NAMES lists that isn't module.name with a name it allows,
    in a place it allows it (see allowed_in_place), such as os.remove, or os itself passed to a
    function or given another name."""
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    names = module_names(tree)
    found: list[ast.AST] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Name) or node.id not in names:
            continue
        # The attributes after the name, with the node that ends at each: for os.path.join,
        # path then join.
        parts = [node.id]
        ends: list[ast.AST] = [node]
        while isinstance(parent := parents.get(ends[-1]), ast.Attribute) and (
            parent.value is ends[-1]
        ):
            parts.append(parent.attr)
            ends.append(parent)
        for module in sorted(names[node.id], key=len, reverse=True):
            # The words after the module's own: for importlib.util.module_from_spec, the
            # module is importlib.util and the name module_from_spec.
            words = module.split(".")
            rest = parts[len(words) :]
            if parts[1 : len(words)] == words[1:] and rest:
                use = ends[len(words)]
                if rest[0] not in REPORTING_NAMES[module] or not allowed_in_place(
                    module, rest[0], use, parents
                ):
                    found.append(node)
                break
        else:
            found.append(node)
    return found


def defined_names(tree: ast.Module) -> set[str]:
    """The names a script defines: its functions, classes, and module-level names, and the
    fields, names, and methods of its classes."""
    names: set[str] = set()
    bodies = [tree.body] + [n.body for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    for body in bodies:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            targets = node.targets if isinstance(node, ast.Assign) else []
            if isinstance(node, ast.AnnAssign):
                targets = [node.target]
            names.update(t.id for t in targets if isinstance(t, ast.Name))
    return names


def find_disallowed_attributes(
    tree: ast.Module, modules: Collection[str], defined: Collection[str]
) -> list[ast.AST]:
    """Each attribute of an object, not a module, read without calling it, that isn't in
    REPORTING_ATTRIBUTES, a method in REPORTING_METHODS, or a name in defined. A method called
    is checked by is_changing_call instead. This is what stops a method being used by
    reference, as in map(Path.unlink, files). replace counts only when called, where its
    arguments tell str.replace from Path.replace."""
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    allowed = (REPORTING_METHODS - {"replace"}) | REPORTING_ATTRIBUTES | set(defined)
    found: list[ast.AST] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or node.attr in allowed:
            continue
        root = node.value
        while isinstance(root, ast.Attribute):
            root = root.value
        parent = parents.get(node)
        called = isinstance(parent, ast.Call) and parent.func is node
        if not called and not (isinstance(root, ast.Name) and root.id in modules):
            found.append(node)
    return found


def find_changes_or_network_use(
    tree: ast.Module, programs: Collection[str] = ("git", "gh"), loads: Sequence[ast.Module] = ()
) -> list[ast.AST]:
    """Where a script that should only report changes something or reaches the network, as far
    as its code can show: an import of a module REPORTING_NAMES doesn't list, or a name from one
    that it doesn't allow; a DLL call beyond DLL_CALLS; a method on an object that
    REPORTING_METHODS doesn't list, or an attribute read that find_disallowed_attributes doesn't
    allow; open, exec, getattr, and the like; a change to os.environ; or a program started,
    unless it's one of the programs given, started by its runner: git by run_git with a command
    that only reads, or gh api graphql by run_gh. loads are the scripts it loads, whose names
    it may read too, as issue_status.py reads facts.py's."""
    found: list[ast.AST] = find_disallowed_module_uses(tree)
    modules = module_names(tree)
    defined = set().union(*(defined_names(t) for t in (tree, *loads)))
    found.extend(find_disallowed_attributes(tree, modules, defined))
    runners: dict[ast.AST, str] = {}
    allowed_runners = {f"run_{program}" for program in programs} & PROGRAM_RUNNERS
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in allowed_runners:
            runners.update(dict.fromkeys(ast.walk(node), node.name))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(node for alias in node.names if alias.name not in REPORTING_NAMES)
        elif isinstance(node, ast.ImportFrom):
            allowed = REPORTING_NAMES.get(node.module or "") if node.level == 0 else None
            if allowed is None or any(alias.name not in allowed for alias in node.names):
                found.append(node)
        elif (
            isinstance(node, ast.Call) and is_changing_call(node, runners.get(node), modules)
        ) or (isinstance(node, ast.Name) and node.id in CHANGING_BUILTINS):
            found.append(node)
        elif isinstance(node, (ast.Assign, ast.AugAssign, ast.Delete)):
            targets = node.targets if isinstance(node, (ast.Assign, ast.Delete)) else [node.target]
            for target in targets:
                if isinstance(target, ast.Subscript) and ast.unparse(target.value) == "os.environ":
                    found.append(node)
    return found


# Calls that change what a whole process shares, by their dotted name or its start.
PROCESS_WIDE_CALLS = (
    "os.chdir",
    "os.putenv",
    "os.unsetenv",
    "os.umask",
    "sys.setrecursionlimit",
    "sys.setswitchinterval",
    "locale.setlocale",
    "signal.signal",
    "atexit.register",
    "codecs.register",
)
PROCESS_WIDE_METHODS = {
    "sys.stdout": {"reconfigure"},
    "sys.stderr": {"reconfigure"},
    "sys.stdin": {"reconfigure"},
    "sys.path": {"append", "insert", "extend", "remove", "pop", "clear"},
    "sys.modules": {"pop", "update", "setdefault", "clear", "__setitem__"},
    "os.environ": ENVIRON_CHANGES,
}


def find_process_wide_changes(tree: ast.Module) -> list[ast.AST]:
    """Where a script changes what its whole process shares, outside the block that runs only
    when it's run as a script: environment variables, the current folder, the import path,
    sys's streams, or anything else assigned in sys or os."""
    main_block = main_block_nodes(tree)
    found: list[ast.AST] = []
    for node in ast.walk(tree):
        if node in main_block:
            continue
        if isinstance(node, ast.Call):
            name = call_name(node)
            owner, _, method = name.rpartition(".")
            if name.startswith(PROCESS_WIDE_CALLS) or method in PROCESS_WIDE_METHODS.get(owner, ()):
                found.append(node)
        elif isinstance(node, (ast.Assign, ast.AugAssign, ast.Delete)):
            targets = node.targets if isinstance(node, (ast.Assign, ast.Delete)) else [node.target]
            for target in targets:
                text = ast.unparse(target)
                if text.startswith(("sys.", "os.")):
                    found.append(node)
    return found


def non_standard_imports(tree: ast.Module) -> list[str]:
    """Each module a script imports that isn't part of Python's standard library."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module)
    return [n for n in names if n.split(".")[0] not in sys.stdlib_module_names]
