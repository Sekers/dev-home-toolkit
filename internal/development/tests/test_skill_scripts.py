"""The Python scripts and the skills that run them, read without running anything: the skills'
shared scripts in templates/shared-skill-scripts/, the scripts in a skill's own folder, the entry
points in the root, and the code they load from internal/shared/."""

import ast
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from helpers import (
    REPO_ROOT,
    find_changes_or_network_use,
    find_process_wide_changes,
    non_standard_imports,
)
from read_only_launcher import PROGRAMS, allowed_command, split_command_line

SCRIPTS = REPO_ROOT / "templates" / "shared-skill-scripts"
SKILLS = REPO_ROOT / "templates" / "skills"
SHARED = REPO_ROOT / "internal" / "shared"
ENTRY_POINTS = [REPO_ROOT / "setup.py", REPO_ROOT / "sync.py", REPO_ROOT / "update.py"]


def scripts() -> list[Path]:
    return sorted(SCRIPTS.glob("*.py"))


def shared_modules() -> list[Path]:
    return sorted(SHARED.glob("*.py"))


def skill_scripts() -> list[Path]:
    """The scripts in a skill's own folder, which only that skill runs."""
    return sorted(SKILLS.glob("*/*.py"))


def python_files() -> list[Path]:
    """Every Python file that people or skills run."""
    return scripts() + skill_scripts() + shared_modules() + ENTRY_POINTS


def repo_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def skills() -> list[Path]:
    """Each skill, as setup sees one: a folder with a SKILL.md."""
    return sorted(folder for folder in SKILLS.iterdir() if (folder / "SKILL.md").is_file())


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def lines_of(nodes: list[ast.AST], source: Path) -> list[str]:
    text = source.read_text(encoding="utf-8").splitlines()
    numbers = [getattr(node, "lineno", 0) for node in nodes]
    return [f"{source.name}:{n}: {text[n - 1].strip()}" for n in numbers]


@pytest.mark.parametrize("script", scripts(), ids=lambda p: p.name)
def test_each_script_lists_exactly_the_skills_that_run_it(script: Path) -> None:
    # So whoever changes the script knows what depends on it. A skill runs it when any of the
    # skill's files holds its path.
    match = re.search(r"^Called by: (.+)$", script.read_text(encoding="utf-8"), re.MULTILINE)
    listed = sorted(re.split(r",\s*", match.group(1).strip())) if match else []
    needle = "{{SHARED_SKILL_SCRIPTS_DIR}}/" + script.name
    callers = sorted(
        skill.name
        for skill in skills()
        if any(needle in f.read_text(encoding="utf-8") for f in skill.rglob("*") if f.is_file())
    )
    assert listed == callers, f'"Called by: {", ".join(listed)}", but run by: {callers}'


@pytest.mark.parametrize("skill", skills(), ids=lambda p: p.name)
def test_each_shared_script_command_is_stamped_and_pre_approved_word_for_word(
    skill: Path,
) -> None:
    # A command that differs from its pre-approval by one word would ask the user first. Each
    # carries the skill's own name and stamp, which the scripts check against the skill on disk.
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    allowed = re.search(r'^allowed-tools:\s*"(.*)"\s*$', text, re.MULTILINE)
    approvals = allowed.group(1) if allowed else ""
    prefix = "{{PYTHON}} -I {{SHARED_SKILL_SCRIPTS_DIR}}/"
    commands = set(re.findall(rf"`({re.escape(prefix)}[^`]*)`", text))
    assert commands, f"{skill.name} runs no shared script"
    for command in commands:
        script = command[len(prefix) :].split(" ")[0]
        assert (SCRIPTS / script).is_file(), f"{skill.name} runs {script}, which doesn't exist"
        assert f" --skill {skill.name} --stamp {{{{SKILL_STAMP}}}}" in command, command
        assert f"Bash({command})" in approvals, f"not pre-approved for Bash: {command}"
        assert f"PowerShell({command})" in approvals, f"not pre-approved for PowerShell: {command}"


