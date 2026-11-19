# 0017: Command-line options

**Built:** yes.

**Decision:** the Python scripts take long options with two dashes, such as `sync.py --message`
and `update.py --quiet`, each with exactly one spelling: no short forms such as `-m`, and no
shortened names such as `--mess`. Setup's are `--quiet`, `--content-dir`, `--configure`, and
`--what-if`.

**Why:** one spelling keeps the skills, the docs, and the tests to one form of each command. And
since the skills pre-approve each script with any arguments
([0094: Pre-approved commands](0094-pre-approved-commands.md)), a script that refuses every
spelling but the one listed here never acts on an option an agent guessed at. Every command's
text changed in phase 2 anyway, since `pwsh -NoProfile -File .../sync.ps1` became
`<python> -I .../sync.py`.

**Option set aside:** PowerShell's form, `-Message` and `-Quiet`. Python can take it, and it
would look familiar, but it's unusual for Python and out of place on macOS and Linux.

**Look again if:** an agent the skills run in can't pass an option that starts with two dashes.
