# The knowledge index lists subjects, and each subject lists its notes

**Decision:** dev-home's knowledge index becomes two levels. `knowledge/README.md` lists only the
subjects, one line each, and each subject folder has its own `README.md` listing its notes, one
line each. Not built yet. Decided by the developer on 2026-10-18.

```text
knowledge/
  README.md                 the subject list
  python/
    README.md               this subject's notes
    virtual-environments.md
    windows-launcher.md
  git-and-github/
    README.md
    ...
```

`knowledge/README.md`:

```markdown
# Knowledge base

- python/: Python on Windows and macOS: launchers, virtual environments, packaging.
- git-and-github/: git behavior and GitHub features: line endings, merges, Actions.
```

`knowledge/python/README.md`:

```markdown
# python

- virtual-environments.md: where venv and uv put environments, and which Python each one uses.
- windows-launcher.md: which Python the py launcher starts on Windows, and how to pick another.
```

- **A lookup** reads the subject list, then a subject's list (or two, when a question spans
  them), then only the note it needs.
- **Filing a note** adds its line to its subject's list in the same commit. A new subject adds its
  folder, its `README.md`, and a line in the subject list. Subjects stay one level deep, as before.
- **Lines:** a subject's line stays as broad as the subject. A note's line names the tools the note
  covers, and changes with the note.
- **Owner:** the indexes are the end user's, kept by the knowledge skill. Setup never changes
  them; it only creates `knowledge/README.md`, with its title, when it's missing ([Every file in dev-home belongs to dev-home-toolkit or to the end user](every-file-in-dev-home-belongs-to-dev-home-toolkit-or-to-the-end-user.md)).
  The explanation of what belongs in the knowledge base lives in the knowledge skill, where its
  filing rules already say it, and in dev-home's root README. The old index's intro paragraph,
  which repeated it, goes.
- **Layout:** this is the `knowledge` part's layout, with its own layout version
  ([dev-home records the newest version and each part's layout](dev-home-records-the-newest-version-and-each-parts-layout.md)).
  `merge=union` in dev-home's `.gitattributes` widens to every index in `knowledge/`.
- **Moving an existing knowledge base:** before 1.0.0, the rows are rewritten into subject lists
  once, by hand. The knowledge skill's new steps are shown to the developer with their word count
  before they're built, as AGENTS.md's "AI usage" asks.

**Why:**

- The index is read on every lookup (the filing rules say so). Measured 2026-10-18 on one end
  user's knowledge base: 73 rows, about 24.5 KB, roughly 6,100 tokens per lookup, about 85 per
  note, so 300 notes would cost about 25,000. This design is about 750 tokens per lookup for the
  same base, and grows with subjects, not notes.
- It follows two established patterns, adapted: Claude Code's auto memory keeps one index of short
  lines and opens each file only when needed, and Anthropic's skill authoring guide splits
  reference material by domain, so an agent reads only the part it needs.
- A note's line names the tools it covers so an agent can skip a note that doesn't apply, rather
  than open it and find nothing. A subject's line stays broad so the subject list doesn't go stale
  as notes are added.
- GitHub shows a folder's `README.md` below its file list, so each level reads on GitHub too
  (checked on a live folder on 2026-10-18). It doesn't show an `index.md`, checked the same way,
  so the files keep the name `README.md`.

**Costs:** one more file read per lookup, and a note that fits two subjects lives in one, so an
agent may read two subject lists.

**Options set aside:**

- One index of short rows, the path and a line of key terms: about 2,600 tokens for the same base,
  still growing with every note.
- A lookup script that prints only the rows matching the question's words: the fewest tokens, but
  a process per lookup, and it misses when the question uses other words, so it would need an
  index behind it anyway.
- The old table without its intro: about 6,000 tokens per lookup, growing by about 85 per note.
- Splitting the old file between dev-home-toolkit's text and the end user's rows, with setup
  rewriting the top: two owners in one file, and the repeated text stays.
- A hook that names no tool, such as "AI agents' instruction files": an agent would open a note
  about other tools and find nothing.
- `index.md` in place of `README.md`: GitHub doesn't show it.

**This changes:**
[The sync checks the knowledge index before committing it](the-sync-checks-the-knowledge-index-before-committing-it.md),
whose checks now cover every index file.

**Look again if:** a subject grows past what one list reads cheaply, or the agents gain a search
that makes an index unnecessary.
