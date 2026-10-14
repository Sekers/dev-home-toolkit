# The scripts

| Script | What it's for |
| --- | --- |
| `setup.py` | Sets up this PC. Safe to run any number of times. `--what-if` previews; `--quiet` prints only changes and problems, and never asks (agents run it this way); `--content-dir <folder>` points it at a different dev-home; `--configure` shows a menu of every setting to change. An agent changes one with `--configure '<name>=<value>'` after you approve it, and `--configure` alone, run where nobody can answer, lists the names and values. |
| `sync.py` | Syncs your dev-home with GitHub, and commits only the files it's given. Agents run all their git in dev-home through it. Then it checks for updates as `update.py` does, and runs setup quietly (see [When they run](#when-they-run)). You can run it too; `--help` says how to commit with it, and how `--fetch` chooses when to check GitHub for dev-home's changes. |
| `update.py` | Shows the dev-home-tools commits waiting on GitHub, and installs them after a yes. With `--quiet`, as a sync runs it, it never asks: it reports what's waiting, and installs it only when `updates.installAutomatically` is on. |

All three are Python. Run them with the Python install manager's `py`, such as
`py C:\Programming\dev-home-tools\setup.py`. Each is a short entry point that loads its code from
`internal/shared/`, and `--help` says what it does.

The skills also run two Python scripts of their own, which only agents run, from
`templates/shared-skill-scripts/`: `prepare.py` starts each skill command that syncs, by running
the sync inside its own process and then reporting what the skill needs, such as where the
project's handoff is; and `facts.py` reports that alone, without syncing, which is how the
handoff skill starts in Codex, and how `/dev-home skills` lists the skills.

## When they run

Nothing runs on a schedule. Each script runs only when you or an agent starts it.

