"""facts.py, run as the handoff skill runs it in Codex, from a sandbox's generated copy."""

import importlib.util
import json
import os
import re
import shutil
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from helpers import (
    LAUNCHER,
    Run,
    Sandbox,
    git,
    new_repo,
    run,
    run_command,
    sandbox_for,
    shared_module,
    skill_command,
    write_text,
)
from read_only_launcher import EXIT_CODE, FAILED

pytestmark = pytest.mark.xdist_group("facts")


@pytest.fixture(scope="module")
def box(request: pytest.FixtureRequest) -> Iterator[Sandbox]:
    yield from sandbox_for(request, "facts")


def facts(
    box: Sandbox,
    folder: Path,
    *topics: str,
    env: dict[str, str | None] | None = None,
) -> Run:
    """Runs facts.py in a folder with the handoff skill's own command, for the topics given in
    place of the skill's, or the handoff topic when none are given."""
    words = skill_command(box, "handoff", "facts.py").split(" ")
    options = words[: words.index("--stamp") + 2]
    return run_command(box, " ".join([*options, *(topics or ("handoff",))]), cwd=folder, env=env)


def first_commit(repo: Path) -> str:
    """The start of a repo's first commit on the main line, worked out here without facts.py."""
    return git("-C", str(repo), "rev-list", "--first-parent", "--max-parents=0", "HEAD")[0][:7]


def short_head(repo: Path) -> str:
    return git("-C", str(repo), "rev-parse", "--short=7", "HEAD")[0]


# Each address, and the folder under handoffs/ it should get. {id} stands for the start of the
# sample repo's first commit.
ADDRESSES = {
    "https://github.com/You/Tool.git": "github/you/tool",
    "git@github.com:You/Tool.git": "github/you/tool",
    "ssh://git@github.com/You/Tool": "github/you/tool",
    "https://user:secret@github.com:443/you/tool/": "github/you/tool",
    "https://gitlab.com/Team/Sub/App.git": "gitlab/team/sub/app",
    "git@gitlab.com:team/sub/app.git": "gitlab/team/sub/app",
    "https://someone@bitbucket.org/Space/Repo.git": "bitbucket/space/repo",
    "git@bitbucket.org:space/repo.git": "bitbucket/space/repo",
    "https://Org@dev.azure.com/Org/My%20Project/_git/Repo": "azure-devops/org/my project/repo",
    "git@ssh.dev.azure.com:v3/Org/My%20Project/Repo": "azure-devops/org/my project/repo",
    "https://dev.azure.com/Org/_git/Repo": "azure-devops/org/repo/repo",
    "https://git.example.com/team/app.git": "other/sample repo-{id}",
    "git@git.example.com:team/app.git": "other/sample repo-{id}",
    "https://github.com/just-an-owner": "other/sample repo-{id}",
    "https://github.com/you/%2E%2E": "other/sample repo-{id}",
    "https://gitlab.com/team/../../outside": "other/sample repo-{id}",
    "https://github.com/you/to*ol": "other/sample repo-{id}",
    "C:/repos/tool": "local/sample repo-{id}",
    "C:\\repos\\tool": "local/sample repo-{id}",
    "file:///C:/repos/tool": "local/sample repo-{id}",
    "../tool": "local/sample repo-{id}",
}


@pytest.fixture(scope="module")
def sample(box: Sandbox) -> Path:
    return new_repo(box, "Sample Repo", origin="https://github.com/You/Tool.git")


@pytest.mark.parametrize(("address", "folder"), ADDRESSES.items())
def test_files_each_address_under_its_folder(
    box: Sandbox, sample: Path, address: str, folder: str
) -> None:
    git("-C", str(sample), "remote", "set-url", "origin", address)
    try:
        result = facts(box, sample)
    finally:
        git("-C", str(sample), "remote", "set-url", "origin", "https://github.com/You/Tool.git")
    expected = f"handoffs/{folder.replace('{id}', first_commit(sample))}/HANDOFF.md"
    assert result.code == 0, str(result)
    assert result.facts["handoff"] == expected, str(result)


def test_prints_the_handoff_topics_six_lines_in_order(box: Sandbox, sample: Path) -> None:
    result = facts(box, sample)
    assert result.keys == ["service", "name", "handoff", "draft", "link", "project"], str(result)
    assert len(result.lines) == 6, str(result)
    assert result.facts["service"] == "github"
    assert result.facts["name"] == "you/tool"
    assert result.facts["draft"] == ".drafts/github/you/tool/issue.md"
    # The sandbox keeps dev-home beside the sample repo.
    assert result.facts["link"] == "../dev-home/handoffs/github/you/tool/HANDOFF.md"
    assert result.facts["project"] == "."


