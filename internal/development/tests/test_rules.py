"""Reading dev-home's rules/ and joining it into each agent's file (internal/shared/rules.py):
which files join, in what order, how each is read, and how their headings combine."""

from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

from helpers import Sandbox, make_junction, remove_link, sandbox_for, shared_module, write_text

OPERATING = "# Private repo: dev-home (rules loaded)\n\n- An operating rule.\n"
# A file's - Rule, as it joins, with no heading of its own.
RULE = "# My rules\n\n- Rule"


@pytest.fixture(scope="module")
def box(request: pytest.FixtureRequest) -> Iterator[Sandbox]:
    yield from sandbox_for(request, "rules")


@pytest.fixture
def code(box: Sandbox) -> ModuleType:
    return shared_module(box, "rules")


@pytest.fixture
def rules(tmp_path: Path) -> Path:
    return tmp_path / "dev-home" / "rules"


def write(path: Path, text: str) -> None:
    write_text(path, text)


def joined(code: ModuleType, rules: Path, system: str = "windows") -> object:
    return code.joined_rules(OPERATING, rules, "office", "codex", system)


def own(code: ModuleType, rules: Path, system: str = "windows") -> str:
    """The end user's part of codex's joined rules on the PC office."""
    text: str = joined(code, rules, system).text  # type: ignore[attr-defined]
    assert text.startswith(OPERATING.rstrip("\n")), text
    return text[len(OPERATING.rstrip("\n")) :].strip("\n")


# Where the rules are, and which join


@pytest.mark.parametrize(
    ("name", "folder"),
    [
        ("OFFICE", "office"),
        ("Lab PC_2.local", "lab-pc-2-local"),
        ("Caf\u00e9", "caf-"),
        ("A" * 40, "a" * 32),
        ("", "pc"),
    ],
)
def test_a_pcs_folder_is_its_name_in_lowercase_with_other_characters_as_hyphens(
    code: ModuleType, name: str, folder: str
) -> None:
    assert code.pc_folder(name) == folder


def test_levels_join_in_order_with_this_pcs_unanswered_lines_last(
    code: ModuleType, rules: Path
) -> None:
    for folder, text in [
        ("pcs/office/codex/unanswered", "Six"),
        ("pcs/office/codex/mine", "Five"),
        ("pcs/office/_all-agents/mine", "Four"),
        ("codex/mine", "Three"),
        ("_all-agents/mine", "One"),
    ]:
        write(rules / folder / "my-rules.md", f"- {text}\n")
    write(rules / "_all-agents" / "mine" / "zz.md", "- Two\n")
    # Another agent's, and another PC's, never join.
    write(rules / "claude-code" / "mine" / "my-rules.md", "- Claude Code's\n")
    write(rules / "pcs" / "lab" / "codex" / "mine" / "my-rules.md", "- The lab's\n")
    assert own(code, rules) == (
        "# My rules\n\n- One\n\n- Two\n\n- Three\n\n- Four\n\n- Five\n\n- Six"
    )


def test_files_join_alphabetically_by_path_subfolders_included_in_any_case(
    code: ModuleType, rules: Path
) -> None:
    mine = rules / "_all-agents" / "mine"
    for relative in ["b.md", "A.md", "c/a.md", "B/z.md", "notes.txt", "C.MD"]:
        write(mine / relative, f"- {relative}\n")
    # Compared by path, so c.md comes before c/a.md: "." sorts before "/".
    assert own(code, rules).split("\n\n") == [
        "# My rules",
        "- A.md",
        "- b.md",
        "- B/z.md",
        "- C.MD",
        "- c/a.md",
    ]


@pytest.mark.skipif(not hasattr(Path, "is_junction"), reason="needs junctions")
def test_a_linked_folder_isnt_followed(code: ModuleType, rules: Path) -> None:
    mine = rules / "_all-agents" / "mine"
    write(mine / "my-rules.md", "- Mine\n")
    loop = mine / "loop"
    make_junction(loop, mine)
    try:
        assert own(code, rules) == "# My rules\n\n- Mine"
    finally:
        remove_link(loop)


