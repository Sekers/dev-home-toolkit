# Skills share text through committed copies

**Decision:** text that several of dev-home-toolkit's skills need word for word has one source, a
file in `templates/shared-skill-text/` named for what it says, such as `other-sessions.md`. It
isn't built yet.

- Each skill's template marks where a passage goes with an HTML comment, such as
  `<!-- shared: other-sessions -->`, indented to the text around it. The markers are the only
  record of which skills share which passage.
- A script in `internal/development/` copies each passage into its marked places, and the copies
  are committed. It stops and names a copy that differs from the others, so it never overwrites a
  hand edit, and after a merge conflict is settled in the shared file, it can rebuild every copy.
- A test fails when a copy differs from its source, when a marker isn't indented to the text
  around it, or when a skill lacks a passage a rule requires of it, such as every skill that
  commits through `sync.py`.
- Passages that differ on purpose, such as one naming the handoff in one skill and the knowledge
  base in another, stay as each skill words them, marked as related. The test keeps a fingerprint
  of each. When one changes, it fails and names the others, and the new fingerprint is recorded
  once they've been checked.
- A passage is whole lines. Setup removes the marker lines when it generates the skills.
- It covers only dev-home-toolkit's own skills. A person's own skills in dev-home are separate.

**The problem:** about 11 lines are the same word for word in the handoff, knowledge, and dev-home
skills, and about 15 more in the handoff and knowledge skills, with more that differ only in a
noun. Only a reminder in [skills.md](../skills.md) keeps them in line, and the planned global-rules
skill adds another copy. As skills are added, each passage may be shared by a different set of
them.

**Why:**

- A copy can't drift, a new skill can't miss a passage it needs, and the marker tells anyone
  editing a passage that it's shared.
- One file per passage, not per group of skills, so passages shared by different, overlapping
  sets of skills need nothing extra.
- Committed copies keep each template complete, so the skill pages' links show the whole skill,
  and the review AGENTS.md asks for after a change reads the template as it is. Nothing new runs
  on people's PCs except removing the markers, so the tests catch a mistake before a commit, and
  the stamp needs no change.
- The rule in [skills.md](../skills.md) that a similar rule in another skill may need the same
  change, but "never a given", stays. The fingerprints make sure each change to a related passage
  gets that check.
- Indented markers: GitHub ends a list at a marker that starts a line between its items, splitting
  it in two, while a marker indented to the item's text keeps the list whole and shows nothing
  (checked through GitHub's Markdown API, 2026-10-10).
- The folder stays in `templates/`, though only the script and the tests read it: it's skill
  text, with the same placeholders, edited along with the skills.
- Tokens: sessions using the skills load the same text as before. Sessions working on
  dev-home-toolkit read a few more lines of the rules for skills, and bigger diffs.

**What it costs:** one more thing to learn. A change to a shared passage shows up in each skill
that has it, and two branches that change the same passage conflict in each copy. A passage that
starts partway through a line needs the text around it rewrapped.

**Options set aside:**

- Setup pasting the text in on each PC: a conflict would land only in the shared file, but the
  templates on GitHub would silently lack each passage, every PC would run the pasting on every
  sync, and the stamp would have to be taken after pasting. A person's own skills, which only
  setup could reach, don't need these passages.
- A copy in each skill, kept the same by a test, with no shared files: simplest, but with more
  skills, a change means an edit in each, a failing test can't say which copy is right, and
  nothing records which skills share what.
- Moving text every skill needs into the operating rules: they load in every session, can't serve
  a passage only some skills share, and each skill has to stand on its own.
- A pointer to a shared file, or instructions in a command's output: an agent may act before
  reading the file, and a rule in a command's output is weaker than one in the skill's own text.
- Building each skill from a list of fragments: the most reuse, but no skill would read as a
  whole.

**Look again if:** merge conflicts across the copies become a regular cost, or shared text comes
along that whole lines can't hold.
