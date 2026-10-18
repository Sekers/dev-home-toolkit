# setup.py --configure changes every setting

**Decision:** `setup.py --configure` is how people and agents change a setting after the first
run: `devHome.folder`, `updates.installAutomatically`, `updates.checkEveryHours`,
`devHome.checkEveryHours`, the answer for each `~/.claude-*` folder, and the shared
`multiMachine`.

- At a console, it shows a menu: every setting with its current value, under "This PC" and
  "Shared by every copy of dev-home", in aligned columns, with headings and setup's colors, in
  ASCII like every script. A number changes one setting, `a` goes through all of them with the
  current answers as defaults, and Enter finishes. Each entry asks the question the first run
  asks, so the questions are one piece of code. The Claude folders entry asks about each folder,
  one answered no included, so a no can be taken back. (Later changed by
  [A run of setup by hand asks what's unanswered, then shows every setting](a-run-of-setup-by-hand-asks-whats-unanswered-then-shows-every-setting.md):
  every run at a console shows the menu after its questions, `--configure` or not, and Enter goes
  on with setup's work.)
- An agent can't answer at a console, so it names one setting per run:
  `--configure '<name>=<value>'`, with a plain value, always in single quotes: `true` or `false`,
  a whole number of hours, a path, or `claudeCode.folders+=<folder>` to set up a folder and
  `claudeCode.folders-=<folder>` to stop. `--what-if` shows the change first. With neither a
  console nor a setting, it prints the current settings and how to change them.
- A change to `local-settings.json` keeps a dated backup first, as setup's changes to Claude
  Code's and Codex's settings do. (It kept any key it didn't know until
  [Settings record answers, not just values](settings-record-answers-not-just-values.md) had one
  nothing declares removed.) A new `devHome.folder` never
  moves a folder. The backup goes beside the file, in dev-home-toolkit's root, and git ignores it,
  as it does the file.
- The `dev-home` skill pre-approves `setup.py --configure *`, as the skills pre-approve
  `sync.py *` for commits: the person's yes in chat to the exact preview is the approval.
- Before it sets dev-home's git config, setup checks that the folder looks like a dev-home: it
  has the files the starter makes, `global-rules/global-rules.md` and `knowledge/README.md`.
  With `--quiet`, it stops when they're missing, before saving or setting anything, and at a
  console it asks for the folder again, where Enter stops. A clone gets the same check before
  setup sets its git config.

**Why:**

- One way to change a setting, so it's checked and written the same way whoever changes it.
- A menu, because a person runs `--configure` to change one thing: it shows every value, and
  changes only what they pick. A question for each setting suits the first run, which needs
  every answer, and `a` keeps that for a full review.
- Plain values, because they reached the script unchanged in every shell tried (2026-10-06:
  PowerShell 7.6.6, Windows PowerShell 5.1, and Git Bash 5.3.9), while Windows PowerShell 5.1
  dropped JSON's inner double quotes, so `["~/.claude-other"]` arrived as `[~/.claude-other]`.
  Single quotes also stop Git Bash from turning a `~` after `=` into a full path. Adding or
  removing one folder means an agent never repeats the whole list.
- A pre-approval with a wildcard, because the value changes with each call. Without one, a
  change would ask three times: the preview, the change, and the question in chat.
- The dev-home check, because setup turns commit signing off in that repo, and an agent can now
  change `devHome.folder`, so a mistake must not reach a project's repo.
- The backup beside the file, because every other backup setup makes is beside its file, where
  the README teaches people to look. Git ignores it because it holds the PC's paths, and the
  repo is public.

**Changed on 2026-10-17,** with skills per PC. In the list printed with neither a console nor a
setting, which in practice an agent reads and sums up for the person:

- A setting nobody has answered shows as "not answered yet (defaults to yes)", or "no", where it
  said "not answered yet, so yes", and the copies setting as "not answered yet (until then, each
  sync checks GitHub)". The parenthesis reads better beside the rest of a line, and stays apart
  from "yes (the default)", an answer of default.
- Under "Skills added to your agents on this PC", a skill whose recorded state isn't what its
  answer alone gives, such as one that works only on another operating system, gets ", but on
  this PC it's ..." with that state, on the same line, before "To change it", so neither the
  agent nor the person changes an answer for nothing. The settings menu's Skills section, in step
  8 of setup's new order, is to show the same, in a layout shown to the developer first.
- Set aside: leaving the list as it was (its heading says "added", while its lines showed
  answers); changing the heading instead (a heading already approved, and it still wouldn't say
  why a "yes" skill is missing); the state on a second, indented line (an agent summing up the
  list could split one skill's two lines apart).

**Options set aside:**

- At a console, every question again with the current answers as defaults: six or more
  questions to change one setting, and a habitual "y" can change the wrong one.
- The backups in a folder of their own under `internal/`: a tidier root, but more code, a
  backup that isn't beside its file, unlike every other, and a `.gitignore` line still needed
  for the new copy a save swaps in, which has to sit beside the file.
- No backup of `local-settings.json`: the change is shown and waits for a yes, and every value
  can be set again, but a wrong `devHome.folder` would leave no file to copy back.
- JSON values (see above); one switch per setting, such as `--content-dir` (the list grows with
  every setting, and a person has to know each one exists); and editing the file by hand only
  (a JSON typo stops setup).
- No pre-approval.

**Look again if:** an agent's tool can answer setup's questions, or the settings outgrow a menu.
