# A run of setup by hand asks what's unanswered, then shows every setting

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
4. The changes to confirm: the change to `dev-home.json`, if any, and each settings file's diff,
   each shown and asked about.
5. The work, without stopping, holding the sync's lock: save this PC's answers, commit
   `dev-home.json` if it changed, then the Python link, the generated files, the skill links, and
   the rules. Then, with the lock let go, the settings files. Each is read again first; if it
   changed since its diff was shown, setup shows the new diff and asks again. `dev-home.json` is
   read again too, and left as it is, with a `PROBLEM`, if it changed since its change was shown.

A run with no console, such as a quiet one, asks nothing and shows no menu, and does the rest in
the same order, its work holding the lock too, unless a sync that runs it holds the lock already.

Setup also detects which tools a PC has, Claude Code when `~/.claude` exists and Codex when
`~/.codex` does, instead of always setting up `~/.claude`.

Every Claude Code folder setup finds is asked about, `~/.claude` included, in the shared prompt
for optional lists, each one recommended, so a first setup is still one Enter. Setup never sets up
a folder without an answer, the session's own included: it adds no links there and removes none,
so a folder linked before setup asked about it keeps working until a run by hand answers. A quiet
run names each folder nobody has answered for, on every run, since a missed work account is easy
to overlook. Every folder's `setUp` is written once it's answered.

Codex gets one question for every Codex home it finds, recommended: `~/.codex` once Codex has
made it, each `~/.codex-*` folder that holds a `config.toml` or an `auth.json`, the folder in
`CODEX_HOME`, and each listed by its path in `codex.homes`
([Codex is set up in every Codex home, or in none](codex-is-set-up-in-every-codex-home-or-in-none.md)).
Until it's answered, setup adds no links and removes none, as for a folder.

**Why:** running setup by hand is a normal way to use dev-home-tools, so it should offer every
setting, not only the unanswered ones. Questions first and the work after is what people expect
from a setup program, and keeps every question in one place as the lists grow. dev-home comes
first because later steps need it, and only the questions the clone needs come before it, so a
clone that can't work stops setup after one or two answers. Committing `dev-home.json` after the
questions, not between them, means nothing has been pushed until the work starts, so Ctrl+C
during the questions leaves everything as it was.

The diffs come after the menu, because the menu can change the folders and the dev-home they're
for. The work holds the sync's lock, so a sync in another session can't set up at the same moment
or save this PC's settings in between, and since every question comes first, no sync waits for a
person. The settings files come after the lock is let go: no sync writes them, and asking again
about one that changed would otherwise hold the lock while a question waits. A changed
`dev-home.json` isn't asked about again: it's committed while the lock is held, where a question
would hold up every sync, and only a sync bringing in another copy's change can change it, which
is rare.

Asking about every folder, the default one included, means dev-home-tools does nothing the person
may not want: an extra account is often kept apart on purpose, such as a work one; the
`~/.claude-*` match also catches folders that aren't accounts, such as a backup; and someone who
doesn't want their default account set up sees the choice. It's one rule for every folder, and
for both tools. A folder linked before setup asked about it gets no special case, `~/.codex`
included: only PCs set up before this change are in that state, and one run by hand answers.

This changes three other decisions: the menu from
[setup.py --configure changes every setting](setup-py-configure-changes-every-setting.md) becomes
part of every run by hand; the copies question from
[A dev-home has one active copy, or several](a-dev-home-has-one-active-copy-or-several.md) is
asked on every PC's first setup; and the save in
[Settings record answers, not just values](settings-record-answers-not-just-values.md), which
held the lock only while it saved, now runs inside the work's lock.

**Options set aside:**

- Asking at each step, as before: questions mixed into the status lines, easy to miss.
- Every question again on every run, with the current answers as defaults: a long run of Enters
  as the lists grow.
- Every question before the clone, checked afterward: the copies question would be asked blind on
  the usual way to add a PC, and personal skills can't be listed before the clone.
- Skipping the copies question when `dev-home.json` answers it: moving to a new PC and retiring
  the old one would leave it at several copies for good.
- The settings files' diffs before the menu: a change made in the menu could make them wrong.
- Holding the lock for the settings files too: asking again about a changed file would hold up
  every sync until the person answered.
- A sync setting up a folder it finds right away, then asking to confirm: it would link dev-home
  into a backup copy or a work account before the person says anything.
- An off switch on the default folders: hidden from the people who need it, and two rules.
- Leaving it to the tools' own switches for skills: the always-on rules would still load.
- A separate dev-home per account: a different need, and a much bigger change, since one dev-home
  per PC is filled into the generated files.
- Writing `setUp: true` for the default folders without asking: the file would claim choices
  nobody made, quiet runs would have to write it, and a tool uninstalled later would leave a stale
  entry.
- Treating a folder already linked as set up until it's answered: code kept for a state no new
  install reaches.

**Look again if:** a question comes to depend on work that setup does after the questions.
