# 0089: Where a handoff lives

**Built:** yes.

**Decision:** a project's handoff is filed by what recognizes the project on every PC, as
`facts.py` (`find_handoff_place`) works it out. A repo whose `origin` names another computer
follows that address: a known hosting service's repo under the service's folder, as
`handoffs/github/<owner>/<repo>/`, and any other under `handoffs/other/<host>/<path>/`, a network
share's path, such as `\\nas\git\tool.git`, included. Anything else gets a handoff on its own PC,
under `handoffs/pcs/<pc>/<folder>-<hash>/`: a folder outside git, and a repo with no `origin`, or
whose `origin` is a path on this PC, a mapped drive included, or names a computer that every PC
takes as itself. Decided by the developer on 2026-11-02, replacing filing by folder name and
first commit under `other/` and `local/`, and by folder name alone, and changed on 2026-11-03
and 2026-11-05 (an `origin` that names this PC). Sessions started in the home folder getting a
handoff of their PC's was decided on 2026-10-03, and every other folder outside git on
2026-10-19.

- **`<pc>`** is the PC's folder as `rules/pcs/` names it
  ([0065: Where end users' rules live](0065-where-end-users-rules-live.md)), and the `service`
  fact is `pcs`, so the folder matches the value, as every other service's does.
- **`<hash>`** is the CRC-32, as 8 hexadecimal characters, of the folder's full path, resolved
  first, following junctions, links, and short names, then compared in any letter case where the
  file system ignores it (`os.path.normcase`). `<folder>` is the resolved folder's own name, in
  lowercase, cut from its end when the path would pass the path budget
  ([0088: Path lengths](0088-path-lengths.md)). A repo's folder is its main checkout's, so a
  worktree shares its handoff.
- **One short hash.** CRC-32 also ends a handoff folder cut to fit the path budget, in place of
  SHA-256 (0088).
- **Commits play no part.** A repo with no commits yet, or a shallow clone, goes by its `origin`
  like any other.
- **A computer every PC takes as itself** is a host of `localhost`, `localhost.localdomain`, or a
  name that ends in `.localhost` or `.localhost.localdomain`; an IPv4 address that starts with
  `127.`, such as `127.0.0.1` (a name such as `127.example.com` doesn't count); `0.0.0.0`; or
  `wsl$` or `wsl.localhost`, through which Windows reaches the PC's own WSL. Any letter case
  counts. It's a check of the text alone, with no git call and no lookup. An IPv6 address,
  such as `[::1]`, goes under `pcs/` too, since `facts.py` reads no IPv6 host as a computer.
- **The move question.** When the handoff skill finds no handoff at the project's path, it lists
  the existing ones to move, and marks each in another PC's folder under `handoffs/pcs/` as that
  PC's, since moving it takes it from that PC.

**Why:**

- Filing by folder name alone mixed up unrelated folders with the same name, on one PC or across
  PCs, without a word: the agent works from another project's to-dos and writes into them.
- A project can be recognized by its address, the same on every PC; by its history, its first
  commit; or by its place, its path on one PC. The address is how a repo moves between PCs, by
  pushing on one and pulling on another, so a handoff that follows it reaches every PC with the
  repo, whatever its folder is called. A project with no such address can't be recognized on
  another PC, so its handoff stays on its own. A split shows, since the second PC finds no
  handoff and is offered a new one; a mix-up doesn't.
- Not the first commit, which named `other/` and `local/`: the folder name in the name split
  clones kept in differently named folders; projects started from one starter repo share a first
  commit; finding it took three git calls on every `/handoff`; and the names were hard to read.
- `local/`, beside `pcs/`, read as "this PC only", though its handoffs were shared.
- `pcs/` matches `rules/pcs/<pc>/`, and is how Claude Code keeps its own data outside a repo: its
  memory docs key it by the folder's root and keep it on that machine (read 2026-10-19). Nothing is
  asked, and nothing is written in the end user's folders.
- An `origin` that names this PC, such as `ssh://git@localhost/you/tool` or
  `\\wsl$\Ubuntu\home\you\tool`, reaches a different computer from each PC. Filed under
  `other/`, two PCs' unrelated repos at the same such address would share one handoff, without a
  word. On Linux, systemd-resolved answers `localhost`, `localhost.localdomain`, and every name
  that ends in either with the PC's own address (its man page, read 2026-11-05), and a connection
  to `0.0.0.0` reaches the PC too (Wikipedia's "0.0.0.0", read 2026-11-05). Windows didn't
  resolve `gitea.localhost` or `wsl.localhost` (tested 2026-11-05), so names that end in
  `.localhost` matter mainly on Linux, which dev-home-toolkit will support.
- A network share's path names a computer, as an address does, with the same text on every PC
  that uses it. A mapped drive's letter can differ between PCs, and telling that it's a share
  would mean asking Windows about the network on every `/handoff`, which is slow, and hangs while
  the share is offline.
- The path resolved and its case ignored, so a folder gets one handoff however a session reaches
  it: an editor gave one session's folder as `C:\` and as `c:\` (2026-11-02), and a junction or a
  short name such as `PROGRA~1` leads to the same folder. Resolving took about 0.07 ms, and 0.1 ms
  through a junction (measured 2026-11-02).
- CRC-32: nothing chooses the text to make two hashes clash, and only two folders with the same
  name on one PC can, about 1 in 4 billion for each pair, so a hash made for security adds
  nothing. Loading SHA-256's module took 6 to 9 ms, and `binascii` about 0.2 ms (measured
  2026-11-02), paid on every `/handoff` in a folder under `pcs/`. Shorter than 8 characters would
  give the folder's name only 2 more.
- Marking other PCs' handoffs in the move question: moving one takes it from the PC that uses it,
  while a folder copied to a new PC, whose old PC is retired, may still want its handoff.

**Costs:** a folder outside git, or a repo whose `origin` names no other computer, never shares a
handoff across PCs, even when a sync service keeps it on both; to share one, give the repo a
remote. A server reached by two names, such as an SSH alias on one PC and its real name on
another, gets a handoff under each, as known services already did. A server every PC reaches
through an SSH tunnel, as `localhost:<port>`, gets a handoff on each PC; to share one, use the
server's real name in the `origin`. A folder that moves or is renamed, and a repo that moves to
another host, gets a new handoff, which the move question offers to bring along. Before 1.0.0,
existing handoffs under `local/` and `other/` move by hand, through the move question
([0080: Compatibility before 1.0.0](0080-compatibility-before-1-0-0.md)).

**Options set aside:**

- For folders outside git, on 2026-10-19: the folder name alone, as before (mix-ups without a
  word); the PC plus the folder name (same-named folders on one PC still mix); the folder name plus
  a hash of the full path, with no PC folder (whether two PCs share depends on whether the user
  names in their paths match, which nobody can predict); a path under the home folder, and naming
  a synced folder by its library's web address from OneDrive's registry entry (both account for
  sync services, which the developer chose to leave out; OneDrive's `UrlNamespace` value isn't
  documented); a marker file with an ID in the folder, as `.git` and `.idea` work (it writes into
  the end user's folders, which colleagues see in a shared library, fails in a read-only folder,
  and its main advantage is surviving a sync); and recording each handoff's folders, asking about
  an unlisted one (the developer doesn't want that choice left to the end user).
- On 2026-10-03: no handoff for the home folder (that session had just made one to track real
  work there).
- On 2026-10-30: a path of the home folder's own, `handoffs/pcs/<pc>/HANDOFF.md` or
  `handoffs/pcs/<pc>/home/HANDOFF.md`: it already gets a handoff on its PC; a handoff in
  `handoffs/pcs/<pc>/` would sit above every other folder's, which an agent would take for its
  further files; and it needed code to detect the home folder.
- Repos by folder name and first commit, under `other/` and `local/` (see Why); merging `local/`
  into `other/` that way; and moving only `local/`'s into `pcs/`, which keeps two ways of naming
  shared handoffs.
- Every repo not on a known service under `pcs/`: a repo on a company's Git server moves between
  PCs as a GitHub one does.
- For an `origin` that names this PC, on 2026-11-03: leaving it under `other/`, with a line in
  Costs (the mix-up stays silent); looking the host up (it uses the network, is slow, can hang
  offline, and `facts.py` never uses the network); and every share path, `\\<host>\...`, under
  `pcs/` (a real network share would stop being shared, and `ssh://git@localhost/...` would
  still mix). On 2026-11-05: only `localhost`, `127.x`, `wsl$`, and `wsl.localhost`, the hosts
  decided on 2026-11-03 (two Linux PCs, each with its own server at a name that ends in
  `.localhost`, would still share one handoff).
- Known services by host too, such as `handoffs/github.com/you/tool/`: Azure DevOps' HTTPS and SSH
  addresses differ, so its clones would split, and every existing handoff would move.
- For the hash: the raw path (a drive letter's case changes between sessions); ignoring case
  without resolving (a junction or a short name gets a second handoff); lowercasing everywhere (on
  Linux, it merges folders that differ only in case); SHA-256, for both kinds of folder or for cut
  ones alone (its load time, and two hashes doing one job).
- `service: pc` under `handoffs/pcs/` (the only service whose folder differs from its value),
  under `handoffs/pc/` (it differs from `rules/pcs/`), and `local` under `handoffs/local/<pc>/`
  (it mixes PC folders with handoffs).
- In the move question: leaving other PCs' handoffs out (taking one to a new PC then needs
  steps outside the skill's), and listing them unmarked (a yes takes one from the PC that uses it).

**Look again if:** end users want folders kept by a sync service to share handoffs, or a host's
two names split handoffs in practice, which reading `~/.ssh/config` could join.
