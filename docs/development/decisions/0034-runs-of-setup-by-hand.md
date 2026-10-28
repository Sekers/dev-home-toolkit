# 0034: Runs of setup by hand

**Built:** yes, except: the questions about skills, in steps 2 and 3.

**Decision:** every run of `setup.py` at a console goes in this order:

1. dev-home first: its folder, then, when it's missing, clone or create it, with the repo's name,
   after checking that `gh` is there and signed in. If that fails, setup stops and saves nothing.
2. The questions not answered yet: extra Claude folders and Codex, automatic updates, the
   copies question, skills, and recommended settings. The copies question is always asked on a
   PC's first setup, with `dev-home.json`'s answer as the default, since adding a PC is when that
   answer most often changes, except for a dev-home setup has just created, which nothing else
   can be using yet. Wherever a saved answer exists, a question shows it as the default.
3. The settings list that `--configure` shows, with skills and recommended settings added, so any
   setting can be changed: a number for one, `a` for all, and Enter to go on. A dev-home folder
   changed here goes back through step 1, and the new dev-home's copies question.
4. The change to confirm: the change to `dev-home.json`, if any, shown and asked about. The
   settings files' changes aren't asked about, since the folder's yes approved them
   ([0053: What a folder's yes approves](0053-what-a-folders-yes-approves.md)). Then each hand
   edit to dev-home's `AGENTS.md` or `CLAUDE.md` that the Recycle Bin can't take, shown, with
   whether to delete it for good ([0069: Dropped text](0069-dropped-text.md)).
5. The work, without stopping, holding the sync's lock: save this PC's answers, commit
   `dev-home.json` if it changed, then dev-home's `AGENTS.md` and `CLAUDE.md`, the Python link,
   the generated files, the skill links, the rules, and the settings files, then each yes to a
   recommended setting, which is saved only once its change is written
   ([0032: Recommended settings](0032-recommended-settings.md)). A settings file that changed
   since the work planned its change is left alone until the next run. `dev-home.json` is read
   again too, and left as it is, with a `PROBLEM`, if it changed since its change was shown.

A run with no console, such as a quiet one, asks nothing and shows no menu, and does the rest in
the same order, its work holding the lock too, unless a sync that runs it holds the lock already.

Setup also detects which agents a PC has, Claude Code when `~/.claude` exists and Codex when
`~/.codex` does, instead of always setting up `~/.claude`.

Every Claude Code folder setup finds is asked about, `~/.claude` included, in the shared prompt
for optional lists, each one recommended, so a first setup is still one Enter. Setup never sets up
a folder without an answer, the session's own included: it adds no links there and removes none,
so a folder linked before setup asked about it keeps working until a run by hand answers. A quiet
run names each folder nobody has answered for in a `NEW` line, on every run, since a missed work
account is easy to overlook ([0036: New items](0036-new-items.md)). A folder can hold a reminder,
which setup doesn't ask about until its date. Every folder's `setUp` is written once it's
answered.

Codex gets one question for every Codex home it finds, recommended: `~/.codex` once Codex has
made it, each `~/.codex-*` folder that holds a `config.toml` or an `auth.json`, the folder in
`CODEX_HOME`, and each other home with an entry in `codex.homes`
([0052: Codex homes](0052-codex-homes.md)).
Until it's answered, setup adds no links and removes none, as for a folder.

Changed on 2026-10-15, 2026-10-16, 2026-10-20, 2026-10-23, and 2026-10-24 (when a yes to a
recommended setting is saved).

**Why:** running setup by hand is a normal way to use dev-home-toolkit, so it should offer every
setting, not only the unanswered ones. Questions first and the work after is what people expect
from a setup program, and keeps every question in one place as the lists grow. dev-home comes
first because later steps need it, and only the questions the clone needs come before it, so a
clone that can't work stops setup after one or two answers. Committing `dev-home.json` after the
questions, not between them, means nothing has been pushed until the work starts, so Ctrl+C
during the questions leaves everything as it was.

The changes come after the menu, because the menu can change the folders and the dev-home they're
for. The work holds the sync's lock, so a sync in another session can't set up at the same moment
or save this PC's settings in between, and since every question comes first, no sync waits for a
person. The settings files are written while the lock is held, since a sync writes them too, and
nothing asks about them, since the folder's yes approved them. A changed `dev-home.json` isn't
asked about again: it's committed while the lock is held, where a question would hold up every
sync, and only a sync bringing in another copy's change can change it, which is rare.

Asking about every folder, the default one included, means dev-home-toolkit does nothing the person
may not want: an extra account is often kept apart on purpose, such as a work one; the
`~/.claude-*` match also catches folders that aren't accounts, such as a backup; and someone who
doesn't want their default account set up sees the choice. It's one rule for every folder, and
for both agents. A folder linked before setup asked about it gets no special case, `~/.codex`
included: only PCs set up before this change are in that state, and one run by hand answers.

**Options set aside:**

- Asking at each step, as before: questions mixed into the status lines, easy to miss.
- Every question again on every run, with the current answers as defaults: a long run of Enters
  as the lists grow.
- Every question before the clone, checked afterward: the copies question would be asked blind on
  the usual way to add a PC, and personal skills can't be listed before the clone.
- Skipping the copies question when `dev-home.json` answers it: moving to a new PC and retiring
  the old one would leave it at several copies for good.
- The settings files' diffs before the menu: a change made in the menu could make them wrong.
- Writing the settings files after the lock is let go, asking again about one that changed, as
  until 2026-10-15: a sync writes them too, and since the folder's yes approves them, there's no
  question to hold the lock for.
- A sync setting up a folder it finds right away, then asking to confirm: it would link dev-home
  into a backup copy or a work account before the person says anything.
- An off switch on the default folders: hidden from the people who need it, and two rules.
- Leaving it to the agents' own switches for skills: the always-on rules would still load.
- A separate dev-home per account: a different need, and a much bigger change, since one dev-home
  per PC is filled into the generated files.
- Writing `setUp: true` for the default folders without asking: the file would claim choices
  nobody made, quiet runs would have to write it, and an agent uninstalled later would leave a
  stale entry.
- Treating a folder already linked as set up until it's answered: code kept for a state no new
  install reaches.

**Look again if:** a question comes to depend on work that setup does after the questions.
