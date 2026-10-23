# Your rules

Your rules are your own always-on preferences, such as "Never use em dashes." or "My project
repos are in C:/Programming.", which your agents load in every session. They live in your
dev-home, in `rules/`, so every PC gets them, with their history. This page shows where a rule
goes and how your agents get it. [Rule files](../reference/rule-files.md) has the details to
look up.

## Where a rule goes

`rules/` has four levels, from the widest to the narrowest:

| Folder | Its rules apply to | For example |
| --- | --- | --- |
| `rules/_all-agents/` | every agent, on every PC | "Never use em dashes." |
| `rules/<agent>/` | one agent, on every PC | in `rules/codex/`: "Ask before running a command outside the sandbox." |
| `rules/pcs/<pc>/_all-agents/` | every agent, on one PC | in `rules/pcs/office/_all-agents/`: "My project repos are in D:/Code." |
| `rules/pcs/<pc>/<agent>/` | one agent, on one PC | in `rules/pcs/office/claude-code/`: "Use the Bash tool for git." |

`<agent>` is `claude-code` or `codex`. `<pc>` is the PC's name in lowercase, with any character
other than a letter or a digit as a hyphen, such as `office` for a PC named OFFICE.

Put a rule at the widest level it's true for. Nothing says which rule wins when two disagree,
whether both are yours or one is from the operating rules, so fix the disagreement instead: an
agent tends to follow the later, narrower one, but not always.

## Your files

Each level keeps your files in its `mine/` folder. On each PC, setup makes sure that `mine/`
holds a `my-rules.md` at every level that applies there: `_all-agents` and each agent set up on
that PC, both for every PC and for that PC alone. It creates an empty one wherever it's missing,
and commits it, so you, or an agent you ask, always know which file to open: to add a rule for
Codex on this PC, open `rules/pcs/<pc>/codex/mine/my-rules.md`.

You can add other `.md` files to `mine/` too, in subfolders if you like. They join in alphabetical
order by their path. A file put directly in a level folder, outside `mine/`, never loads, and
setup says so on every sync.

An agent can add a rule for you: say where it applies, such as "add a rule for every agent: never
use em dashes", and it edits the right `my-rules.md`. Like any change in dev-home, it reaches your
other PCs once it's committed and pushed, at each one's next sync. Ask the agent to commit and
push it, or leave it: once nobody has touched the file for 15 minutes, a later `/handoff` or
`/knowledge` offers to.

## Rules for one operating system

A file can start with a note, an HTML comment that no agent sees:

```markdown
<!-- note
os: windows
-->

- Windows treats file names that differ only in letter case as the same file.
```

The file then loads only on that system. `os:` takes `windows`, `macos`, or `linux`, or several,
separated by commas. A name setup doesn't know, such as a misspelling, is reported on every sync,
and the file loads on every system until it's fixed, since a needed rule left out costs more than
an extra one.

## How your agents get them

Setup joins the operating rules, which come with dev-home-toolkit, and then your rules, from the
widest level to the narrowest, into one file for each agent:

- `dev-home-rules.md` in each Claude Code folder's `rules\`, such as `~\.claude\rules\`
- `AGENTS.md` in each Codex home, such as `~\.codex\`

Setup writes that file again at each sync, which comes at the start of nearly every skill
command, and whenever you run setup. A session loads it when it starts, so a change reaches
sessions started after that. When you answer no for an agent's folder in setup, setup removes
its file there, as long as it holds only what setup wrote; your rules stay in dev-home.

After the operating rules, whatever a file of yours has that isn't under a top-level heading (`#`)
of its own goes under `# My rules`. Headings with the same text and level, under the same heading,
combine into one section, letter case aside, so a `## Writing style` in two of your files reads as
one section. Comments that start a line, notes included, are left out, so they cost nothing. A
heading with nothing under it is left out too.

Edit your rules in dev-home, never in those files: setup keeps its own copy of what it last wrote
to each, and rewrites one only while it still matches that copy. When one of those files has
lines setup didn't write, or was there before setup, setup leaves it as it is, so that agent keeps
loading its old text, and says so on every sync. Move anything you want to keep from it into the
right `mine/`, delete the file, then run setup again.

## Keep them short

Every line costs tokens in every session, in every agent that loads it. Claude Code advises
keeping each instructions file under 200 lines, and each agent's file holds the operating rules
as well as yours.

A sync says so, in a `LARGE` line, when your rules for one agent on a PC pass 32 KiB. To change
that size, or turn the warning off with 0, change "Warn when your rules for one agent pass" with
`/dev-home configure`. Codex reads `AGENTS.md`, from its home and a project's folders together,
only up to "Codex's instruction limit", 128 KiB unless you change it, and leaves the rest out
without saying so.
