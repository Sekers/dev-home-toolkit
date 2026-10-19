# No safety net for hand edits to generated files

**Decision:** none for now, beyond the note at the top of each generated file.

**The problem:** setup rewrites `internal/.generated/` (and Codex's `AGENTS.md`) on every run
without checking for edits, so an edit made there is lost at the next sync, with no message.
Each skill's `SKILL.md` and the operating rules open with a note naming the template to change
instead, which agents see when the skill or rules load, and people see when they open the file.
That leaves the generated files with no note (`facts.py`, `prepare.py`, `filing-rules.md`, and
the handoff `template.md`, which can't have one because it's copied into every new handoff), and
anyone who ignores the note.

**Options set aside:** record what setup last wrote and, when a file differs, keep a copy and
report a `PROBLEM` (as chezmoi does); keep a `.bak` of the old file (as Ruler does); or make the
generated files read-only.

**Changed on 2026-10-18,** not built yet, with the reasons in
[Each agent gets its rules as one file setup writes in its own folder](each-agent-gets-its-rules-as-one-file-setup-writes-in-its-own-folder.md)
and
[Every file in dev-home belongs to dev-home-toolkit or to the end user](every-file-in-dev-home-belongs-to-dev-home-toolkit-or-to-the-end-user.md):
the notes go, from every generated file. Two kinds of file get a safety net. Setup's rules file
in each agent's folder: setup keeps a copy of what it last wrote, and asks where any added lines
go. And the files dev-home-toolkit owns in dev-home: a hand edit goes to the Recycle Bin before
setup puts the file back. What's left with no net is `internal/.generated/`, where an edit is
still lost at the next sync, now with no note warning against it.

**Look again if:** an edit is ever actually lost, or plugins are looked at again (see
[The skills are not shipped as plugins](the-skills-are-not-shipped-as-plugins.md)), where a hook
could block agents' edits under `internal/.generated/`.