# Samples for the searches below: each line in a "found" list must be found, and nothing in a
# "not found" list.
CHANGES = [
    "import socket\nsocket.create_connection(('example.com', 80))",
    "from socket import socket",
    "from urllib.request import urlopen",
    "import tempfile",
    "os.remove('x')",
    "os.system('git fetch')",
    "shutil.rmtree('x')",
    "Path('x').write_text('y')",
    "Path('x').replace('y')",
    "open('x', 'w')",
    "subprocess.run(['git', 'fetch'])",
    "run_git('fetch', 'origin')",
    "run_git('remote', 'add', 'x', 'y')",
    "os.environ['X'] = '1'",
    "os.environ.update(X='1')",
    "ctypes.windll.kernel32.DeleteFileW('x')",
    "ctypes.WinDLL('kernel32').DeleteFileW('x')",
    "ctypes.WinDLL('kernel32').GetComputerNameW(b, s)",
    "exec('x')",
    "importlib.import_module('socket')",
    "import importlib\nimportlib.import_module('socket')",
    "import io\nio.FileIO('x', 'w')",
    "import json\njson.dump({}, f)",
    "import os as o\no.remove('x')",
    "write = os",
    "getattr(shutil, 'rmtree')('x')",
    "from os import remove",
    "from shutil import *",
    "from . import facts",
    "subprocess.Popen(['git', 'status'])",
    "def run_gh(gh, text):\n    return subprocess.run([gh, 'issue', 'close', text])",
    "def run_gh(gh, text):\n    return subprocess.run(text)",
    "def run_gh(gh, path):\n    return subprocess.run([gh, 'api', 'graphql', '--input', path])",
    "sys.modules['os'].remove('x')",
    "sys.modules.get('os')",
    "kernel32 = ctypes.WinDLL('kernel32')\nkernel32.DeleteFileW('x')",
    "Path('x').copy('y')",
    "Path('x').move_into('y')",
    "Path('x').open('w')",
    "text.encode('utf-8')",
    "getattr(Path('x'), 'write_text')('y')",
    "write = open\nwrite('x', 'w')",
    "__builtins__.open('x', 'w')",
    "env = os.environ\nenv['X'] = '1'",
    "os.environ.copy()",
    "for p in map(Path.unlink, files):\n    pass",
    "write = Path('x').write_text\nwrite('y')",
    "move = Path('x').replace\nmove('y')",
]
READS = [
    "import os, re, subprocess",
    "from urllib.parse import quote",
    "from pathlib import Path",
    "os.environ.get('X')",
    "x = os.environ['X'] if 'X' in os.environ else ''",
    "env = os.environ | {'X': '1'}",
    "os.path.abspath('x')",
    "shutil.which('git')",
    "Path('x').read_text()",
    "'a\\r\\n'.replace('\\r\\n', '\\n')",
    "import json\njson.loads('{}')",
    "import io\nisinstance(sys.stdout, io.TextIOWrapper)",
    "import importlib.util\nimportlib.util.spec_from_file_location('x', 'x.py')",
    "run_git('rev-parse', 'HEAD')",
    "run_git('remote', 'get-url', 'origin')",
    "run_git('cat-file', '--batch-check')",
    "import socket\nsocket.gethostname().split('.')[0].upper()",
    "def run_git(*args):\n    return subprocess.run(['git', *args])",
    "def run_gh(gh, q):\n    return subprocess.run([gh, 'api', 'graphql', '-f', f'query={q}'])",
    "sys.modules[spec.name] = module",
    "print(done.returncode, done.stdout)",
    "sorted(names, key=str.lower)",
    "@dataclass\nclass Place:\n    url: str\n\nprint(Place('x').url)",
]
PROCESS_WIDE = [
    "os.environ['X'] = '1'",
    "os.chdir('x')",
    "sys.path.insert(0, 'x')",
    "sys.stdout.reconfigure(encoding='utf-8')",
    "sys.modules['x'] = None",
    "sys.stdout = None",
]
PROCESS_READS = [
    "x = os.environ.get('X')",
    "print(sys.path)",
    "if __name__ == '__main__':\n    sys.stdout.reconfigure(encoding='utf-8')",
]


