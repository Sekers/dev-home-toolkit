# 0038: Recommended settings from chat

**Built:** not yet.

**Decision:** `setup.py --configure` can apply a recommended setting to an agent's settings file,
not only change dev-home-toolkit's own settings. With `--what-if`, it prints the diff for each file
and a fingerprint of that preview. The agent shows it, the person says yes in chat, and the agent
runs the same command with the fingerprint. Setup writes only if the files still match what was
shown, with a backup as usual. Only values from the recommended-settings list can be applied this
way, never an arbitrary key, and the `dev-home` skill keeps pre-approving
`setup.py --configure *`, as the skills pre-approve their commits.

**Why:** chat is where most later questions reach people, between runs of setup by hand. The
fingerprint makes a yes in chat as exact as a typed yes, as `update.py` pulls exactly the commit
it showed. If Claude Code changed the file in between, such as through `/config`, nothing is
written.

**Options set aside:** the console only (every later recommendation would need a terminal), and
chat without the fingerprint (a changed file could be written with something the person didn't
see).

**Look again if:** an agent can show a diff and take the yes itself.
