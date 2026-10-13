# Folders for what several skills share

**Decision:** one skill's files live in its own folder under `templates/skills/`, and what
several skills share lives in a `templates/shared-skill-*` folder for its kind:
`templates/shared-skill-scripts/` for scripts, which setup fills in and installs, and
`templates/shared-skill-text/` for instruction text several skills need word for word, which a
development script copies into the skills' templates (see "Skills share text through committed
copies").

**Why sibling folders, not one folder with `scripts/` and `text/` inside:** setup installs the
scripts and never reads the text, so each folder keeps one job, with no extra layer and shorter
command paths. "shared" is in both names because `skill-scripts` read as every skill's scripts,
and "skill" keeps them apart from `internal/shared/`, the code behind the scripts in the root,
which `prepare.py` loads the sync from too.

**Look again if:** a third kind of shared file comes along that doesn't fit either.
