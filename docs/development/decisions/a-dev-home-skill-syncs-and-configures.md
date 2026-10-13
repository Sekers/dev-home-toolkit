# A dev-home skill syncs and configures

**Decision:** a general `dev-home` skill. `/dev-home` alone lists its commands. `/dev-home sync`
fetches, merges, and pushes in either mode, lists the files left uncommitted, and keeps to
`updates.checkEveryHours`. `/dev-home configure` runs `setup.py --configure`: it shows the current
values, previews the exact change, and makes it after the person's yes. Typing `/dev-home sync`
allows a sync, never a commit: it offers to commit a `STALE` file, and leaves a `LEFT` one alone
unless the person says it's theirs. In Codex, both say which command to run in a terminal, and
change nothing, while Codex can't use git's and gh's sign-ins.

Plain `/knowledge` stops being the sync someone asks for. It reads the local copy, unless
`devHome.checkEveryHours` has passed, when it syncs first, in both modes.
`/knowledge <question>` still never syncs.

**Why:** one place to sync and configure that's easy to find, with room for more dev-home
commands without a skill for each. `/dev-home` alone lists rather than syncs, so typing the name
never reaches the network unasked. Plain `/knowledge` is a lookup, so it follows the lookups'
rule, with a check at the interval so its list of subjects is never far behind.

**Options set aside:** a skill only for syncing; plain `/knowledge` syncing as before (a fetch
when the person only wanted the list of subjects); and plain `/knowledge` never checking at all.

**Look again if:** the skill gathers commands that don't belong together.
