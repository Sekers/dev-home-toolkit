# 0087: Cloning dev-home

**Built:** yes.

**Decision:** setup clones dev-home into a folder beside dev-home's, named for it with `.cloning`
added, such as `C:\Programming\dev-home.cloning`, and moves that folder to dev-home's path only
once the clone is complete, in place of the empty folder that may be there. However a clone
stops, dev-home's path is then as it was, missing or an empty folder, or holds the whole clone.
While Windows refuses the move, as while a program holds a new file open, or a terminal is open
in that empty folder, setup tries 10 times, 0.2 seconds apart, then puts back the empty folder
it removed for the move and reports both folders. When dev-home's folder is a link, such as to an
empty folder on another drive, the clone goes beside the folder at the end of the link, and of
any link that one leads to, and then into it, and every link stays: setup never removes a link it
didn't make. A link that leads nowhere, as to a drive that isn't plugged in, stops setup with a
`PROBLEM` line before it asks whether to clone or create, since what it led to may be the real
dev-home. Setup holds a lock while it
clears the cloning folder, clones, and moves the clone into place, and while it creates a new
dev-home instead, of the kind the sync holds
([0018: One sync at a time](0018-one-sync-at-a-time.md)), on
`internal/.generated/new-dev-home.lock` in dev-home-toolkit's folder, since dev-home's own `.git`
isn't there yet. It takes the lock after the questions, as setup's work takes the sync's. A
second run waits up to 2 minutes for it, then uses the dev-home the first run put in place,
whether it was to clone or to create, or changes nothing and says why. A folder the first run
left with files but not a whole dev-home, with `dev-home.json` and `.git`, as when it stopped
partway, gets a `PROBLEM` line. A run that ends without dev-home always says why in a `PROBLEM`
line, so it never ends with "All checks passed". Before it clones, and when a clone fails, setup deletes what a clone that didn't finish left
in that folder, but only an empty folder or a git repo, which a clone would have made there;
anything else in its place, setup reports and leaves alone. The delete removes each link inside by itself first, deletes `.git`
last, so a delete that stops partway leaves a folder setup still deletes at its next run, and
works through Windows' long form of the path, so it deletes what git checked out past Windows'
path limit. A `--what-if` preview names the delete as well as the clone. A
failed clone's `PROBLEM` line quotes git's first error line, not the output's first line, which
for git is "Cloning into", or the last line when there's none, as when `gh` stops before git
runs. Decided by the developer on 2026-10-29.

**Why:**

- A clone that stops once its checkout has started leaves a folder that holds `dev-home.json`
  but not every file, and no index, so git counts every file as deleted. Tested on 2026-10-29
  with a repo of 30,001 files: killed 1.5 seconds in, the clone had written 24,811 of them,
  `dev-home.json` among them, and no index. Setup took such a folder for a dev-home, in the same
  run when `gh` failed and at every run after. The sync's merge then refused, and after 15
  minutes the sync listed each missing file as `STALE`, whose commit would delete it on every PC.
- A killed process runs nothing more, so only a design where dev-home's path never holds a clone
  that's partly there covers a closed window or a power cut. A move within one folder is all or
  nothing.
- The move worked at the first try in all 10 tries made right after a clone, with Windows
  Defender's real-time protection on, in 1 to 18 ms, for 300 files and for 30,000 (2026-10-29, on
  a fast PC). The later tries are for a slower PC, where antivirus may still hold a new file open.
- Deleted for good, not sent to the Recycle Bin: the folder holds only part of what GitHub has.
- A clone holds a link only when dev-home tracks a symbolic link and the PC's git has
  `core.symlinks` on, which Windows allows only with Developer Mode or admin rights, and setup
  puts no link in dev-home. The links still come out first, since a recursive delete must never
  reach what a link points to ([scripts.md](../scripts.md)).
- The lock: without it, a second run of setup cloning at the same moment would delete the first
  one's clone as something left by a clone that didn't finish, while git kept writing it, and the
  first run would move a dev-home with files missing into place. A run creating a new dev-home
  while another clones would fill dev-home's folder, so the clone couldn't move into place, and
  the end user would have a new, empty dev-home where they meant to clone theirs. Every other
  place where two runs could clash holds a lock of this kind, which the operating system lets go
  of when a run ends, even one that's killed, so it never needs deleting.
- When another host's support comes
  ([0086: dev-home's host](0086-dev-homes-host.md)), its clone goes in the same place: the folder
  and the move don't depend on which program clones.

**Options set aside:**

- Stopping the run when a clone fails, and repairing a half-made dev-home at later runs. The
  cheap sign of one, a missing `.git/index`, is gone as soon as anything stages a file, such as
  setup's own commit of `dev-home.json`, so a check that holds needs a git call on every run. The
  repair also has to overwrite files cut short, which is safe only while nothing of the end
  user's is there. git's own advice, `git restore --source=HEAD :/`, writes the files but leaves
  the index missing (tested on 2026-10-29).
- Only stopping the run on failure, and quoting git's error: a closed window or a power cut
  still leaves the half-made folder.
- Leaving what an unfinished clone left for the end user to delete: a step by hand, right after
  something went wrong, for a folder that's setup's own.
- Sending it to the Recycle Bin: that fills the bin with a copy that GitHub still has, a large
  folder is slow to send, and setup's code for the bin has only been used on files.
- No lock, since a race needs two runs of setup by hand at once, both putting a missing dev-home
  in place: every other place where two runs could clash has one, and this is where a race does
  the most harm. A lock for the clone alone: two runs creating at once lose nothing, since GitHub
  refuses the second repo, but a run creating while another clones leaves the mix-up above, easy
  to miss.
- For a complete clone in the cloning folder, left when the move failed: moving it into place
  rather than cloning again. It saves only a download of dev-home, after a move that failed, and
  would use whatever repo an earlier run named rather than the one just named. Nothing else works
  in that folder, so nothing in it needs keeping. Nor reporting it for the end user to move or
  delete: a step by hand for no gain.

**Look again if:** another host's support is built, or the tries to move the clone run out on
real PCs.
