# 0038: Recommended settings from chat

**Built:** not yet.

**Decision:** `setup.py --configure` can apply a recommended setting to an agent's settings file,
not only change dev-home-toolkit's own settings. With `--what-if`, it prints the offer in the same
plain words as setup's question, with no diff
([0032: Recommended settings](0032-recommended-settings.md)), and a fingerprint of the setting as
the file has it now. The agent shows the offer, the person says yes in chat, and the agent runs
the same command with the fingerprint. Setup writes only if the setting still has that value,
with a backup as usual. Only values from the recommended-settings list can be applied this way,
never an arbitrary key, and the `dev-home` skill keeps pre-approving `setup.py --configure *`, as
the skills pre-approve their commits.

The fingerprint goes at the end of the value, as `'<name>=<value>@<fingerprint>'`, as a reminder
takes `@<days>`. Like a skill's stamp, it's the first 12 hex digits of a SHA-256: here, of the
setting's value that the offer described, as setup read it from `settings.json`, or from
`.claude.json` where the offer counted that file's value, or of nothing when the setting is
missing. Answers to setup's questions through `--configure`
already carry one this way ([0026: setup.py --configure](0026-setup-py-configure.md)). Changed on
2026-10-23 (its form), and by the developer on 2026-10-24 (plain words in place of a diff).

**Why:** chat is where most later questions reach people, between runs of setup by hand. The
fingerprint makes a yes in chat as exact as a typed yes, as `update.py` pulls exactly the commit
it showed. If Claude Code changed the setting in between, such as through `/config`, nothing is
written. It covers only the setting, so a change elsewhere in the file, such as a sync adding the
lines a folder needs, doesn't undo the yes.

**Options set aside:** the console only (every later recommendation would need a terminal); chat
without the fingerprint (a setting changed in between could be overwritten without the person
seeing it); and a diff of each file with a fingerprint of that preview (the plan until
2026-10-24; 0032 says why the offers have no diff), which a change anywhere in the file also
undid.

**Look again if:** an agent can show a change and take the yes itself.
