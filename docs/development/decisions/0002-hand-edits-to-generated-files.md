# 0002: Hand edits to generated files

**Built:** yes, except: the rules file setup writes in each Codex home still carries its note, and
neither safety net exists yet.

**Decision:** no safety net for hand edits to `internal/.generated/`, and no note in any generated
file warning against them. Two kinds of file that end users do edit get a net: setup's rules file
in each agent's folder, where setup keeps a copy of what it last wrote and asks where any added
lines go ([0064: Each agent's rules file](0064-each-agents-rules-file.md)), and the files
dev-home-toolkit owns in dev-home, where a hand edit goes to the Recycle Bin before setup puts the
file back ([0070: Who owns each file in dev-home](0070-who-owns-each-file-in-dev-home.md)).
Changed on 2026-10-18.

**The problem:** setup rewrites `internal/.generated/` on every run without checking for edits,
so an edit made there is lost at the next sync, with no message.

**Why:** `internal/.generated/` is machinery nobody runs or edits by hand. The notes cost tokens
on every load and differ by agent, as decision 0064 measured, so they go, and the files end users
have a reason to edit get a net instead.

**Options set aside:** for `internal/.generated/`, recording what setup last wrote and, when a
file differs, keeping a copy and reporting a `PROBLEM`, as chezmoi does (setup does this for its
rules file); keeping a `.bak` of the old file, as Ruler does; making the generated files
read-only; and keeping a note at the top of each generated file.

**Look again if:** an edit is ever actually lost, or plugins are looked at again (see
[0001: Plugins](0001-plugins.md)), where a hook
could block agents' edits under `internal/.generated/`.