| Script | When it runs |
| --- | --- |
| `sync.py` | In Claude Code, agents run it at the start of every `/handoff` command, for a plain `/knowledge`, before adding to the knowledge base, and for `/dev-home sync`, through the skills' `prepare.py`; that sync also checks for updates and runs setup, and checks GitHub for dev-home's changes as often as the command needs (see [How often a sync checks GitHub](#how-often-a-sync-checks-github)). Then they run it again to commit and push each change they make. That second sync pushes without fetching first, and fetches and merges only if GitHub rejects the push because it has commits this PC lacks. It skips the update check, and runs setup only if it brought in commits from GitHub, because the sync just before it did both. A lookup, `/knowledge <question>`, never syncs, and Codex never runs it. You can run it any time. |
| `update.py` | Each sync that isn't committing runs its check, quietly, and that check asks GitHub only once `updates.checkEveryHours` have passed (see [Updates](#updates)). You run it yourself to look at an update and install it, when `updates.installAutomatically` is off. |
| `setup.py` | You run it once per PC, and again to change a setting, to answer a question it hasn't asked yet, or to say yes to a settings change. After that, syncs run it quietly, as above. That quiet run never asks anything, and never changes Claude Code's or Codex's settings. When you install an update with `update.py`, it runs setup as you would by hand, so in a terminal setup asks about anything new. |

### How often a sync checks GitHub

A sync that isn't committing checks GitHub for dev-home's changes as its `--fetch` says, and each
command passes the one it needs:

| Command | `--fetch` | Checks GitHub for dev-home's changes |
| --- | --- | --- |
| Every `/handoff` command, and adding to the knowledge base | `auto` | With dev-home in active use on several copies, such as two PCs, every time. With one, only once `devHome.checkEveryHours` have passed since the last check, since nothing else changes it. |
| Plain `/knowledge` | `when-due` | Only once `devHome.checkEveryHours` have passed, however many copies are in use, so its list of subjects is never far behind. |
| `/dev-home sync`, and `sync.py` run by hand | `always` | Every time. |

`devHome.checkEveryHours` is 12 unless you set it in `local-settings.json`, where 0 means every
time. Whether dev-home has one active copy or several is `multiMachine` in your dev-home's
`dev-home.json`, which every copy shares, and `/dev-home configure` changes it; a missing or
unreadable file, one in a layout this dev-home-tools doesn't know, or one with no answer, counts
as several. A sync that skips the check still
merges what an earlier check brought in, pushes commits waiting on this PC, and lists the files
left uncommitted.

## What they report

Agents pass on what `sync.py` reports, and `prepare.py` with it. A change in your dev-home is in
one of three places, and each has its own words:

| Where the change is | What the sync reports |
| --- | --- |
| In a file on this PC, not in a commit yet | `LEFT` or `STALE`, naming the file |
| In a commit on this PC, not on GitHub yet | `PUSHED` once the sync sends it, or `PENDING` when it couldn't |
| On GitHub, not on this PC yet | `PULLED` or `MERGED` once the sync brings it in, `OFFLINE` when GitHub couldn't be reached, or an `OK` line saying GitHub wasn't checked this time |

So `LEFT` and `STALE` never mean a commit that isn't pushed: a change that isn't in a commit
can't be pushed, so it's only on this PC. Every sync tries to send the commits waiting on this
PC, and says so when it can't.

| Word | Meaning |
| --- | --- |
| `OK` | Nothing needed doing. `dev-home is up to date with GitHub` means the sync checked GitHub just now, and found the same commits there as on this PC; any `LEFT` or `STALE` lines after it are changes not in a commit yet. The other `OK` lines say that GitHub wasn't checked this time and why, or that there was nothing to commit. |
| `COMMITTED` | Committed the files it was given. |
| `PULLED`, `MERGED` | Brought in commits from GitHub. `MERGED` means two PCs both had new commits. When a dev-home-tools update changes the default of a setting you haven't chosen a value for, its `PULLED` line names it and its new value. |
| `PUSHED` | Sent this PC's commits to GitHub. |
| `PENDING` | Commits saved on this PC, not synced to GitHub yet. The next sync sends them. |
| `OFFLINE` | GitHub couldn't be reached. The line says for which repo: your dev-home may be behind, or dev-home-tools wasn't checked for updates. When dev-home is set to one active copy, it says nothing should be missing, since no other copy writes to it. |
| `SETTING` | dev-home is set to one active copy, but a sync brought in commits from another copy. If another copy is in use, switch the setting with `/dev-home configure`. |
| `LEFT` | A file on this PC changed in the last 15 minutes, and the change isn't in a commit yet. Another session may be working on it, so the agent leaves it alone. |
| `STALE` | A file on this PC whose change isn't in a commit yet, and that nobody has touched for 15 minutes. The agent asks whether to commit and push it. Stale means nobody is working on it, not that it's behind GitHub. |
| `UPDATE` | New dev-home-tools commits are waiting. |
| `PROBLEM` | Needs you. The message says what to do. |
| `RELOAD` | From `prepare.py`: the skill has changed since the session loaded it, such as after an update, so the agent stops. Type the skill's command again to load its new steps. |

Setup's lines, such as `LINKED` or `WROTE`, say what it changed on this PC.

## Updates

Your copy of dev-home-tools never changes by itself. Instead, each sync that isn't committing a
change, such as the one every `/handoff` starts with, checks for new commits to dev-home-tools.
It asks GitHub once `updates.checkEveryHours` have passed since it last did, 24 by default, and
in between uses what it found then; set it in `local-settings.json`, where 0 means every sync.
`update.py` run by hand always asks GitHub. What happens when commits are waiting depends on your
answer to setup's question about installing them automatically, `updates.installAutomatically`:

| `updates.installAutomatically` | When new commits are waiting | What you do |
| --- | --- | --- |
| On (the default, and until you answer) | The sync installs them, and the agent tells you it did. | Nothing. |
| Off | Nothing is installed, and the agent tells you an update is waiting. | When you're ready, run `update.py` (below). It lists the commits and the files they change, and installs them only if you answer `y`. |

A settings file the update check can't read installs nothing, whatever the default.

```powershell
py C:\Programming\dev-home-tools\update.py
```

Either way, `update.py`'s code does the work: the sync runs it quietly, and you run it yourself
to look first. So an update is always installed the same way:

- **It only moves your copy forward to GitHub's version.** It never merges, so if you've made
  commits of your own in your dev-home-tools folder, nothing is installed, and the agent says
  so: pull and merge the update yourself with git. A change you haven't committed is never
  overwritten either: an update that touches the same file waits until it's gone.
- **Setup runs afterwards,** so the new skills and rules take effect.
- **It changes only your dev-home-tools folder.** Your dev-home and everything in it stay as
  they are.

To switch it, run `/dev-home configure`, or set `updates.installAutomatically` to `true` or
`false` in `local-settings.json`, in your dev-home-tools folder.

### Where updates come from

Updates come from the repo your copy was cloned from: git's `origin`, which the branch you're on
follows. dev-home-tools' own settings don't name it; git keeps it in `.git/config`, in your
dev-home-tools folder. To see it:

```powershell
git -C C:\Programming\dev-home-tools remote -v
```

To get updates from somewhere else, run one of these in your dev-home-tools folder:

| You want updates from | Run |
| --- | --- |
| Your own fork, after cloning the original | `git remote set-url origin <your fork's address>` |
| The original, after cloning your fork | `git remote add upstream <the original's address>`, then `git fetch upstream`, then `git branch --set-upstream-to=upstream/main main` |
| The same repo at a new address, after it's renamed or moved | `git remote set-url origin <the new address>` |

The original's address is the one in the README's clone command. The next `update.py`, or the
next sync's check, uses the new source.

- **With your fork as the source,** updates arrive only after you sync the fork with the
  original, such as with GitHub's "Sync fork" button or `gh repo sync <you>/dev-home-tools`.
- **With the original as the source while you keep a fork,**
  `git config remote.pushDefault origin` keeps your own pushes going to the fork. Once you have
  commits of your own, though, an update can't simply move your copy forward, so you merge each
  one by hand, as above.
