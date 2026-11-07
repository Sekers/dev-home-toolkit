# 0092: Decision drafts

**Built:** yes.

**Decision:** in a project whose AGENTS.md says where it records its decisions, a design that's
decided but not built yet goes into a further file beside the handoff
([0091: Further files](0091-further-files.md)), whatever its length, written in that project's
decision format with its reasons and the options set aside, so it can move into the project with
only its number to add. Its To do item keeps a summary and the link. Once it's built, its
**Built:** line says so. When it's built, or earlier when the person asks, an update offers, after
committing, to move it into the project, showing the exact text and where it goes:

- On a yes, the project is edited (committing it follows the project's own rules), and the item
  and its draft are removed and committed.
- On a no, the draft stays, and its item moves to Private notes, starting with the design's title,
  saying it's built and the person chose to keep its decision out of the project, with any issue
  link after "See also:", so the closed issue doesn't bring the offer back.
- With no answer, nothing changes, and a later update asks again.

An item filed as a GitHub issue keeps its draft whole, and when that issue closes as completed, the
item stays, saying the design is built, until the offer is answered. Reasons that must stay private
go into the handoff, not the project. Decided by the developer on 2026-11-07.

**Why:**

- Written once, in its final form: moving it is a file move, not a rewrite of handoff notes into a
  decision, which was easy to forget at build time.
- Private until built, with no approval round or project commit for each decision while the design
  is still settling. A dropped plan is just deleted.
- It's simply the item's further file, so it needs no layout of its own.

**Costs:** other developers can't see planned designs until they move. "Earlier when the person
asks" covers a plan that should be public sooner.

**Options set aside:**

- Keeping the design in the handoff's own words until built, as before: it gets written twice.
- A decision file marked "Built: not yet" in the project right away (proposed on 2026-10-23): an
  approval round and a project commit for each decision, and plans public before they're built.

**Look again if:** other developers work on a project and need to see its planned designs.
