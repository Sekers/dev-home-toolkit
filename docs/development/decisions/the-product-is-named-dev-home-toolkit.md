# The product is named dev-home-toolkit

**Decision:** the public tooling is named dev-home-toolkit; it was dev-home-tools until 2026-10-17.
The name covers the GitHub repo, the folder each PC clones it into, and every file that names it,
including the code's names for the toolkit's folder, such as `TOOLKIT_ROOT` and the placeholder
`{{TOOLKIT_DIR}}`. Each person's private repo keeps its name, dev-home. Decided by the developer
on 2026-10-17.

- GitHub redirects a renamed repo's old address, so `git clone`, `git fetch`, and `git push` to it
  keep working, and a clone made under the old name keeps getting updates. GitHub recommends
  pointing each clone at the new address with `git remote set-url`, and warns that a new repo
  given the old name breaks the redirect
  ([Renaming a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository),
  read 2026-10-17).
- A copy whose folder still has the old name keeps working, since setup finds every path from its
  own folder. After the folder moves, a run of setup replaces each link whose target is gone.
- On 2026-10-17, no GitHub repo was named dev-home-toolkit, and PyPI had no project named
  dev-home-toolkit or dev-home-tools.

**Why:**

- "Tool" means at least four things in this repo, and the glossary keeps "tools" for development
  tools ([Skill requirements](../research/skill-requirements.md), "Words: tool, agent, program").
  dev-home-tools was the one name with "tools" in it outside development tools: a word search for
  "tool" matched inside it 338 times in 73 files on 2026-10-17, so the glossary's test would have
  needed an exception for it.
- "dev-home-tools'" is an awkward possessive.
- Before the first public release, a rename costs only the developer's own PCs. It comes before
  the glossary and the rest of setup's new order, so text approved word for word is written once,
  in its final name.

**Options set aside:**

- **Keeping dev-home-tools:** the awkward possessive, and the one name containing "tools" outside
  development tools.
- **dev-home-kit:** "kit" is unclear to many people.
- **dev-home-manager:** suggests an app with a window.
- **dev-home-keeper:** set aside in the same discussion; no reason was recorded.
- **A name for one job, such as dev-home-setup:** it names only one of the things the toolkit
  does.

**Look again if:** a project with a confusingly similar name turns up. After the first public
release, a rename also reaches every end user's folder and settings, so it costs far more than it
did here.