def found_lines(search: Callable[[ast.Module], list[ast.AST]], samples: list[str]) -> list[str]:
    return [s for s in samples if search(ast.parse(s))]


def test_the_search_for_changes_and_network_use_finds_each_kind_and_no_reads() -> None:
    assert found_lines(find_changes_or_network_use, CHANGES) == CHANGES
    assert found_lines(find_changes_or_network_use, READS) == []


def test_the_search_for_process_wide_changes_finds_each_kind_and_no_reads() -> None:
    assert found_lines(find_process_wide_changes, PROCESS_WIDE) == PROCESS_WIDE
    assert found_lines(find_process_wide_changes, PROCESS_READS) == []


# The scripts each script that only reports loads into its own process, and whose names it may
# read.
LOADS = {"issue_status.py": [SCRIPTS / "facts.py"]}


@pytest.mark.parametrize(
    "script", [SCRIPTS / "facts.py", SKILLS / "handoff" / "issue_status.py"], ids=repo_path
)
def test_the_scripts_that_only_report_change_nothing_as_far_as_their_code_shows(
    script: Path,
) -> None:
    # Which is what lets a skill run them without asking first. Each may start only the programs
    # the launcher allows it: issue_status.py reaches the network only through gh api graphql,
    # with queries the tests that fake gh check.
    loads = [parse(loaded) for loaded in LOADS.get(script.name, [])]
    found = find_changes_or_network_use(parse(script), PROGRAMS[script.name], loads)
    assert lines_of(found, script) == [], (
        "Each line uses something the check doesn't allow. If it can't change anything or reach "
        "the network, add the name to REPORTING_NAMES, REPORTING_METHODS, or "
        "REPORTING_ATTRIBUTES in helpers.py, and say in the commit that it's a safety change."
    )


def test_a_script_may_start_only_its_own_programs() -> None:
    # facts.py may run git, but not gh, even through a function called run_gh.
    code = "def run_gh(gh, text):\n    return subprocess.run([gh, 'api', 'graphql', '-f', text])"
    assert find_changes_or_network_use(ast.parse(code), PROGRAMS["facts.py"])


@pytest.mark.parametrize(
    ("command", "programs", "allowed"),
    [
        (["C:/Git/cmd/git.exe", "rev-parse", "HEAD"], {"git"}, True),
        (["/usr/bin/git", "remote", "get-url", "origin"], {"git"}, True),
        (["git", "remote", "add", "x", "y"], {"git"}, False),
        (["git", "status"], {"git"}, False),
        (["gh", "api", "graphql", "-f", "query=query { viewer { login } }"], {"git", "gh"}, True),
        (["gh", "api", "graphql", "-f", "query=mutation { closeIssue }"], {"git", "gh"}, False),
        (["gh", "issue", "close", "1"], {"git", "gh"}, False),
        (["gh", "api", "graphql", "--input", "query.json"], {"git", "gh"}, False),
        (["gh", "api", "graphql", "-F", "query=@query.graphql"], {"git", "gh"}, False),
        (["gh", "api", "graphql", "-f", "query=query { x }", "-X", "PUT"], {"git", "gh"}, False),
        (["gh", "api", "graphql", "-f", "query=query { x }"], {"git"}, False),
        (["cmd.exe", "/c", "git rev-parse HEAD"], {"git"}, False),
    ],
    ids=[
        "git read",
        "git remote read",
        "git remote add",
        "git status",
        "gh query",
        "gh mutation",
        "gh issue close",
        "gh query from a file",
        "gh query from a file with -F",
        "gh with more options",
        "gh not allowed",
        "a shell",
    ],
)
def test_the_launcher_allows_only_git_reads_and_gh_queries_that_read(
    command: list[str], programs: set[str], allowed: bool
) -> None:
    assert allowed_command(command, programs) is allowed
    if sys.platform == "win32":
        # Where subprocess gives the audit event the command line it builds.
        assert allowed_command(subprocess.list2cmdline(command), programs) is allowed


