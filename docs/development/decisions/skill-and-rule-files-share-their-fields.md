# Skill and rule files share their fields

**Decision:** a skill's `dev-home-skill.json` and a built-in rule's `dev-home-rule.json` use the
same fields for the same facts, read by one reader in `internal/shared/`. Each file holds only what
its skill or rule needs, and neither has a schema version. Decided by the developer on 2026-10-18.
Built for skills on 2026-10-21: `usedFor`, the rule for names, and the reference page's notes.
Not built yet: `summary`, which comes with the settings menu's Skills section, the first place
that shows it, and rules' files, which come with built-in rules.

| Field | Skills | Rules | What it says |
| --- | --- | --- | --- |
| `summary` | yes | yes | One line for people, shown in notices and menus |
| `recommended` | yes | yes | Whether dev-home-toolkit recommends it; `true` when left out |
| `supportedOn` | yes | yes | Where it works: an `os` entry and an `agent` entry, each with `anyOf` listing one or more names |
| `formerNames` | yes | yes | Its earlier names, so each PC's answers move to the new one |
| `dependsOn` | yes | no | What it uses: a `program` (`name`, and `usedFor`) or a `python` minimum (`atLeast`) |
| `preferences` | yes | no | Its own yes-or-no settings: `default`, `label`, `help`, `formerNames` |
| `alwaysAddedToAgents` | built-in skills only | no | Added everywhere, with no answer to change; only `dev-home` uses it |

- **Every OS:** a skill or rule for every operating system has no `os` entry. An `os` entry with an
  empty, `null`, or missing `anyOf` stays a mistake that keeps a skill off, as built, and there's
  no word such as `"any"`. The reference page says that a skill with no `os` entry works on every
  system, and that listing all three systems leaves out any other, such as Android. Likewise for
  `agent`: no entry means every agent, agents added later included.
- **No template** lists every field: each file holds only what its skill or rule needs.
- **`summary`:** one sentence of plain text, with no Markdown and no line breaks. Built-in skills
  and rules must have one of at most 80 characters, which a test checks. An end user's own skill
  may have one, which the reference page asks to keep to the same, and setup shows a longer one
  whole, with no `PROBLEM` line. Setup's menu wraps every summary under its row with a hanging
  indent, the way it wraps its other console text.
