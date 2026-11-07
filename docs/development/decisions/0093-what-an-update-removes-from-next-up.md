# 0093: What an update removes from Next up

**Built:** yes.

**Decision:** Next up is the person's plan in their words: only they add to it or reword it, through
`/handoff next` or the text of `/handoff update`. An update removes from it, without asking, what's
finished, even when that's only part of a step: what its session finished, or confirmed finished
from the project itself, such as in commits it brought in, the code, or an issue closed as
completed. It keeps the rest as written, apart from list numbers, and leaves what it's unsure of,
such as work done but not yet checked, or a commit that may cover only part of a step. After
committing, it quotes what it removed, says what it left because it was unsure, and says that
`/handoff next` changes it. Text after `/handoff update`, such as "keep next up", still decides.
There's no setting. Decided by the developer on 2026-11-07, replacing the question "Next up looks
done: clear it?".

**Why:**

- The question was answered yes 6 times in 7, and the seventh asked for a recommendation, in
  transcripts from 2026-10-02 to 2026-11-04. It was never answered no.
- One fewer question and turn on those updates, and Next up stays current when nobody answers:
  with the question, no answer left finished work for the next session to start on.
- An audit's update rarely has a question to hold back without it
  ([0042: /handoff audit](0042-handoff-audit.md)).
- Work confirmed finished from the project, not only the session's own: in tests, a step a
  contributor finished, in a commit the session pulled, stayed in Next up, against the update's
  rule to remove what's finished everywhere else.
- Removing part of a step: in tests, an agent kept a half-finished step whole, so the next session
  would have started by adding something that already existed.

**Costs:** a wrong removal hides the person's plan until they read the update's report. The report
quotes what was removed, git keeps it, and `/handoff next` restores it.

**Options set aside:**

- Keeping the question.
- A setting for asking: a per-PC setting for a file every PC shares, skill text for both
  behaviors, and tests and docs for both, while the text after `/handoff update` already covers an
  exception.
- Removing only the session's own work: steps finished elsewhere stay.
- Asking only about work finished elsewhere: the question comes back for a rare case.

**Look again if:** people often restore removed steps.
