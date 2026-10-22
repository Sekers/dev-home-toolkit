# 0032: Recommended settings

**Built:** not yet.

**Decision:** setup offers settings that dev-home-toolkit recommends for the agents, from a list in
`templates/recommended-settings/recommended-settings.json`. Each entry has an id that is never
reused, what it does, why it's recommended, and the setting for each agent that has one. The first
two are for Claude Code: `"attribution": false` (id `attribution-off`), which leaves commits and
pull requests without a line naming the agent, and `"feedbackSurveyRate": 0` (id
`feedback-survey-off`), which stops the session quality survey and its request to upload the
session's transcript.

- Setup offers one for each Claude folder whose `settings.json` doesn't already have the
  recommended value: the setting is missing, set to something else, or written more than once.
- Each offer says what the value there now does and what the recommended value would change,
  fitted to what's there. For `attribution-off`: when it's missing, commits get a co-author line,
  pull requests get "Generated with Claude Code", and cloud and Remote Control sessions add a
  link to the session; the older form with empty `commit` and `pr` hides the first two but not
  the link; and text the person wrote would be removed, which the offer says, so someone keeping
  it can answer no.
- A setting written more than once: Claude Code silently uses only the last copy (Claude Code
  2.1.296, tested 2026-10-10). The offer shows every copy, and accepting leaves one, with the
  recommended value. When setup changes a file in which some other key is written more than
  once, its diff keeps the last copy of that key, the one Claude Code uses, and says so.
- Answers are saved per PC and per Claude folder, in that folder's entry in
  `local-settings.json`, under `recommendedSettings`, such as
  `"~/.claude": {"setUp": true, "recommendedSettings": {"attribution-off": true}}` in
  `claudeCode.folders`. A no is never asked
  again. If the value changes after a yes, setup asks again rather than changing it back. An
  answer is saved only once its change is written, so a run that stops partway records nothing.
- A settings file gets one backup for everything setup changes in it. The lines a folder needs
  take no yes of their own, since the folder's yes approved them
  ([0053: What a folder's yes approves](0053-what-a-folders-yes-approves.md)); how a
  recommendation's diff shares a file with them is settled when recommended settings are built.

Changed on 2026-10-15.

**Why:** these settings suit most people, but each changes the person's own file, so each needs
their yes on each PC. Codex has neither: its commit and pull request attribution is a setting of
the ChatGPT workspace, which Codex asks OpenAI for, and it has no session survey (checked in
Codex's source at rust-v0.161.0, 2026-10-07). `"attribution": false` needs Claude Code 2.1.281
or later, which decision 0014, "Supported versions of Claude Code and Codex", allows. Answers are
per folder because a work account can need different settings, and a saved yes never causes a later
write by itself, so setup never undoes an edit the person made. A value already there gets an
offer too, because it isn't always a choice: an older form can hide less than the person meant,
and a setting written twice keeps only its last copy, without a word.

**Options set aside:**

- Answers shared in `dev-home.json`: every PC still needs its own yes to change its files, so
  sharing saves only a question, and adds a second record that can disagree with what a PC's
  answer was. Recommendations tied to what a PC has installed don't fit a shared answer at all.
- One answer for every Claude folder on a PC: a folder set up later would be changed without
  being asked.
- Offering only where the setting is missing, and treating any value already there as the
  person's choice: it left an older form that hides less than the person meant, and a setting
  written more than once, as they were.
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

**Look again if:** Codex gains a local setting for attribution or a survey, or Claude Code's
settings start syncing between machines.
