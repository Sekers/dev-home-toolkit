# 0029: The dev-home skill

**Built:** yes.

**Decision:** a general `dev-home` skill. `/dev-home` alone lists its commands. `/dev-home sync`
fetches, merges, and pushes in either mode, lists the files left uncommitted, and keeps to
`updates.checkEveryHours`. `/dev-home configure` runs `setup.py --configure`: it shows the current
values, previews the exact change, and makes it after the person's yes. Typing `/dev-home sync`
allows a sync, never a commit: it offers to commit a `STALE` file, and leaves a `LEFT` one alone
unless the person says it's theirs. In Codex, both say which command to run in a terminal, and
change nothing, while Codex can't use git's and gh's sign-ins.

Plain `/knowledge` stops being the sync someone asks for. It syncs as adding a note does, with
`--fetch auto`: with several active copies it checks GitHub every time, and with one only once
`devHome.checkEveryHours` has passed. `/knowledge <question>` still never syncs. Changed on
2026-10-20.

**Why:** one place to sync and configure that's easy to find, with room for more dev-home
commands without a skill for each. `/dev-home` alone lists rather than syncs, so typing the name
never reaches the network unasked. Plain `/knowledge` follows adding a note because, with several
copies, an interval of its own left it up to 12 hours behind another copy after a switch between
PCs, the case several copies exist for; and it was the one command the setting covered there,
which made the setting hard to predict. It costs about 0.8 to 1.3 s more per plain `/knowledge`
with several copies, measured on two developer PCs.

**Options set aside:** a skill only for syncing; plain `/knowledge` fetching every time with one
active copy too (a fetch when the person only wanted the list of subjects); plain `/knowledge`
reading the local copy until `devHome.checkEveryHours` passed, in both modes, as until 2026-10-20
(the stale list above); keeping that interval and rewording only setup's menu, which leaves the
stale list; and plain `/knowledge` never checking at all.

**Look again if:** the skill gathers commands that don't belong together.