def test_no_rules_of_the_end_users_leaves_the_operating_rules_alone(
    code: ModuleType, rules: Path
) -> None:
    write(rules / "_all-agents" / "mine" / "my-rules.md", "")
    write(rules / "codex" / "mine" / "note-only.md", "<!-- note\nby: user\n-->\n")
    result = joined(code, rules)
    assert result.text == OPERATING  # type: ignore[attr-defined]
    assert result.own_bytes == 0  # type: ignore[attr-defined]


def test_own_bytes_count_only_the_end_users_rules_as_utf8(code: ModuleType, rules: Path) -> None:
    write(rules / "_all-agents" / "mine" / "my-rules.md", "- Caf\u00e9\n")
    own_bytes = joined(code, rules).own_bytes  # type: ignore[attr-defined]
    assert own_bytes == len("# My rules\n\n- Caf\u00e9".encode())


def test_a_file_directly_in_a_level_folder_is_reported_and_never_joins(
    code: ModuleType, rules: Path
) -> None:
    write(rules / "codex" / "rule.md", "- Misplaced\n")
    write(rules / "pcs" / "office" / "_all-agents" / "rule.md", "- Misplaced too\n")
    write(rules / "codex" / "desktop.ini", "[.ShellClassInfo]\n")
    write(rules / "gemini" / "rule.md", "- Not an agent set up here\n")
    assert own(code, rules) == ""
    strays = code.stray_files(rules, "office", ["codex"])
    assert strays == [rules / "codex" / "rule.md", rules / "pcs/office/_all-agents/rule.md"]
    assert code.stray_file_problem(rules, strays[0]) == (
        f"{strays[0]} is directly in rules/codex/, where setup doesn't read rules, so no agent "
        "loads it: move it into rules/codex/mine/."
    )


def test_my_rules_is_missing_wherever_an_agent_set_up_here_has_none_in_any_case(
    code: ModuleType, rules: Path
) -> None:
    write(rules / "_all-agents" / "mine" / "My-Rules.md", "")
    write(rules / "codex" / "mine" / "other.md", "- Another file isn't my-rules.md.\n")
    missing = code.missing_my_rules(rules, "office", ["claude-code", "codex"])
    assert missing == [
        rules / "claude-code" / "mine" / "my-rules.md",
        rules / "pcs" / "office" / "_all-agents" / "mine" / "my-rules.md",
        rules / "pcs" / "office" / "claude-code" / "mine" / "my-rules.md",
        rules / "codex" / "mine" / "my-rules.md",
        rules / "pcs" / "office" / "codex" / "mine" / "my-rules.md",
    ]


# Operating systems


@pytest.mark.parametrize(
    ("field", "on_windows", "on_linux"),
    [
        ("os: windows", True, False),
        ("os: Windows, macOS", True, False),
        ('os: "linux"', False, True),
        ("os:", True, True),
    ],
)
def test_a_notes_os_field_limits_the_file_to_those_systems(
    code: ModuleType, rules: Path, field: str, on_windows: bool, on_linux: bool
) -> None:
    write(rules / "_all-agents" / "mine" / "my-rules.md", f"<!-- note\n{field}\n-->\n- Rule\n")
    assert (own(code, rules, "windows") == RULE) is on_windows
    assert (own(code, rules, "linux") == RULE) is on_linux
    assert joined(code, rules).problems == []  # type: ignore[attr-defined]


