# 0026: setup.py --configure

**Built:** yes, except: the settings menu's Skills section.

**Decision:** `setup.py --configure` is how people and agents change a setting after the first
run: `devHome.folder`, `updates.installAutomatically`, `updates.checkEveryHours`,
`devHome.checkEveryHours`, the answer for each Claude Code folder and for Codex's homes, each
skill's answer and preferences, and the shared `multiMachine`. It's also where an agent answers
setup's questions about files. Changed on 2026-10-17, 2026-10-20, and 2026-10-23 (setup's
questions).

- At a console, it shows a menu: every setting with its current value, under "This PC" and
  "Shared by every copy of dev-home", in aligned columns, with headings and setup's colors, in
  ASCII like every script. A number changes one setting, `a` goes through all of them with the
  current answers as defaults, and Enter finishes. Each entry asks the question the first run
  asks, so the questions are one piece of code. The Claude folders entry asks about each folder,
  one answered no included, so a no can be taken back. Every run of setup at a console shows the
  same menu after its questions, `--configure` or not, where Enter goes on with setup's work
  ([0034: Runs of setup by hand](0034-runs-of-setup-by-hand.md)).
- An agent can't answer at a console, so it names one setting per run:
  `--configure '<name>=<value>'`, with a plain value, always in single quotes: `true` or `false`,
  a whole number of hours, a path, or `default` for a setting with a default. A folder takes
  `claudeCode.folders+=<folder>` to set it up, `-=` to stop, and `?=<folder>@<days>` to be asked
  again in that many days while it has no answer, and `codex.homes` the same. For a reminder,
  setup works out the date from the PC's clock, `--what-if` shows it before the yes, and a folder
  already answered is refused, with the `+=` and `-=` that change its answer. `--what-if` shows
  any change first. With neither a console nor a setting, it prints the current settings and how
  to change them.
- **Setup's questions about files go through it too,** for an agent: where rules setup set aside
  in `unanswered/` go, and whether to delete a hand edit to dev-home's `AGENTS.md` or `CLAUDE.md`
  that the Recycle Bin can't take
  ([0064: Each agent's rules file](0064-each-agents-rules-file.md),
  [0069: Dropped text](0069-dropped-text.md)). With neither a console nor a setting,
  `--configure` first prints a "Waiting for your answer" section, only while one waits: how the
  agent asks, then each question by its file's path in dev-home, with what the file holds, where
  it loads, its answers, and its command, `--configure '<path>=<answer>@<fingerprint>'`, the
  fingerprint being of the file as shown
  ([0038: Recommended settings from chat](0038-recommended-settings-from-chat.md)). It lists the
  same files the questions at a console ask about. The answers are the console's: for a waiting
  file, one of the four `mine/` levels or `drop`, with `delete` named once the bin can't take a
  drop, when setup changes nothing; for a hand edit, `delete`. The person's answer is the
  go-ahead, so the agent runs it with no `--what-if` round, and setup takes it only while the
  file still has that fingerprint. Each answer is a run of its own, and the work acts on it as on
  an answer at a console, so a failed commit takes it all back. A refused answer gets no usage
  text after it, since the listing says how to answer.
- In the list printed with neither a console nor a setting, which in practice an agent reads and
  sums up for the person, a setting nobody has answered shows as "not answered yet (defaults to
  ...)" with its default, such as "yes", and the copies setting as "not answered yet (until then,
  each sync checks GitHub)". Under "Skills added to your agents on this PC", a skill whose
  recorded state isn't what its answer alone gives, such as one that works only on another
  operating system, gets ", but on this PC it's ..." with that state, on the same line, before "To
  change it". The settings menu's Skills section is to show the same once it's built, in a layout
  shown to the developer first.
- A change to `local-settings.json` keeps a dated backup first, as setup's changes to Claude
  Code's and Codex's settings do. (A key nothing declares is removed, as
  [0049: Answers in the settings](0049-answers-in-the-settings.md) says.) A new `devHome.folder`
  never moves a folder. The backup goes beside the file, in dev-home-toolkit's root, and git
  ignores it, as it does the file.
- The `dev-home` skill pre-approves `setup.py --configure *`, as the skills pre-approve
  `sync.py *` for commits: the person's yes in chat to the exact preview is the approval.
- Before it sets dev-home's git config, setup checks that the folder looks like a dev-home: it
  has `dev-home.json`
  ([0070: Who owns each file in dev-home](0070-who-owns-each-file-in-dev-home.md)).
  With `--quiet`, it stops when that's missing, before saving or setting anything, and at a
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
- A reminder in days, not a date: the offer in the `NEW` line reads "remind me in N days", so the
  usual request is a number the agent passes on as it is, with no date to work out, and no extra
  turn to fix one it got wrong; it matches what a person types in a terminal; and one form is one
  thing to check and document. A request for a date makes the agent count days, and `--what-if`
  shows the date that gives before the yes. The developer's choice.
- The parenthesis for an unanswered setting reads better beside the rest of a line, and stays
  apart from "yes (the default)", an answer of default. A skill's real state on its own line
  keeps the agent and the person from changing an answer for nothing.
- A pre-approval with a wildcard, because the value changes with each call. Without one, a
  change would ask three times: the preview, the change, and the question in chat.
- The dev-home check, because setup turns commit signing off in that repo, and an agent can now
  change `devHome.folder`, so a mistake must not reach a project's repo.
- Setup's questions here: decisions 0036, 0038, and 0067 already send every question an agent
  answers to `/dev-home configure`, and one place keeps answers checked and acted on one way,
  through the code the console's answers use. The listing carries the agent's steps, read only
  while something waits, so the `dev-home` skill grows by one sentence. The listing is the
  preview, so a second yes would only ask twice, and the fingerprint makes the answer as exact as
  one at a console. A file's path names it as the `NEW` line does, so the agent can match the
  two. The developer's choice, 2026-10-23.
- The backup beside the file, because every other backup setup makes is beside its file, where
  the README teaches people to look. Git ignores it because it holds the PC's paths, and the
  repo is public.

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
- For a reminder: `@<date>` (the agent works out the date for the usual request, from its own idea
  of today); both forms, as uv's `exclude-newer` and Docker's `--since` take a duration or a
  timestamp (two forms for one thing, and more usage text that agents read on every
  `/dev-home configure`).
- For the agents' list: leaving it as it was (its heading says "added", while its lines showed
  answers); changing the heading instead (a heading already approved, and it still wouldn't say
  why a "yes" skill is missing); the state on a second, indented line (an agent summing up the
  list could split one skill's two lines apart).
- For setup's questions: a new `--answer` option (four more pre-approved command patterns and
  more skill text, for nothing an end user would notice); the agent moving the files itself
  (every safety rule becomes steps each agent must follow, and a deleted file skips the Recycle
  Bin); naming a question by a number (it shifts as questions are answered) or by its file's name
  alone (two agents' folders can give the same name); the fingerprint as an option of its own,
  such as `--seen` (one more option, and easy to leave off); and the agent's steps in the skill
  (read on every `/dev-home` command).

**Look again if:** the settings outgrow a menu, or people often ask for a reminder on a date
rather than in a number of days.
