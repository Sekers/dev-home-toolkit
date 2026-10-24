"""Reading dev-home's rules/ and joining it into each agent's file (internal/shared/rules.py):
which files join, in what order, how each is read, and how their headings combine. And what setup
moves into rules/ from an agent's file: the lines it didn't write, with their headings, and the
moved file's name, note, and duplicates."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta, timezone
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


# The Codex home's rules file the joined rules are for.
SOURCE = Path("C:/Users/you/.codex/AGENTS.md")


def joined(code: ModuleType, rules: Path, system: str = "windows") -> object:
    return code.joined_rules(OPERATING, rules, "office", "codex", system, SOURCE)


def set_aside_from(source: Path, text: str) -> str:
    """A file setup set aside in unanswered/, from source, holding text."""
    return f"<!-- note\nby: setup\nfrom: {source}\n-->\n\n{text}"


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
        ("pcs/office/codex/mine", "Five"),
        ("pcs/office/_all-agents/mine", "Four"),
        ("codex/mine", "Three"),
        ("_all-agents/mine", "One"),
    ]:
        write(rules / folder / "my-rules.md", f"- {text}\n")
    write(rules / "pcs/office/codex/unanswered/moved.md", set_aside_from(SOURCE, "- Six\n"))
    write(rules / "_all-agents" / "mine" / "zz.md", "- Two\n")
    # Another agent's, and another PC's, never join.
    write(rules / "claude-code" / "mine" / "my-rules.md", "- Claude Code's\n")
    write(rules / "pcs" / "lab" / "codex" / "mine" / "my-rules.md", "- The lab's\n")
    assert own(code, rules) == (
        "# My rules\n\n- One\n\n- Two\n\n- Three\n\n- Four\n\n- Five\n\n- Six"
    )


def test_a_file_set_aside_joins_only_for_the_rules_file_its_note_names(
    code: ModuleType, rules: Path
) -> None:
    waiting = rules / "pcs" / "office" / "codex" / "unanswered"
    # Its note names the file in any letter case, with either kind of slash.
    write(waiting / "a.md", set_aside_from(Path(str(SOURCE).upper()), "- From this home.\n"))
    write(waiting / "b.md", set_aside_from(Path("C:/Users/you/.codex-work/AGENTS.md"), "- Work.\n"))
    write(waiting / "c.md", "- No note, so from nowhere setup knows.\n")
    # Outside unanswered/, the note's from field changes nothing.
    write(rules / "codex" / "mine" / "d.md", set_aside_from(Path("C:/elsewhere.md"), "- Mine.\n"))
    assert own(code, rules) == "# My rules\n\n- Mine.\n\n- From this home."


def test_rules_already_held_count_only_where_they_join_for_the_file_they_come_from(
    code: ModuleType, rules: Path
) -> None:
    waiting = rules / "pcs" / "office" / "codex" / "unanswered"
    work = Path("C:/Users/you/.codex-work/AGENTS.md")
    write(waiting / "work.md", set_aside_from(work, "- A rule.\n"))

    def held(text: str, source: Path | None, skip: Path | None = None) -> object:
        return code.already_held(text, rules, "office", "codex", "windows", source, skip)

    # Set aside from another home, it loads only there.
    assert held("- A rule.", SOURCE) is None
    assert held("- A rule.", work) == waiting / "work.md"
    # In any mine/ that joins for the agent here, it counts for every file.
    write(rules / "pcs" / "office" / "_all-agents" / "mine" / "kept.md", "- A rule.\n")
    assert (
        held("- A rule.", SOURCE) == rules / "pcs" / "office" / "_all-agents" / "mine" / "kept.md"
    )
    # Another agent's, or another PC's, doesn't.
    write(rules / "claude-code" / "mine" / "other.md", "- Another.\n")
    write(rules / "pcs" / "lab" / "codex" / "mine" / "lab.md", "- Another.\n")
    assert held("- Another.", SOURCE) is None
    # A file never counts as holding its own text.
    assert held("- A rule.", None, skip=waiting / "work.md") == (
        rules / "pcs" / "office" / "_all-agents" / "mine" / "kept.md"
    )
    # One whose note leaves this system out doesn't load here, so it doesn't count.
    write(rules / "codex" / "mine" / "mac.md", "<!-- note\nos: macos\n-->\n\n- On a Mac.\n")
    assert held("- On a Mac.", SOURCE) is None


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


# What setup moves into rules/ from an agent's file

# What setup last wrote in an agent's file, the operating rules and then the end user's.
WRITTEN = (
    f"{OPERATING}\n# My rules\n\n## Writing style\n\n- Never use em dashes.\n\n"
    "## Git\n\n- Sign every commit.\n"
)


def added(
    code: ModuleType, current: str, written: str = WRITTEN, operating: str = OPERATING
) -> str:
    text: str = code.added_text(current, written, operating)
    return text


def test_lines_added_to_setups_file_keep_the_headings_they_sat_under(code: ModuleType) -> None:
    current = WRITTEN.replace(
        "- Never use em dashes.\n", "- Never use em dashes.\n- Use sentence case in headings.\n"
    )
    assert (
        added(code, current) == "# My rules\n\n## Writing style\n\n- Use sentence case in headings."
    )


@pytest.mark.parametrize("level", ["#", "##"])
def test_lines_added_under_the_operating_rules_keep_none_of_their_headings(
    code: ModuleType, level: str
) -> None:
    # The operating rules' own sections, such as a skill's block, at either level.
    operating = f"{OPERATING}\n{level} When the `handoff` skill is available\n\n- A skill's rule.\n"
    written = WRITTEN.replace(OPERATING, operating)
    for after in ("- An operating rule.\n", "- A skill's rule.\n"):
        current = written.replace(after, f"{after}- My own line.\n")
        assert added(code, current, written, operating) == "# My rules\n\n- My own line."


def test_runs_of_added_lines_share_the_headings_they_have_in_common(code: ModuleType) -> None:
    current = (
        WRITTEN.replace("## Writing style\n\n", "## Writing style\n\n- First.\n\n")
        .replace("- Never use em dashes.\n", "- Never use em dashes.\n- Second.\n")
        .replace("- Sign every commit.\n", "- Sign every commit.\n- Third.\n")
    )
    assert added(code, current) == (
        "# My rules\n\n## Writing style\n\n- First.\n\n- Second.\n\n## Git\n\n- Third."
    )


def test_a_changed_line_counts_as_added_and_a_removed_one_adds_nothing(code: ModuleType) -> None:
    changed = WRITTEN.replace("- Never use em dashes.", "- Never use em dashes, ever.")
    assert added(code, changed) == "# My rules\n\n## Writing style\n\n- Never use em dashes, ever."
    assert added(code, WRITTEN.replace("- Sign every commit.\n", "")) == ""


def test_blank_lines_and_spaces_at_a_lines_end_add_nothing(code: ModuleType) -> None:
    current = WRITTEN.replace("- Never use em dashes.\n", "- Never use em dashes.  \n\n\n")
    assert added(code, current) == ""


def test_a_heading_in_fenced_code_isnt_one_that_lines_sit_under(code: ModuleType) -> None:
    written = f"{OPERATING}\n# My rules\n\n## Examples\n\n```\n# Not a heading\n```\n"
    assert added(code, f"{written}- Added.\n", written) == "# My rules\n\n## Examples\n\n- Added."


def test_added_lines_in_a_code_block_stay_code(code: ModuleType) -> None:
    written = f"{OPERATING}\n# My rules\n\n## Examples\n\n~~~text\nold command\n~~~\n"
    # Changed inside the block: the block's fence goes around it.
    changed = written.replace("old command", "new command")
    assert added(code, changed, written) == (
        "# My rules\n\n## Examples\n\n~~~text\nnew command\n~~~"
    )
    # A block added whose fence never closes is closed at the run's end.
    opened = f"{written}\n```\nunclosed\n"
    assert added(code, opened, written) == "# My rules\n\n## Examples\n\n```\nunclosed\n```"
    # Every block changed, each fence matching the same line in many places.
    blocks = f"{OPERATING}\n# My rules\n\n## A\n\n```\none\n```\n\n## B\n\n```\ntwo\n```\n"
    renamed = blocks.replace("one", "uno").replace("two", "dos")
    assert added(code, renamed, blocks) == (
        "# My rules\n\n## A\n\n```\nuno\n```\n\n## B\n\n```\ndos\n```"
    )


def test_what_moves_depends_on_the_copy_and_the_operating_rules_heading(
    code: ModuleType,
) -> None:
    more = WRITTEN.replace("- Sign every commit.\n", "- Sign every commit.\n- Push often.\n")
    new = f"{OPERATING}\n# My rules\n\n- A newer rule.\n"

    def to_move(current: str, kept: str | None) -> object:
        return code.to_move(current, kept, new, OPERATING)

    # With a copy, the lines that aren't in it.
    assert to_move(more, WRITTEN) == code.ToMove("# My rules\n\n## Git\n\n- Push often.")
    # With no copy, a file that isn't setup's moves whole.
    theirs = "\n\n# Mine\n\n- An old rule.\n\n"
    assert to_move(theirs, None) == code.ToMove("# Mine\n\n- An old rule.", whole=True)
    # With no copy, setup's own from another PC: the lines that aren't in what it writes now.
    assert to_move(WRITTEN, None) == code.ToMove(
        "# My rules\n\n## Writing style\n\n- Never use em dashes.\n\n## Git\n\n- Sign every commit."
    )
    assert to_move(new, None) == code.ToMove("")
    # Nothing moves from a file of blank lines alone.
    assert to_move("\n \n", None) == code.ToMove("")


def test_a_large_file_with_every_rule_changed_moves_every_rule(code: ModuleType) -> None:
    """Thousands of blank lines, which difflib alone would pair with each other for over a
    minute."""
    own = "\n\n".join(f"## Section {n}\n\n- Rule {n}, with some words." for n in range(1500))
    written = f"{OPERATING}\n# My rules\n\n{own}\n"
    moved = added(code, written.replace("some words", "other words"), written)
    assert moved == f"# My rules\n\n{own.replace('some words', 'other words')}"


@pytest.mark.parametrize(("repeats", "between"), [(50, "\n"), (150, "- Same.\n" * 148)])
def test_lines_between_anchors_that_all_repeat_match_only_when_few(
    code: ModuleType, repeats: int, between: str
) -> None:
    """No line between the first and the last change occurs once on each side, so difflib
    compares them only when there are few: two runs move. With many, every line moves."""
    written = f"{OPERATING}\n# My rules\n\n" + "- Same.\n" * repeats
    lines = written.split("\n")
    first, last = lines.index("- Same."), len(lines) - 2
    lines[first], lines[last] = "- First.", "- Last."
    assert added(code, "\n".join(lines), written) == f"# My rules\n\n- First.\n{between}- Last."


@pytest.mark.parametrize(
    ("pc", "folder", "path", "name"),
    [
        ("office", "C:/Users/you/.codex", "AGENTS.md", "moved-office-codex-agents.md"),
        (
            "office",
            "C:/Users/you/.claude",
            "rules/dev-home-rules.md",
            "moved-office-claude-rules-dev-home-rules.md",
        ),
        (
            "office",
            "C:/Users/you/.claude-work",
            "rules/dev-home-rules.MD",
            "moved-office-claude-work-rules-dev-home-rules.md",
        ),
        # A PC's folder can end in a hyphen, as pc_folder writes Caf\u00e9; the name has one.
        ("caf-", "C:/Users/you/.codex", "AGENTS.md", "moved-caf-codex-agents.md"),
    ],
)
def test_a_moved_files_name_says_where_it_came_from(
    code: ModuleType, pc: str, folder: str, path: str, name: str
) -> None:
    assert code.moved_name(pc, Path(folder), Path(path), []) == name


def test_a_taken_name_in_any_letter_case_gets_the_first_free_number(code: ModuleType) -> None:
    taken = ["MOVED-OFFICE-CODEX-AGENTS.md", "moved-office-codex-agents-2.md", "my-rules.md"]
    name = code.moved_name("office", Path("C:/Users/you/.codex"), Path("AGENTS.md"), taken)
    assert name == "moved-office-codex-agents-3.md"


def test_a_moved_files_name_with_its_number_is_cut_to_60_characters(code: ModuleType) -> None:
    pc = "a" * 32
    folder, path = Path("C:/Users/you/.claude-work"), Path("rules/dev-home-rules.md")
    # Cut where a hyphen would end it, the hyphen goes too.
    first = code.moved_name(pc, folder, path, [])
    assert first == f"moved-{pc}-claude-work-rules.md"
    second = code.moved_name(pc, folder, path, [first])
    assert second == f"moved-{pc}-claude-work-rule-2.md"
    assert (len(first), len(second)) == (59, 60)


def test_a_moved_file_starts_with_a_note_setup_reads_and_joining_leaves_out(
    code: ModuleType, rules: Path
) -> None:
    source = Path("C:/Users/you/.codex/AGENTS.md")
    when = datetime(2030, 1, 15, 9, 30, tzinfo=timezone(timedelta(hours=1)))
    about = "Moved here when setup took over this PC's Codex home."
    text = code.moved_file("\n- A rule.\n\n", when=when, pc="office", source=source, about=about)
    assert text == (
        "<!-- note\nby: setup\nwhen: 2030-01-15 09:30:00+01:00\npc: office\n"
        f"from: {source}\n\n{about}\n-->\n\n- A rule.\n"
    )
    assert code.note_fields(text.split("\n")) == {
        "by": "setup",
        "when": "2030-01-15 09:30:00+01:00",
        "pc": "office",
        "from": str(source),
    }
    write(rules / "_all-agents" / "mine" / "moved.md", text)
    assert own(code, rules) == RULE.replace("- Rule", "- A rule.")


def test_a_file_that_already_holds_the_text_is_found_whatever_its_note(
    code: ModuleType, rules: Path
) -> None:
    mine = rules / "_all-agents" / "mine"
    write(mine / "my-rules.md", "- Something else.\n")
    # Its own note, Windows line endings, and blank lines at its end.
    copied = b"<!-- note\r\nby: user\r\n-->\r\n\r\n- A rule.\r\n\r\n"
    (mine / "older").mkdir()
    (mine / "older" / "copied.md").write_bytes(copied)
    when = datetime(2030, 1, 15, 9, 30, tzinfo=UTC)
    moving = code.moved_file(
        "- A rule.", when=when, pc="office", source=Path("AGENTS.md"), about="Moved."
    )
    assert code.duplicate_of(moving, mine) == mine / "older" / "copied.md"
    assert code.duplicate_of("- Another rule.", mine) is None
    assert code.duplicate_of("- A rule.", rules / "codex" / "mine") is None


def test_a_note_that_never_ends_takes_the_whole_file(code: ModuleType) -> None:
    assert code.evened("\n<!-- note\nby: user\n\n- Inside the note.\n") == ""
    assert code.evened("- No note.\n<!-- note\n-->\n") == "- No note.\n<!-- note\n-->"


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
