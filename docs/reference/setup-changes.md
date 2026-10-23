# What setup changes on your PC

Setup doesn't copy the skills into Claude Code's and Codex's folders. It adds links there
instead: a link is a folder entry that points to a folder somewhere else, and the agents read
through it as if the files were right there. So when a sync or an update changes a skill, the
agents see the change at once, with nothing to copy. On Windows, setup makes each folder link as
a directory junction, which needs no admin rights and no Developer Mode. Your always-on rules are
the exception: each agent gets them as one file setup writes in its folder, the operating rules
and your rules joined, which setup writes again at each sync.

- **In your dev-home-toolkit folder,** three things that belong to this PC only. Git ignores them,
  so they never go to GitHub, and an update never overwrites them.
  - `internal\.generated\`: this PC's copy of the skills and the scripts they share, at the same
    paths they have under `templates/`. In this repo, they hold a placeholder wherever a folder
    path goes, because everyone keeps their folders in different places. Setup writes a copy with
    this PC's real paths filled in, and that copy is what the agents use. The paths have to be
    written out in full, because the commands a skill may run without asking you are matched by
    their exact text. Setup rewrites this folder whenever it runs, so don't edit it; put skills of
    your own in your dev-home. Python adds `__pycache__` folders beside the scripts when they
    run, so they start faster next time; setup leaves those alone. Setup also writes
    `skill-states.json` there: whether it added each skill to your agents on this PC, and if not,
    why, which `/dev-home skills` shows. In `last-written\`, it keeps a copy of the rules file it
    last wrote in each agent's folder, and of your dev-home's `AGENTS.md` and `CLAUDE.md`, by
    which it knows each file is still its own. And when a Python doesn't run as setup checks it,
    setup notes it in `failed-pythons.json` there, so syncs don't wait for it again until that
    Python changes.
  - `internal\.python\`: a directory junction to the folder of the Python the skills' scripts
    run with, so every skill command can name `internal\.python\python.exe` here: a short path,
    the same on every PC, with no spaces to quote. Setup only uses a Python you've installed,
    and never installs one. It picks the first of these that runs:
    1. The Python install manager's commands, in `%LocalAppData%\Python\bin`, whose
       `python.exe` runs the install manager's default Python, and moves on to newer ones as
       you install them.
    2. The newest Python 3.12 or later in the registry, which is where the traditional installer
       records one, leaving out test releases such as 3.16.0a1.

    Every run checks that the junction still leads to the first of those, which starts no
    program. When another comes first, such as a newer Python you installed with the
    traditional installer, setup starts it once to check that it runs, then points the junction
    at it and says so in a `LINKED` line.
  - `local-settings.json`: this PC's answers to setup's questions: where your dev-home is,
    whether to install updates automatically, which Claude Code folders to set up, and which not
    to, whether to set up Codex, the date to ask again about a folder you're to be reminded of,
    which skills to add to your agents, and the skills' preferences.
    The scripts read it to find your dev-home.
    Setup removes a setting nothing declares any more, such as one misspelled in a hand edit,
    and says so, after a backup of the file. It never overwrites a file it can't read as JSON,
    or one with a `schemaVersion` it doesn't know. One in an older layout, from before its
    settings were grouped, it offers to set aside, as a dated backup beside it, and then asks its
    questions again.
- **In each Claude Code folder you said yes to** (`~\.claude`, and any extra ones):
  - Links in `skills\` to each skill added to your agents on this PC (this repo's, and your own
    from dev-home; see [A skill's dev-home-skill.json](dev-home-skill-json.md)).
  - `rules\dev-home-rules.md`: the operating rules and your rules joined, which Claude Code loads
    with every other `.md` file in `rules\` (see [Rule files](rule-files.md)). Setup rewrites it
    whenever it runs, while it still matches what setup last wrote there, and never replaces one
    with changes it didn't make.
  - `settings.json` gets your dev-home and dev-home-toolkit folders in
    `permissions.additionalDirectories`, so Claude Code can use them from any project. Your yes to
    the folder approves this, and every sync puts it back if it goes missing, with a backup.
  - In each folder other than `~\.claude`, `settings.json` also gets two patterns in
    `claudeMdExcludes`. Claude Code loads the `CLAUDE.md` and `rules\` it finds in every folder
    above where a session starts. So a session of another account, started anywhere under your
    user folder, loads `~\.claude`'s as if they were the project's own instructions, until Claude
    Code fixes it ([anthropics/claude-code#79233](https://github.com/anthropics/claude-code/issues/79233)).
    The patterns keep them out of that folder's sessions. Your yes to the folder approves them
    too, and every sync puts them back if they go missing.
  - Your own `CLAUDE.md` there is never touched.
- **For Codex,** once you've said yes to it, in every Codex home (`~\.codex`, and any extra
  ones). Every home reads the same skills, so it's all of them or none:
  - Links in `~\.agents\skills\`, which every Codex home reads, to each skill added to your
    agents on this PC.
  - `AGENTS.md` in each home, such as `~\.codex\AGENTS.md`: the operating rules and your rules
    joined, as for Claude Code, since Codex reads one always-on file there. Setup rewrites it
    whenever it runs, while it still matches what setup last wrote there, and never replaces an
    `AGENTS.md` it didn't write, or one with changes it didn't make.
  - `config.toml` gets dev-home in `[sandbox_workspace_write]` `writable_roots`, so Codex can
    edit handoffs and knowledge from any project. Your yes to Codex approves this, and every sync
    puts it back if it goes missing, with a backup. Its `project_doc_max_bytes` is raised to at
    least `codex.instructionsMaxKiB`, 128 KiB unless set, and never lowered. Codex joins its
    global `AGENTS.md` with a project's own `AGENTS.md` files and stops reading at 32 KiB by
    default. The global file comes first, so the cut would fall on the project's own
    instructions, without a warning.
- **If you say no later,** to a Claude Code folder or to Codex, setup removes what it set up
  there, naming each as it goes:
  - In a Claude Code folder: its links in `skills\`, its `rules\dev-home-rules.md`, your
    dev-home and dev-home-toolkit folders in `settings.json`'s
    `permissions.additionalDirectories`, and its two patterns in `claudeMdExcludes`, with a
    backup.
  - For Codex: the `AGENTS.md` it wrote in each home, its links in `~\.agents\skills\`, and your
    dev-home in each `config.toml`'s `writable_roots`, with a backup.
    `project_doc_max_bytes` stays, since it gives Codex no access.

  A rules file with changes setup didn't make stays, and setup says so: move anything you want to
  keep into your dev-home's `rules\`, then delete it. Your own files, links, and settings there
  stay, though an entry you added yourself for the same folder, or the same pattern, goes too;
  the backup keeps it. Other agents that read those
  skills folders lose dev-home's skills too: GitHub Copilot, Gemini CLI, and Cursor read
  `~\.agents\skills\`, and Cursor also reads `~\.claude\skills\`.
- **If a skill isn't added to your agents on this PC,** because you said no to it, it's marked as
  not recommended and you haven't said yes, it works only on another operating system or in
  another agent, or it's one of yours named `synced`, a name Claude Code keeps for the skills it
  downloads from claude.ai, setup removes its links from those skills folders, naming each as it
  goes, and puts them back once that changes. A program or a Python version the skill needs
  never takes its links out. The skill's copy in `internal\.generated\` stays where it is.
- **In your dev-home's own git config:** commit signing off, pulls that merge rather than rebase,
  and `core.longpaths` on, since `rules\` can need paths longer than Windows' default limit. With
  signing off, a commit never stops in the middle of a sync to ask for your signing passphrase.
  Your project repos keep signing as usual. Setup does this only in a folder that is a dev-home,
  with `dev-home.json`.
- **In your dev-home itself:** an empty `my-rules.md` wherever one is missing in `rules\`, for
  every agent and for each agent set up on this PC (see [Your rules](../guide/your-rules.md)),
  committed and pushed. And after your yes, `dev-home.json`, which says whether dev-home is in
  active use on one PC or on several, so each sync knows how often to check GitHub. Every copy
  shares it, so setup commits and pushes the change; git's history is its backup.
- **`AGENTS.md` and `CLAUDE.md` in your dev-home:** what an agent working in dev-home needs to
  know, with this PC's commands, so they differ from PC to PC, and dev-home's `.gitignore`
  keeps them out of git. Setup rewrites both whenever it runs. An edit you make to either goes
  to the Recycle Bin first, as a file named such as `AGENTS from dev-home, as edited.md`, and
  setup puts the file back and says so. Your own guidance for agents goes in your rules. If the
  Recycle Bin can't take the edit, setup leaves the file as you edited it and says so on every
  sync, until the bin takes it. Running setup in a terminal tries the bin again, and if it still
  can't take the edit, shows it to you and asks whether to delete it for good instead.

**To remove it all:** delete each link with `cmd /c rmdir <link>`, `internal\.python` included,
delete the rules file setup wrote in each agent's folder, `rules\dev-home-rules.md` in each
Claude Code folder and `AGENTS.md` in each Codex home, take the added lines out of the settings
files, then delete your dev-home-toolkit folder. Your dev-home stays as it is, but its
`AGENTS.md` and `CLAUDE.md` name commands in the folder you deleted, so delete them too.
