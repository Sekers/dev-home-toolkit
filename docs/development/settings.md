# Settings

The rules for adding or changing a setting: one of dev-home-toolkit's own, in `local-settings.json`
or `dev-home.json`, or a skill's preference.
[0049: Answers in the settings](decisions/0049-answers-in-the-settings.md)
defines the forms a saved setting takes and the four kinds of setting, with the reasons.
AGENTS.md's rules apply too.

## Adding a setting

- Declare it in one place: one of dev-home-toolkit's own in `internal/shared/setting-definitions.json`,
  and a skill's preference under `preferences` in that skill's `dev-home-skill.json`. Give it a
  kind, a default or none, a label, and help. Setup, the menu, `--configure`, and `facts.py` all
  read the declaration, so never write a setting's default or label anywhere else.
- Pick its kind from the four in the decision. The help of a setting with no default says what
  happens until it's answered.
- Ask about a yes-or-no setting with a default through setup's `choose_or_default`, so every
  such question reads the same: `'y', 'n', or 'd' for the default (<its default>)`, with the
  capital letter showing what Enter gives, such as `[y/n/D]`. Any key or answer a prompt names
  goes through `console.key`
  ([0055: Keys and answers in prompts](decisions/0055-keys-and-answers-in-prompts.md)).
- Decide what Enter does at its question when nothing is answered yet, apart from its default:
  for a setting with a default, Enter means default; a folder's question, and Codex's, takes
  Enter as yes, though a folder nobody has answered for isn't set up; and `multiMachine`'s
  question has no Enter answer, since either wrong answer costs something. Once a question is
  answered, Enter always keeps the saved answer.
- An agent setup sets up, such as Claude Code or Codex, keeps its folders in one shape: an entry
  for each folder by its path, in the agent's group, named in the agent's own words, such as
  `claudeCode.folders` or `codex.homes`, each with its own answer, `setUp`. When every folder
  reads the same skills, as Codex's homes do, setup's code keeps their answers the same, and the
  file's shape doesn't change
  ([0052: Codex homes](decisions/0052-codex-homes.md)).
- A setting is per PC, in `local-settings.json`, unless it describes dev-home itself, which every
  copy shares in `dev-home.json`. A skill's preferences are always per PC.
- A skill's preference reaches end users who never run setup by hand through the feature it
  shapes: each time the skill acts on it, it says what the preference does there, by its label,
  and that `/dev-home configure` changes it. A new preference gets no `NEW` line, which would
  come on every sync for something that's fine at its default.
- Test each form it accepts, one it doesn't, and a plain value of the wrong type.

## Reading and writing

- Read every setting through the reader in `internal/shared/settings.py`. `facts.py` can't load
  setup's code, so it keeps a small reader of its own for skill preferences, and a test checks
  that the two agree.
- Write a plain value only when the end user chose that value, and `{"$state": "default"}` only
  when they chose the default. Never write a default as a plain value: that pins it.
- Quiet runs never ask, and the only state they write is `unanswered`, for something they
  announce. The one exception: a run gives each of a shared agent's folders the main folder's
  answer, with a line saying so
  ([0052: Codex homes](decisions/0052-codex-homes.md)).
- Save `local-settings.json` only through setup's save, which holds the sync's lock while it
  reads the file again and makes there only the changes a person made in that run. Anything setup
  works out by itself, such as a mark or an answer moved for a rename, is worked out again in
  `Setup.settle`, in `internal/shared/setup.py`, from the file as it is then, never carried over
  from an earlier read. One that the questions or the menu should show is also made before them,
  as each Codex home's shared answer is, outside `Setup.answering`, which records only a person's
  changes ([why](decisions/0049-answers-in-the-settings.md)).
- Make a backup only when a person changes a setting, or answers are deleted.

## Changing a setting later

- To rename one, add its old name to its `formerNames`. Setup moves each PC's answer, and
  `schemaVersion` stays as it is. Renaming or removing a whole skill is in
  [skills.md](skills.md).
- To remove one, delete its declaration. Setup deletes each PC's answer on its next run. When a
  whole skill is gone, the next sync's setup deletes its answers: it holds the sync's lock from
  its start, when it reads the skills, so a skill that a sync or an update is replacing at that
  moment never looks gone, while a run of setup by hand, which reads them before its work takes
  the lock, leaves them. A skill whose `dev-home-skill.json` can't be read keeps its
  answers, and so does every skill while dev-home's folder isn't there.
- Never give a new setting a removed one's name: a PC that gets both changes in one update would
  apply the old answer to the new setting.
- To change its default, change the declaration. Each PC that follows the default gets the new
  one, and the update that installs it says so once, in its `PULLED` line or, run by hand,
  after "Pulled". It compares the declarations before and after the pull, so a setting renamed
  in the same update gets no notice. A person's own skills don't come with updates, so their
  preferences get none either.
- To change what a setting holds, such as hours to minutes, or the structure of a file, raise the
  file's `schemaVersion`, and add a conversion step for that version, with a test (not built
  yet).
