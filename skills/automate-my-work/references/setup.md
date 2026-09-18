# Setup — probe, nudge, install, verify

Goal: the user never opens a download page. You detect, you offer in one
sentence what it unlocks, you install, you verify, you report.

## Probe (run first, every time the skill starts)

One command per OS; read the output, do not show it to the user.

**Windows (PowerShell)**
```powershell
foreach ($c in 'uv','python','node','npm','git','winget','choco') { "$c=" + (Get-Command $c -ErrorAction SilentlyContinue).Version }
"pw=" + (Test-Path "$env:LOCALAPPDATA\ms-playwright"); "browsers=" + ((Get-ItemProperty 'HKLM:\SOFTWARE\Clients\StartMenuInternet\*' -EA 0).'(default)' -join ',')
```
**macOS / Linux**
```bash
for c in uv python3 node npm git brew; do printf '%s=' $c; command -v $c >/dev/null && $c --version 2>&1 | head -1 || echo missing; done
ls ~/Library/Caches/ms-playwright ~/.cache/ms-playwright 2>/dev/null | head -3
ls /Applications 2>/dev/null | grep -iE 'chrome|firefox|edge|brave|arc'; ls /usr/bin /opt 2>/dev/null | grep -iE 'chrome|chromium|firefox|brave' | head
```
Also check what Claude itself has: MCP servers configured (Claude Desktop:
`claude_desktop_config.json` under `%APPDATA%\Claude` / `~/Library/Application Support/Claude`
→ read the `mcpServers` keys), and whether you can run shell commands at
all in this environment. **If you cannot run commands, the probe above is
impossible and everything else in this skill is blocked** — go straight to
§"MCP servers worth offering" and get Desktop Commander (or equivalent)
installed first.

## The nudge (mandatory output after the probe)

Format, in the user's language, max 5 lines:

- What already works ("I can read and write your files and open websites").
- Each missing piece → **what it unlocks for THEM** → time to install →
  "install now?" Examples:
  - uv/Python → "scripts that run every morning by themselves" — 2 min
  - Node → "a button inside the website you use" (extensions) — 3 min
  - Playwright → "I can watch you do the task once and copy it" — 5 min
  - Violentmonkey → "a button on the page, no program to open" — 1 min
  - MCP Gmail/Calendar/Drive/Chrome → "I can act directly in X instead of you copy-pasting"
- Reassure: nothing changes in how the computer works; removable any time.

Repeat the nudge later whenever a missing tool is the difference between a
clunky solution and a clean one. Do not repeat it if they said no this
session — note it in the handoff README instead.

## MCP servers worth offering (Claude Desktop especially)

Claude Desktop out of the box can only read what is pasted into the chat.
Each server below is a one-time setup and turns Claude into a worker on
their machine. Offer in this order, one at a time, with the gain in their
words; install only what the task needs.

| Server | What Claude gains | Say it like | Needs | Install |
|-|-|-|-|-|
| **Desktop Commander** (`@wonderwhy-er/desktop-commander`) | terminal + read/write files + run scripts + edit configs. Turns Claude Desktop into something close to Claude Code | "I can install things and run the script here myself instead of telling you what to type" | Node LTS | `npx @wonderwhy-er/desktop-commander@latest setup` (writes the config entry itself), then restart Claude Desktop |
| **Windows-MCP** (`CursorTouch/Windows-MCP`) | sees the screen, clicks, types, opens desktop apps | "I can operate that program that has no website, like you do with the mouse" | uv/Python, Windows | clone the repo, `uv sync`, add a `mcpServers` entry that runs `uv --directory <path> run main.py`; check the repo README for the current command |
| **Claude in Chrome** (official extension) / **Playwright MCP** (`@playwright/mcp`) | acts inside the browser tabs they are logged into; reads the network log | "I can watch you do it once, in your own browser, and copy the requests" | Chrome / Node | extension from the Chrome store (official) · `npx @playwright/mcp@latest` entry in config |
| **Filesystem** (`@modelcontextprotocol/server-filesystem`) | read/write a chosen folder only (safer than Desktop Commander when they only need files) | "I can see your Downloads and Documents" | Node | config entry `npx -y @modelcontextprotocol/server-filesystem <folder>` |
| **Gmail / Calendar / Drive / Slack** connectors | act directly in the systems they copy-paste from | "I can read the e-mail and fill the sheet, no copy-paste" | account login | Claude Desktop → Settings → Connectors |
| **macOS computer use** (Claude Desktop, when available) | same as Windows-MCP for Mac | same | Claude Desktop, permissions in System Settings | Settings → Capabilities |