def test_a_misspelled_system_loads_the_rule_everywhere_and_says_so(
    code: ModuleType, rules: Path
) -> None:
    path = rules / "_all-agents" / "mine" / "my-rules.md"
    write(path, "<!-- note\nos: windows, linnux\n-->\n- Rule\n")
    assert own(code, rules, "macos") == RULE
    assert joined(code, rules).problems == [  # type: ignore[attr-defined]
        f"{path} names \"linnux\" in its note's os: field, which this dev-home-toolkit doesn't "
        'know, so the rule loads on every system. Did you mean "linux"? If not, name one or more '
        'of "windows", "macos", and "linux", separated by commas.'
    ]


def test_only_a_note_at_the_files_start_counts(code: ModuleType, rules: Path) -> None:
    write(rules / "_all-agents" / "mine" / "my-rules.md", "- Rule\n\n<!-- note\nos: linux\n-->\n")
    assert own(code, rules, "windows") == RULE


# Reading each file


def test_comments_that_start_a_line_go_whole_lines_and_all(code: ModuleType, rules: Path) -> None:
    write(
        rules / "_all-agents" / "mine" / "my-rules.md",
        "<!-- note\nby: user\n\nWhy.\n-->\n"
        "- One <!-- kept, mid-line -->\n"
        "   <!-- gone -->\n"
        "<!--\ngone\ntoo --> and this\n"
        "- Two\n"
        "```text\n<!-- kept, in code -->\n```\n",
    )
    assert own(code, rules) == (
        "# My rules\n\n- One <!-- kept, mid-line -->\n- Two\n```text\n<!-- kept, in code -->\n```"
    )


def test_a_comment_that_never_ends_goes_to_its_files_end_and_is_reported(
    code: ModuleType, rules: Path
) -> None:
    path = rules / "_all-agents" / "mine" / "a.md"
    write(path, "- One\n<!-- never ends\n- Hidden\n")
    write(rules / "_all-agents" / "mine" / "b.md", "- Two\n")
    result = joined(code, rules)
    assert own(code, rules) == "# My rules\n\n- One\n\n- Two"
    assert result.problems == [  # type: ignore[attr-defined]
        f"{path} has a comment, <!--, that never ends with -->, so setup leaves out everything "
        "from there to the file's end: end the comment."
    ]


def test_a_code_block_that_never_closes_is_closed_at_its_files_end_and_reported(
    code: ModuleType, rules: Path
) -> None:
    path = rules / "_all-agents" / "mine" / "a.md"
    write(path, "## Notes\n\n~~~~\n## Not a heading\n")
    write(rules / "_all-agents" / "mine" / "b.md", "## Notes\n\n- After\n")
    assert own(code, rules) == "# My rules\n\n## Notes\n\n~~~~\n## Not a heading\n~~~~\n\n- After"
    assert joined(code, rules).problems == [  # type: ignore[attr-defined]
        f"{path} opens a code block with ~~~~ that never closes, so setup closes it at the "
        "file's end: close it where it should end."
    ]


def test_blank_lines_at_a_files_ends_go_and_inside_it_stay(code: ModuleType, rules: Path) -> None:
    write(rules / "_all-agents" / "mine" / "a.md", "\n\n- One\n\n\n- Two\n\n\n")
    write(rules / "codex" / "mine" / "b.md", "\r\n- Three\r\n")
    text = joined(code, rules).text  # type: ignore[attr-defined]
    assert text.endswith("\n\n# My rules\n\n- One\n\n\n- Two\n\n- Three\n"), text


def test_a_byte_order_mark_decides_and_utf16_is_read_but_reported(
    code: ModuleType, rules: Path
) -> None:
    mine = rules / "_all-agents" / "mine"
    mine.mkdir(parents=True)
    (mine / "a.md").write_bytes(b"\xef\xbb\xbf- UTF-8 with a mark\n")
    (mine / "b.md").write_bytes("- UTF-16\n".encode("utf-16"))
    assert own(code, rules) == "# My rules\n\n- UTF-8 with a mark\n\n- UTF-16"
    assert joined(code, rules).problems == [  # type: ignore[attr-defined]
        f"{mine / 'b.md'} is saved as UTF-16, which git counts as binary, so a sync can't merge "
        "it: save it as UTF-8."
    ]


