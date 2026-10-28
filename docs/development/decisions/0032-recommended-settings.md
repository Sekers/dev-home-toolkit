# 0032: Recommended settings

**Built:** yes.

**Decision:** setup offers settings that dev-home-toolkit recommends for the agents, from a list in
`templates/recommended-settings/recommended-settings.json`. Each entry has an id that is never
reused, what it does, why it's recommended, and the setting for each agent that has one, with any
older form of it that the recommended value replaces. The first three are for Claude Code:
`"attribution": false` (id `attribution-off`), which leaves commits and pull requests without a
line naming the agent; `"feedbackSurveyRate": 0` (id `feedback-survey-off`), which stops the
session quality survey and its request to upload the session's transcript; and
`"remoteControlAtStartup": true` (id `remote-control-at-startup`), which connects Remote Control
when each interactive session starts, so the session can be picked up from claude.ai/code or the
Claude app.

- Setup offers one for each Claude folder set up whose `settings.json` doesn't already have the
  recommended value: the setting is missing, or set to something else. It offers none in a
  folder whose `settings.json` it won't rewrite, such as one with comments, since a yes couldn't
  be written there.
- Each offer asks in plain words, with no diff, in columns: the setting, by its key in
  `settings.json`; its value now, with what that value means; and the recommended value, with
  what it does and why. Each text that says what a value means starts with whether the feature is
  on or off, and the list has one for a missing setting, one for an older form, and one for any
  other value someone chose (`whenOther`). For `attribution-off`: when it's missing, attribution
  is on, so commits get a co-author line, pull requests get "Generated with Claude Code", and
  cloud and Remote Control sessions add a link to the session; the older form with empty
  `commit` and `pr` is partly off, hiding the first two but not the link; and text the person
  wrote shows as its value, which a yes replaces, so someone keeping it can answer no.
- The `remote-control-at-startup` offer is the same in every folder, since setup can't see the
  plan or the organization's switch it depends on. Its words say what it needs: a claude.ai
  sign-in on a Pro, Max, Team, or Enterprise plan, where on Team and Enterprise an Owner must
  turn Remote Control on first; and that where it can't connect, each session shows a notice, and
  `/config` switches it off. Claude Code uses a value that older versions left in `.claude.json`
  (`~/.claude.json` for `~/.claude`, and the `.claude.json` inside any other folder) only where
  no settings file sets one. So where `settings.json` has none, setup takes that value as the
  folder's, one the person chose like any other; a yes writes `settings.json` alone, which then
  wins. A value in both files isn't a setting written more than once.
- What Enter picks depends on what the folder's settings have now. Where the setting is missing,
  or in an older form, the offer is recommended for that folder, and Enter changes it to the
  recommended value, whatever its type, and whatever Claude Code does without it. Where it has
  any other value, which the person chose, such as `"remoteControlAtStartup": false` from
  `/config` or attribution text they wrote, the offer isn't recommended for that folder: Enter
  answers no, which is saved like any no, and the value stays as it is. The answers are the same
  either way ([0040: Answers to offers](0040-answers-to-offers.md)), and in the list of
  recommended settings, "All recommended" follows each item's default.
- A recommended setting written more than once in a folder set up: Claude Code silently uses
  only the last copy (Claude Code 2.1.296, tested 2026-10-10), so on every run, quiet ones
  included, setup keeps that copy alone, without asking, since nothing Claude Code does changes.
  It writes the file with a backup and a `SET` line naming the setting it kept the last copy of,
  and the offer then judges the one value left, as for any setting. When setup changes a file in
  which some other key is written more than once, it keeps the last copy of that key too, and
  its `SET` line says so.
- Answers are saved per PC and per Claude folder, in that folder's entry in
  `local-settings.json`, under `recommendedSettings`, such as
  `"~/.claude": {"setUp": true, "recommendedSettings": {"attribution-off": true}}` in
  `claudeCode.folders`. A no is never asked again, and neither is a yes: a later change to the
  setting, such as through `/config`, is the person's own, which setup never changes back or
  asks about. Where the file's value differs from a saved yes, the settings menu and the
  `/dev-home configure` list show the real value beside it, and choosing yes there again writes
  the setting again. An answer is saved only once its change is written, so a run that stops
  partway records nothing.
