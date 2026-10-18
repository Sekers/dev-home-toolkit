# dev-home-toolkit updates install themselves unless you say no

**Decision:** `updates.installAutomatically` defaults to yes: a PC that hasn't answered installs
dev-home-toolkit updates at its next sync, as one that answered yes does. Setup asks about it with
yes, no, or default, as every yes-or-no setting with a default is asked, so Enter on a first run
follows the default. A settings file that `update.py` can't read installs nothing, whatever the default.

**Why:** almost every app updates itself this way, and an end user who installs dev-home-toolkit
already trusts its publisher with code that runs on their PC. Fixes then reach every PC without
anyone remembering to run `update.py`, and someone who wants to look at each update first answers
no. A settings file that can't be read means something has gone wrong on that PC, so nothing is
installed there. A sync stops before its update check when it can't read the file, so this
matters only if the file breaks between the two reads.

**Options set aside:**

- No as the default, as before: updates waited until someone ran `update.py`. The README's reason
  for it, that whoever controls this repo on GitHub controls code that runs on the PC, holds
  whichever way a PC answers, so the README now says it beside how to turn updates off.
- Treating a settings file that can't be read as missing, so the default installs: it would
  install code on a PC whose settings are broken.

**Look again if:** dev-home-toolkit gains a check that an update comes from its publisher, such as
a signature, or an update ever breaks the PCs that followed the default.
