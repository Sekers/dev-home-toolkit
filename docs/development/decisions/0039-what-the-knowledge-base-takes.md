# 0039: What the knowledge base takes

**Built:** yes.

**Decision:** a fact belongs in the knowledge base when it helps any project that uses the same
language, platform, program, extension, library, or service, whoever makes it, the person's own
projects included, and it names no tenant, personal path, or other private detail. Judge the fact,
not the project where it came up. What only helps work on one project's own code (its internals, its
tests, why it was built that way) goes where that project's AGENTS.md says research goes. When a
finding is a normal docs item for a project whose docs the person can change, their own or one they
contribute to, the candidate asks whether it goes in those docs instead. A minor note that would
clutter the docs goes in the knowledge base without asking.

**Why:** the old general test ("still true in a brand-new project, and names none of your
functions, files, or tenants") shut out a person's own module even when other projects use it,
and read as if a fact that came up in one project belonged to that project, though facts about
someone else's SDK were already in the knowledge base. Ownership alone doesn't decide where a
fact goes: a person's repos can be shared, and they can be an author on someone else's. A
project's docs are the better home for what its users need, since they change with the code and
reach every user, but minor notes there confuse readers.

**Options set aside:** always the project's docs (minor notes clutter them); always the
knowledge base (a fact that belongs in the docs never reaches the project's other users, and the
copy goes stale when the project changes); and the old test (a person's shared modules stay out).

**Look again if:** facts about a person's own projects go stale in the knowledge base as those
projects change.