- The work plans the change on the file as it is by then, and writes a setting only if it still
  has the value the offer described. Otherwise it leaves that setting out, saves no answer for
  it, and says so, and the offer comes back as the setting is now. It writes every accepted
  setting together with the lines the folder needs, which take no yes of their own, since the
  folder's yes approved them
  ([0053: What a folder's yes approves](0053-what-a-folders-yes-approves.md)): one write, with
  one backup of the file, and a `SET` line naming the file and each setting. It judges the value
  on the same read of the file that the write plans on. A setting it leaves out, or can't write,
  gets a `NEW` line, and any answer the yes replaced goes too, so its offer really waits again.
  When the work can't read this PC's settings again, it writes no yes, since its answer couldn't
  be saved.
  `setup.py --what-if` still shows the diff, for anyone who wants the exact change.
- A sync names the folders whose recommended settings wait for an answer in one `NEW` line, with
  how many in each ([0036: New items](0036-new-items.md)). To find out, it reads a folder's
  `settings.json`, and `.claude.json` where that counts, only while one there has no yes or no,
  and no reminder before its date: about 1 ms a folder on the developer's PC (2026-10-28), and
  nothing once every one there is answered.
- The settings menu has one row for them, counting each folder's answers, which goes through
  each setting in each folder set up, in the offer's columns, with the answer. A yes whose value
  changed since is asked whether to set it again, with Enter keeping it as it is.

Changed on 2026-10-15, by the developer on 2026-10-19 (Remote Control at startup), by the
developer on 2026-10-24 (plain words in place of a diff, what Enter picks, the Remote Control
offer's words, keeping only the last copy of a setting written more than once, and no question
about a change made after a yes), and by the developer on 2026-10-28 (each value shown, with what
it means, in columns; the menu's one row).

**Why:** these settings suit most people, but each changes the person's own file, so each needs
their yes on each PC. Codex has neither of the first two: its commit and pull request attribution
is a setting of the ChatGPT workspace, which Codex asks OpenAI for, and it has no session survey
(checked in Codex's source at rust-v0.161.0, 2026-10-07). `"attribution": false` needs Claude
Code 2.1.281 or later, which decision 0014, "Supported versions of Claude Code and Codex", allows.
Answers are per folder because a work account can need different settings, and a saved yes never
causes a later write by itself, so setup never undoes an edit the person made. Nor does it ask
about one: Claude Code's own settings are where people manage these, and a missing value can be a
choice too, since `/config`'s "default" for Remote Control deletes the key. The menu shows the
real value instead, as the Skills section shows a skill's real state where it differs from its
answer. A value already there gets an offer too, because it isn't always a choice: an older form
can hide less than the person meant. A recommended setting written twice is tidied without a
question because keeping the last copy changes nothing Claude Code does, and leaving both would
keep a value in the file that does nothing; it's only that setting, since other keys may repeat
on purpose.

Remote Control at startup was added by the developer on 2026-10-19. Only user and managed
settings can turn it on, since Claude Code ignores a `true` in a project's settings; that and
what it needs are from Claude Code's Remote Control page and settings reference (read 2026-10-19
and 2026-10-24). The page says a session that can't connect still starts, with a notice, for
`--remote-control`; the setting is expected to do the same, not tested. That a value in
`.claude.json` counts only where no settings file sets one is from Claude Code 2.1.309's own code
(read 2026-10-24, not run).

The offers ask in plain words because each is an on-off choice whose effect words can say
exactly, as Claude Code's own `/config` changes such settings with no diff. A diff would turn a
first setup's one Enter ([0033: Prompts for optional lists](0033-prompts-for-optional-lists.md))
into reading JSON, and cost tokens in chat. The backup, the `SET` line, and `--what-if` show the
exact change to anyone who wants it. Enter changes what's missing or broken, and keeps a value
the person chose, so a hurried Enter never undoes a choice, while each offer still comes up once.

The values go in a column of their own, each with what it means, because a sentence describing
what a setting does didn't say whether it was on or off now (the developer, 2026-10-28). The menu
gets one row, like the row for Claude Code folders, rather than a submenu ahead of the Skills
submenu (the developer's choice, 2026-10-28).

**Options set aside:**

- Answers shared in `dev-home.json`: every PC still needs its own yes to change its files, so
  sharing saves only a question, and adds a second record that can disagree with what a PC's
  answer was. Recommendations tied to what a PC has installed don't fit a shared answer at all.
- One answer for every Claude folder on a PC: a folder set up later would be changed without
  being asked.
- Offering only where the setting is missing, and treating any value already there as the
  person's choice: it left an older form that hides less than the person meant as it was.
- The three-key form of `attribution` (`commit`, `pr`, and `sessionUrl`), which only older
  versions of Claude Code need.
- Turning off telemetry: in Claude Code it also stops feature flags, which can make Remote
  Control unavailable, so it's not a safe default for everyone.
- Turning off Claude Code's built-in git instructions (`"includeGitInstructions": false`): the
  one line in them that's a matter of choice, "If on the default branch, branch first", is for
  each repo to settle in its own instruction files, and `attribution-off` already covers the
  attribution lines. Turning them off would also drop the git status snapshot at the start of a
  session, and on a PC without the PowerShell tool, perhaps every built-in git safety line (not
  tested; seen with Claude Code 2.1.296 on 2026-10-10).
- A diff of the file for each offer, with a typed yes (the plan until 2026-10-24): JSON to read
  for an on-off choice, tokens in chat, a typed yes that clashed with Enter taking every
  recommended item in 0033, and the question of how the diff shares a file with the lines the
  folder needs.
- Enter changing every setting to the recommended value: a hurried Enter would undo a choice the
  person made, such as Remote Control switched off in `/config`, or delete attribution text they
  wrote.
- No offer where the person chose another value: they'd never learn it's recommended, and each
  setting would need an exception of its own.
- Leaving Remote Control off where setup sees it can't work, such as with an API key, a cloud
  provider, or a variable that turns off feature flags: it misses the most likely case, a work
  account whose organization hasn't turned it on, which setup can't see; it can be wrong when
  sessions start with other variables than setup's; and it needs a list of Claude Code's
  variables kept current.
- Enter leaving Remote Control off everywhere: most people it would help, on Pro and Max plans,
  would pass it by.
- For a recommended setting written more than once:
  - Enter changing it to the recommended value, as until 2026-10-24: where the last copy is a
    value the person chose, it would switch on what Claude Code has off, and the default would
    depend on whether a sync had already rewritten the file.
  - Judging it by its last copy, and leaving the copies after a no: two copies would stay in the
    file.
  - Tidying it only as part of its offer: skip, a reminder, or no run by hand would leave the
    copies, and a no would still edit the file.
  - Tidying every key written more than once: it would touch keys dev-home-toolkit has no
    business with, such as a `"//"` key some people repeat to hold notes.
  - A `PROBLEM` line asking for it to be fixed by hand: hand work, repeated on every sync, for
    what setup can do safely.
- For a setting changed after a yes:
  - Asking again, as until 2026-10-24: a `NEW` line every session for a switch the person just
    made, and a hurried Enter could undo `/config`'s "default" for Remote Control.
  - Asking again only when the setting went missing: `/config`'s "default" deletes the key on
    purpose, so that choice would come back as a question.
- For how an offer reads (2026-10-28): a sentence of what the agent does now, with the
  recommended value in a sentence of its own ("A yes sets attribution to false"), which never
  said whether the setting was on or off; and two paragraphs starting "Now:" and "Recommended:",
  each a sentence with the value in it, which the developer passed over for values in a column.
- For the settings menu (2026-10-28): a submenu with a numbered row for each folder and setting,
  which would build a submenu ahead of the design of the menu's Skills section
  ([0026: setup.py --configure](0026-setup-py-configure.md)).

**Look again if:** Codex gains a local setting for attribution or a survey, Claude Code's
settings start syncing between machines, or Claude Code lets a program see whether Remote Control
can work for an account.
