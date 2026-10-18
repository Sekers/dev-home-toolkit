# Offers use the same answers

**Decision:** every question that offers something a person can take or turn down uses the same
answers, built and planned offers alike: issue and knowledge candidates, setup's optional lists
(skills, recommended settings, example rules), the `NEW` line, dev-home-toolkit updates, starter
updates, and copied skills. Two terms:

- **Session:** one conversation with an agent. A new conversation, or `/clear`, starts a new
  one; resuming a conversation continues it. At a terminal, one run of setup is one session.
- **Trigger:** the moment a question comes up, which each offer defines, such as a
  `/handoff update` in which the session changed the item, or every session until answered for
  a `NEW` line.

| Answer | Remembered | Asked again |
| --- | --- | --- |
| Yes, in the offer's own words, such as "Create a GitHub issue for it" | It's done | Never, for that item |
| Skip (no reminder) | Nothing | Not in this session; later only when its trigger fires again |
| Remind me next session | Yes | The first time it comes up in a later session |
| Remind me in N days | Yes, with the date | The first time it comes up on or after that date |
| No (never ask again) | Yes | Never, for that item; for an item with versions, a newer version is a new offer |

- The yes answer says what it does and where, never only a verb such as "File it".
- Nothing is asked twice in one session, whatever the answer. Saying nothing changes nothing, not
  even an earlier answer: a reminder that's due stays due, so a later session asks again. Skip,
  by contrast, ends a reminder.
- A list of items of one type adds All, All recommended (when items have recommendations),
  None, and Ask for each, which asks the answers above for each item. Skip and the reminders
  can also answer the whole list. Items of different types are never in one list: each type
  gets its own question.
- A question lists only the answers that do something different for it, each with its note in
  parentheses, so it explains itself. A `NEW` line comes back every session anyway, so it offers
  no "remind me next session". That's part of the standard, not a departure.

**Departure:** approving exact text, such as a draft's "Save, commit, and push this?" or a
settings diff's typed yes, stays yes or no. It's one change shown once, not an offer that comes
back.

**Departure,** decided 2026-10-16: the `NEW` line for a new skill is a notice, not an offer. The
skill already works at its default, so the line says once what happened and how to change it,
with no answers, as a new preference gets no line at all
([New items reach the person at a terminal, or in a NEW line](new-items-reach-the-person-at-a-terminal-or-in-a-new-line.md)).
A folder setup hasn't asked about is still an offer, with the answers above, so a folder can now
hold a reminder ([Settings record answers, not just values](settings-record-answers-not-just-values.md)).

**Why:** the offers grew one at a time, with different words for the same idea ("decide later",
"remind me later", "skip this version"), and "later" never said when. Defining each answer by
what's remembered and when it comes back makes every question mean the same thing. One type per
list keeps a quick "All" from accepting something the person didn't look at.

**This changes:**

- "One prompt for every optional list": it gains skip and the reminders, and different types
  are asked separately.
- "New items reach the person at a terminal, or in a NEW line": one answer covers a batch of one
  type.
- Issue candidates: "File it, decide later, or no?" becomes these answers.
- Knowledge candidates: they gain the reminders and a remembered no, where a no now lasts only
  for the session and nothing records it. Both need a record in dev-home of the finding and its
  evidence; where is decided when it's built.

**Options set aside:** a "later" with no time (nobody can tell when it comes back); "not now"
beside "remind me later" (both sound like a reminder will come); one answer for a list of mixed
types.

**Look again if:** an offer needs an answer these don't cover.
