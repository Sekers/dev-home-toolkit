# dev-home-toolkit moves from PowerShell to Python, in phases

**Decision:** the scripts move to Python 3.12 or later, in three phases: 1. the scripts the
skills share, `facts.py` and `prepare.py`, with `prepare.py` still running `sync.ps1`; 2.
`sync.ps1` and `update.ps1`, loaded into `prepare.py`'s process; 3. `setup.ps1`, and then
PowerShell is no longer needed. No phase may add script time: measure each one against the
flow before it, and ask before anything adds time (AGENTS.md's "Speed"). All three phases are
done.

**The problem:** starting PowerShell is slow, and a `/handoff` started four PowerShell
processes: about 2.6 s on one laptop, where Python started from its full path took about
0.11 s. There, the Python facts took 0.63 s against 1.6 s for `facts.ps1`, and the flow as a
whole took about 7.8 s of script time (the sync 6.6 s, `facts.ps1` 1.2 s). On a faster PC, the
first phase's start of a `/handoff` (`prepare.py` with three topics) took 1.2 s, against 1.4 s
for `sync.ps1` and `facts.ps1` before it, in one call instead of two. PowerShell also writes and
reads in the console's code page, so an accented letter in a path or commit subject reached the
agent garbled, and fixing that took about 30 lines; Python takes one setting. And Python 3 comes
with nearly every macOS and Linux system, where PowerShell is a rare extra install.

**Python is required, never bundled:** a copy in the repo would need its own security updates,
a build for each platform, and room in every clone's history. On Windows, people install it
with the Python install manager, since the traditional installer stops with Python 3.16. The
floor is 3.12, which the tests need too (`os.path.isjunction`, and `shutil.rmtree`'s `onexc`).

**Phase 2, measured:** on the faster PC, a plain `/knowledge`'s `prepare.py` took 1.7 to 1.8 s
in place of 2.2 to 2.5 s, most of it the two GitHub fetches and setup's 0.6 s, which still started
PowerShell. A commit no longer starts PowerShell at all.

**Phase 3, measured:** on the same PC, `prepare.py` took 1.45 to 1.49 s, and setup on its own
0.16 s in place of 0.6 s. What's left is mostly the two GitHub fetches.

**Setup never waits for input nobody can give,** as `setup.ps1` never did. In Python,
`sys.stdin.isatty()` is the wrong check on Windows: it's true for the `NUL` input that agents'
commands get. So: `--quiet` never asks; it asks only when input comes from a real console and
output goes to one (`GetConsoleMode` on Windows, `isatty()` elsewhere), since Python writes a
question to the output, and output sent to a file would hide it; `EOFError` counts as no; and the
tests run setup with input from `NUL` and from an open, silent pipe.

**Phase 3, beyond the port:** setup's settings preview comes from Python's `difflib` in place
of the hand-written diff in `setup.ps1`. It shows the same "Line N:" runs with two lines of
context, and may now and then line up a change differently. And what needs a person (setup's
questions, a yes or no to a settings change, and creating dev-home with gh) now has tests, with
a fake for the person and for gh, where before it was checked only by hand.

**Look again if:** a phase can't be done without adding time.