def test_bytes_that_arent_utf8_and_nul_bytes_are_reported(code: ModuleType, rules: Path) -> None:
    mine = rules / "_all-agents" / "mine"
    mine.mkdir(parents=True)
    (mine / "a.md").write_bytes(b"- Caf\xe9\n")
    (mine / "b.md").write_bytes(b"- N\x00UL\n")
    assert own(code, rules) == "# My rules\n\n- Caf\ufffd\n\n- NUL"
    problems = joined(code, rules).problems  # type: ignore[attr-defined]
    assert problems == [
        f"{mine / 'a.md'} isn't saved as UTF-8, so setup reads each byte that isn't as the "
        "replacement character: save it as UTF-8.",
        f"{mine / 'b.md'} has NUL bytes, which setup leaves out, and which make git count it as "
        "binary: save it as UTF-8 without them.",
    ]


# Headings


def test_matching_headings_combine_where_they_first_appear(code: ModuleType, rules: Path) -> None:
    write(
        rules / "_all-agents" / "mine" / "my-rules.md",
        "# My rules\n\n## Writing style\n\n- One\n\n## Commits\n\n- Two\n",
    )
    write(
        rules / "codex" / "mine" / "my-rules.md", "# MY RULES\n\n##  writing style  ##\n- Three\n"
    )
    assert own(code, rules) == (
        "# My rules\n\n## Writing style\n\n- One\n\n- Three\n\n## Commits\n\n- Two"
    )


def test_a_sections_own_text_comes_before_its_subsections(code: ModuleType, rules: Path) -> None:
    # So text keeps the heading it had: the second file's - Three stays under ## A.
    write(rules / "_all-agents" / "mine" / "a.md", "## A\n\n- One\n\n### B\n\n- Two\n")
    write(rules / "_all-agents" / "mine" / "b.md", "## A\n\n- Three\n\n### C\n\n- Four\n")
    assert own(code, rules) == (
        "# My rules\n\n## A\n\n- One\n\n- Three\n\n### B\n\n- Two\n\n### C\n\n- Four"
    )


@pytest.mark.parametrize(
    ("first", "second", "result"),
    [
        (
            "# R\n\n## Commits\n\n- One\n",
            "# R\n\n### Python\n\n- Two\n",
            "# R\n\n### Python\n\n- Two\n\n## Commits\n\n- One",
        ),
        (
            "## Commits\n\n- One\n",
            "### Python\n\n- Two\n",
            "# My rules\n\n### Python\n\n- Two\n\n## Commits\n\n- One",
        ),
    ],
)
def test_a_deeper_heading_never_lands_under_a_shallower_one_from_another_file(
    code: ModuleType, rules: Path, first: str, second: str, result: str
) -> None:
    # After ## Commits, ### Python would read as part of it, which neither file says.
    write(rules / "_all-agents" / "mine" / "a.md", first)
    write(rules / "_all-agents" / "mine" / "b.md", second)
    assert own(code, rules) == result


def test_a_comment_ends_on_its_own_line_even_when_its_ends_overlap(
    code: ModuleType, rules: Path
) -> None:
    write(rules / "_all-agents" / "mine" / "a.md", "- One\n<!-->\n- Two\n<!--->\n- Three\n")
    assert own(code, rules) == "# My rules\n\n- One\n- Two\n- Three"
    assert joined(code, rules).problems == []  # type: ignore[attr-defined]


