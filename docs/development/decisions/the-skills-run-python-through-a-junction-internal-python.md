# The skills run Python through a junction, internal/.python

**Decision:** every skill command starts with `{{PYTHON}} -I`, and setup fills in `{{PYTHON}}`
as `internal/.python/python.exe` in dev-home-toolkit's folder. `internal/.python/` is a directory
junction setup makes to the Python install manager's shortcut folder,
`%LocalAppData%\Python\bin`, or else to the folder of the newest Python 3.12 or later in the
registry (PEP 514), which covers the traditional installer. Each run checks only that the
junction's `python.exe` is there, which starts no process. Setup starts Python to check its
version only when it makes the junction, or re-points it because that `python.exe` is gone. A
symbolic link will do the same job on macOS and Linux.

**Why a junction:** dev-home-toolkit's path has no spaces, so the command is the same unquoted text
in Claude Code's Bash and PowerShell tools and in Codex, and each is pre-approved as both
`Bash(...)` and `PowerShell(...)`. Python's own path is usually under the end user's profile, which
can have a space, and a quoted path needs a different text in each tool (a probe skill showed
both tools pre-approving a Python command). Python runs normally through a junction, which added
3 to 5 ms to a start of about 32 ms.

**Why the install manager's shortcuts first:** each runs the default runtime and moves on to newer
ones as they're installed, with no work for setup. They ignore a virtual environment and a
script's request for a version, so a project's environment can't change which Python runs.

**Why `internal/`:** it's machinery nobody runs directly, which is what `internal/` is for, and
the root is kept to what must be there (see "What the root holds"). It isn't generated content,
so not `internal/.generated/`; and sync's and setup's agent commands run through it too, so not
`shared-skill-scripts/`. The dot keeps it apart from the Python code in `internal/shared/`.
Setup's cleanup of the generated files never looks inside a link, so a junction nearby can't
lead it into the Python install.

**Why `-I`:** it ignores `PYTHON*` environment variables and the end user's site-packages, so
nothing in a project's environment can change what loads. It costs no measurable time. It also
leaves the script's folder off the import path, so `prepare.py` loads `facts.py` by its path.

**The bytecode cache stays:** Python writes `__pycache__` beside the scripts, and setup leaves it
alone. Without it, compiling a 600-line module took about 8 ms on every run.

**Options set aside:**

- A `.cmd` launcher: it added about 38 ms, and cmd.exe parses arguments again, which isn't safe
  for phase 2's commit messages.
- `python` from the PATH: on Windows it goes through the Microsoft Store alias, which took about
  0.42 s to start.
- Pointing a test sandbox's Python link at the test environment's Python: a virtual
  environment's `python.exe` can't run through a junction ("failed to locate pyvenv.cfg",
  tested with uv's virtual environment and Python 3.14). The tests start the skills' commands
  with that environment's Python by its real path instead, and one test runs a command through
  the link.
- One root folder for everything that belongs to the PC (the settings, the generated files, and
  the link): a bigger change, for files that had no need to move.

**Not tested yet:** the install manager's shortcut after its runtime is uninstalled
(`py install --refresh` repairs it); a junction on a Dev Drive, which is ReFS and documented as
supporting junctions; and symbolic links on macOS and Linux.

**Look again if:** setup goes beyond Windows, or a Python the scripts need can't be reached
through a junction.
