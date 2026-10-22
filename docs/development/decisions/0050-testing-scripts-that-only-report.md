# 0050: Testing scripts that only report

**Built:** yes.

**Decision:** `facts.py` and the handoff skill's `issue_status.py` must change nothing, and reach
the network only as allowed: `issue_status.py` through `gh api graphql`, with queries that only
read. The tests check both scripts in two layers.

1. Reading the code (`find_changes_or_network_use` in `internal/development/tests/helpers.py`).
   Each module the scripts may import has a list of the names they may use from it
   (`REPORTING_NAMES`), such as `json` only as `json.loads` and `json.dumps`. Any other name
   fails, and so does any other use of the module, such as passing it to a function or giving it
   another name. Three names can hand out more than they look, so each is allowed only where it
   can't: `sys.modules` to save a module (`sys.modules[name] = module`), `ctypes.WinDLL` to call
   a function in `DLL_CALLS` at once, and `os.environ` read in place, such as
   `os.environ.get(name)`. A method called on an object, such as `text.split()` or
   `path.read_text()`, must be in a list of allowed methods (`REPORTING_METHODS`). An attribute
   read without a call, such as `done.returncode`, must be one of those methods, in a list of
   Python's own data attributes (`REPORTING_ATTRIBUTES`), or a name the script, or a script it
   loads, defines itself, such as a field of its own dataclass; so a method can't be used by
   reference, as in `map(Path.unlink, files)`. Any mention of `open`, `exec`, `getattr`, and
   the like fails, not only a call. Each script may
   start only its own programs, `facts.py` git and `issue_status.py` git and `gh`, each through
   one function: `run_git`, with a command in `GIT_READS`, and `run_gh`, as
   `gh api graphql -f query=<the query>`, so the query is in the command, never in a file.
   Adding a name to a list is a safety change, and its commit says so.
2. Watching the runs. Every run of either script as a process of its own, through the tests'
   `run_command`, goes through `internal/development/tests/read_only_launcher.py`, which turns on
   Python's audit hooks. Every kind of audit event is sorted into one of three groups:
   - harmless, such as `import` or `os.listdir`
   - checked by its arguments, such as `open`, which may read but not write;
     `subprocess.Popen`, which may start only the script's own programs, doing only what they
     may; and `ctypes.dlsym`, which may look up only the functions in `DLL_CALLS`
   - forbidden, such as removing a file, changing an environment variable, or anything that
     reaches the network

   The run stops, failing the test, at a forbidden event, a checked one whose arguments aren't
   allowed, or a kind that isn't sorted yet. The failure for an unsorted kind names it and says
   how to sort it. Sorting a kind as harmless is a safety change, and its commit says so.
   Python's own writes to `__pycache__` are allowed, and watching stops when the script ends.
   The tests that run `issue_status.py`'s code with `gh` faked fail on any query that isn't a
   read.

**Why:**

- A skill pre-approves these scripts, so they run without asking, and anything they changed
  would change without anyone seeing it first.
- Each layer catches what the other misses. Reading the code can't follow a module passed around
  at run time, or tell what an object's method does, which is why it allows only the methods it
  lists. The audit hooks see what a call actually does, but only what the tests make a script
  do.
- A list of names for every module, rather than a list of allowed modules, closes the gap that
  let `io` through: importing `io` changes nothing, so the whole module was allowed, and
  `io.FileIO(path, "w")` would have passed.
- Both layers allow only what they list, and fail on anything else, as a check on a
  pre-approved script should. A new method or kind of event costs a developer one line, and a
  missed risk could cost end users their files.
- An unsorted kind of event fails, rather than passing, so the watcher fails closed. PEP 578
  built audit hooks for detecting, not preventing, and a comment on Python's tracker notes that
  a check that only forbids known events can't be complete; failing on what isn't sorted is what
  makes them dependable here. The cost falls on developers only: a new Python version, or a first
  run on another operating system, can fail the tests until its new kinds are sorted, a one-line
  change each.
- What reading the code still can't see: a name the script defines is allowed as any object's
  attribute, so a field named like a method that writes would let that method through; and
  `issue_status.py` loads `facts.py` by a path the check doesn't follow, so it could load
  another file the same way. The watcher sees both at run time, on the lines the tests run.
- The hooks run in a process of their own, the launcher's, because an audit hook can't be
  removed once added: in the test process, it would watch pytest too.
- Tested on Python 3.14.7 on 2026-10-10, where the hooks reported `io.FileIO` opened for
  writing, `os.open`, `Path.write_text`, `os.remove`, `subprocess.Popen`, and `socket.connect`.
  Tested again on Python 3.14.8 on 2026-10-14:
  - On Windows, `subprocess.Popen`'s event gives the command line subprocess builds rather than
    a list of words, so the launcher splits it back into words the way Windows does.
  - A normal run of `facts.py` raises about 16 kinds of event, and coverage adds two.
  - Python's table of audit events, which says it lists them all, has no entry for
    `_thread.start_joinable_thread`, which subprocess raises there. So the sorted kinds come
    from real runs, not the documentation.

**Options set aside:**

- Forbidding only risky kinds of event, and letting everything else through: the watcher's
  first design, until 2026-10-14. It fails open. Probes found three ways to write a file that its list missed,
  `_winapi.CreateFile`, `sqlite3.connect`, and `_winapi.CopyFile2` (which `Path.copy` uses on
  Windows).
- A list of methods that write files: what the code check used until 2026-10-14. It fails open, and Python 3.14's `Path.copy`, `copy_into`, `move`, and `move_into` weren't on
  it, so `Path.copy` got past both layers.
- Allowing only listed kinds, with no forbidden group: an unlisted kind would fail with no hint
  of whether it's risky. The forbidden group gives each known risk its own reason.
- Name lists only for modules that can touch files or the network: sorting modules that way is
  how `io` slipped through.
- Only one of the two layers: each leaves the other's gaps open.
- Comparing the sandbox's files before and after each run: it would also catch writes by the
  programs a script starts, but the code check already limits those to commands that only read,
  and it misses the network and anything outside the sandbox.
- Running the tests inside an operating system's sandbox, with a read-only file system and no
  network: the established way to make sure code can't change anything, and the one that would
  catch everything. But as of October 2026, the Windows options are alpha or experimental, or
  need administrator setup and new software, it needs separate work for each operating system,
  and macOS's `sandbox-exec` is deprecated.

**Look again if:** a cross-platform operating system sandbox works on Windows without
administrator setup and is no longer alpha or experimental: then the tests should run these
scripts inside it. And if a skill pre-approves another script that should only report, add it to
`PROGRAMS` in the launcher, and to the test that reads the scripts' code.
