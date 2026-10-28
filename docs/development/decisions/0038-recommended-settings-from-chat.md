# 0038: Recommended settings from chat

**Built:** yes.

**Decision:** `setup.py --configure` can apply a recommended setting to an agent's settings file,
not only change dev-home-toolkit's own settings. With neither a console nor a setting, its
"Waiting for your answer" section lists the recommended settings with no answer yet in each Claude
Code folder set up, as it lists setup's questions about files
([0026: setup.py --configure](0026-setup-py-configure.md)): each in the same columns as setup's
question, with no diff ([0032: Recommended settings](0032-recommended-settings.md)), and the
command for a yes, with a fingerprint of the setting as the file has it now. Then the answers for
all of them at once: all recommended, none, or remind me in N days, and where only some are
recommended, all, which is each yes command in turn. The agent shows them, the
person answers in chat, and the agent runs the command the answer names, with no `--what-if`
round, since the listing was the preview. Setup writes a yes only if the setting still has that
value, with a backup as usual. Only values from the recommended-settings list can be applied this
way, never an arbitrary key, and the `dev-home` skill keeps pre-approving
`setup.py --configure *`, as the skills pre-approve their commits. The list of settings after
that section shows each one answered, with the value now where it differs from a yes, and the
commands that change it.

The commands work like a folder's (`claudeCode.folders+=`, `-=`, and `?=`), under
`claudeCode.recommendedSettings`, followed by a setting's id:

- `claudeCode.recommendedSettings.<id>+=<folder>@<fingerprint>` is yes: setup writes it, then
  saves the answer, as after a yes at a console. It takes one already answered too, which writes
  the setting again.
- `claudeCode.recommendedSettings.<id>-=<folder>` is no, answered before or not.
- `claudeCode.recommendedSettings.<id>?=<folder>@<days>` is a reminder, only for one with no yes
  or no, as for a folder. Neither a no nor a reminder writes the settings file, so neither takes
  a fingerprint.
- Without an id, each answers every one waiting in that folder. `+=` is all recommended: yes to
  each one recommended there, and no to each with a value someone chose, as Enter at a console.

The fingerprint goes at the end of the value, as `'<name>=<value>@<fingerprint>'`, as a reminder
takes `@<days>`. Like a skill's stamp, it's the first 12 hex digits of a SHA-256: here, of the
setting's value that the offer described, with the file it's from, `settings.json`, or
`.claude.json` where the offer counted that file's value, or of nothing when the setting is
missing. For all of them at once, it's of each waiting one's id with that, so a setting answered
or changed meanwhile changes it. Answers to setup's questions through `--configure` already carry
one this way ([0026: setup.py --configure](0026-setup-py-configure.md)). Changed on 2026-10-23
(its form), by the developer on 2026-10-24 (plain words in place of a diff), and by the developer
on 2026-10-28 (the commands, and the listing in place of a `--what-if` round).

**Why:** chat is where most later questions reach people, between runs of setup by hand. The
fingerprint makes a yes in chat as exact as a typed yes, as `update.py` pulls exactly the commit
it showed. If Claude Code changed the setting in between, such as through `/config`, nothing is
written. It covers only the setting, so a change elsewhere in the file, such as a sync adding the
lines a folder needs, doesn't undo the yes. The commands mirror a folder's, so one set of
operators means yes, no, and a reminder everywhere (the developer's choice, 2026-10-28). The
listing shows what waits, as it does for setup's questions about files, so a `--what-if` round
would only ask twice.

**Options set aside:** the console only (every later recommendation would need a terminal); chat
without the fingerprint (a setting changed in between could be overwritten without the person
seeing it); a diff of each file with a fingerprint of that preview (the plan until 2026-10-24;
0032 says why the offers have no diff), which a change anywhere in the file also undid; the offer
printed by `--what-if`, with the agent running the same command after a yes (the plan until
2026-10-28: a second round for what the listing already shows); and one operator, `=`, with the
answer as a word, such as `<id>=yes@<folder>@<fingerprint>` (unlike every other folder setting,
and a value with two `@` parts).

**Look again if:** an agent can show a change and take the yes itself.
