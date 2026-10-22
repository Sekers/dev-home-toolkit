# 0022: Active copies

**Built:** yes.

**Decision:** dev-home has two uses, and both are fully supported. With one active copy, it's
private storage with a backup and full history on GitHub: nothing else writes to it, so the local
copy is always the latest. With several, it's the same, plus sharing between the copies, so a
copy can fall behind. A copy is any clone in active use on its own: a PC, a virtual machine, a
container, a remote server, or a cloud environment. Two sessions sharing one clone are one copy,
and a replacement PC whose old copy is retired still makes one. `dev-home.json`, in dev-home's
root, says which, as `{ "multiMachine": false }` or `true`, and the commands act on it:

| Command | One active copy | Several active copies |
| --- | --- | --- |
| `/handoff`, `/handoff <question>` | The local copy. GitHub only to push commits still waiting, and to check once `devHome.checkEveryHours` has passed | Fetch first, every time |
| `/handoff update`, `next`, `issue`, `audit` | Edit, commit, push | Fetch first, edit, commit, push |
| `/knowledge <question>` | The local copy | The local copy |
| Plain `/knowledge` | The local copy. GitHub only to push commits still waiting, and to check once `devHome.checkEveryHours` has passed | Fetch first, every time |
| `/knowledge add` | Add, commit, push | Fetch first, add, commit, push |
| `/dev-home sync` | Fetch, merge, push | The same |

Plain `/knowledge` syncs as adding a note does
([0029: The dev-home skill](0029-the-dev-home-skill.md)).

- A new dev-home starts with `multiMachine: false`. Every PC's first setup asks "Is dev-home in
  active use anywhere besides this PC?", with the file's answer as the default, except for a
  dev-home setup has just created
  ([0034: Runs of setup by hand](0034-runs-of-setup-by-hand.md)). Only a dev-home with no
  answer, such as an older one with no `dev-home.json`, gets the question with no default: the
  person types y or n, and Enter asks again. `--quiet` says so and changes nothing.
- A missing or unreadable `dev-home.json` means fetching every time.
- With one active copy, a sync that brings in commits this PC didn't make says so in one line,
  naming `/dev-home configure`. It never changes the setting itself: that's a commit every copy
  shares.
- When setup changes the setting, it shows the change, writes only `dev-home.json` (keeping any
  key it doesn't know), and commits and pushes it through the sync's code, in its own process: a
  function that commits the one file and syncs, but skips the update check and setup, since
  setup is already running. It commits before it links skills, so whatever a merge brings in is
  linked in the same run. After a switch to several copies, it tells the person to run
  `/dev-home sync` on the others; before a switch back to one, it asks them to confirm the
  others are retired.
- The sync's lines say what's true for the mode: with one copy, a read never says that dev-home
  may be behind.

Changed on 2026-10-14 and 2026-10-20.

**Why:**

- With one copy, a fetch finds nothing, and an offline PC shouldn't be told its own copy may be
  out of date. With several, the start of a session is where a stale handoff costs the most.
- The setting is shared because it describes the repo, and every copy has to agree on it. Kept
  on each PC, every PC would repeat the choice, and one could disagree without anyone noticing.
- Several copies fetch before every command that syncs, with no window of a few minutes in which
  a fetch is skipped. On one PC, a dev-home fetch took about 1.2 s, about 1% of a `/handoff` from
  the prompt to the finished reply, while a stale handoff costs a wrong Next up or work done
  twice. On that PC, over ten days, about half the syncs came within 5 minutes of the one before,
  so a window would have saved fetches, but none a person would notice.
- The clone question has no default because both wrong answers cost something. A wrong "one
  copy" leaves each copy up to `devHome.checkEveryHours` behind the other; the line above catches it
  at the first fetch that brings in the other copy's commits. A wrong "several" costs a fetch per
  command for good, and nothing points it out.
- Setup commits through a function of the sync's, in its own process, because a sync that
  commits runs setup when it brought in commits, as a rejected push followed by a merge does.
  Through `sync.py`, setup would start again inside itself.
- `dev-home.json` stands out in the root, says what it configures, and can hold another setting
  for the whole repo later. `multiMachine` is the familiar idea, and defining it by copies in
  active use makes it right for cloud environments and replacements too.

**Options set aside:**

- No setting, with every command that syncs fetching: simpler, but one copy is a first-class
  use, where every fetch finds nothing and an offline read would warn for no reason.
- The setting on each PC only; a shared default with each PC able to override it (rules for
  which wins, with no need for them yet); and a list of the machines (identities to keep up to
  date, when the sync only needs a yes or no).
- Other names: `config.json` (too general), `shared-settings.json` (names how it's stored, not
  what it's for), `multipleCopies` or `multipleClones` (exact, but less familiar), `syncMode`
  (hides the fact that decides the mode), and `syncAcrossMachines` (sounds as if false might stop
  pushes). And a schema version, which nothing needs until the format changes: it came with
  decision 0046, "Settings files' layout and versions".
- Changing the setting by itself when another copy's commits arrive: a shared commit needs a
  yes.
- A window of 5 or 15 minutes in which several copies skip the fetch.
- A default for the clone question: No (the costlier mistake) or Yes (never pointed out).
- Setup committing through `sync.py --message` in a process of its own with a `--no-setup`
  option (a public option only setup would use, plus a process start), or by running git itself
  (around the sync's lock, its staging of exact files, and its handling of conflicts).

**Look again if:** fetches become slow enough to notice, or the sync needs to know more about the
copies than one or several.
