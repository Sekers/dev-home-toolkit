# Claude Code's attribution setting

On 2026-11-11, these checks looked at what Claude Code does with `"attribution": false` in a
settings file when it saves another setting there, and what Anthropic says the two forms of the
setting mean. They are the evidence for how
[0032: Recommended settings](../decisions/0032-recommended-settings.md) writes attribution. Each
item says whether it was tested or only read.

## Results

- **Tested: the CLI replaces `false` when it saves a user setting.** Claude Code 2.1.322 (the copy
  inside the VS Code extension of the same version) and 2.1.321 (the copy the Claude desktop app
  5.1231.2 keeps for its Code tab) each saved an effort level into a settings file that held
  `"attribution": false`. Afterwards the file held
  `"attribution": {"commit": "", "pr": "", "sessionUrl": false}`, and the other keys were kept.
  Both versions did the same.
- **Read in 2.1.322's code, not run: why.** Its settings parser turns `false` into exactly that
  object, and `true` into `{}`. The test shows the CLI writes back what it parsed; the writer's
  own code wasn't read. Its writer for the user settings file is called from 56 places, for keys
  such as `model`, `permissions`, `fastMode`, `switchModelsOnFlag`, and `language`. The effort
  level goes through the same function from `/effort`, from `/model` when it carries an effort,
  and from the request the test sent.
- **Read in the VS Code extension 2.1.322's code, not run.** The extension saves the effort level
  by sending the CLI that request, so it replaces `false` too. For the switches in its own panel,
  `switchModelsOnFlag`, `remoteControlAtStartup`, and fast mode, it writes the file itself: it
  reads it as plain JSON, sets only the keys it was given, and writes every other value back as
  the file had it, with its own spacing, so those keep `false`.
- **Read in the Claude desktop app 5.1231.2's code, not run.** It saves no Claude Code settings
  itself: the only mention of the Agent SDK's call for saving them is its definition, and it
  mentions flag settings (`apply_flag_settings`), which the CLI applies to a running session
  without saving, 49 times. The writes found near its mentions of `settings.json` go to its own
  files, such as `cowork_settings.json`. The CLI it runs replaces `false` as above when that CLI
  saves a setting.
- **Anthropic's own text.** Claude Code's changelog, in its GitHub repository (read 2026-11-11):
  - 2.1.183: "Added `attribution.sessionUrl` setting to omit the claude.ai session link from
    commits and PRs in web and Remote Control sessions"
  - 2.1.281: "Added `"attribution": false` in `settings.json` to hide all commit and PR
    attribution; older CLI versions skip a settings file that holds it, so keep the object form in
    files shared across versions"

  The settings schema in 2.1.322 says: "Set to false to hide all attribution, the same as {
  "commit": "", "pr": "", "sessionUrl": false }. Setting it to true is the same as leaving it out.
  Older Claude Code versions reject true or false here, so use the object form in settings files
  shared across versions." For `sessionUrl` it says "(default: true)", and "Set to false to omit
  the Claude-Session trailer and PR-body link". Its message for a value it can't use still gives
  the two-part form as its example: "Expected false, true, or an object such as { "commit": "",
  "pr": "" }".
- **No report of it.** A search of the issues in `anthropics/claude-code` (2026-11-11) found none
  about the writer replacing `false`. A related open issue,
  [#88113](https://github.com/anthropics/claude-code/issues/88113), "settings.json writes silently
  strip unknown keys from hook groups and hook items", reports what looks like the same behavior:
  the writer dropping what it doesn't parse when it saves. Whether it's the same code wasn't
  checked.

## How it was run

Claude Code's CLI ran with `CLAUDE_CONFIG_DIR` set to a scratch folder, so no real settings were
read or changed, and with `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`. The folder's
`settings.json` held `{"attribution": false, "feedbackSurveyRate": 0}`. The CLI started in a
scratch project folder as
`claude -p --input-format stream-json --output-format stream-json --verbose`, and got two control
requests on its input: `initialize`, then
`{"subtype": "update_settings", "source": "userSettings", "settings": {"effortLevel": "high"}}`,
the request the VS Code extension sends to save an effort level. The CLI answered both with
`success`, and the settings file was read afterwards. It saved the effort level under
`modelSettings`, for the session's model.

The code was read by searching each program's bundled JavaScript for the names above: the CLI's
`claude.exe`, the extension's `extension.js`, and the desktop app's `app.asar`.

## Limits

- Windows only, and only Claude Code 2.1.321 and 2.1.322.
- One save was tested, the effort level. The other 55 calls to the same writer were read, not
  run.
- `/effort` and `/model` typed in an interactive session weren't run. The code shows they call
  the function the test went through.
- The extension's and the desktop app's own writes were read in their code, not run.

## When to redo it

When Claude Code's changelog adds, removes, or changes a part of `attribution`, or says its
settings writer keeps a file's own values, as a fix for #88113 might. Decision 0032 names the
first under "Look again if".
