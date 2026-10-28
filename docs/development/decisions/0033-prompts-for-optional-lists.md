# 0033: Prompts for optional lists

**Built:** yes, except: the list of skills, which isn't built. Claude Code folders and recommended
settings are asked through it.

**Decision:** every list of optional items setup offers, recommended settings and skills now and
later lists such as built-in rules, is asked with one prompt: **All**, **All recommended** (the
default, which Enter takes), **None**, or **Ask for each**, where each item's question defaults to
whether it's recommended (`[Y/n]` or `[y/N]`); whether a recommended setting is recommended for a
folder depends on what that folder's settings have now
([0032: Recommended settings](0032-recommended-settings.md)). All is left out when it would do
the same as All recommended, and so is None: with every item recommended, `a` means All
recommended, and with none, `n` does, so a letter and Enter shown as the same are always the
same answer. The prompt also takes `s`, to skip every item for now, or a number of days, for a
reminder about every item, and Ask for each asks each item the same: yes, no, skip, or a number
of days. A list of one asks those for its item. Setup says back the date a number gives, as
`Setup asks again from YYYY-MM-DD.`, so a typo shows at once. What skip and a reminder save is
each list's own; for a folder, see [0049: Answers in the settings](0049-answers-in-the-settings.md). In the settings
menu, the question about an item that has a reminder offers no skip: Enter keeps the reminder
there, which is what saying nothing does. The prompt covers only the items not answered yet, and
chat offers the same answers. A list may show rows about each item under its name, such as a
recommended setting's value now, in a column of their own, and may name its own marks for an
item that's recommended or not: the recommended settings' list marks one with a value someone
chose as "your own value, which Enter keeps", since every item in it is a recommended setting.
Changed on 2026-10-20, with skip and the reminders that
[0040: Answers to offers](0040-answers-to-offers.md) set out, by the developer on 2026-10-24 (a
recommended setting's default depends on the file), and on 2026-10-28 (rows and marks of a list's
own).

**Why:** one prompt to learn, however long the lists grow, and each new list costs only its
catalog. Someone in a hurry presses Enter, and someone careful goes through each. With every
default matching the recommendation, pressing Enter can never record a choice dev-home-toolkit
doesn't recommend. A number of days is typed straight in: one step, and a number can't clash with
a letter, as `r` already means the recommended ones in a mixed list. The developer's choice.

**Options set aside:** a question for each item (a long run of questions as the lists grow); all
or nothing (no way to pick); no default (a hurried Enter would only ask again); and, for a
reminder, a letter for later, then a question asking how many days (two steps, and one more
letter to learn).

**Look again if:** a list needs answers other than these for each item.
