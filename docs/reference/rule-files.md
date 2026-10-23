# Rule files

The facts about the files in your dev-home's `rules/` and how setup joins them. [Your
rules](../guide/your-rules.md) explains them from the start.

## Where they are

| Folder | Joins for |
| --- | --- |
| `rules/_all-agents/mine/` | every agent, on every PC |
| `rules/<agent>/mine/` | one agent, on every PC: `claude-code` or `codex` |
| `rules/pcs/<pc>/_all-agents/mine/` | every agent, on the PC named `<pc>` |
| `rules/pcs/<pc>/<agent>/mine/` | one agent, on the PC named `<pc>` |

- `<pc>` is the computer's name in lowercase, with any character other than a letter or a digit
  as a hyphen, cut to 32 characters.
- Every `.md` file in one of those folders joins, subfolders included. Any other file is left
  out, and so is a file directly in a level folder, which setup reports on every sync.
- Setup creates an empty `my-rules.md`, and commits it, wherever one is missing, in any letter
  case: in `_all-agents/mine/` and in `<agent>/mine/` for each agent set up on the PC, at both the
  every-PC level and the PC's own. It never changes any other file there.

## The order they join in

Each agent's file holds the operating rules first, then the folders in the table's order, from
the top: `_all-agents`, `<agent>`, the PC's `_all-agents`, then the PC's `<agent>`. Within a
folder, files join alphabetically by their path, letter case aside.

Each file is read like this:

- **Encoding:** UTF-8, unless a byte-order mark says UTF-16. A byte that isn't UTF-8 is read as
  the replacement character, and a NUL byte is left out. A file with either kind of byte, or
  saved as UTF-16, is reported on every sync until it's saved as UTF-8. Setup never rewrites
  your files.
- **Comments:** an HTML comment that starts a line, outside a code block, is left out, whole
  lines and all, notes included. A comment in the middle of a line stays. A comment with no
  `-->` is left out to the file's end, and reported on every sync.
- **Code blocks:** a fenced code block a file leaves open is closed at the file's end, so it can't
  turn the files after it into code, and reported on every sync.
- **Blank lines:** a file's blank lines at its start and end are dropped, and one blank line
  separates two files. An empty file, or one with only a note, adds nothing.

## Headings

Markdown headings are lines that start with one to six `#` and then a space or nothing more,
outside code blocks. What a file has that isn't under a top-level heading (`#`) of its own, its
text before any heading and any deeper heading before its first top-level one, goes under
`# My rules`, so none of it reads as part of the operating rules.

Headings combine when they have the same level and text, letter case and spaces around them aside,
under the same heading. A combined section sits where its heading first appears. It holds its own
text first, from each file in the order they join, then its subsections, each where it first
appears, except that a deeper heading goes before a shallower one, so no text ends up under a
heading it didn't have. A heading with nothing under it is left out. The operating rules never
combine with your headings, and nothing is ever left out as a duplicate.

## Notes

A file may start with a note: an HTML comment whose first line is only `note`, then one field to
a line, `name: value`, until the first line that isn't one, then a blank line and any text.

```markdown
<!-- note
os: windows, macos

Why this rule is only for these systems.
-->
```

Setup reads one field: `os`, the operating systems the file loads on, `windows`, `macos`, or
`linux`, separated by commas, in any letter case. A name it doesn't know loads the file on every
system and is reported, with the name it may mean. Every other field is yours.

## Where they go

| Agent | File |
| --- | --- |
| Claude Code | `dev-home-rules.md` in each Claude Code folder's `rules\`, such as `~\.claude\rules\dev-home-rules.md` |
| Codex | `AGENTS.md` in each Codex home, such as `~\.codex\AGENTS.md` |

Setup keeps its own copy of what it last wrote to each, in `internal\.generated\last-written\` in
dev-home-toolkit's folder, and rewrites a file only while it still matches that copy, or while
there's no copy and the file already holds what setup would write. Any other file there is left as
it is and reported on every sync.

## Size

Setup measures your part of each agent's file on a PC, as UTF-8 bytes. Past
`rules.warnAboveKiB`, 32 KiB unless set, every sync says so in a `LARGE` line; 0 never warns. In
each Codex home, it raises `project_doc_max_bytes` to at least `codex.instructionsMaxKiB`, 128 KiB
unless set, and never lowers it. With no `project_doc_max_bytes` in its `config.toml`, Codex
reads 32 KiB of `AGENTS.md`, its home's and a project's together, and leaves the rest out without
saying so.

## Path length

dev-home's folder can be up to 89 characters long, so the longest path `rules/` can hold, with
room for git, stays under Windows' limit of 260. Setup reports a longer one on every sync, and
turns on git's `core.longpaths` in dev-home's own settings.
