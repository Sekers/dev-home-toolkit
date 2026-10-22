"""README.md, docs/, and the rest of the repo's text, read without running anything: links,
headings, the pages for skills, and the words for the developer."""

import re
from pathlib import Path

from helpers import REPO_ROOT

DOCS = REPO_ROOT / "docs"
SKILLS = REPO_ROOT / "templates" / "skills"


def markdown_links(lines: list[str]) -> list[str]:
    """The target of each link in Markdown text, which is what's between the parentheses of
    [text](target). Leaves out code, where a link is only an example, and links to the web."""
    targets: list[str] = []
    in_code = False
    for line in lines:
        if re.match(r"\s*```", line):
            in_code = not in_code
            continue
        if in_code:
            continue
        for match in re.finditer(r"\]\(([^)\s]+)\)", re.sub(r"`[^`]*`", "", line)):
            target = match.group(1)
            if not re.match(r"[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                targets.append(target)
    return targets


def markdown_anchors(lines: list[str]) -> list[str]:
    """The anchor GitHub gives each heading: lower case, punctuation dropped, and a hyphen for
    each space."""
    anchors: list[str] = []
    in_code = False
    for line in lines:
        if re.match(r"\s*```", line):
            in_code = not in_code
            continue
        if in_code:
            continue
        heading = re.match(r"#{1,6}\s+(.+?)\s*$", line)
        if heading:
            anchors.append(re.sub(r"[^a-z0-9 _-]", "", heading.group(1).lower()).replace(" ", "-"))
    return anchors


def lines_of(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


# Raw HTML as CommonMark defines it: an open tag, with any attributes, or a closing tag. GitHub
# hides it, so <what we ran or read> vanishes from the page. Anything else in angle brackets
# shows as written, such as <folder/file>, an autolink, or a comment.
ATTRIBUTE = r"""\s+[A-Za-z_:][A-Za-z0-9_.:-]*(?:\s*=\s*(?:[^\s"'=<>`]+|'[^']*'|"[^"]*"))?"""
HTML_TAG = re.compile(rf"<[A-Za-z][A-Za-z0-9-]*(?:{ATTRIBUTE})*\s*/?>|</[A-Za-z][A-Za-z0-9-]*\s*>")
# A code span ends at the next run of exactly as many backticks, which may be on a later line of
# the same paragraph.
CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)", re.DOTALL)


def html_tags(lines: list[str]) -> list[tuple[int, str]]:
    """Each piece of text that renders as an HTML tag, with its line number, outside code: fenced
    blocks, code spans, and a skill's frontmatter, which isn't rendered as Markdown. Lines are
    taken a paragraph at a time, so a code span can carry on to the next line."""
    found: list[tuple[int, str]] = []
    start = 0
    if lines and lines[0].strip() == "---":
        start = next((n + 1 for n in range(1, len(lines)) if lines[n].strip() == "---"), 0)
    paragraph: list[str] = []
    first = start
    in_code = False

    def check(text: str, at: int) -> None:
        # Blank out code spans and escaped brackets, keeping line breaks, so line numbers hold.
        text = CODE_SPAN.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text.replace("\\<", "  "))
        for match in HTML_TAG.finditer(text):
            found.append((at + text[: match.start()].count("\n") + 1, match.group()))

    for number in range(start, len(lines)):
        line = lines[number]
        if re.match(r"\s*(```|~~~)", line):
            check("\n".join(paragraph), first)
            paragraph = []
            in_code = not in_code
            continue
        if in_code:
            continue
        if not line.strip():
            check("\n".join(paragraph), first)
            paragraph = []
            continue
        if not paragraph:
            first = number
        paragraph.append(line)
    check("\n".join(paragraph), first)
    return found


def pages() -> list[Path]:
    return [REPO_ROOT / "README.md", *sorted(DOCS.rglob("*.md"))]


def linked_files(page: Path) -> list[tuple[str, Path, str]]:
    """Each link on a page: its target as written, the file it leads to, and its anchor."""
    found: list[tuple[str, Path, str]] = []
    for target in markdown_links(lines_of(page)):
        path, _, anchor = target.partition("#")
        file = (page.parent / path).resolve() if path else page
        found.append((target, file, anchor))
    return found


