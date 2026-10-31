# 0086: dev-home's host

**Built:** yes.

**Decision:** dev-home works only on GitHub for now. dev-home-toolkit supports no other host for
it, in code or in docs: no workaround, and no step by hand offered in place of setup. But
dev-home-toolkit will need to support at least some of GitLab, Bitbucket, and Azure DevOps later,
so every design weighs that need: build what's GitHub's own, such as a call to `gh`, so that
another host can be added beside it without reworking what's built around it. How each host
works, such as which program it needs, is decided when its support is built, not before. This
covers dev-home itself only: projects on any host already have handoffs. Decided by the developer
on 2026-10-29.

**Why:**

- Supporting a host takes more than syncing with it: setup creating and cloning dev-home there,
  signing in, filing issues, and docs, each checked on that host. A route that's only partly
  there misses what setup does for GitHub, such as turning on git's long-path option before a
  clone's checkout ([0088: Path lengths](0088-path-lengths.md)).
- The hosts differ in ways that would change a design made now. By their docs, read on
  2026-10-29: GitLab's `glab repo clone` works like `gh repo clone`, taking short names and
  passing options to git; the Azure DevOps CLI, `az repos`, has no clone command; and Atlassian's
  CLI, `acli`, has no Bitbucket commands.
- A design made only around GitHub would turn adding a host into reworking what's built on it.

**Options set aside:**

- The README's route for a dev-home on another host: clone it by hand, and setup uses it as it is
  (removed on 2026-10-29). The developer never approved it, and such a clone misses setup's
  long-path option.
- Deciding now how each host will work: the facts above may change before any host's support is
  built.

**Look again if:** the developer decides to support another host.
