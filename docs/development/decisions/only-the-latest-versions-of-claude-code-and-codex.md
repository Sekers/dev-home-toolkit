# Only the latest versions of Claude Code and Codex

**Decision:** dev-home-toolkit builds on what the latest versions of Claude Code and Codex read
and document, in every current form that reads what it sets up, and carries no workaround or
fallback for an older version.

**Why:** both agents change their settings and features often. Keeping older versions working
would mean checking each setting against versions nobody here runs, and keeping code and docs
for cases that go away as people update.

**Look again if:** people use dev-home-toolkit where an agent can't update, such as a managed PC
whose admin holds versions back.
