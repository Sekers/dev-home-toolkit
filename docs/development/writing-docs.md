# Writing the docs

The rules for changing the README and the pages under `docs/`. AGENTS.md points here; its rules
apply too.

- The README is the front door: what dev-home is, what it needs, setup, a typical day, safety,
  and a table of every page under `docs/`. Everything else goes in `docs/`:
  - `docs/skills/`: one page per skill in `templates/skills/`, with the same name.
  - `docs/reference/`: facts to look up, such as what the scripts report and what setup changes.
  - `docs/guide/` (not made yet): how-to pages read start to finish, when one leaves the README.
  - `docs/development/`: for people and agents changing dev-home-toolkit (see AGENTS.md's "Docs"):
    - one page for each area's rules, such as `skills.md`, which AGENTS.md points to
    - `decisions/`: one file per design decision, numbered and named for its subject, in the
      format its [README](decisions/README.md) gives, which also lists them all
    - `research/`: one page per investigation, saying what was tested, how, when, the results,
      the limits, and when to redo it, listed in its [README](research/README.md). Data a page
      cites sits beside it with the same name, such as `pylance-comparison.json`. Research can
      come before any decision, and a decision cites the research it rests on.
- `docs/` is for reading, and `internal/` for running: a script that produces research data goes
  in `internal/development/`, never in `docs/`.
- The README links to a skill's page in `docs/skills/`, never to its `SKILL.md`: the page is
  written for people, and the `SKILL.md` for agents. Each skill's page links to its `SKILL.md`,
  in its opening paragraph. Tests check both.
- Keep `docs/` ready to publish as a website: lowercase file names with hyphens, one `#` title
  per page, relative links between pages, and as few links out of `docs/` as possible, because
  those would break on a site, where each would have to become a full GitHub address.
- When you add, rename, or remove a page, update the README's table, or for a decision or a
  research page, its folder's `README.md`, which the README links. A test checks it.