def test_the_launcher_checks_the_program_subprocess_starts_not_just_the_first_word() -> None:
    # subprocess.run(["git", "rev-parse"], executable="other") starts other.
    command = ["git", "rev-parse", "HEAD"]
    assert allowed_command(command, {"git"}, "C:/Git/cmd/git.exe")
    assert not allowed_command(command, {"git"}, "C:/Windows/System32/cmd.exe")


@pytest.mark.parametrize(
    "words",
    [
        ["C:/Program Files/Git/cmd/git.exe", "rev-parse", "HEAD"],
        ["gh", "-f", 'query=query { r(owner: "you", name: "a b") }', "", 'a\\"b', "c:\\x\\"],
    ],
    ids=["spaces", "quotes, an empty word, and backslashes"],
)
def test_the_launcher_splits_a_windows_command_line_back_into_its_words(words: list[str]) -> None:
    assert split_command_line(subprocess.list2cmdline(words)) == words


def test_facts_changes_nothing_the_whole_process_shares() -> None:
    # prepare.py runs it inside its own process.
    facts = SCRIPTS / "facts.py"
    assert lines_of(find_process_wide_changes(parse(facts)), facts) == []


@pytest.mark.parametrize("module", shared_modules(), ids=repo_path)
def test_internal_shared_changes_nothing_the_whole_process_shares(module: Path) -> None:
    # prepare.py runs the sync inside its own process, and the sync runs update there too.
    assert lines_of(find_process_wide_changes(parse(module)), module) == []


@pytest.mark.parametrize("entry", ENTRY_POINTS, ids=repo_path)
def test_each_entry_point_runs_the_module_of_its_own_name(entry: Path) -> None:
    text = entry.read_text(encoding="utf-8")
    assert f'load("{entry.stem}").main(sys.argv[1:])' in text
    assert (SHARED / entry.name).is_file()


@pytest.mark.parametrize("skill", skills(), ids=lambda p: p.name)
def test_each_python_command_a_skill_gives_is_pre_approved_for_both_tools(skill: Path) -> None:
    # Word for word, or by an approval ending in a wildcard, for a command whose last words
    # change each time, such as a commit message or a setting.
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    allowed = re.search(r'^allowed-tools:\s*"(.*)"\s*$', text, re.MULTILINE)
    approvals = re.findall(r"(Bash|PowerShell)\(([^)]*)\)", allowed.group(1) if allowed else "")
    commands = set(re.findall(r"`(\{\{PYTHON\}\} -I [^`]*)`", text))
    assert commands, f"{skill.name} gives no Python command"

    def approved(tool: str, command: str) -> bool:
        return any(
            kind == tool
            and (rule == command or (rule.endswith(" *") and command.startswith(rule[:-1])))
            for kind, rule in approvals
        )

    missing = [
        f"{tool}: {command}"
        for command in sorted(commands)
        for tool in ("Bash", "PowerShell")
        if not approved(tool, command)
    ]
    assert missing == []


@pytest.mark.parametrize("skill", skills(), ids=lambda p: p.name)
def test_each_skill_pre_approves_its_sync_commands_for_both_tools(skill: Path) -> None:
    # A commit message differs every time, so these end in a wildcard.
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    allowed = re.search(r'^allowed-tools:\s*"(.*)"\s*$', text, re.MULTILINE)
    approvals = allowed.group(1) if allowed else ""
    prefix = "{{PYTHON}} -I {{TOOLKIT_DIR}}/sync.py"
    assert re.search(rf"`{re.escape(prefix)} --message ", text), f"{skill.name} never commits"
    for tool in ("Bash", "PowerShell"):
        assert f"{tool}({prefix})" in approvals, f"{tool} plain sync"
        assert f"{tool}({prefix} *)" in approvals, f"{tool} sync that commits"


