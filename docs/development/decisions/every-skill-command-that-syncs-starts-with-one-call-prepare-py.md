# Every skill command that syncs starts with one call: prepare.py

**Decision:** `templates/shared-skill-scripts/prepare.py` runs the sync inside its own process
(the code of `sync.py`, from `internal/shared/`), then loads `facts.py` into the same process,
checks the skill's stamp, and prints the facts for the topics a skill names. It's the first
command of every skill command that syncs. Skills still commit through `sync.py --message`.

**The problem:** each command an agent runs costs a turn of the model, and turns cost more time
than the scripts do. A plain `/handoff` took five: `facts.ps1`, `sync.ps1`, reading the handoff,
a `git log` that agents added on their own to see what changed since the handoff's last check,
and the summary. Now it takes three.

**Why one script:** it's one literal command, with one pre-approval, that an agent can't split,
reorder, or send as two calls at once, and it works the same in every tool and on every
platform. The order matters: setup, which the sync runs, rewrites the generated `facts.py` when
its template has changed, so the facts come from the new copy, never from one being written. It
always exits 0, because a failing exit code makes a tool report the whole call as failed, and an
agent could then stop instead of following the skill's steps for each line.

**Why shared:** every skill command that syncs starts the same way, so this is the one place for
what would otherwise be copied into each skill, such as handling a tool that can't sync.

**Options set aside:**

- Each skill joining `sync.ps1; facts.ps1` in one line: it rests on each tool approving joined
  commands, and gives other skills nothing to build on.
- A switch on the sync that also prints the facts: `sync.py` is for people too, while this is
  only for agents.
- Printing the handoff from the script as well, to save reading it: a long handoff passes the
  30,000 characters Claude Code shows of a command's output, and editing a file needs a real read
  of it anyway.

**Look again if:** a skill needs something at its start that one call can't give it.
