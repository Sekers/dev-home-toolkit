# Further files

A handoff keeps a long item's details in a further file beside `HANDOFF.md`, so that a session
reads them only when its work needs them. These rules hold for every handoff.

## When an item moves

- Once an item in any section but Next up and the State line passes about 100 words, move its
  details into a file of its own, and leave in its place a summary of at most about 40 words:
  what it is, where it stands, and what's next.
- The summary keeps, word for word, the item's opening words (other items refer to it by them),
  and any label, prefix, issue link, or issue mark it has, such as "For the user:", "Decide
  whether", or `(Issue: remind me)`. It also keeps every rule a session must always follow, such
  as "never mention ..." or "ask before ...", in the item's own words, with enough around it to
  make sense, on top of the 40.
- End the summary with `([details](<file>))`, before any "See also:" link or issue mark.
- An item stays moved until it's finished, even if it shrinks. Filing one as a GitHub issue
  changes it as the skill's "GitHub issues" says.
- An environment's subsection moves the same way once it passes about 100 words: its facts go
  to its own file. Under its heading stays a summary of at most about 40 words, naming what a
  session running something there needs most, plus every rule a session must always follow
  there.

## The file

- Name an item's file from its title or opening words, in lowercase letters, digits, and
  hyphens, cut so the name, with `.md`, is at most 60 characters, such as
  `build-further-files.md`. Add `-2` when that name is taken. When an item says which part of
  the repo it's about, such as one script in a repo of several, start its file's name with that
  part's name, such as `report-builder-csv-export.md`.
- An environment's file is named `environment-<name>.md` instead, with the name as its heading
  writes it, and each character other than a letter, digit, or hyphen written as a hyphen, such
  as `environment-WORK-PC.md`. It's cut to 60 characters too.
- Never rename a file once made. Every file sits in the handoff's own folder, never in a
  subfolder.
- Start the file with the item's title as a `#` heading, then its details.

## Keeping them right

- Read an item's file before changing the item. When you change either the file or its
  summary, check the other, including that the summary keeps every rule the file says always to
  follow.
- In an update, search the files you didn't read for what this session changed, such as the
  names of files, settings, branches, or decisions, and fix what that made wrong. When you find
  a summary and its file disagreeing, fix whichever is out of date, and ask when you can't tell.
- When an item is finished and removed, delete its file too. A decision draft's item stays,
  saying the design is built, until the offer below is answered.
- Commit every file you added, changed, or deleted, by naming each one after the handoff in step
  5 of "Changing the handoff".

## Decisions not built yet

In a project whose AGENTS.md says where it records its decisions, a decided design that isn't
built yet goes into a file of its own, whatever its length, written in that project's decision
format, with its reasons and the options set aside, so that it can move there with only its
number to add. Its To do item keeps the summary and the link. Once it's built, say so in it, as
the project's format does, such as in a **Built:** line.

When it's built, or earlier when the user asks, offer after committing to move it into the
project: show the exact text and where it goes, and edit the project only after a yes; then
remove its item, delete the file, and commit that. On a no, keep the file, move its item to
Private notes, starting with the design's title and saying the design is built and the user
chose to keep its decision out of the project, with any issue link moved after "See also:", and
commit that. With no answer, change nothing, and a later update asks again. Reasons that must
stay private go into the handoff, not the project.