- **`usedFor`** replaces a program entry's `description`: `{ "type": "program", "name": "jira",
  "usedFor": "filing and reading Jira issues" }`. A `NEW` line or `/dev-home skills` then says
  "jira isn't on the PATH, and the skill uses it for filing and reading Jira issues".
- **Names** follow the Agent Skills standard: lowercase letters, digits, and hyphens; no hyphen at
  the start or the end, and no two in a row; matching the folder. Anthropic's reserved words,
  `anthropic` and `claude`, are ruled out too. A test checks built-in skills and rules. An end
  user's own skill that breaks the rule gets a `PROBLEM` line on every sync naming the fix, and is
  still added:

  ```text
  PROBLEM   The skill My_Notes has a name the Agent Skills standard doesn't allow: use lowercase letters, digits, and hyphens, such as "my-notes". Rename its folder and the name: line in its SKILL.md, and add "My_Notes" to formerNames in its dev-home-skill.json so your answers move with it.
  ```

  A dot in a skill's name also still stops setup saving answers for it, as built. And `synced`,
  in any case, is ruled out, and an end user's skill of that name is never added (see the change
  of 2026-10-21 below).
- **No schema version** in either file. A rule for developers covers what one would catch: a field
  never changes meaning, and a new meaning gets a new name. From 1.0.0 on, a replaced field's old
  name keeps being read, as backwards compatibility requires; before then, a rename such as
  `description` to `usedFor` is simply made. The existing handling stays: anything the reader
  doesn't know under `supportedOn` keeps a skill off, anything else is ignored, and each is named
  in a `PROBLEM` line.
- **Built-in rules' files,** which only developers write, are checked by tests, as built-in skills'
  are, so they need no `PROBLEM` lines.

**Why:**

- Shared facts behave the same way in every kind of file, and one reader handles them. The release
  data file already shares `supportedOn` and `dependsOn` with skills
  ([Skills and releases declare their requirements as facts](skills-and-releases-declare-their-requirements-as-facts.md)).
- Skills keep their OS limit. Whole skills for one OS are rare but real: counted 2026-10-18, 0 of
  Anthropic's 19 skills, 1 of OpenAI's 39 curated Codex skills, and 7 of OpenClaw's 49 bundled
  skills, all 7 also needing a program the other systems lack; and 3 of the 257 rule files in
  awesome-cursorrules are about the operating system the agent runs on. Leaving the entry out is
  how npm and OpenClaw say every system.
- "Any of" nothing is false in logic: Rust's `any()` with no predicates is false (its reference,
  read 2026-10-18), Python's `any([])` is `False`, and JSON Schema requires a non-empty `anyOf`. So
  an empty list fails safe as a mistake, and a list emptied by accident never spreads a skill onto
  every PC. npm does treat an empty `os` list, and `["any"]`, as every system (its
  `npm-install-checks` code, read 2026-10-18), but npm's field is a plain `os` list, not `anyOf`.
- `summary` is for people, while a skill's `description` in `SKILL.md` is for agents deciding when
  to use it, so it's long and full of trigger phrases. Codex splits them the same way:
  `interface.short_description` in `agents/openai.yaml` is an "Optional user-facing description",
  while matching uses `description` (its skills docs, read 2026-10-18). 80 characters keeps a
  summary readable at a glance and keeps `NEW` lines short, since agents read them. A long summary
  harms nothing, so an end user's isn't cut or reported.
- `usedFor`: in a skill's folder, "description" means `SKILL.md`'s text for agents, and an agent
  asked to fill in a program's `description` could write trigger text there. The field is what
  lets a missing program's warning say which part of the skill stops working.
- Names: the standard already has the rule, and dev-home-toolkit's skills follow it. Built-in rule
  names end up in file names such as `windows-file-names.added.md`, so a dot would break the state
  suffix. Reporting an end user's skill names the fix in one step, without changing their files or
  hiding a skill that works; and it's the least code (the developer chose it as the easiest).
- No schema version: setup never rewrites a skill file, so a version there could only make an
  older copy refuse the whole file, while reporting each unknown word names it. A rule's file is
  read only by the code in the same commit. Docker Compose made its top-level `version` obsolete
  ("only informative", with a warning if used; its docs, read 2026-10-18), and `package.json`,
  `tsconfig.json`, and Claude Code's `settings.json` carry none. Kubernetes' `apiVersion` is the
  exception, for objects a server converts between versions.

**Options set aside:**

- Dropping the OS check for skills, which the developer first wondered about and then kept.
- `"any"` for every OS, which npm accepts, as a second way to say one thing; an empty or missing
  `anyOf` meaning every OS; a template listing every field with neutral values (`"supportedOn": []`
  works but reads as "supported nowhere").
- `summary` for rules only; a skill's summary taken from its description's first sentence (those
  run long, and descriptions from elsewhere vary); no cap; cutting a long summary of the end
  user's.
- Keeping `description` for a program, or dropping the field (a warning would read as if the whole
  skill were broken).
- For an end user's skill with a name the standard doesn't allow: only the dot check, as built (the
  developer: their skills follow the rules going forward); keeping the skill off until it's renamed;
  renaming it automatically (the most code: the folder, a frontmatter edit with no YAML library,
  `formerNames`, a taken name, a change of letter case alone, which Windows needs in two steps, and
  changing an end user's files without asking).
- An optional `schemaVersion` in skill files: most people writing skills wouldn't know what number
  to write, and refusing a whole file over one new field hides the skill or drops its preferences.
- `recommended` meaning the same in the release data file: matching it there was cosmetic, since
  a release's field grades how much it matters ([A release data file holds the version and what end users need to know](a-release-data-file-holds-the-version-and-what-end-users-need-to-know.md)).

**Changed on 2026-10-21,** before any release, when the rule for names was built:

- **`synced` is ruled out,** in any case, and an end user's skill of that name is never added: setup
  gives it a `PROBLEM` line on every sync, and links it into no skills folder. Claude Code's skills
  page (read 2026-10-21) says it saves the skills it downloads from claude.ai in
  `~/.claude/skills/synced/`, and skips a skill an end user names `synced` in any capitalization.
  On a PC without that folder yet, a link setup made there would take those downloads into the
  skill's own folder in dev-home, where Claude Code's later downloads can overwrite or remove
  files. So adding it is what does the harm, unlike any other name.
- **`anthropic-skills`,** which Claude Code also skips, already breaks the rule through
  `anthropic`; its `PROBLEM` line says that Claude Code skips it too.
- **`claude` and `anthropic` stay ruled out** for every skill, the end user's included (the
  developer's choice). The same page shows that Claude Code doesn't reserve them: they come from
  Anthropic's skill authoring guide, for skills on claude.ai and its API. They stay for the same
  reason as the standard's own rule, which Claude Code doesn't enforce either: a skill that
  follows both can move to claude.ai, where Claude Code then downloads it on every PC.
- **The standard's characters** are checked as its reference validator, skills-ref, checks them
  (its `validator.py`, read 2026-10-21): after Unicode's NFKC normalizing, lowercase letters from
  any alphabet, digits, and hyphens. skills-ref checks no reserved words.
- **The `name:` line** in `SKILL.md` gets a `PROBLEM` line of its own when it's missing or
  doesn't match the folder, which the standard asks for. Claude Code's skills page says `name`
  sets the command a skill runs by, beside the folder's name.
- **`summary` waits** for the settings menu's Skills section, the first place that shows it
  (the developer's choice): nothing reads it before then.

Set aside on 2026-10-21: stopping the check for `claude` and `anthropic` in end users' skills
(fewer `PROBLEM` lines, but it treats that rule unlike the standard's, and drops the warning before
a skill moves to claude.ai); `synced` as a `PROBLEM` line only, still added (adding it is the
harm); showing `summary` now, in `/dev-home skills` and the `NEW` line (its display would be
designed twice, once now and again with the Skills section); and the rule repeated in the
starter's `AGENTS.md` (setup copies the starter once, so existing dev-homes never get it and its
copies go stale; only sessions started in dev-home load that file; and the rule's `PROBLEM` line
already says what to fix).

**This changes:**
[Skills and releases declare their requirements as facts](skills-and-releases-declare-their-requirements-as-facts.md),
for `usedFor` and for rules joining the format.

**Look again if:** the Agent Skills standard adds a requirements format or a field for people, or a
field ever needs a new meaning.
