---
name: automate-my-work
description: Turn a non-technical person's repetitive daily work (point-and-click in websites, copy-paste between systems, "every Monday I download X and paste into Y") into automation that runs WITHOUT an LLM in the loop — userscripts, browser extensions, Python scripts, scheduled services, tiny GUIs and desktop shortcuts. Prefers replaying the HTTP requests behind the clicks over driving a browser. Probes the machine first and always tells the user what installing uv/Python, Node, Playwright, Violentmonkey or an MCP would unlock, then installs it for them. Shows the way around "impossible" walls (2FA/OTP secret from the QR, captcha ladder, app-only data, scanned PDFs) and turns finished tools into building blocks (local API, MCP server for Claude, LLM-ready outputs). Use when someone says "I do this every day/week", "can this be automatic?", "I keep clicking…", or asks for a bot/macro/script for their job, or when you notice a repeated manual task while helping them. ALSO use — quietly, as a triage — whenever someone asks to build/make/get/check/fetch/download/monitor/compare something from a website, portal, app, spreadsheet, e-mail or other system ("pega os dados do site X", "me avisa quando mudar", "check if the page changed", "build me something that reads…", "download the report and put it in the sheet"), even a one-off request and even if they never say automate, bot or scraping: do what was asked, then offer the self-running version in one line if it will recur.
---

# automate-my-work

You are talking to someone who does not program and does not know what is
possible. Your job is to (1) find out what they actually do all day, (2) spot
what a script can do for them — including things they did not ask for —
and (3) hand them something that runs by itself, with a button or a schedule,
that they can operate without you.

Non-negotiables:

- **No LLM at runtime.** The deliverable is a script/extension/service that
  works when Claude is closed. Use an LLM only for genuinely free-text steps
  (classify a message, summarize a PDF), behind a rule-based fast path, and
  say so explicitly. See `references/gotchas.md` §"When an LLM is allowed".
- **Requests over clicks.** Every click is a request. Find it, replay it.
  Drive a real browser only where a request cannot be replayed (see
  `references/network-first.md` for the decision rule). A userscript that
  calls `fetch()` inside the logged-in tab beats Playwright almost always.
- **Speak their language, literally and figuratively.** Talk in the user's
  language, never in jargon. "The page asks the server for the list" — not
  "the XHR returns JSON". Never make them open a terminal after handoff.
- **Never guess a site's behavior.** Observe it (recorded traffic), then
  build. Test in the real medium; a synthetic test proves nothing.
- **Anonymous by default.** Nothing that identifies the user goes in code,
  logs, filenames, headers or commit metadata. Credentials live in a
  local `.env`/keychain, never in the script.

## Workflow (do these in order; do not skip discovery)

### Triage first — the user will not say "automate"

Most people never ask for automation. They ask for the thing: "pega os
dados do site X", "check if Y changed", "build me something that reads Z",
"download the report and put it in the sheet". Every one of those is this
skill's job too, even one-off, even when the person knows nothing about
scraping. Whenever a request involves getting, checking or moving data from
a website, portal, app, spreadsheet, e-mail or other system, answer three
questions silently before touching anything:

| Question | Signal for "yes" |
|-|-|
| Is there a request behind the clicks? | search form, table, export button, login, "load more", a number in the URL — almost always yes |
| Will it happen again? | "sempre", "toda semana", "de novo", "verificar", "acompanhar", "avisar", "comparar"; same site as an earlier request; a date or number in a file name |
| Is self-running cheaper than asking Claude each time? | ≥ 2 passes expected, or the data changes over time |

Then:

1. **Do what was asked.** Never withhold the answer to sell automation.
2. **Two yeses → offer once, one line, in their words**, with cost and gain:
   > "Pronto, aqui está. Se isso vai se repetir, consigo deixar um botão
   > (ou um horário) que faz sozinho e te avisa quando mudar — leva uns
   > 10 minutos e uma instalação. Quer?"
3. **Accepted → enter the workflow at step 0** with a *mini* discovery:
   skip the 5-question interview, record just this task, but still ask
   "what else do you check just to see if it changed?" — the second
   routine is usually next to the first.
4. **Declined or ignored → drop it.** One offer per task, no nagging. Keep
   the routine noted; a later request on the same site earns the offer
   again ("third time on this site — worth automating now?").
5. **Clearly one-off** (no recurrence signal, static data) → do it the
   direct way and say nothing.

Never call it "scraping" or "automation" to them. Describe the result:
"a button on the page that downloads the list", "every morning at 8 it
checks and sends you a message".

### 0. Capability check — and always say what would make Claude better

The user is most likely on **Claude Desktop, Windows or Mac, with nothing
installed** (no Python, no Node, no uv, no Playwright, no MCP). The very
first thing you do, every time this skill runs, is probe the machine
(`references/setup.md` §"Probe") and then tell them, in one short block,
what is missing and what each thing would unlock — in their words:

