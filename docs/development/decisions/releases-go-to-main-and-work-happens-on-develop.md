# Releases go to main, and work happens on develop

**Decision:** `main` holds only releases, and day-to-day work happens on `develop`. Not built
yet: until it is, work goes to `main` as before.

- A release: on `develop`, set the version and date the changelog; open a pull request from
  `develop` into `main`, and merge it with a merge commit; tag that merge commit with the
  version; then merge `main` back into `develop`.
- End users' copies are on `main`, so their updates install releases only. `update.py` keeps
  installing what the branch's upstream holds, so this needs no new setting, and a new clone gets
  the latest release.
- A developer's copy, or anyone's who wants every change, is on `develop`, switched by hand once.
- Releases are numbered with [Semantic Versioning 2.0.0](https://semver.org/), and the first
  public release is 1.0.0. The version lives in the release data file, and the tag matches it
  ([A release data file holds the version and what end users need to know](a-release-data-file-holds-the-version-and-what-end-users-need-to-know.md)).
- The release steps, the public contract, and how to decide hard cases go in a page in
  `docs/development/` when this is built. The tags' exact form is decided then too.

**Why:** for "1.1.0 is available; you have 1.0.0" to be true, an update has to move from one
version to the next, not deliver every commit. With releases on `main`, everything an end user
touches matches the release they have: what they clone, the README they read on GitHub, and what
they update to, and `update.py` needs no new code to find releases. Merge commits, because a
GitHub pull request is merged with a merge commit, a squash, or a rebase, with no fast-forward,
and a rebase merge drops signature verification
([About merge methods on GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github),
read 2026-10-16). So a `main` that only fast-forwards would need someone to bypass its rules once
it's protected and other developers use pull requests. 1.0.0 first, because that's where
Semantic Versioning's promise starts: after it, a breaking change raises the first number.

**Options set aside:**

- Work stays on `main`, releases are tags on it, and `update.py` installs the newest tag, with a
  setting on each PC to follow `main` instead: a new clone would get unreleased commits unless its
  clone command named a tag changed at every release, the README on GitHub would describe
  unreleased changes, and `update.py` would need new code to find tags.
- A `main` that only fast-forwards to tagged commits on `develop`: fewer merges, but not
  possible through GitHub's pull requests.
- Public 0.x test versions before 1.0.0: Semantic Versioning lets anything change during 0.x, so
  early end users could get breaking updates.
- Building `develop` alone before the rest: it changes nothing for end users before 1.0.0.

**Look again if:** GitHub's pull requests gain a fast-forward merge, or releases have to be kept
up in parallel, such as fixes for an older major version.
