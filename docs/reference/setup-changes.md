# What setup changes on your PC

Setup doesn't copy the skills and rules into Claude Code's and Codex's folders. It adds links
there instead: a link is a folder entry that points to a folder somewhere else, and the agents
read through it as if the files were right there. So when a sync or an update changes a skill
or a rule, the agents see the change at once, with nothing to copy. On Windows, setup makes each
folder link as a directory junction, which needs no admin rights and no Developer Mode.

- **In your dev-home-toolkit folder,** three things that belong to this PC only. Git ignores them,
  so they never go to GitHub, and an update never overwrites them.
  - `internal\.generated\`: this PC's copy of the skills, the scripts they share, and the
    operating rules, at the same paths they have under `templates/`. In this repo, they hold a
    placeholder wherever a folder path goes, because everyone keeps their folders in different
    places. Setup writes a copy with this PC's real paths filled in, and that copy is what the
    agents use. The paths have to be written out in full, because the commands a skill may run
    without asking you are matched by their exact text. Setup rewrites this folder whenever it
    runs, so don't edit it; put skills of your own in your dev-home. Each skill's `SKILL.md` and
    the operating rules carry a note saying so, with the path of the template to change
    instead, because an agent working in another project sees only this copy. Python adds
    `__pycache__` folders beside the scripts when they run, so they start faster next time;
    setup leaves those alone. Setup also writes `skill-states.json` there: whether it added each
    skill to your agents on this PC, and if not, why, which `/dev-home skills` shows.
  - `internal\.python\`: a directory junction to the folder of the Python the skills' scripts
    run with, so every skill command can name `internal\.python\python.exe` here: a short path,
    the same on every PC, with no spaces to quote. Setup looks first for the Python install
    manager's shortcuts, in `%LocalAppData%\Python\bin`, whose `python.exe` moves on to newer
    Pythons as you install them, and then for the newest Python 3.12 or later in the registry,
    which is where the traditional installer records one. It looks only when it makes the
    junction, or when the `python.exe` the junction leads to is gone; other runs just check that
    it's there.
  - `local-settings.json`: this PC's answers to setup's questions: where your dev-home is,
    whether to install updates automatically, which Claude Code folders to set up, and which not
    to, whether to set up Codex, which skills to add to your agents, and the skills' preferences.
    The scripts read it to find your dev-home.
    Setup removes a setting nothing declares any more, such as one misspelled in a hand edit,
    and says so, after a backup of the file. It never overwrites a file it can't read as JSON,
    or one with a `schemaVersion` it doesn't know. One in an older layout, from before its settings were grouped, it offers to set
    aside, as a dated backup beside it, and then asks its questions again.
- **In each Claude Code folder you said yes to** (`~\.claude`, and any extra ones):
  - Links in `skills\` to each skill added to your agents on this PC (this repo's, and your own
    from dev-home; see [A skill's dev-home-skill.json](dev-home-skill-json.md)). In `rules\`,
    `dev-home-operating-rules` links to the operating rules, and `dev-home-global-rules` to your
    dev-home's `global-rules\`. Nothing in that folder says which repo a name belongs to, so
    each link starts with `dev-home-`.
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
  - `AGENTS.md` in each home, such as `~\.codex\AGENTS.md`: the operating rules and your global
    rules joined into one file, because Codex reads only one always-on file. Setup rewrites it
    whenever it runs, but never replaces an `AGENTS.md` it didn't write.
  - `config.toml` gets dev-home in `[sandbox_workspace_write]` `writable_roots`, so Codex can
    edit handoffs and knowledge from any project. Your yes to Codex approves this, and every sync
    puts it back if it goes missing, with a backup. It also gets
    `project_doc_max_bytes = 65536`. Codex joins its global `AGENTS.md` with a project's own
    `AGENTS.md` files and stops reading at 32 KiB by default. The global file comes first, so
    the cut would fall on the project's own instructions, without a warning. Twice the default
    leaves room.
- **If you say no later,** to a Claude Code folder or to Codex, setup removes what it set up
  there, naming each as it goes:
  - In a Claude Code folder: its links in `skills\` and `rules\`, your dev-home and
    dev-home-toolkit folders in `settings.json`'s `permissions.additionalDirectories`, and its two
    patterns in `claudeMdExcludes`, with a backup.
  - For Codex: the `AGENTS.md` it wrote in each home, its links in `~\.agents\skills\`, and your
    dev-home in each `config.toml`'s `writable_roots`, with a backup.
    `project_doc_max_bytes` stays, since it gives Codex no access.

  Your own files, links, and settings there stay, though an entry you added yourself for the same
  folder, or the same pattern, goes too; the backup keeps it. Other agents that read those
  skills folders lose dev-home's skills too: GitHub Copilot, Gemini CLI, and Cursor read
  `~\.agents\skills\`, and Cursor also reads `~\.claude\skills\`.
- **If a skill isn't added to your agents on this PC,** because you said no to it, it's marked as
  not recommended and you haven't said yes, or it works only on another operating system or in
  another agent, setup removes its links from those skills folders, naming each as it goes, and
  puts them back once that changes. A program or a Python version the skill needs never takes its
  links out. The skill's copy in `internal\.generated\` stays where it is.
- **In your dev-home's own git config:** commit signing off, and pulls that merge rather than
  rebase. With signing off, a commit never stops in the middle of a sync to ask for your signing
  passphrase. Your project repos keep signing as usual. Setup does this only in a folder that
  looks like a dev-home, with `global-rules\global-rules.md` and `knowledge\README.md`.
- **In your dev-home itself,** after your yes: `dev-home.json`, which says whether dev-home is in
  active use on one PC or on several, so each sync knows how often to check GitHub. Every copy
  shares it, so setup commits and pushes the change; git's history is its backup.

**To remove it all:** delete each link with `cmd /c rmdir <link>`, `internal\.python` included,
delete the `AGENTS.md` setup wrote in each Codex home, take the added lines out of the settings
files, then delete your dev-home-toolkit folder. Your dev-home stays as it is.
