# One prompt for every optional list

**Decision:** every list of optional items setup offers, recommended settings and skills now and
later lists such as example rules, is asked with one prompt: **All**, **All recommended** (the
default, which Enter takes), **None**, or **Ask for each**, where each item's question defaults to
whether it's recommended (`[Y/n]` or `[y/N]`). All is left out when it would do the same as All
recommended, and so is None: with every item recommended, `a` means All recommended, and with
none, `n` does, so a letter and Enter shown as the same are always the same answer. A list of one
asks its item's question alone. The prompt covers only the items not answered yet, and chat
offers the same four answers.

**Why:** one prompt to learn, however long the lists grow, and each new list costs only its
catalog. Someone in a hurry presses Enter, and someone careful goes through each. With every
default matching the recommendation, pressing Enter can never record a choice dev-home-tools
doesn't recommend.

**Options set aside:** a question for each item (a long run of questions as the lists grow); all
or nothing (no way to pick); and no default (a hurried Enter would only ask again).

**Look again if:** a list needs answers other than yes or no for each item.