def test_rules_outside_a_top_level_heading_go_under_my_rules(code: ModuleType, rules: Path) -> None:
    # Rather than after the operating rules' last line, as if they were part of them.
    write(rules / "_all-agents" / "mine" / "a.md", "# My rules\n\n## Writing style\n\n- One\n")
    write(
        rules / "codex" / "mine" / "b.md",
        "- Two, under no heading\n\n## Writing style\n\n- Three\n\n# Python\n\n- Four\n",
    )
    write(rules / "codex" / "mine" / "c.md", "### Git\n\n- Five\n\n# my rules\n\n- Six\n")
    assert own(code, rules) == (
        "# My rules\n\n- Two, under no heading\n\n- Six\n\n### Git\n\n- Five\n\n"
        "## Writing style\n\n- One\n\n- Three\n\n# Python\n\n- Four"
    )


def test_a_file_with_only_top_level_headings_adds_no_my_rules(
    code: ModuleType, rules: Path
) -> None:
    write(rules / "_all-agents" / "mine" / "a.md", "# Python\n\n- One\n")
    assert own(code, rules) == "# Python\n\n- One"


def test_a_heading_with_nothing_under_it_is_left_out(code: ModuleType, rules: Path) -> None:
    # As a my-rules.md with only a heading and a comment is, once the comment is left out.
    write(rules / "_all-agents" / "mine" / "my-rules.md", "# My rules\n\n<!-- Your rules. -->\n")
    write(rules / "codex" / "mine" / "a.md", "# Python\n\n## Empty\n\n### Also empty\n")
    result = joined(code, rules)
    assert result.text == OPERATING  # type: ignore[attr-defined]
    assert result.own_bytes == 0  # type: ignore[attr-defined]
    write(rules / "codex" / "mine" / "b.md", "## Empty\n\n## Kept\n\n- One\n")
    assert own(code, rules) == "# My rules\n\n## Kept\n\n- One"


def test_headings_under_different_parents_or_levels_stay_apart(
    code: ModuleType, rules: Path
) -> None:
    write(rules / "_all-agents" / "mine" / "a.md", "## A\n\n### Notes\n\n- One\n")
    write(
        rules / "_all-agents" / "mine" / "b.md", "## B\n\n### Notes\n\n- Two\n\n## Notes\n\n- 3\n"
    )
    assert own(code, rules) == (
        "# My rules\n\n## A\n\n### Notes\n\n- One\n\n## B\n\n### Notes\n\n- Two\n\n## Notes\n\n- 3"
    )


def test_only_markdown_headings_outside_code_count(code: ModuleType, rules: Path) -> None:
    write(rules / "_all-agents" / "mine" / "a.md", "## Notes\n\n- One\n")
    write(
        rules / "_all-agents" / "mine" / "b.md",
        "#Notes is no heading\n    ## Nor is code\n```\n## Notes\n```\n",
    )
    assert own(code, rules) == (
        "# My rules\n\n#Notes is no heading\n    ## Nor is code\n```\n## Notes\n```\n\n"
        "## Notes\n\n- One"
    )


def test_the_operating_rules_never_merge_and_nothing_is_deduplicated(
    code: ModuleType, rules: Path
) -> None:
    write(
        rules / "_all-agents" / "mine" / "a.md",
        "# Private repo: dev-home (rules loaded)\n\n- An operating rule.\n",
    )
    write(rules / "codex" / "mine" / "b.md", "# Private repo: dev-home (rules loaded)\n\n- Mine\n")
    text = joined(code, rules).text  # type: ignore[attr-defined]
    assert text == (
        f"{OPERATING}\n# Private repo: dev-home (rules loaded)\n\n- An operating rule.\n\n- Mine\n"
    )


# The path's length


def test_the_longest_rules_path_leaves_dev_home_about_90_characters(code: ModuleType) -> None:
    assert code.longest_rules_path() == 139
    assert code.path_problem(Path("C:/" + "d" * 86)) == ""
    long_path = Path("C:/" + "d" * 87)
    assert code.path_problem(long_path) == (
        f"dev-home's folder, {long_path}, is 90 characters long, and the longest path setup may "
        "make in it would pass Windows' limit of 260 characters. Move dev-home to a folder of 89 "
        "characters or fewer, such as C:\\Programming\\dev-home."
    )
