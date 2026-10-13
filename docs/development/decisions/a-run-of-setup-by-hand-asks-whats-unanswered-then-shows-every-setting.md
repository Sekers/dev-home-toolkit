# A run of setup by hand asks what's unanswered, then shows every setting

**Decision:** every run of `setup.py` at a console goes in this order:

1. dev-home first: its folder, then, when it's missing, clone or create it, with the repo's name,
   after checking that `gh` is there and signed in. If that fails, setup stops and saves nothing.
2. The questions not answered yet: extra Claude folders and Codex homes, automatic updates, the
   copies question, skills, recommended settings, and each settings file's diff. The copies
   question is always asked on a PC's first setup, with `dev-home.json`'s answer as the default,
   since adding a PC is when that answer most often changes. Wherever a saved answer exists, a
   question shows it as the default.
3. The settings list that `--configure` shows, with skills and recommended settings added, so any
   setting can be changed: a number for one, `a` for all, and Enter to go on.
4. The work, without stopping: save this PC's answers, commit `dev-home.json` if it changed, then
   the Python link, the generated files, the skill links, the rules, and the settings files. Each
   settings file is read again first; if it changed since its diff was shown, setup shows the new
   diff and asks again.

Setup also detects which tools a PC has, Claude Code when `~/.claude` exists and Codex when
`~/.codex` does, instead of always setting up `~/.claude`.

**Why:** running setup by hand is a normal way to use dev-home-tools, so it should offer every
setting, not only the unanswered ones. Questions first and the work after is what people expect
from a setup program, and keeps every question in one place as the lists grow. dev-home comes
first because later steps need it, and only the questions the clone needs come before it, so a
clone that can't work stops setup after one or two answers. Committing `dev-home.json` after the
questions, not between them, means nothing has been pushed until the work starts, so Ctrl+C
during the questions leaves everything as it was.

This changes two other decisions: the menu from
[setup.py --configure changes every setting](setup-py-configure-changes-every-setting.md) becomes
part of every run by hand, and the copies question from
[A dev-home has one active copy, or several](a-dev-home-has-one-active-copy-or-several.md) is
asked on every PC's first setup.

**Options set aside:**

- Asking at each step, as before: questions mixed into the status lines, easy to miss.
- Every question again on every run, with the current answers as defaults: a long run of Enters
  as the lists grow.
- Every question before the clone, checked afterward: the copies question would be asked blind on
  the usual way to add a PC, and personal skills can't be listed before the clone.
- Skipping the copies question when `dev-home.json` answers it: moving to a new PC and retiring
  the old one would leave it at several copies for good.

**Look again if:** a question comes to depend on work that setup does after the questions.
