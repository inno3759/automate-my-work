# automate-my-work — CLAUDE.md

Read this whole file before touching anything. It is the memory of the
project: what it is, why it is shaped this way, how every piece works, how
to change it safely, and where it stands.

## 1. What this is

A **distributable Claude skill**. This repository IS the skill: `SKILL.md`
at the root, `references/` loaded on demand by the model, `templates/`
copied into the user's own automation folder. Installing = cloning into
`~/.claude/skills/automate-my-work` (or uploading the ZIP to Claude
Desktop's Skills). There is no build, no runtime, no server.

When active, the skill makes Claude behave as an **automation engineer for
people who do not program**: it maps their working day, proposes what a
script can take over (including things they never asked for), finds the
HTTP requests behind their clicks, builds the tool, installs it so it runs
alone, and hands it over with a README written in their language.

## 2. Who it is for, and what that changes

The target user is on **Claude Desktop, Windows or Mac, with nothing
installed** (no Python, Node, uv, Playwright, no MCP). They do their
automation today by asking Claude to "click here, then there" every time.
They do not know what is possible, so they cannot ask for it.

Consequences baked into every file:
- The skill **probes the machine first** and says, in plain words, what
  installing each missing tool would unlock, then installs it for them
  (never "go to python.org"). This nudge repeats whenever a missing tool
  separates a clunky solution from a clean one. It also covers MCP servers.
- Language: files are in **English** (portable), but the skill orders
  Claude to speak the **user's language, without jargon**. "The page asks
  the server for the list", not "the XHR returns JSON".
- After handoff the user **never opens a terminal**. Everything has a
  button, a shortcut or a schedule, plus a README with "how to run / how
  to know it worked / what to do if it fails / how to stop".
- **Anonymous by default**: nothing that identifies the user goes into
  code, logs, file names, headers or commit metadata. Secrets in `.env`.

## 3. Principles (and why each exists)

| Principle | Why |
|-|-|
| **No LLM at runtime.** The deliverable works with Claude closed. | Cost, speed, determinism. Non-technical users cannot debug a model that "decided differently today". An LLM is allowed only for free-text steps, behind a rule-based fast path that resolves most cases, cached, validated, with a human fallback — and the user is told it costs money. |
| **Requests over clicks.** Every click is an HTTP request; record, find, replay. | 10–100× faster, no window to break, no selectors that die on redesign, no browser needed on the schedule machine. Browser automation (Playwright) is the last resort and must be justified in the README. A userscript calling `fetch()` inside the logged-in tab is the middle path and covers most "needs my login" cases. |
| **Observe, never guess.** Record real traffic (HAR) before building. Test in the real medium. | Synthetic tests and model memory both lied on real work (a message limit that differed per API). Sites lazy-load, sign URLs, and expire sessions in ways you only see live. |
| **Three failure bins.** Legit "nothing new" · blocked/unavailable · transport. | Collapsing them silently destroys data: an outage read as "not found" stamps "checked" on things never checked. Transport exceptions are library-specific and unrelated classes; one helper per project converts them. |
| **Idempotent, stable keys.** Second run = 0 new. Never change a dedupe key for stored rows. | A key "improvement" once re-notified an entire office with its whole history. |
| **Proactive.** Propose what they did not ask; show the way around "impossible" walls. | The user's imagination is the bottleneck. 2FA, captchas, app-only data, scanned PDFs and "must be at the office" all have known workarounds with known costs. |
| **Building blocks.** Logic in `core/`, thin surfaces (CLI, GUI, local API, MCP). | The second automation reuses the first; Claude can call the tools directly through MCP; page buttons reach files/OCR through a localhost API. |
| **Their account, their data.** Only what they may do by hand. Destructive actions keep a human "confirm". | Captcha-solving services and stored OTP secrets are offered only for the user's own account, with the cost and the terms-of-use caveat. No fingerprint spoofing, no fighting bot managers — fall back to the userscript in their tab. |

## 4. Architecture — file by file

```
automate-my-work/
├── SKILL.md                  entry point; the workflow Claude follows (official guidance: under 500 lines)
├── README.md                 two audiences: humans (top) + the installing agent (collapsible)
├── CLAUDE.md                 this file
├── LICENSE                   MIT
├── VERSION                   YYYY.M.D release stamp (semver); ZIP installs compare it with GitHub to detect updates
├── .claude-plugin/           plugin.json (name, version, license) + marketplace.json (this repo is its own marketplace `inno3759`, source "./")
├── evals/                    `claude plugin eval .` cases: 3 trigger phrasings that must fire the skill + 1 unrelated prompt that must not
├── .gitignore                __pycache__, .env, data/, logs/
├── references/               loaded on demand; each is self-contained
│   ├── setup.md              probe commands per OS → the nudge → install table → verify → project folder layout → keep the skill itself updated
│   ├── audit.md              existing automations: read/run first, 19-row shortcut checklist, rank risk×frequency÷effort, one fix at a time, same-input-same-output proof
│   ├── discovery.md          5-question interview, Playwright recording, machine inspection, opportunity map, 5-line spec
│   ├── network-first.md      capture → replay by hand → trace the dependency chain backwards → auth patterns → reading responses → decision rule → good citizen
│   ├── delivery-forms.md     decision table + checklists: userscript, extension, Python script, GUI, shortcut, Playwright
│   ├── scheduling.md         systemd user timers, launchd, Task Scheduler, browser alarms, verification
│   ├── gotchas.md            10 sections of hard-won traps + "when an LLM is allowed"
│   ├── unblockers.md         2FA/OTP via QR, captcha ladder, desktop apps, PDFs/OCR, spreadsheets, logouts, office PC, chat channels, human review, drift
│   ├── composability.md      core/surfaces split, local API, MCP server, LLM-ready outputs, when to suggest each
│   └── handoff.md            README template for the user + the real walkthrough + what NOT to leave behind
└── templates/                copied into ~/Automations/<name>/ and filled at the TODOs
    ├── record_session.py     Playwright persistent profile → HAR (bodies embedded) + storage_state + screenshot per navigation
    ├── har_digest.py         one line per non-asset request; --grep marks the request whose RESPONSE contains a value seen on screen
    ├── fetch_job.py          unattended HTTP job skeleton: 3 failure bins, login-page detection, backoff, state.json, lock, human+debug logs, Telegram notify, exit codes
    ├── userscript.user.js    Violentmonkey/Tampermonkey: one button, fetch() with credentials, GM_setValue dedupe, politeness delay
    ├── extension/            Manifest V3: background.js (alarms, fetch, storage, badge, notifications), content.js (button → message)
    ├── gui_tk.py             Tkinter one-window app: sentence, file picker, big button, log box; work in a thread; plain-word errors
    ├── otp_from_qr.py        otpauth:// URL or QR screenshot → secret → .env; prints a test code
    ├── api_server.py         FastAPI on 127.0.0.1 with X-Token and origin-restricted CORS
    ├── mcp_server.py         FastMCP exposing core functions; writes need confirm=True
    └── service/              NAME.service + NAME.timer (systemd user), com.automations.NAME.plist (launchd), register_task.ps1, run.sh/.bat/.command wrappers
```

### How the workflow runs (SKILL.md)
-1. **Triage** — any build/get/check/fetch request touching a site, app, sheet or mailbox: do it, then (if there is a request behind the clicks AND it will recur) offer the self-running version in one line, once. Accepted → step 0 with mini discovery. The user will not say "automate" or "scraping"; the skill must notice.
0. **Capability check + nudge** — first, once per session, check whether the skill itself has updates (`git fetch`/`log HEAD..@{u}`, or `VERSION` vs GitHub for ZIP installs) and offer them in one line; never pull silently or over local edits (`setup.md` §"Keep the skill itself up to date"). Then probe, say what each missing tool unlocks, install, verify. Mandatory, every time.
0b. **Audit** — they already have a script/macro/flow (or one is found on the machine): read and run it once, walk `audit.md`'s checklist, show ≤ 5 findings in their words, fix one at a time with their yes, prove same input → same output. Working code is the asset; no rewrites for style.
1. **Discovery** — interview → record one real pass → inspect the machine → opportunity map (ranked by minutes saved × determinism, max 5, at least one unrequested) → 5-line spec agreed with the user. "Impossible" walls → `unblockers.md`.
2. **Observe** — HAR → the request behind each click → replay with curl → strip headers → learn what the session is bound to → decision rule (HTTP script / userscript / extension / Playwright).
3. **Build** — templates; idempotent; 3 bins; loud single failure; `.env`; plain-language logs; `--dry-run`.
3b. **Building block** — `core/` + surfaces; offer local API, MCP, LLM-ready output, `_shared` package.
4. **Install** — timer/service/shortcut per OS; trigger once; watch it fire.
5. **Handoff** — README in their words; real run together; second run = 0 new; break it once on purpose.

### Design decisions worth knowing
- **Repo root = skill root.** Chosen so install is one `git clone` into the skills folder. Do not nest the skill in a subfolder.
- **Violentmonkey over Tampermonkey** (open source, same API, all browsers). Use Tampermonkey if already installed.
- **uv over python.org/pip.** One command, no PATH prompts, per-project venv, `uv run` everywhere. Never `pip install`.
- **Tkinter for GUIs.** Zero dependencies; NiceGUI only when the user is in a browser anyway.
- **Telegram as the default failure channel.** 5 minutes to set up, reaches the phone. E-mail/toast as alternatives.
- **Wrappers, not python, in schedulers.** `run.sh/.bat/.command` set PATH and cwd; shortcuts and timers call them.
- **Exit codes** in `fetch_job.py`: 0 ok · 1 blocked (retry later) · 2 needs the human · 3 bug. Schedulers and the README rely on them.
- **Ad-blocker-safe ids** (`am-` prefix; never ad/banner/sponsor).
- **Gotchas are generalized on purpose.** They come from scraping/integration work on a legal-process system (court portals, sessions, 2FA, dedupe, bot managers). Only the patterns were kept. Never re-add anything site-specific.

## 5. Conventions

- **SKILL.md under 500 lines** (official Claude Code guidance). Move detail to `references/` only when it is not needed on every run. The description in the frontmatter is the trigger: keep the phrases users actually say ("I do this every day", "can this be automatic?") AND the build/get/check phrasings of people who do not know automation exists ("pega os dados do site X", "me avisa quando mudar") — the skill must fire on the task, not only on the word "automate".
- **Each reference is self-contained** and can be read alone; cross-reference by file name and section (`gotchas.md §2`).
- **Templates**: Python ≥ 3.12, type hints, `from __future__ import annotations`, docstring at the top saying how to install deps and run, `TODO` marks exactly what must be filled. They must compile without the optional deps installed (imports of playwright/mcp/fastapi/pyotp are fine at module level only in files whose sole purpose needs them).
- **Prose**: rules stated as rules, one incident line for the "why". Tables over paragraphs. No site names, no personal names.
- **Releases**: bump `VERSION`, `metadata.version` in the SKILL.md frontmatter and `version` in `.claude-plugin/plugin.json` (all equal; `YYYY.M.D`, semver so no leading zeros, `-2` for a second release the same day) in every commit that changes SKILL.md, references or templates — ZIP installs detect updates only through it.
- **Commits**: `feat|fix|docs: short description`. Author is the anonymous GitHub identity. No `.env` in this repo (the skill has no secrets); user automations get their own `.env` + `.env.example`.
- **README** has two audiences; the collapsible "Instructions for the agent" must always match SKILL.md step 0 and the install paths.

## 6. Testing and quality gates

Before every commit:
```bash
claude plugin validate . && grep -q "$(cat VERSION)" SKILL.md .claude-plugin/plugin.json && echo versions ok
python3 -m py_compile templates/*.py && rm -rf templates/__pycache__
node -e "const fs=require('fs');for(const f of ['templates/userscript.user.js','templates/extension/background.js','templates/extension/content.js'])new Function(fs.readFileSync(f,'utf8'));JSON.parse(fs.readFileSync('templates/extension/manifest.json'));console.log('js ok')"
grep -rnoIE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}|https?://[^ )]+' . | grep -vE 'example\.com|127\.0\.0\.1|astral\.sh|nodesource|apple\.com|api\.telegram|githubusercontent\.com/inno3759/automate-my-work|github\.com/inno3759/automate-my-work' ; echo "identity scan: e-mails/links above must be empty; also grep your own name, domains and IPs from a list kept OUTSIDE the repo"
```
Trigger test: `claude plugin eval .` runs `evals/` (3 phrasings that must fire the skill, 1 unrelated prompt that must not) against a no-plugin baseline; a failing `skill-fired` grader means the description lost a trigger phrase. Costs real model runs; run it before a release, not on every edit.

Real test (the one that matters): run the skill with a non-technical user
(or role-play one) on a Windows/Mac machine with nothing installed. Watch
step 0 (does the nudge read naturally? did the install succeed?), step 1
(did the opportunity map surprise them?), and the handoff (can they run it
alone?). Fix what confused them before anything else.

Live reload: `~/.claude/skills/automate-my-work` is a symlink to this repo
on the dev machine; SKILL.md changes need a new Claude session to be
picked up.

## 7. Distribution

- Install paths: marketplace (`claude plugin marketplace add inno3759/automate-my-work && claude plugin install automate-my-work@inno3759`, updates via `claude plugin update`), git clone into `~/.claude/skills/` (loads as `automate-my-work@skills-dir`; slash name becomes `/automate-my-work:automate-my-work`, model invocation unchanged), or ZIP upload for Claude Desktop.
- GitHub: `inno3759/automate-my-work`, **public** since 2026-09-18, single-commit
  history (recreated after an identity scan). Never push without the scan;
  author is always the anonymous `inno3759` noreply identity; no AI
  attribution trailers.
- Users install by pasting the README's one-line prompt into their Claude.
  Claude Code: clone into `~/.claude/skills/`. Claude Desktop / claude.ai:
  ZIP upload in Settings → Capabilities → Skills (path to verify — see §9).
- Versioning: bump nothing yet; when public, tag releases (`v1.0.0`) so the
  ZIP link in the README is stable.

## 8. Roadmap (not implemented)

- pt-BR README (the primary audience is Brazilian; the agent block can stay English).
- `install.sh` / `install.ps1` one-liners for people without git.
- A worked example folder (`examples/`) showing one finished automation end to end: recording → digest → job → timer → README.
- Windows-specific: hidden console wrapper (`wscript` VBS) in `service/`; pythonw shortcut recipe with icon.
- OCR template (`ocr.py`: tesseract + cache), spreadsheet writer template (`openpyxl` atomic write), IMAP/Graph mail fetch template.
- A `_shared` package template (session, state store, notify) matching `composability.md`.
- Anti-drift monitor in `fetch_job.py`: alert when today's row count is far below yesterday's.

## 9. State (update this block every session)

- **2026-09-12 — v1 created.** SKILL.md + 9 references + 14 templates, README (human + agent), MIT. Templates compile; identity scan clean. **Never exercised with a real user.** First real test is the next milestone; expect the nudge wording and the discovery questions to change after it.
- Open decisions (user's): pt-BR README.
- Unverified claims to check on first real use:
  - Claude Desktop skill upload path in the README (Settings → Capabilities → Skills).
  - `record_har_content="embed"` and persistent profile paths on Windows.
  - `pyzbar` on Windows needs the zbar DLL; fallback already documented (user pastes the `otpauth://` text or the manual key).
  - `launchctl bootstrap` syntax on current macOS; `-lc` so PATH includes uv.
  - Task Scheduler `-MultipleInstances IgnoreNew` with `-StartWhenAvailable` catch-up behavior.
- 2026-09-12 later: added §2b dependency-chain tracing (network-first.md) + `har_digest.py --trace`, tested on a synthetic HAR (origin in body / POST body / header; no-origin case).
- 2026-09-18 (later): Desktop Commander is now the DEFAULT recommendation (also so Claude can edit Claude's own config later); decline → remind once per session when it would have saved a step. New rules: anything the user runs is ONE chained line; if they ask how to stop the permission prompts, setup.md §"Fewer confirmations" lists the official settings — they decide and apply. Desktop Commander `set_config_value` key names and the winget/npx one-liners are from memory — verify on first real use.
- 2026-09-18: setup.md gained §"MCP servers worth offering" (Desktop Commander, Windows-MCP, Chrome/Playwright MCP, Filesystem, connectors) + SKILL.md step 0 now says: Claude Desktop with no MCP can only talk → offer an MCP that gives Claude hands before anything else. Install commands for Desktop Commander / Windows-MCP are from memory — **verify against the projects' READMEs on first real use**.
- 2026-09-18: added the **Triage first** step (SKILL.md, before step 0) + wider description trigger: the skill now fires on "build/get/check X from site Y" requests, does the task, and offers the self-running version once if it will recur. Files list in SKILL.md compacted to stay near the 200-line budget.
- Nothing pending in code. Nothing broken known.
