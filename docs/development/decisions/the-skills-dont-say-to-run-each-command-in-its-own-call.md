# The skills don't say to run each command in its own call

**Decision:** no such rule.

**The problem:** agents joined the commands a skill gave them, such as `sync.ps1; facts.ps1`,
although the skill said to run them exactly as written. A joined call asks the end user first when
any part of it isn't pre-approved.

**Why not:** a joined call whose parts are all pre-approved runs without asking (seen in Claude
Code 2.1.286), so joining isn't what causes a prompt: an unapproved part is. The fix for that is
a pre-approved way to get what the agent wanted, which is how the facts came to include the
computer's name. Running two commands in one call also saves a round trip. Since then, every
skill command that syncs starts with one script anyway (see
[Every skill command that syncs starts with one call: prepare.py](every-skill-command-that-syncs-starts-with-one-call-prepare-py.md)).

**Look again if:** an agent starts asking about joined commands whose parts are all pre-approved.