def name(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_the_link_search_finds_each_kind_and_nothing_in_code_or_on_the_web() -> None:
    sample = [
        "See [a page](docs/a.md), [a heading](#part-two), and [both](../b.md#top).",
        "Not `[code](docs/no.md)`, and not [the web](https://example.com/no.md).",
        "```",
        "[fenced](docs/no.md)",
        "```",
        "A link with [`code` as its text](c.md).",
    ]
    assert markdown_links(sample) == ["docs/a.md", "#part-two", "../b.md#top", "c.md"]


def test_the_tag_search_follows_commonmark_and_skips_code() -> None:
    sample = [
        "---",
        "description: <in frontmatter>",
        "---",
        "Offer <what we ran or read>, and </b> closes one.",
        "Not <folder/file>, <https://example.com>, <a@example.com>, <!-- a comment -->, or \\<x>.",
        "Not `<in a span>`, or `a span that goes on",
        "to the next line <name>`.",
        "```",
        "<fenced>",
        "```",
        "And <br/> on line 11.",
    ]
    assert html_tags(sample) == [(4, "<what we ran or read>"), (4, "</b>"), (11, "<br/>")]


def test_no_text_renders_as_an_html_tag() -> None:
    # GitHub would hide it. The handoff template is left out: agents copy it into new handoffs,
    # where code formatting could end up around text that isn't code.
    template = REPO_ROOT / "templates" / "skills" / "handoff" / "template.md"
    files = pages() + sorted(
        path for path in (REPO_ROOT / "templates").rglob("*.md") if path != template
    )
    found = [f"{name(path)}:{n}: {tag}" for path in files for n, tag in html_tags(lines_of(path))]
    assert found == []


def test_every_link_points_to_a_file_that_exists() -> None:
    missing = [f"{name(p)}: {t}" for p in pages() for t, f, _ in linked_files(p) if not f.exists()]
    assert len(pages()) > 1
    assert missing == []


def test_every_link_to_a_heading_points_to_one_that_exists() -> None:
    missing = [
        f"{name(page)}: {target}"
        for page in pages()
        for target, file, anchor in linked_files(page)
        if anchor and file.exists() and anchor not in markdown_anchors(lines_of(file))
    ]
    assert missing == []


def test_the_readme_links_to_every_page_under_docs() -> None:
    # The README's table lists the pages, and a folder of many, such as the decisions, lists its
    # own in its README.md, which the README links. A page neither lists can't be found.
    listed = {file for _, file, _ in linked_files(REPO_ROOT / "README.md")}
    for index in [file for file in listed if file.name == "README.md"]:
        listed |= {file for _, file, _ in linked_files(index)}
    unlisted = [name(page) for page in pages()[1:] if page.resolve() not in listed]
    assert unlisted == []


DECISIONS = DOCS / "development" / "decisions"


def file_name_for(decision: str) -> str:
    """A decision's name as its file names it: lower case, apostrophes dropped, and a hyphen for
    each run of anything else that isn't a letter or digit."""
    return re.sub(r"[^a-z0-9]+", "-", decision.lower().replace("'", "")).strip("-")


# The values a decision's opening line may have, as decisions/README.md gives them.
BUILT_LINE = re.compile(
    r"\*\*Built:\*\* (?:yes\.|not yet\.|nothing to build\.|yes, except: \S.*)"
    r"|\*\*Replaced by:\*\* \[\d{4}: [^]]+\]\(\d{4}-[a-z0-9-]+\.md\)\.?"
)


def decision_problems(folder: Path) -> list[str]:
    """What breaks the format decisions/README.md gives: files named NNNN-<name>.md, numbered
    from 0001 with no gaps, each titled "# NNNN: <name>", where the file's name is the title's
    name in lower case with hyphens, opening with a Built line of one of the format's values, or
    a Replaced by line, and listed in the folder's README.md by its number and name."""
    files = sorted(folder.glob("[0-9]*.md"))
    problems: list[str] = []
    expected = [f"{n:04d}" for n in range(1, len(files) + 1)]
    if [file.name[:4] for file in files] != expected:
        problems.append("the numbers don't run from 0001 with no gaps")
    readme = folder / "README.md"
    listed = {
        (readme.parent / link[2]).resolve(): link[1]
        for line in lines_of(readme)
        for link in re.finditer(r"\[([^]]+)\]\(([^)\s#]+)\)", line)
    }
    for file in files:
        lines = lines_of(file)
        title = re.fullmatch(r"# (\d{4}): (.+)", lines[0]) if lines else None
        if not title or file.name != f"{title[1]}-{file_name_for(title[2])}.md":
            problems.append(f"{file.name}: its name and title don't match NNNN-<name>.md")
        opening = next((line for line in lines[1:] if line.strip()), "")
        if not opening.startswith(("**Built:** ", "**Replaced by:** ")):
            problems.append(f"{file.name}: doesn't open with its Built line")
        elif not BUILT_LINE.fullmatch(opening):
            problems.append(f"{file.name}: its Built line isn't one of the format's values")
        text = listed.get(file.resolve())
        if text is None:
            problems.append(f"{file.name}: not listed in README.md")
        elif title and text != f"{title[1]}: {title[2]}":
            problems.append(f"{file.name}: README.md lists it as {text!r}")
    return problems


def test_each_decision_is_numbered_named_and_listed() -> None:
    assert decision_problems(DECISIONS) == []


def test_the_decision_check_finds_each_kind_of_problem(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("- [0001: Fine](0001-fine.md)\n", encoding="utf-8")
    (tmp_path / "0001-fine.md").write_text("# 0001: Fine\n\n**Built:** yes.\n", encoding="utf-8")
    assert decision_problems(tmp_path) == []
    (tmp_path / "0003-gap.md").write_text("# 0003: Gap\n\n**Built:** yes.\n", encoding="utf-8")
    (tmp_path / "0002-wrong-name.md").write_text("# 0002: Right name\n\nText.\n", encoding="utf-8")
    assert decision_problems(tmp_path) == [
        "0002-wrong-name.md: its name and title don't match NNNN-<name>.md",
        "0002-wrong-name.md: doesn't open with its Built line",
        "0002-wrong-name.md: not listed in README.md",
        "0003-gap.md: not listed in README.md",
    ]
    (tmp_path / "0004-also.md").write_text("# 0004: Also\n\n**Built:** yes.\n", encoding="utf-8")
    (tmp_path / "0002-wrong-name.md").unlink()
    assert decision_problems(tmp_path)[0] == "the numbers don't run from 0001 with no gaps"


def test_the_decision_check_reads_the_built_line_and_the_list(tmp_path: Path) -> None:
    readme = "- [0001: Fine](0001-fine.md)\n- [0002: Old name](0002-new-name.md)\n"
    (tmp_path / "README.md").write_text(readme, encoding="utf-8")
    fine = "# 0001: Fine\n\n**Built:** yes, except: the part\nthat wraps.\n"
    (tmp_path / "0001-fine.md").write_text(fine, encoding="utf-8")
    renamed = "# 0002: New name\n\n**Built:** maybe.\n"
    (tmp_path / "0002-new-name.md").write_text(renamed, encoding="utf-8")
    assert decision_problems(tmp_path) == [
        "0002-new-name.md: its Built line isn't one of the format's values",
        "0002-new-name.md: README.md lists it as '0002: Old name'",
    ]
    for value in ("not yet.", "nothing to build.", "yes."):
        (tmp_path / "0001-fine.md").write_text(f"# 0001: Fine\n\n**Built:** {value}\n", "utf-8")
        assert decision_problems(tmp_path)[0].startswith("0002-")
    replaced = "# 0001: Fine\n\n**Replaced by:** [0002: New name](0002-new-name.md).\n"
    (tmp_path / "0001-fine.md").write_text(replaced, encoding="utf-8")
    assert decision_problems(tmp_path)[0].startswith("0002-")


def test_every_skill_has_a_page_and_every_page_a_skill() -> None:
    skills = sorted(folder.name for folder in SKILLS.iterdir() if folder.is_dir())
    skill_pages = sorted(page.stem for page in (DOCS / "skills").glob("*.md"))
    assert skills
    assert skills == skill_pages


def test_the_readme_links_to_each_skills_page_never_its_skill_file() -> None:
    # A skill's page is written for people and its SKILL.md for agents.
    from_readme = [name(file) for _, file, _ in linked_files(REPO_ROOT / "README.md")]
    assert [f for f in from_readme if f.endswith("/SKILL.md")] == []


def written_files() -> list[Path]:
    """Every Markdown and Python file in the repo, leaving out what git, the development tools,
    and setup make."""
    made = {".git", ".venv", ".test-sandbox", ".generated", ".python", "__pycache__"}
    return sorted(
        path
        for pattern in ("*.md", "*.py")
        for path in REPO_ROOT.rglob(pattern)
        if not made.intersection(path.relative_to(REPO_ROOT).parts)
        and not any(part.endswith("_cache") for part in path.parts)
    )


# The names for the developer that AGENTS.md's "Who's who" section rules out, so that every other
# word for a person means an end user. Spaced as patterns, so this file doesn't match itself.
OTHER_NAMES = re.compile(
    r"\b(?:the|its)\s+(?:author|maintainers?)\b|\bperson\s+you\s+work\s+for\b", re.IGNORECASE
)


def test_no_file_calls_the_developer_anything_but_the_developer() -> None:
    found: list[str] = []
    for path in written_files():
        in_rule = False
        for number, line in enumerate(lines_of(path), 1):
            # The section that sets the rule names what it rules out.
            if path.name == "AGENTS.md" and line.startswith("## "):
                in_rule = line.startswith("## Who's who")
            if not in_rule and OTHER_NAMES.search(line):
                found.append(f"{name(path)}:{number}: {line.strip()}")
    assert len(written_files()) > 10
    assert found == []


# Wording that uses "tool" for an agent or a program, which the glossary rules out, such as "both
# tools" for Claude Code and Codex, "a tool's settings file", or "the tools are on the PATH". An
# agent's own tools keep the word, such as Claude Code's Bash tool, and so do the development
# tools.
TOOL_FOR_AN_AGENT = re.compile(
    r"\b(?:both|either|neither|each|every|another|other|any|all|your|their|those|these|which"
    r"|most|some|many|the|an?)\s+(?:AI\s+(?:agent\s+)?)?tools?\b"
    r"|\bAI\s+(?:agent\s+)?tools?\b"
    r"|\b(\w+)\s+tool(?:'s|s')",
    re.IGNORECASE,
)
# The words before "tools'" or "tool's" that name an agent's own tools, or the development tools.
OWN_TOOLS = {"bash", "powershell", "shell", "file", "development"}
# Text in double quotes or in a code span is talked about, not used, such as "both tools" here.
# Either may wrap onto the next line, but never past a blank one.
MENTIONED = re.compile(r'"(?:[^"\n]|\n(?!\s*\n))*"|`(?:[^`\n]|\n(?!\s*\n))*`')


def tool_mix_ups(text: str, *, markdown: bool) -> list[str]:
    """Each place in a file's text that uses "tool" for an agent or a program, as its line number
    and the words, such as 3: both tools."""
    if markdown:
        text = MENTIONED.sub(lambda match: re.sub(r"\S", " ", match.group()), text)
    found: list[str] = []
    for match in TOOL_FOR_AN_AGENT.finditer(text):
        if match.group(1) and match.group(1).lower() in OWN_TOOLS:
            continue
        number = text.count("\n", 0, match.start()) + 1
        found.append(f"{number}: {' '.join(match.group().split())}")
    return found


def test_no_file_uses_tool_for_an_agent_or_a_program() -> None:
    # The glossary and this file name the words they rule out.
    naming = {"docs/development/glossary.md", "internal/development/tests/test_docs.py"}
    found = [
        f"{name(path)}:{place}"
        for path in written_files()
        if name(path) not in naming
        for place in tool_mix_ups(path.read_text(encoding="utf-8"), markdown=path.suffix == ".md")
    ]
    assert all((REPO_ROOT / file).is_file() for file in naming)
    assert found == []


def test_the_tool_search_tells_a_mix_up_from_a_name() -> None:
    sample = (
        "Both tools read it, and each\ntool's settings file changes. Claude Code's Bash tool, its\n"
        "PowerShell tool's rules, the development tools' settings, and \"both tools\" stay.\n"
        "`allowed-tools` and dev-home-tools stay too, but an AI tool and the tools don't.\n"
    )
    assert tool_mix_ups(sample, markdown=True) == [
        "1: Both tools",
        "1: each tool",
        "4: an AI tool",
        "4: the tools",
    ]
    # A quote can wrap onto the next line, but a stray one doesn't hide the next paragraph.
    wrapped = 'The "both\ntools" phrase, and a stray " mark.\n\nThen each tool.\n'
    assert tool_mix_ups(wrapped, markdown=True) == ["4: each tool"]
    # In Python, quotes hold strings that get printed, so they're checked too.
    assert tool_mix_ups('print("both tools")', markdown=False) == ["1: both tools"]


def test_every_skills_page_links_to_its_skill_file() -> None:
    unlinked = []
    for skill in sorted(folder for folder in SKILLS.iterdir() if folder.is_dir()):
        page = DOCS / "skills" / f"{skill.name}.md"
        if not page.exists():
            continue
        linked = {file for _, file, _ in linked_files(page)}
        if (skill / "SKILL.md").resolve() not in linked:
            unlinked.append(skill.name)
    assert unlinked == []
