# Research

One page per investigation, as [Writing the docs](../writing-docs.md) says. A decision links the
research it rests on.

| Page | What's in it |
| --- | --- |
| [Skill requirements](skill-requirements.md) | What keeps a skill off a PC: why a missing program can't decide it reliably, the options weighed, and a recommended design, with the words "tool", "agent", and "program". |
| [Pylance comparison](pylance-comparison.md) | Pylance's standard and strict type checking compared on this repo's code, with the data, so it needn't be run again. |
| [claudeMdExcludes for another Claude Code folder](claude-md-excludes.md) | Tests of which `claudeMdExcludes` patterns keep `~\.claude`'s instructions out of another account's sessions on Windows, and which fail. |
| [Long paths on Windows](long-paths-on-windows.md) | Windows' 260-character path limit across every path dev-home-toolkit creates: tests of git, `gh`, Python, PowerShell, `cmd.exe`, Claude Code, and Codex with long paths, with Windows' long-path setting on and off, where each path's length comes from, the cost of checking paths at a sync, and the options for handoff paths and cloning, with what decision 0088 took. |
| [Syncing at session start](syncing-at-session-start.md) | A test of whether a session sees the rules its own start-up hook brings in, and how similar projects keep a second PC current. |
| [Handoff further files](handoff-further-files.md) | How handoffs are read and what a long one costs, tests of five ways to split a handoff into `HANDOFF.md` and further files, and the fresh-agent tests of the skill text that came out of it. |
| [Claude Code's attribution setting](claude-code-attribution.md) | What Claude Code does with `"attribution": false` when it saves another setting: a test of its CLI in two versions, what its VS Code extension and the desktop app do, and what Anthropic's changelog and settings schema say the forms mean. |
| [Test suite timings](test-suite-timings.md) | Where the tests spend their time, measured on one worker, why one worker per core doesn't shorten it much, and what would. |
