# Options take Python's usual form

**Decision:** the Python scripts take long options with two dashes, such as `sync.py --message`
and `update.py --quiet`, each with exactly one spelling: no short forms such as `-m`, and no
shortened names such as `--mess`. Setup's are `--quiet`, `--content-dir`, `--configure`, and
`--what-if`.

**Why:** a skill's pre-approval matches a command's text literally, so a second spelling of an
option could make a command ask first. Every command's text changed in phase 2 anyway, since
`pwsh -NoProfile -File .../sync.ps1` became `<python> -I .../sync.py`.

**Option set aside:** PowerShell's form, `-Message` and `-Quiet`. Python can take it, and it
would look familiar, but it's unusual for Python and out of place on macOS and Linux.

**Look again if:** a tool the skills run in can't pass an option that starts with two dashes.
