# Research

One page per investigation, as [Writing the docs](../writing-docs.md) says. A decision links the
research it rests on.

| Page | What's in it |
| --- | --- |
| [Skill requirements](skill-requirements.md) | What keeps a skill off a PC: why a missing program can't decide it reliably, the options weighed, and a recommended design, with the words "tool", "agent", and "program". |
| [Pylance comparison](pylance-comparison.md) | Pylance's standard and strict type checking compared on this repo's code, with the data, so it needn't be run again. |
| [claudeMdExcludes for another Claude Code folder](claude-md-excludes.md) | Tests of which `claudeMdExcludes` patterns keep `~\.claude`'s instructions out of another account's sessions on Windows, and which fail. |
| [Long paths on Windows](long-paths-on-windows.md) | Windows' 260-character path limit across every path dev-home-toolkit creates: tests of git, `gh`, Python, PowerShell, and Claude Code with long paths, where each path's length comes from, and the options for handoff paths and cloning, not yet decided. |
| [Syncing at session start](syncing-at-session-start.md) | A test of whether a session sees the rules its own start-up hook brings in, and how similar projects keep a second PC current. |