def test_the_environment_topic_prints_this_computers_name(box: Sandbox, sample: Path) -> None:
    result = facts(box, sample, "environment")
    if sys.platform == "win32":
        name = os.environ["COMPUTERNAME"]
    else:
        name = os.uname().nodename.split(".")[0]
    assert result.code == 0, str(result)
    assert result.lines == [f"environment: {name}"], str(result)


def dev_home_skills(box: Sandbox) -> Run:
    """The dev-home skill's command for the skills topic, word for word. It needs no project, so
    it runs in the sandbox's root."""
    return run_command(box, skill_command(box, "dev-home", "facts.py"), cwd=box.root)


def test_the_skills_topic_lists_dev_home_toolkit_skills_then_the_users(box: Sandbox) -> None:
    result = dev_home_skills(box)
    ours = sorted(
        folder.name
        for folder in (box.toolkit / "templates" / "skills").iterdir()
        if (folder / "SKILL.md").is_file()
    )
    listed = [re.fullmatch(r"skill: (\S+) \(([^)]*)\): (.+)", line) for line in result.lines]
    assert result.code == 0 and all(listed), str(result)
    # Each with its state, as setup recorded it: dev-home is always added.
    assert [(m.group(1), m.group(2)) for m in listed if m] == [
        *(
            (
                name,
                f"dev-home-toolkit, {'always ' if name == 'dev-home' else ''}added to your agents",
            )
            for name in ours
        ),
        ("mine", "yours, added to your agents"),
    ], str(result)
    assert any(
        line.startswith(
            "skill: handoff (dev-home-toolkit, added to your agents): Read, update, or audit"
        )
        for line in result.lines
    )
    expected = "skill: mine (yours, added to your agents): A personal test skill."
    assert result.lines[-1] == expected, str(result)


def test_the_skills_topic_says_only_whose_a_skill_is_before_setup_records_states(
    box: Sandbox,
) -> None:
    # Such as on the first sync after an update that brings the record.
    states = box.generated / "skill-states.json"
    aside = box.generated / "skill-states.json.aside"
    states.rename(aside)
    try:
        result = dev_home_skills(box)
    finally:
        aside.rename(states)
    assert result.code == 0, str(result)
    assert result.lines[-1] == "skill: mine (yours): A personal test skill.", str(result)
    assert all(
        re.match(r"skill: \S+ \((dev-home-toolkit|yours)\): ", line) for line in result.lines
    )


def test_the_skills_topic_reads_each_description_form_and_says_what_isnt_set_up(
    box: Sandbox,
) -> None:
    skills = box.content / "skills"
    added = {
        "folded": "---\nname: folded\ndescription: >\n  Folded onto\n  one line.\nx: y\n---\n",
        "quoted": '---\nname: quoted\ndescription: "Quoted: with a \\"colon\\"."\n---\n',
        "single": "---\nname: single\ndescription: 'The project''s own.'\n---\n",
        "carried": "---\nname: carried\ndescription: Starts here\n  and carries on.\n---\n",
        "bare": "---\nname: bare\n---\nThe body's description: not this.\n",
        "handoff": "---\nname: handoff\ndescription: Mine too.\n---\n",
    }
    for name, text in added.items():
        write_text(skills / name / "SKILL.md", text)
    # A folder without a SKILL.md isn't a skill, as setup sees it.
    write_text(skills / "notes" / "README.md", "Not a skill.\n")
    try:
        result = dev_home_skills(box)
    finally:
        for name in [*added, "notes"]:
            shutil.rmtree(skills / name)
    assert result.code == 0, str(result)
    # Setup hasn't run since they were added, so it hasn't recorded their states.
    unseen = "yours, not added yet: setup hasn't seen it"
    assert [line for line in result.lines if "(yours" in line] == [
        f"skill: bare ({unseen}): no description",
        f"skill: carried ({unseen}): Starts here and carries on.",
        f"skill: folded ({unseen}): Folded onto one line.",
        "skill: handoff (yours, not added: it has the same name as a dev-home-toolkit skill): "
        "Mine too.",
        "skill: mine (yours, added to your agents): A personal test skill.",
        f'skill: quoted ({unseen}): Quoted: with a "colon".',
        f"skill: single ({unseen}): The project's own.",
    ], str(result)