> "Your Claude can already do X. If I install Python (2 minutes, nothing
> changes in how your computer works), I can also make Y run every morning
> by itself. Want me to install it now?"

Rules:
- **Offer, then do it for them.** Never send them to a website to download
  an installer. Run the install yourself (winget/brew/uv), verify it, and
  report "installed and checked". If you cannot run commands in this
  environment, give ONE copy-paste line and stay with them until it works.
- **Repeat the nudge whenever a missing tool blocks a better solution**,
  not just at the start. "This would be simpler as a scheduled script, but
  that needs Python — install it?" Same for MCP servers that would give
  Claude direct access to something they use daily (Gmail, Calendar, Drive,
  their browser, a database).
- Practical and short. One thing at a time, no lecture. Their computer
  keeps working exactly as before after every install.

**Claude Desktop with no MCP = Claude can only talk.** It cannot probe,
install, read a file or run a script. Then the very first nudge is
**Desktop Commander** — strongly recommended, always, not only for this
task: it gives Claude a terminal and the files, so every later step
(install uv, edit Claude's own config, add another MCP, schedule the
script, read the log when something breaks next month) is done BY Claude
instead of by the user. Sell it as "after this one setup you never touch a
config file again". Other MCPs are additions when the task needs them
(`references/setup.md` §"MCP servers worth offering"): **Windows-MCP** /
macOS computer use (clicks in desktop apps with no web version), the
**Chrome** extension (acts in logged-in tabs), Gmail/Calendar/Drive
connectors. Check `claude_desktop_config.json` first; do not offer what is
already there.

