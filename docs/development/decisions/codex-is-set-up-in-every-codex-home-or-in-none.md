# Codex is set up in every Codex home, or in none

**Decision:** every Codex home on a PC has the same answer, since every home reads the same
skills. Codex homes are saved exactly as Claude Code folders are, an entry for each home in
`codex.homes` with its own `setUp`, and only setup's code keeps the answers the same:

```json
"claudeCode": { "folders": { "~/.claude": { "setUp": true } } },
"codex": { "homes": { "~/.codex": { "setUp": true }, "~/.codex-work": { "setUp": true } } }
```

- One question covers every home, recommended, and its answer goes into every home's entry. A
  yes sets up each home: the always-on rules in its `AGENTS.md`, dev-home in its `config.toml`,
  and dev-home's skills, linked into `~/.agents/skills`. A no sets up none. (Later changed by
  [Setup removes what it set up in a folder answered no](setup-removes-what-it-set-up-in-a-folder-answered-no.md):
  a no also removes the rules file setup wrote in each home and its links in `~/.agents/skills`,
  and takes dev-home back out of each home's `writable_roots`.) Until it's answered, setup adds no
  links and removes none, and a quiet run names the homes.
- The main home is `~/.codex` when it's there; otherwise the first other `~/.codex-<name>` there,
  by folder name; otherwise the first home elsewhere, by full path. Its answer is every home's.
  When it has none, the next home there, in that order, that has one gives it. With none, Codex
  is unanswered.
- Setup keeps `codex.homes` in that order on every save. A file out of order, which only a hand
  edit leaves, is put back in order by the next run, with no backup and no line, once setup has
  checked that only the order changes; otherwise it saves nothing and reports a `PROBLEM`.
- Every run, quiet ones included, gives each home that's there the main home's answer when its
  own differs or it has none: a new home, or one whose answer was changed by hand, the main
  home's included. It keeps no backup, since nobody changed a setting, and prints one line in
  place of the save's own, such as
  `SET       dev-home is now turned off for Codex in ~/.codex-work and D:/codex-test, to match ~/.codex. Codex only supports one set of skills for all your Codex homes, so they share one setting.`
- `--configure` and the menu: a change to the main home's answer changes every home, those that
  are gone included. A change that would leave the homes with different answers is refused, with
  a message that all of them share one answer, naming the main home. Adding a home with the
  shared answer is allowed. While no home has an answer, a change to any home answers for all of
  them.
- A home that's gone keeps its answer, so it applies if the home comes back, and a home missing
  for a while, such as on an unplugged drive, isn't asked about again. The menu offers to remove
  it, as it does a Claude Code folder.
- Answers saved for each home before this decision are read as they are: nothing is deleted or
  converted, and mixed answers follow the main home.

**Why:**

- Codex has no skills of a home's own: every home reads `~/.agents/skills` (Codex's source at
  rust-v0.161.0), and Codex calls the folder of a home's own, `$CODEX_HOME/skills`, deprecated.
  So an answer for each home could only imitate one. Built in `7928593` and `769bbfc`, a home
  answered no got dev-home's skills hidden with `[[skills.config]]` entries in its `config.toml`,
  with a record of the entries, so a skill turned back on through Codex's `/skills` menu stayed
  on; and with every home answered no, the shared links stayed, listed in every home.
- The rules and the settings are per home in Codex, but setting those up per home while the
  skills are shared would leave a home answered no listing skills that work without the rules or
  write access to dev-home.
- Both tools are saved the same way, as far as possible, in a shape that won't need redesigning
  (the developer, 2026-10-15): if Codex ever reads skills per home, only setup's code changes,
  never the settings file.
- A sync makes the homes match, rather than naming a mismatch on every sync, because the answer
  that counts is already known: the main home's.

**Costs, accepted:**

- With two Codex accounts, such as a work one, dev-home can't be kept out of just one: a yes puts
  the always-on rules, the person's global rules included, write access to dev-home, and the
  skills in every home.
- A folder that only looks like a home, such as a backup copy with a `config.toml`, is set up
  too.

**Options set aside:**

- An answer for each home, with dev-home's skills hidden in each home answered no: see Why. It
  was built in `7928593` and `769bbfc`, and taken out by this decision.
- One answer, `codex.setUp`, with `codex.homes` listing only the homes setup can't find by itself
  (built in `642a5c5`): the answer would later live in two places, the file wouldn't show every
  home, and `-=` would mean something different than for Claude Code.
- Every home listed under a top-level `codex.setUp`: still two places.
- An answer for each home for the rules and the settings, with the skills shared: a home
  answered no would list skills with neither the rules nor write access to dev-home.
- Asking again about a home found later: the skills reach it anyway, through
  `~/.agents/skills`, so a question could only hold back the rules and the write access they
  need.

**Look again if:** Codex gets a folder of skills for each home that isn't deprecated: each home
can then keep an answer of its own, with only setup's code changed.
