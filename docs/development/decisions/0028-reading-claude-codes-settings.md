# 0028: Reading Claude Code's settings

**Built:** yes.

**Decision:** setup reads a Claude Code `settings.json` as strict JSON, and doesn't edit one it
can't read that way, such as one with a comment or a trailing comma; it prints what to add by
hand instead.

**Why:** Claude Code's settings docs say settings files are strict JSON, and a `//` comment or a
trailing comma is a syntax error: an interactive session reports a Settings Error, and a `-p` run
skips the file (read 2026-10-11). So a file with comments is already broken for Claude Code, and
keeping its comments would serve nothing.

**Options set aside:** a text edit that inserts only the new lines, so comments survive (more code
for a file Claude Code rejects anyway).

**Look again if:** Claude Code starts accepting comments in its settings files.
