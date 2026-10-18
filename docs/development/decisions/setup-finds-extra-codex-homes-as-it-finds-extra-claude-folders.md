# Setup finds extra Codex homes as it finds extra Claude folders

**Decision:** setup finds each `~/.codex-*` folder that holds a Codex `config.toml` or
`auth.json`, and the folder `CODEX_HOME` names when setup runs from a Codex session. Codex's one
answer covers each
([Codex is set up in every Codex home, or in none](codex-is-set-up-in-every-codex-home-or-in-none.md)),
and a yes gets it what `~/.codex` gets: the always-on rules in its `AGENTS.md`, and dev-home in
its `config.toml`. A home elsewhere can be added by its path, as an entry in `codex.homes`.

**Why:** Codex reads its folder from `CODEX_HOME`, which can point anywhere, and each home has its
own `config.toml`, `AGENTS.md`, and sign-in. Every home on a PC shares `~/.agents/skills` (Codex's
source at rust-v0.161.0), so a second home already sees dev-home-toolkit's skills, but without the
rules they depend on, and with dev-home's writes blocked by Codex's sandbox. Half set up is worse
than not set up. Finding them the same way as Claude folders keeps one rule for both,
and listing `~/.codex-*` costs about what listing `~/.claude-*` does.

**Options set aside:** adding homes by path only (most people would never learn the option
exists), and supporting `~/.codex` only.

**Look again if:** OpenAI adopts a naming convention for extra homes, or Codex's desktop app or
IDE extension turns out not to honor `CODEX_HOME`, which hasn't been checked.
