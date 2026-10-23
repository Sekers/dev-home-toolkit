# 0083: The PC's name

**Built:** yes.

**Decision:** dev-home-toolkit names a PC by its host name, the name its owner gave it, from
Python's `socket.gethostname()`, up to the first dot, in capitals, such as `MY-LAPTOP`. It asks
the system each time, and everything that names a PC uses that one name
(`internal/shared/computer.py`, which `facts.py` copies, with a test that both give the same
name). Decided by the developer on 2026-10-23.

- **The `environment` fact,** which heads a PC's part of a handoff's Environments, shows it as it
  is.
- **Every commit dev-home-toolkit makes in a dev-home** ends its first line with it in
  parentheses, such as `handoff: you/tool (<PC>)`: the commits agents make through
  `sync.py --message`, setup's own commits, and the commit a merge makes, whose subject is
  `sync: merge GitHub's commits (<PC>)`. A first line that already ends with it stays as it is.
- **A PC's rules folder,** `rules/pcs/<pc>/`, uses it in lowercase
  ([0065: Where end users' rules live](0065-where-end-users-rules-live.md)).

**Why:**

- The host name is the name a person gave the PC, in full. Windows' other name for it, the
  NetBIOS computer name (`GetComputerNameW`, `%COMPUTERNAME%`), which the code used before, is a
  legacy copy, cut to 15 characters when the host name is longer (Microsoft's "Computer Names"
  page). On macOS and Linux, the code already used the host name.
- Asked each time, never saved: a PC that gets a new name, such as after a reinstall, is a new PC
  for everything this name does, and two PCs with the same name are rare and usually deliberate,
  such as a replacement taking over an old PC's name, which should then share its rules and notes.
- Up to the first dot: a Windows host name has none, while on macOS and Linux it can carry a
  domain, such as `.local`, and the part before it is the name people use.
- Capitals for what people read: it's how Windows writes computer names; host names ignore case,
  so a change of case alone changes nothing; and the headings handoffs already have keep
  matching. The folders are lowercase for their own reasons.
- `socket.gethostname()` over `platform.node()`, which gives the same name: on Windows,
  `platform.node()` first asks WMI for the Windows version and the processor (about 40 ms against
  4, measured on 2026-10-23 with Python 3.14.7), and it returns an empty string when the name
  can't be found, where `socket.gethostname()` fails with an error.
- In commit subjects: with dev-home in use on several PCs, which PC made a commit is the first
  question when something looks wrong, such as a merge whose page on GitHub lists a day of other
  PCs' changes because the PC that made it had fallen behind. At the end, `<area>: <what>` still
  leads, so a list of commits still scans by area. The merge's subject was "merge another PC's
  commits", and a name after it would read as naming the other PC, so the name always means the
  PC that made the commit. `sync.py` and setup add it, so the skills' text doesn't change.

**Costs:** about 4 ms on each sync that commits, to load `socket`; a few tokens more in each
`COMMITTED` line agents read; a cloud session's throwaway host name in its commits and its
`environment`; and capitals read loud for a long name, and are unusual on macOS and Linux.

**Options set aside:**

- The NetBIOS computer name, as before: cut to 15 characters, and a different kind of name from
  the one macOS and Linux give.
- `%COMPUTERNAME%`: the NetBIOS name, from a variable any program can change for what it starts.
- A name saved once per PC in its settings: it keeps a renamed PC's rules and notes, which isn't
  wanted, and it adds a setting to manage.
- The host name as typed, or in lowercase, for what people read: a change of case alone would
  start new headings in handoffs, and existing ones would need renaming.
- In commit subjects: the name after a word, such as `, from <PC>` (longer, and it reads as part
  of the description); in the area, such as `handoff(<PC>): you/tool` (it breaks the
  `<area>: <what>` form dev-home's AGENTS.md describes, and looks like a Conventional Commits
  scope); a trailer in the commit's body (GitHub's list of commits and `git log --oneline` don't
  show it); a name per PC as the commit's author (GitHub shows the linked account's login instead
  of git's name, and it would override the name the end user set).

**Look again if:** macOS or Linux support comes. Check there whether `socket.gethostname()` stays
the same from one network to another, or whether a Mac needs its `LocalHostName` (from `scutil`),
and whether capitals suit names there.