def skills_that_sync() -> list[Path]:
    return [s for s in skills() if "prepare.py" in (s / "SKILL.md").read_text(encoding="utf-8")]


@pytest.mark.parametrize("skill", skills_that_sync(), ids=lambda p: p.name)
def test_each_skill_that_syncs_passes_repeating_lines_on_with_one_shared_bullet(
    skill: Path,
) -> None:
    # Word for word the same in every skill, and once per session, since an UPDATE, NEW, LARGE,
    # or LONG line can repeat on every sync (decisions 0036, 0065, and 0088).
    words = " ".join((skill / "SKILL.md").read_text(encoding="utf-8").split())
    shared = (
        "- `UPDATE`, `NEW`, `LARGE`, and `LONG`: tell the user each such line once per session,"
        " as its own line, and continue."
    )
    assert shared in words
    for word in ("UPDATE", "NEW", "LARGE", "LONG"):
        assert f"- `{word}`:" not in words


def test_dev_home_sync_names_what_is_still_waiting_even_if_told_earlier() -> None:
    # An end user who runs /dev-home sync asked where things stand, so it names what's still
    # waiting even when told earlier.
    words = " ".join((SKILLS / "dev-home" / "SKILL.md").read_text(encoding="utf-8").split())
    assert (
        "name what any `UPDATE` (dev-home-toolkit), `NEW` (this PC's setup), or `LARGE` (your"
        " rules' size) line says is still waiting, even if told earlier this session, without"
        " asking again." in words
    )


def test_handoff_environment_edits_follow_evidence_not_session_location() -> None:
    # The current computer names the default subsection, but doesn't own it: reliable evidence
    # about another environment must be usable without permitting guesses across environments.
    text = (SKILLS / "handoff" / "SKILL.md").read_text(encoding="utf-8")
    words = " ".join(text.split())
    assert "Only edit the subsection for the environment you're in." not in words
    assert (
        "A session may edit any environment's subsection only when it has reliable evidence"
        in words
    )
    assert "Never infer one environment's state from another." in words
    assert "not an ownership boundary" in words
    assert "current environment's subsection" in words


def test_the_dev_home_skill_changes_settings_only_through_setup() -> None:
    # The person's yes in chat to the exact preview is the approval, as for a commit.
    text = (SKILLS / "dev-home" / "SKILL.md").read_text(encoding="utf-8")
    configure = "{{PYTHON}} -I {{TOOLKIT_DIR}}/setup.py --configure"
    commands = re.findall(rf"`({re.escape(configure)}[^`]*)`", text)
    assert f"{configure} '<name>=<value>' --what-if" in commands, commands
    assert f"{configure} '<name>=<value>'" in commands, commands
    assert "local-settings.json" in text and "never edit a settings file yourself" in text


def test_the_handoff_skill_checks_issue_links_with_its_script_alone() -> None:
    # One gh request for every link, in place of a gh issue view for each.
    text = (SKILLS / "handoff" / "SKILL.md").read_text(encoding="utf-8")
    assert "`{{PYTHON}} -I {{SKILL_DIR}}/issue_status.py`" in text
    assert "gh issue view" not in text


@pytest.mark.parametrize("script", python_files(), ids=repo_path)
def test_each_script_uses_only_the_standard_library(script: Path) -> None:
    # People install only Python, and the development tools are importable when the tests run
    # them.
    assert non_standard_imports(parse(script)) == []


@pytest.mark.parametrize("script", python_files(), ids=repo_path)
def test_each_script_is_ascii(script: Path) -> None:
    text = script.read_bytes()
    assert text.isascii(), [n for n, line in enumerate(text.splitlines(), 1) if not line.isascii()]