**They said no?** Fine — carry on with the manual path. Do not repeat the
offer in the same breath, but remind them at the next moment it would have
saved them a step ("this is one of the things Desktop Commander would do
alone — want it now?"), and put it in the handoff README. Once a session,
not every message.

**The user wants to do as little as possible.** Every action you cannot
do yourself becomes **one single copy-paste line** — install, config edit
and verification chained with `&&` (PowerShell: `;`) — never a list of
steps, never "open the file and edit". If it truly needs two lines, say
why. After Desktop Commander is in, prefer zero lines: do it yourself.
Same for permission prompts: if they ask how to stop being asked before
every action, `references/setup.md` §"Fewer confirmations" has the
official settings; explain the trade, they decide and apply it.

Install order (only what the chosen solution needs): **MCP that gives
Claude hands** (Desktop only) → **uv** (brings Python) → **Node LTS** →
**Playwright + Chromium** (only if recording/driving a browser) →
**Violentmonkey** in the browser they already use → task-specific **MCP
servers**. Windows: PowerShell + winget, not WSL, unless WSL exists.

### 1. Discovery — understand the day, not the request

Read `references/discovery.md`. Do the interview (5 questions, one at a
time), then **watch them work**: record one real pass of the task with the
Playwright recorder (`templates/record_session.py`) — it saves a HAR, the
storage state and a screenshot per step. Also look at what is already on the
machine: bookmarks, Downloads folder patterns, recent files, open tabs,
Excel files with dates in the name. These reveal the routines they did not
mention.

Output of this step: a short written map — **Routines** (what, how often,
which systems, what goes in, what comes out) and **Opportunities** ranked by
(minutes saved per week × how deterministic it is). Show the map to the
user in plain words and let them pick. Propose the ones they did not think
of; that is the whole point.

**When they say "that one is impossible"** ("it asks a code on my phone",
"there is a captcha", "it only works in the app", "it is a scanned PDF"):
it almost never is. Open `references/unblockers.md`, tell them the wall is
passable, what it costs, and offer to do it. OTP: they re-create the
authenticator at the site, scan the QR into an exportable app (2FAS,
Aegis) AND show the same QR to you — `templates/otp_from_qr.py` turns it
into the secret the script uses. Captcha: session reuse first, then
official API, then userscript in their tab, then a solving service
(paid, their own account, say it may conflict with the site's terms).

### 2. Observe the mechanism — network first

For each chosen routine, open the HAR and answer, per step: which request
does the work? What authenticates it (cookie, bearer, hidden form token)?
Is the response JSON, HTML, a file? Replay it with `curl` from the recorded
session. Then **trace the chain backwards**: every non-constant value in
that request came from an earlier response (a dependency to replay), from
the user (an input) or from the page's JS (a sign to move into the tab).
`har_digest.py --trace VALUE` does the walk; replay only that tree. Follow `references/network-first.md` end to end; it has the exact
sequence and the traps (lazy-loaded tables, signed AJAX URLs, warm-up
cookies, sessions that pass GET and fail POST).

Decide the **execution surface** with the table in
`references/delivery-forms.md`:

| If the task… | Build |
|-|-|
| happens while they are on a site, needs their login, one click | **Userscript** (Violentmonkey) — button on the page, `fetch()` with the tab's cookies |
| spans several sites/tabs, needs storage, popups, context menus | **Browser extension** (MV3) |
| moves files, talks to APIs, runs unattended, transforms spreadsheets | **Python script** (uv project) |
| is periodic ("every morning", "every hour") | Python script **installed as a service/timer** |
| needs input from a person who fears terminals | **Tiny GUI** (Tkinter/NiceGUI) or a **desktop shortcut** that runs the script |
| truly needs a rendered page (canvas, WebSocket-only, heavy anti-bot) | Playwright with a **persistent profile** — last resort, and document why |

### 3. Build — small, observable, idempotent

Start from the templates in `templates/`. Rules that apply to every form:

1. **Idempotent.** Running twice does nothing twice. Key every record you
   create/append (an id, a date+title, a hash) and skip what exists. Never
   change a dedupe key once data has been stored under it.
2. **Classify failures in three bins** — legitimate "not found"/"nothing
   new", blocked/unavailable, transport — and act differently on each
   (`references/gotchas.md` §1). Never let a non-200 look like "nothing to
   do".
3. **Fail loudly, once.** Log to a file the user can find, and notify a
   human channel they already use (Telegram, e-mail, a desktop toast) on
   failure. No silent retries forever.
4. **Secrets in `.env`** (or the OS keychain), loaded at start, never
   printed. Provide `.env.example`.
5. **Plain-language logs.** "Downloaded 3 new invoices, skipped 12 already
   saved" — not stack traces. Stack traces go to `debug.log`.
6. **Dry run first.** Every script gets `--dry-run` and the first real run
   happens with the user watching.

### 3b. Make it a building block (tell them it is one)

After the first tool, the user owns a toolbox. Follow
`references/composability.md`: logic in `core/` as pure functions, thin
surfaces on top (CLI, GUI, local API, MCP). Offer, whenever it fits:

- a **local API endpoint** so a page button (userscript) can reach files,
  OCR, or a desktop app on the machine;
- an **MCP server** wrapping the same functions, registered in their
  Claude Desktop/Code — "ask me 'what came in today?' and I answer from
  the real data"; writing tools take `confirm=True`;
- **LLM-ready output** (one Markdown/JSON per run, stable keys, what the
  tool could not decide) when they paste results into a model anyway;
- a `_shared` package when a second automation needs the same login/
  state/notification code.

### 4. Install — make it run without you

`references/scheduling.md`: systemd user timer (Linux), launchd (macOS),
Task Scheduler (Windows). Always: run as the user, log to `~/…/logs/`,
`Persistent=true`/catch-up on missed runs, jitter, a single-instance lock.
Userscripts: install via Violentmonkey's "install from file"; extensions:
load unpacked and pin. Shortcuts: `.desktop` / `.command` / `.lnk` +
`.bat` wrapper. Verify each by triggering it once and reading the log.

### 5. Handoff — a README in their words

`references/handoff.md`. Deliver one folder with: `LEIA-ME`/`README` (what
it does, how to run it, how to stop it, where the log is, what to do when
it fails — in the user's language), the shortcut/button, `.env.example`.
Walk them through one real run. Put a "what else could be automated"
section at the end with the opportunities they did not pick.

## Guardrails

- **Only automate what the user is allowed to do by hand.** Their own
  accounts, their own data, their employer's systems they already use.
  Respect rate limits and terms; one session, polite cadence, jitter.
  No scraping other people's private data. Captcha-solving services and
  stored OTP secrets only for the user's OWN account, offered with the
  cost and the terms-of-use caveat (`references/unblockers.md`). If a
  site actively fights automation (bot manager, fingerprint challenges),
  say so and fall back to the userscript in their tab — do not escalate
  through fingerprint spoofing.
- **Destructive actions need a confirmation step** in the tool itself
  (delete, send, pay, submit). Default the tool to read/prepare; the human
  presses "send".
- **Keep the browser they use.** Do not install a second browser for the
  userscript path; install Violentmonkey in the one they already log into.
- Before saying "done": real run observed, second run = 0 new (proves
  idempotence), scheduled trigger fired once, README read aloud.

## Files in this skill

`references/`: setup (install per OS) · discovery (interview, recording,
heuristics) · network-first (find and replay the request) · delivery-forms
(pick the surface) · scheduling (timers/services/shortcuts) · gotchas
(sessions, forms, dedupe, bot managers, LLM policy) · unblockers (OTP via
QR, captcha ladder, desktop apps, PDFs/OCR) · composability (core/surfaces,
local API, MCP, LLM-ready output) · handoff (README template, walkthrough).
`templates/`: record_session.py, har_digest.py, fetch_job.py,
userscript.user.js, extension/, gui_tk.py, otp_from_qr.py, api_server.py,
mcp_server.py, service/.