Config file: `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS).
Shape:

```json
{ "mcpServers": { "name": { "command": "npx", "args": ["-y", "<package>", "<args>"] } } }
```

Rules:
- **Desktop Commander is the default recommendation, always.** Not only
  when Claude cannot run commands: it is how Claude later edits Claude's
  own config, adds the next MCP, installs uv, reschedules the timer, reads
  the log when something breaks. Without it every one of those is a
  copy-paste the user has to do. Restart Claude Desktop after every config
  change and verify with a trivial call ("list my Downloads").
- Explain the trade in one honest line: "it can run anything on your
  computer that you could run; you can turn it off in the same file".
  Never install it silently. If they decline, keep going and remind them
  at the next moment it would have saved them a step (once per session,
  and in the handoff README).
- Prefer the narrower server only when the user is clearly uneasy
  (Filesystem for files only, Chrome for one site). Windows-MCP is an
  addition for desktop apps with no web/API, not a replacement.
- In Claude Code (CLI) most of this is already there; skip the section.

### One line, always

Anything the user must run themselves is **one copy-paste line**, chained.
They want to do the minimum; a numbered list of three steps is three
chances to stop. Examples:

- Windows (PowerShell), Node + Desktop Commander in one go:
  `winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements; $env:Path += ";$env:ProgramFiles\nodejs"; npx -y @wonderwhy-er/desktop-commander@latest setup`
- macOS, same:
  `(command -v node >/dev/null || brew install node) && npx -y @wonderwhy-er/desktop-commander@latest setup`
- uv + Python + verify (mac/Linux):
  `curl -LsSf https://astral.sh/uv/install.sh | sh && ~/.local/bin/uv python install 3.12 && ~/.local/bin/uv --version`

Then "close and reopen Claude Desktop" is the only other thing they do.
After that, Claude does the rest through Desktop Commander.

### Fewer confirmations — when THEY ask, explain and let them decide

