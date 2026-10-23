# 0084: dev-home's commit history

**Built:** nothing to build.

**Decision:** dev-home keeps every commit dev-home-toolkit makes there: at most one for each run
of `sync.py --message` (none when the files it names already match the last commit), one for each
of setup's commits, and a merge commit whenever a sync brings together new commits from two
copies. Nothing trims or tidies its history: no squashing or rewriting it, no batching changes into
fewer commits, and no scheduled maintenance beyond what git does by itself. Decided by the
developer on 2026-10-23.

**Why:**

- The volume is small for git. Measured on 2026-10-23 on a dev-home in daily use: 650 commits in
  its first four weeks, 242 of them in the last seven days (about 35 a day, or about 13,000 a year
  at that rate), with the whole history at 2.3 MB on disk and 1.4 MB as GitHub reports it, for
  127 files totaling 0.8 MB. The Linux kernel's repository on GitHub had 1,492,783 commits on
  `master` the same day, and is in everyday use.
- Each commit is small. A sync commits a few text files, and git stores the versions of a file in
  its packs as differences from one another, so text history grows slowly. What makes a
  repository large is big files, such as images or archives, changed often, and dev-home holds
  only text.
- Git tidies up by itself. Commands that write to a repository, such as a commit or a fetch,
  start git's automatic maintenance (`git maintenance run --auto`, on by default through
  `maintenance.auto`). By default it runs only the `gc` task: git's docs name a default strategy
  for manual and for scheduled maintenance, but none for automatic maintenance, and of the tasks
  only `maintenance.gc.enabled` is on by default. That task repacks once objects pile up, past
  6,700 loose objects or 50 packs (`gc.auto` and `gc.autoPackLimit`), and then also rewrites the
  commit-graph files that speed up walking the history (`gc.writeCommitGraph`). All of this is
  from git 2.55's `git-maintenance`, `git-gc`, and `git-config` pages. The dev-home measured above
  had 158 loose objects in 3 packs, and commit-graph files already.
- A sync's time doesn't grow with the history: a fetch or a push sends only the commits the other
  side lacks.
- History viewers, such as GitHub's list of commits and VS Code's Source Control graph, load
  commits a page at a time, so a long history doesn't slow them. Each commit's first line names
  its area and what it changed, such as `handoff: you/tool (<PC>)`
  ([0083: The PC's name](0083-the-pcs-name.md)), so searching for that text, or showing the
  history of one file, finds a change among many.
- A commit for each change keeps apart the changes that end users approved one at a time, so each
  can be found and undone on its own.

**Costs:**

- `git blame`, and the full history of one file, walk every version of that file, so a handoff
  edited many thousands of times takes seconds rather than an instant.
- A fresh clone downloads the whole history: a few megabytes now.
- Lists of commits are long, and mostly small handoff updates, so finding one takes a search or a
  filter rather than scrolling.

**Options set aside:**

- Squashing or rewriting dev-home's history from time to time: every other copy shares that
  history, so each would need resetting, and a copy with commits it hadn't pushed yet would meet
  conflicts or lose them.
- Fewer commits, such as one for each session or on a timer: changes would wait uncommitted on
  one PC, so other PCs would see them later and a crash could lose them, and one commit would mix
  changes that end users approved separately.
- Scheduled maintenance on each PC, such as `git maintenance start`: a background task with no
  measurable gain at this size, since git's own housekeeping already covers it.

**Look again if:** a dev-home's `.git` folder passes about 100 MB, a sync or a history viewer
gets noticeably slower, or dev-home starts holding large files that change often. If what grows is
the time a new copy takes to clone, weigh a partial clone first (`git clone --filter=blob:none`,
which fetches old versions of files only when they're needed): it leaves the history as it is.