def test_the_skills_topic_checks_again_what_setup_only_warns_about(box: Sandbox) -> None:
    # Here, where the agent runs: git is on this process's PATH, and the Python is the skills' own.
    # And a skill's compatibility text follows its description.
    states = box.generated / "skill-states.json"
    skill = box.content / "skills" / "mine" / "SKILL.md"
    recorded, written = states.read_text(encoding="utf-8"), skill.read_text(encoding="utf-8")
    entry = {
        "state": "added to your agents",
        "programs": [{"name": "no-such-program-here", "description": "testing"}, {"name": "git"}],
        "python": "99.0",
    }
    write_text(states, json.dumps({**json.loads(recorded), "mine": entry}))
    write_text(
        skill,
        "---\nname: mine\ndescription: A personal test skill.\n"
        "compatibility: Needs the office network.\n---\n",
    )
    try:
        result = dev_home_skills(box)
    finally:
        write_text(states, recorded)
        write_text(skill, written)
    pattern = (
        r"skill: mine \(yours, added to your agents; no-such-program-here isn't on the PATH, and "
        r"the skill uses it for testing; the skill needs Python 99\.0 or later, and this PC's is "
        r"\d+\.\d+\.\d+\): A personal test skill\. Compatibility: Needs the office network\."
    )
    assert result.code == 0 and re.fullmatch(pattern, result.lines[-1]), str(result)