Claude asks before each tool action by default. For a non-technical user
that is one more click they do not understand, dozens of times, and they
will ask "can it stop asking?". Answer with the official settings, the
trade in one honest line ("Claude will run things without asking first;
turn it back on the same way"), and let them apply it. Never enable it on
their behalf, never on a shared or employer-managed machine without saying
the admin may forbid it.

| Where | Official way |
|-|-|
| Claude Desktop tool prompts | on a tool's first prompt choose **"Always allow"** (per tool, per chat) |
| Desktop Commander | its own config (`set_config_value`: `allowedDirectories`, `blockedCommands`) — check the project README for current keys |
| Claude Code, one session | start with `claude --dangerously-skip-permissions` |
| Claude Code, permanent | `/permissions` inside Claude Code, or `"permissions": {"defaultMode": "bypassPermissions"}` in `~/.claude/settings.json` |

## Install commands (run them; quote the outcome only)

| Tool | Windows (PowerShell) | macOS | Linux (Debian/Ubuntu) |
|-|-|-|-|
| uv (+Python) | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | same as macOS |
| Python via uv | `uv python install 3.12` | same | same |
| Node LTS | `winget install OpenJS.NodeJS.LTS` | `brew install node` | `curl -fsSL https://deb.nodesource.com/setup_lts.x \| sudo -E bash - && sudo apt-get install -y nodejs` |
| Playwright (py) | `uv add playwright && uv run playwright install chromium` (inside the project) | same | same + `uv run playwright install-deps chromium` |
| Violentmonkey | Open the store page in their browser: Chrome/Edge/Brave → chrome.google.com/webstore (search "Violentmonkey"); Firefox → addons.mozilla.org | same | same |
| git | `winget install Git.Git` | `xcode-select --install` or `brew install git` | `sudo apt-get install -y git` |

Notes:
- Prefer **uv** over python.org installers: one command, no PATH prompts,
  per-project venv, `uv run` works everywhere. Never `pip install`.
- After installs on Windows, PATH changes need a **new** PowerShell; reopen
  or add `$env:Path += ";$env:USERPROFILE\.local\bin"` for the current one.
- Node is only needed for extensions with a build step or for JS-based
  tooling; plain userscripts/extensions need no Node at all.
- Playwright only if you will record traffic or must drive a browser.
  Chromium only; do not install all three browsers.
- Violentmonkey over Tampermonkey: open source, same API, works in
  Chrome/Edge/Brave/Firefox. If Tampermonkey is already installed, use it.

## Verify (each one, before moving on)

```
uv --version && uv run python -c "print('py ok')"
node -v && npm -v
uv run python -c "from playwright.sync_api import sync_playwright; print('pw ok')"
```
Violentmonkey: ask them to click the extension icon → "Dashboard" opens.
Report: "Installed and checked: Python, Node. Nothing else changed."

## Project folder layout (every deliverable)

```
~/Automations/<task-name>/        (Windows: %USERPROFILE%\Automations\…)
├── README.md            plain language, user's language
├── .env                 secrets (never shared); .env.example alongside
├── run.py / script.user.js / extension/
├── logs/                run.log (human) + debug.log (technical)
├── data/                state: seen ids, last run, downloads
└── run.bat | run.command | run.sh   one-click wrapper → shortcut points here
```
Create it with `uv init --app` for Python deliverables (`uv add requests
python-dotenv` etc.). One folder per automation; never mix.

## Keep the plugin itself up to date (once per session, step 0)

Two install shapes exist; detect which from the folder this `SKILL.md` was
read from (`${CLAUDE_SKILL_DIR}`; its parent's parent is the plugin root).

| Shape | Check (silent, ≤ 3 s, skip if offline) | Update (only after the user says yes) |
|-|-|-|
| **Claude Code plugin** (`${CLAUDE_PLUGIN_ROOT}` is set, or `claude plugin list` shows `automate-my-work@…`) | `claude plugin list` shows the installed version; compare with `curl -fsSL https://raw.githubusercontent.com/inno3759/automate-my-work/main/skills/automate-my-work/VERSION` (PowerShell: `irm <url>`) | `claude plugin update automate-my-work@inno3759`. A `@skills-dir` install is the maintainer's own clone: `git pull --ff-only` there, never over local edits |
| **Claude Desktop ZIP upload** (no `claude` CLI) | compare the folder's `VERSION` with the same URL | You cannot do it for them: "download the ZIP again, zip the `skills/automate-my-work` folder, upload it in Settings → Capabilities → Skills" — two clicks and a drag |

Rules:
- **Never update silently.** Show the pending lines (or "version X → Y")
  and ask in one sentence: "This helper has 2 improvements (better login
  handling). Update now? 5 seconds, then a new conversation." A skill
  that changes under the user mid-task is a bug, not a feature.
- **Local edits win** (maintainer clone): if `git status --porcelain` is
  not empty, or `pull --ff-only` refuses, say so and stop; never stash,
  reset or merge.
- **Check once per session, at step 0**, never in the middle of a build.
  Offline or fetch error → say nothing and continue.
- After updating: the new files load in the **next** session; finish the
  current task with what is loaded.
- `VERSION` (next to SKILL.md), `metadata.version` in SKILL.md and
  `.claude-plugin/plugin.json` at the plugin root carry the same string, bumped on every release commit: `YYYY.M.D`
  (semver, so no leading zeros; a second release the same day appends
  `-2`).
