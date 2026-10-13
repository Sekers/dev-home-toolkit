# AGENTS.md holds only what every session needs

**Decision:** AGENTS.md holds the rules every agent working here needs in every session, each
with a short reason, and stays under 200 lines. The rules for one area, and how things work, live
in pages under `docs/development/`: `skills.md`, `scripts.md`, `testing.md`, `writing-docs.md`,
and `fresh-agent-reads.md`. AGENTS.md's "Rules for each area" says which page to read before
changing which area.

**Why:**

- Claude Code's docs (read 2026-10-12) say to "target under 200 lines per CLAUDE.md file. Longer
  files consume more context and reduce adherence", and Claude Code warns at startup about a
  longer one. AGENTS.md had reached 449 lines.
- Codex stops reading instruction files once the global file and the project's together reach
  `project_doc_max_bytes`, 32 KiB by default, and cuts the project's part without a warning.
  AGENTS.md alone was 32,155 bytes.
- A page is read only when its area changes, so a session pays for it only then.

**Options set aside:**

- Moving only explanations and reference: AGENTS.md stayed at about 350 lines.
- An AGENTS.md in each folder: Claude Code loads one when it works in that folder, but Codex
  reads only from the repo root down to the folder it started in, once at startup (OpenAI's
  docs, read 2026-10-12), so it would miss them.
- A limit with headroom, "well under 200 lines": vague, and the developer chose to readjust when
  it gets close.
- A test that fails at 200 lines, with a rule to ask what to move.

**Look again if:** Codex reads AGENTS.md files in subfolders as it works in them, or Claude
Code's recommended size changes.