def facts_module(box: Sandbox, name: str) -> Any:
    """The sandbox's generated facts.py, loaded into the test's process under a name of its own,
    to call its functions."""
    path = box.generated / "shared-skill-scripts" / "facts.py"
    spec = importlib.util.spec_from_file_location(f"{name}_{box.root.name[-8:]}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_skills_topic_checks_and_words_what_it_checks_as_setup_does(
    box: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    # facts.py can't load setup's code, so each has its own copy of the check and its words.
    module = facts_module(box, "facts_needs")
    requirements = shared_module(box, "requirements")
    on_path = box.root / "needs-on-path"
    write_text(on_path / "jira.cmd", "@echo off\n")
    write_text(box.root / "needs-nearby" / "glab.exe", "")
    monkeypatch.chdir(box.root)
    monkeypatch.setenv("PATH", os.pathsep.join([str(on_path), "needs-nearby", ""]))
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    folders = requirements.path_folders(os.environ["PATH"])
    for name in ("jira", "jira.cmd", "glab", "missing"):
        assert module.on_path(name) == requirements.on_path(name, folders), name
    for description in ("", "filing Jira issues"):
        words = requirements.program_missing("jira", description)
        assert module.program_missing("jira", description) == words
    words = requirements.python_too_old((3, 14), (3, 13, 2))
    assert module.python_too_old((3, 14), (3, 13, 2)) == words


def test_the_skills_topic_without_skills_of_the_users_own(box: Sandbox) -> None:
    skills = box.content / "skills"
    hidden = box.content / "skills-hidden"
    skills.rename(hidden)
    try:
        result = dev_home_skills(box)
    finally:
        hidden.rename(skills)
    assert result.code == 0, str(result)
    assert result.lines and all("(dev-home-toolkit, " in line for line in result.lines), str(result)


# The preferences topic, which reads the sandbox's local-settings.json and the handoff skill's
# dev-home-skill.json. It needs no project.

SECURITY_BUGS = "includeSecurityBugsInIssueOffers"


def preference_facts(box: Sandbox, text: str) -> Run:
    """The preferences topic, with local-settings.json holding the text given, then put back."""
    settings = box.toolkit / "local-settings.json"
    before = settings.read_bytes()
    write_text(settings, text)
    try:
        return facts(box, box.root, "preferences")
    finally:
        settings.write_bytes(before)


@pytest.mark.parametrize(
    ("value", "printed"),
    [
        (None, "true"),
        (False, "false"),
        (True, "true"),
        ({"$state": "default"}, "true"),
        ("no", "true"),
    ],
    ids=["unset", "false", "true", "following the default", "not true or false"],
)
def test_the_preferences_topic_prints_each_preference_or_its_default(
    box: Sandbox, value: object, printed: str
) -> None:
    data = json.loads((box.toolkit / "local-settings.json").read_text(encoding="utf-8"))
    data.pop("skills", None)
    if value is not None:
        # A skill's name matches without case, as its folder's does.
        data["skills"] = {"Handoff": {"preferences": {SECURITY_BUGS: value}}}
    result = preference_facts(box, json.dumps(data, indent=2) + "\n")
    assert result.code == 0, str(result)
    assert result.lines == [f"{SECURITY_BUGS}: {printed}"], str(result)


def test_the_preferences_topic_with_settings_it_cant_read_prints_the_defaults(
    box: Sandbox,
) -> None:
    for text in ("{ not json", "[]"):
        result = preference_facts(box, text)
        assert result.code == 0, str(result)
        assert result.lines == [f"{SECURITY_BUGS}: true"], str(result)


def test_the_preferences_topic_needs_a_skill(box: Sandbox) -> None:
    words = skill_command(box, "handoff", "facts.py").split(" ")
    command = " ".join([*words[: words.index("--skill")], "preferences"])
    result = run_command(box, command, cwd=box.root)
    assert result.code == 1, str(result)
    assert result.has_line(r"The preferences topic needs --skill"), str(result)


def test_the_preferences_topic_reads_saved_values_as_setup_does(box: Sandbox) -> None:
    # facts.py can't load setup's code, so each reads a saved preference its own way.
    module = facts_module(box, "facts_values")
    settings = shared_module(box, "settings")
    for default in (True, False):
        setting = settings.Preference("handoff", "x", default, "X", "").setting
        for saved in (None, True, False, {"$state": "default"}, {"$state": "unanswered"}, "no", 1):
            setup_reads = settings.read_value(settings.MISSING if saved is None else saved, setting)
            assert module.preference_value(saved, default) == setup_reads[0], (saved, default)
    # And the two use the same declarations: here, a personal skill's, one of each kind.
    good = {"default": True, "label": "Good"}
    entries = {
        "good": good,
        "withHelp": {**good, "help": "Why."},
        "renamed": {**good, "formerNames": ["old"]},
        "noLabel": {"default": True},
        "blankLabel": {"default": True, "label": " "},
        "textDefault": {"default": "yes", "label": "X"},
        "numberHelp": {**good, "help": 1},
        "badFormer": {**good, "formerNames": "old"},
        "with.dot": good,
        "notAnObject": True,
    }
    skill = box.content / "skills" / "mine" / "dev-home-skill.json"
    write_text(skill, json.dumps({"preferences": entries}) + "\n")
    try:
        setup_takes = set(settings.skill_declarations(str(box.content)).preferences["mine"])
    finally:
        skill.unlink()
    facts_takes = {name for name, entry in entries.items() if module.usable_preference(name, entry)}
    assert facts_takes == setup_takes == {"good", "withHelp", "renamed"}, (facts_takes, setup_takes)


def test_two_topics_print_in_the_order_asked(box: Sandbox, sample: Path) -> None:
    result = facts(box, sample, "environment", "handoff")
    assert result.code == 0, str(result)
    assert result.keys == ["environment", "service", "name", "handoff", "draft", "link", "project"]


def test_with_no_topic_stops_and_names_the_topics(box: Sandbox, sample: Path) -> None:
    words = skill_command(box, "handoff", "facts.py").split(" ")
    result = run_command(box, " ".join(words[: words.index("--stamp") + 2]), cwd=sample)
    assert result.code == 1, str(result)
    assert result.keys == [], str(result)
    assert result.has_line("at least one topic: handoff, environment, newer-commits"), str(result)


def test_an_unknown_topic_stops_it_before_any_fact(box: Sandbox, sample: Path) -> None:
    result = facts(box, sample, "environment", "weather")
    assert result.code == 1, str(result)
    assert result.keys == [], str(result)
    assert result.has_line("No such topic: weather"), str(result)


def test_writes_what_a_link_cant_hold_encoded_and_the_path_as_utf8(box: Sandbox) -> None:
    # A repo named with an accent, a space, #, %, and parentheses.
    repo = new_repo(
        box,
        "Encoded",
        origin="https://dev.azure.com/Org/My%20Project/_git/R%C3%A9po%20%231%20(100%25)",
    )
    result = facts(box, repo)
    assert result.facts["link"] == (
        "../dev-home/handoffs/azure-devops/org/my%20project/r%C3%A9po%20%231%20%28100%25%29/HANDOFF.md"
    ), str(result)
    assert result.facts["handoff"] == (
        "handoffs/azure-devops/org/my project/r\u00e9po #1 (100%)/HANDOFF.md"
    ), str(result)


def test_another_host_goes_under_other_by_folder_and_first_commit(box: Sandbox) -> None:
    repo = new_repo(box, "Other Host", origin="https://git.example.com/team/app.git")
    result = facts(box, repo)
    name = f"other host-{first_commit(repo)}"
    assert result.facts["service"] == "other", str(result)
    assert result.facts["name"] == name, str(result)
    assert result.facts["draft"] == f".drafts/other/{name}/issue.md", str(result)


def test_no_origin_goes_under_local_and_a_space_becomes_percent_20(box: Sandbox) -> None:
    repo = new_repo(box, "No Origin")
    name = f"no origin-{first_commit(repo)}"
    result = facts(box, repo)
    assert result.facts["service"] == "local", str(result)
    assert result.facts["handoff"] == f"handoffs/local/{name}/HANDOFF.md", str(result)
    assert result.facts["link"] == (
        f"../dev-home/handoffs/local/{name.replace(' ', '%20')}/HANDOFF.md"
    ), str(result)


def test_in_a_subfolder_the_links_lead_up(box: Sandbox) -> None:
    repo = new_repo(box, "With Sub")
    (repo / "docs").mkdir()
    result = facts(box, repo / "docs")
    name = f"with%20sub-{first_commit(repo)}"
    assert result.facts["link"] == f"../../dev-home/handoffs/local/{name}/HANDOFF.md", str(result)
    assert result.facts["project"] == "..", str(result)


def test_in_claude_codes_cli_the_links_are_file_urls(box: Sandbox) -> None:
    # Claude Code's CLI shows replies in a terminal, which opens file:/// URLs but not relative
    # paths. Git may spell the project folder's drive letter in another case.
    repo = new_repo(box, "Cli Links")
    (repo / "docs").mkdir(exist_ok=True)
    result = facts(box, repo / "docs", env={"CLAUDE_CODE_ENTRYPOINT": "cli"})
    name = f"cli%20links-{first_commit(repo)}"
    handoff = f"file:///{box.content.as_posix()}/handoffs/local/{name}/HANDOFF.md"
    project = f"file:///{repo.as_posix().replace(' ', '%20')}"
    assert result.facts["link"] == handoff, str(result)
    assert result.facts["project"].lower() == project.lower(), str(result)


def test_anywhere_else_claude_code_runs_the_links_stay_relative(box: Sandbox) -> None:
    repo = new_repo(box, "Vscode Links")
    result = facts(box, repo, env={"CLAUDE_CODE_ENTRYPOINT": "claude-vscode"})
    name = f"vscode%20links-{first_commit(repo)}"
    assert result.facts["link"] == f"../dev-home/handoffs/local/{name}/HANDOFF.md", str(result)
    assert result.facts["project"] == ".", str(result)


def test_merged_in_unrelated_history_keeps_the_main_lines_first_commit(box: Sandbox) -> None:
    repo = new_repo(box, "Merged")
    first = first_commit(repo)
    git("-C", str(repo), "checkout", "--quiet", "--orphan", "other-history")
    git("-C", str(repo), "commit", "--quiet", "--allow-empty", "-m", "test: other history")
    git("-C", str(repo), "checkout", "--quiet", "main")
    git(
        "-C",
        str(repo),
        "merge",
        "--quiet",
        "--no-ff",
        "--allow-unrelated-histories",
        "-m",
        "test: merge",
        "other-history",
    )
    assert len(git("-C", str(repo), "rev-list", "--max-parents=0", "HEAD")) == 2
    result = facts(box, repo)
    assert result.facts["handoff"] == f"handoffs/local/merged-{first}/HANDOFF.md", str(result)


def test_a_repo_with_no_commits_goes_by_its_folder_name_alone(box: Sandbox) -> None:
    repo = new_repo(box, "Empty Repo", commits=())
    result = facts(box, repo)
    assert result.facts["handoff"] == "handoffs/local/empty repo/HANDOFF.md", str(result)


def test_a_shallow_clone_goes_by_its_folder_name_alone(box: Sandbox) -> None:
    # A shallow clone's oldest commit is only where the download stopped, not the first one.
    source = new_repo(box, "shallow-source", commits=("one", "two"))
    shallow = box.root / "Shallow Clone"
    git("clone", "--quiet", "--depth", "1", f"file:///{source.as_posix()}", str(shallow))
    result = facts(box, shallow)
    assert result.facts["handoff"] == "handoffs/local/shallow clone/HANDOFF.md", str(result)


def test_a_folder_outside_git_goes_under_local_by_its_name(box: Sandbox) -> None:
    plain = box.root / "Plain Folder"
    plain.mkdir()
    result = facts(box, plain)
    assert result.facts["handoff"] == "handoffs/local/plain folder/HANDOFF.md", str(result)
    assert result.facts["project"] == ".", str(result)


def test_a_worktree_uses_its_main_checkouts_name_and_origin(box: Sandbox) -> None:
    main = new_repo(box, "Main Checkout")
    worktree = box.root / "worktree"
    git("-C", str(main), "worktree", "add", "--quiet", str(worktree))
    result = facts(box, worktree)
    expected = f"handoffs/local/main checkout-{first_commit(main)}/HANDOFF.md"
    assert result.facts["handoff"] == expected, str(result)
    git("-C", str(main), "remote", "add", "origin", "git@github.com:you/tool.git")
    result = facts(box, worktree)
    assert result.facts["handoff"] == "handoffs/github/you/tool/HANDOFF.md", str(result)


def test_in_a_repo_git_cant_read_stops_instead_of_guessing(box: Sandbox) -> None:
    # A guessed path would file the handoff in the wrong place.
    broken = new_repo(box, "Broken Repo")
    with (broken / ".git" / "config").open("a", encoding="utf-8") as config:
        config.write("[broken\n")
    result = facts(box, broken)
    assert result.code == 1, str(result)
    assert "handoff" not in result.facts, str(result)
    assert result.has_line("bad config"), str(result)
    result = facts(box, broken, "environment", "handoff")
    assert result.code == 1, str(result)
    assert result.keys == [], "when one topic fails, no fact from the others either"


def test_without_git_stops_instead_of_guessing(box: Sandbox, sample: Path) -> None:
    folders = os.environ["PATH"].split(os.pathsep)
    path = os.pathsep.join(f for f in folders if not shutil.which("git", path=f))
    result = facts(box, sample, env={"PATH": path})
    assert result.code == 1, str(result)
    assert "handoff" not in result.facts, str(result)
    assert result.has_line("git was not found"), str(result)


def test_never_runs_a_git_in_the_project_folder(box: Sandbox) -> None:
    # On Windows a program search looks in the current folder first. This copy of Python can't
    # even start there, so if it ran, facts.py would fail.
    repo = new_repo(box, "Planted Git", origin="https://github.com/you/planted.git")
    shutil.copyfile(sys.executable, repo / "git.exe")
    result = facts(box, repo)
    assert result.code == 0, str(result)
    assert result.facts["handoff"] == "handoffs/github/you/planted/HANDOFF.md", str(result)


# ---------------------------------------------------------------------------------------------
# The newer-commits topic, which reads the State line of the handoff in the sandbox's dev-home.


def write_handoff(box: Sandbox, name: str, text: str) -> None:
    write_text(box.content / "handoffs" / "github" / "you" / name / "HANDOFF.md", text)


def test_with_no_handoff_yet_says_none_and_unknown(box: Sandbox) -> None:
    repo = new_repo(box, "No Handoff", origin="https://github.com/you/no-handoff.git")
    result = facts(box, repo, "newer-commits")
    assert result.code == 0, str(result)
    assert result.lines == ["checked: none", "newer: unknown", "behind: unknown"], str(result)


def test_counts_lists_and_compares_the_commits_since_the_checked_one(box: Sandbox) -> None:
    repo = new_repo(box, "Newer Repo", origin="https://github.com/you/newer.git", commits=("a",))
    checked = short_head(repo)

    # A State line over two lines: a word of hex letters and a number, neither a commit here,
    # then the checked commit.
    state = (
        "**State as of 2026-01-02.** Checked against `deadbee` and `1234567`, then\n"
        f"against `{checked}`, with 140 tests passing."
    )
    write_handoff(box, "newer", f"# newer handoff\n\n---\n\n{state}\n\n## Next up\n\n- None.\n")
    result = facts(box, repo, "newer-commits")
    assert result.lines == [f"checked: {checked}", "newer: 0", "behind: 0"], str(result)

    for message in ("second", "third"):
        git("-C", str(repo), "commit", "--quiet", "--allow-empty", "-m", f"test: {message}")
    result = facts(box, repo, "newer-commits")
    listed = [line for line in result.lines if line.startswith("newer-commit: ")]
    assert result.facts["newer"] == "2", str(result)
    assert [line.split(" ", 2)[2] for line in listed] == ["test: third", "test: second"]

    for n in range(1, 11):
        git("-C", str(repo), "commit", "--quiet", "--allow-empty", "-m", f"test: more {n}")
    result = facts(box, repo, "newer-commits")
    listed = [line for line in result.lines if line.startswith("newer-commit: ")]
    assert result.facts["newer"] == "12", "counts them all"
    assert len(listed) == 10, "lists at most ten"
    assert listed[0].endswith("test: more 10"), str(result)

    subject = "test: r\u00e9sum\u00e9"
    git("-C", str(repo), "commit", "--quiet", "--allow-empty", "-m", subject)
    result = facts(box, repo, "newer-commits")
    listed = [line for line in result.lines if line.startswith("newer-commit: ")]
    assert listed[0].endswith(f" {subject}"), "reads an accented subject as it is"

    # Naming the latest commit after an earlier one: the latest is the one checked.
    head = short_head(repo)
    write_handoff(
        box,
        "newer",
        f"# newer handoff\n\n**State as of 2026-01-03.** Started from `{checked}`, then "
        f"checked against `{head}`.\n",
    )
    result = facts(box, repo, "newer-commits")
    assert result.lines == [f"checked: {head}", "newer: 0", "behind: 0"], str(result)

    # This checkout falls behind the checked commit, as a PC does before it pulls.
    git("-C", str(repo), "reset", "--quiet", "--hard", "HEAD~2")
    result = facts(box, repo, "newer-commits")
    assert result.lines == [f"checked: {head}", "newer: 0", "behind: 2"], str(result)

    # A commit named in backticks that this checkout doesn't have at all, even beside one it has.
    write_handoff(
        box,
        "newer",
        f"# newer handoff\n\n**State as of 2026-01-04.** Checked against `abc1234`, after "
        f"`{checked}`.\n",
    )
    result = facts(box, repo, "newer-commits")
    expected = ["checked: missing abc1234", "newer: unknown", "behind: unknown"]
    assert result.lines == expected, str(result)

    result = facts(box, repo, "handoff", "environment", "newer-commits")
    assert result.keys[:10] == [
        "service",
        "name",
        "handoff",
        "draft",
        "link",
        "project",
        "environment",
        "checked",
        "newer",
        "behind",
    ], str(result)

    # A hash outside the State line doesn't count.
    write_handoff(
        box,
        "newer",
        "# newer handoff\n\n**State as of 2026-01-02.** Nothing checked yet.\n\n## Next up\n\n"
        f"- Start from `{checked}`.\n",
    )
    result = facts(box, repo, "newer-commits")
    assert result.lines == ["checked: none", "newer: unknown", "behind: unknown"], str(result)


def test_when_git_cant_count_says_unknown_and_the_other_topics_print(box: Sandbox) -> None:
    # History git can't walk: the checked commit is there, but one after it is missing.
    repo = new_repo(
        box, "Gap Repo", origin="https://github.com/you/gap.git", commits=("1", "2", "3")
    )
    first = git("-C", str(repo), "rev-parse", "HEAD~2")[0]
    middle = git("-C", str(repo), "rev-parse", "HEAD~1")[0]
    obj = repo / ".git" / "objects" / middle[:2] / middle[2:]
    obj.chmod(0o666)
    obj.unlink()
    write_handoff(box, "gap", f"**State as of 2026-01-02.** Checked against `{first[:7]}`.\n")
    result = facts(box, repo, "handoff", "newer-commits")
    assert result.code == 0, str(result)
    assert result.facts["handoff"] == "handoffs/github/you/gap/HANDOFF.md", str(result)
    assert result.facts["checked"] == first[:7], str(result)
    assert result.facts["newer"] == "unknown", str(result)
    assert result.facts["behind"] == "unknown", str(result)


def test_finds_a_full_sha256_hash_in_the_state_line(box: Sandbox) -> None:
    repo = box.root / "Sha256 Repo"
    git("init", "--quiet", "--object-format=sha256", "-b", "main", str(repo))
    git("-C", str(repo), "remote", "add", "origin", "https://github.com/you/sha256.git")
    git("-C", str(repo), "commit", "--quiet", "--allow-empty", "-m", "test: first")
    long_id = git("-C", str(repo), "rev-parse", "HEAD")[0]
    assert len(long_id) == 64
    write_handoff(box, "sha256", f"**State as of 2026-01-02.** Checked against `{long_id}`.\n")
    result = facts(box, repo, "newer-commits")
    assert result.lines == [f"checked: {long_id[:7]}", "newer: 0", "behind: 0"], str(result)


# ---------------------------------------------------------------------------------------------
# The skill's stamp, and the options.


def test_a_stamp_that_differs_from_the_skill_on_disk_stops_with_why(
    box: Sandbox, sample: Path
) -> None:
    command = skill_command(box, "handoff", "facts.py")
    words = command.split(" ")
    words[words.index("--stamp") + 1] = "000000000000"
    result = run_command(box, " ".join(words), cwd=sample)
    assert result.code == 1, str(result)
    assert result.keys == [], str(result)
    assert result.has_line(r"handoff skill has changed .* run the skill's command again"), str(
        result
    )
    result = run_command(box, command, cwd=sample)
    assert result.code == 0, "the skill's own stamp matches"


def test_options_need_their_values_and_each_other(box: Sandbox, sample: Path) -> None:
    words = skill_command(box, "handoff", "facts.py").split(" ")
    start = words[: words.index("--skill")]
    cases = {
        "--skill handoff handoff": "together",
        "--stamp abc handoff": "together",
        "handoff --skill": "needs a value",
        "--weather handoff": "No such option: --weather",
    }
    for arguments, reason in cases.items():
        result = run_command(box, " ".join([*start, arguments]), cwd=sample)
        assert result.code == 1, f"{arguments}: {result}"
        assert result.has_line(reason), f"{arguments}: {result}"


# ---------------------------------------------------------------------------------------------
# The launcher that watches each run of facts.py (read_only_launcher.py, through run_command).


def watched(box: Sandbox, folder: Path, code: str, *, name: str = "facts.py") -> Run:
    """Runs code through the launcher as a script of that name, in a folder of the sandbox."""
    script = folder / name
    write_text(script, code)
    return run(box, [sys.executable, "-I", str(LAUNCHER), str(script)], cwd=folder)


# Each, in a probe's own folder, which {folder} stands for.
FORBIDDEN = {
    "open for writing": "open({new!r}, 'w')",
    "io.FileIO": "import io\nio.FileIO({new!r}, 'w')",
    "os.open": "import os\nos.open({new!r}, os.O_WRONLY | os.O_CREAT)",
    "Path.write_text": "from pathlib import Path\nPath({new!r}).write_text('x')",
    "os.remove": "import os\nos.remove({kept!r})",
    "os.mkdir": "import os\nos.mkdir({new!r})",
    "environment": "import os\nos.environ['DEV_HOME_PROBE'] = '1'",
    "git that changes": "import subprocess\nsubprocess.run(['git', 'init', {new!r}])",
    "another program": "import subprocess, sys\nsubprocess.run([sys.executable, '-c', 'pass'])",
    "network": "import socket\nsocket.create_connection(('127.0.0.1', 9), timeout=1)",
    "a database": "import sqlite3\nsqlite3.connect({new!r})",
    "a Windows file handle": (
        "import _winapi\n_winapi.CreateFile({new!r}, 0x40000000, 0, 0, 2, 0, 0)"
    ),
    "Path.copy": "from pathlib import Path\nPath({kept!r}).copy({new!r})",
    "a DLL function not allowed": "import ctypes\nctypes.WinDLL('kernel32').DeleteFileW({kept!r})",
}


@pytest.mark.parametrize("code", FORBIDDEN.values(), ids=FORBIDDEN.keys())
def test_the_launcher_stops_a_script_before_it_changes_anything(box: Sandbox, code: str) -> None:
    if ("_winapi" in code or "WinDLL" in code) and sys.platform != "win32":
        pytest.skip("Windows only")
    folder = box.root / "probes" / uuid.uuid4().hex[:8]
    new, kept = folder / "new", folder / "kept.txt"
    write_text(kept, "kept\n")
    result = watched(box, folder, code.format(new=str(new), kept=str(kept)))
    assert result.code == EXIT_CODE, str(result)
    assert result.has_line(re.escape(FAILED)), str(result)
    assert not new.exists() and kept.is_file(), str(result)


def test_the_launcher_stops_at_a_kind_of_event_it_hasnt_sorted_and_says_what_to_do(
    box: Sandbox,
) -> None:
    # Such as one a new Python version raises: it fails until someone decides what it is.
    folder = box.root / "probes" / "unsorted"
    result = watched(box, folder, "import sys\nsys.audit('dev_home.probe.new_kind')\n")
    assert result.code == EXIT_CODE, str(result)
    assert result.has_line(r"hasn't sorted\. .* add it to HARMLESS"), str(result)
    assert result.has_line(r"dev_home\.probe\.new_kind"), str(result)


def test_the_launcher_lets_reads_git_reads_and_pythons_own_cache_through(
    box: Sandbox, sample: Path
) -> None:
    folder = box.root / "probes" / "reads"
    write_text(folder / "helper.py", "VALUE = 1\n")
    code = (
        "import shutil, subprocess, sys\n"
        f"sys.path.insert(0, {str(folder)!r})\n"
        "import helper\n"
        f"print(open({str(folder / 'helper.py')!r}).read().strip())\n"
        "done = subprocess.run([shutil.which('git'), 'cat-file', '--batch-check'],\n"
        f"    input='HEAD\\n', capture_output=True, text=True, cwd={str(sample)!r})\n"
        "print(done.stdout.split()[1])\n"
    )
    result = watched(box, folder, code)
    assert result.code == 0, str(result)
    assert result.lines == ["VALUE = 1", "commit"], str(result)
    assert list((folder / "__pycache__").glob("helper.*.pyc")), "Python saved its cache"
