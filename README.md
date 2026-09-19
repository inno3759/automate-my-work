<div align="center">

# 🛠️ automate-my-work

**A Claude plugin that turns a non-technical person's repetitive daily work into automation that runs by itself — no LLM in the loop.**

Buttons on the pages you already use · scripts that run every morning · tiny apps with one big button · and Claude learns what *your* day looks like before proposing anything.

[Install](#-install-3-clicks-in-claude-desktop) · [What it does](#-what-it-does) · [How it thinks](#-how-it-thinks) · [What's inside](#-whats-inside) · [FAQ](#-faq)

</div>

---

## 📦 Install (3 clicks in Claude Desktop)

1. Open **Customize** in the sidebar → **Plugins** → **Add marketplace**.
2. Paste `inno3759/automate-my-work` and confirm.
3. Find **automate-my-work** in that marketplace → **Install**. Start a new conversation.

Updates: Claude checks for them and asks you at the start of a session; or open **Customize → Plugins** and click **Update** on the marketplace.

**Claude Code** (terminal, VS Code, or the Claude Code tab in the desktop app):
```bash
claude plugin marketplace add inno3759/automate-my-work && claude plugin install automate-my-work@inno3759
```
Updates: `claude plugin update automate-my-work@inno3759`.

Or paste this to any Claude that can run commands:
```text
Install the Claude plugin from https://github.com/inno3759/automate-my-work
and then start it: look at what I do every day and propose what you could automate.
```

<details>
<summary><b>Instructions for the agent</b> (Claude: read this section and do it, do not ask the user to)</summary>

1. **Claude Code** (CLI / VS Code / desktop app tab): run `claude plugin marketplace add inno3759/automate-my-work && claude plugin install automate-my-work@inno3759` (same in PowerShell). Verify with `claude plugin list`, then tell the user to start a new session.
2. **Claude Desktop (Cowork) or claude.ai**: you cannot click for the user. Give the three steps above in one line: Customize → Plugins → Add marketplace → paste `inno3759/automate-my-work` → Install **automate-my-work** → new conversation.
3. **Updating later**: the plugin checks for updates itself at the start of each session and asks before doing anything. Claude Code: `claude plugin update automate-my-work@inno3759`. Desktop: Customize → Plugins → **Update** on the marketplace.
4. Start it: invoke the skill `automate-my-work`. Its first step is a **capability check** — it will probe the machine and tell the user, in plain words, what installing uv/Python, Node, Playwright, Violentmonkey or an MCP would unlock, and offer to install it. Do not skip that step; do not skip discovery.
5. Tell the user in one line: "Installed. I'll now ask five short questions about your day."

Requirements: none to install the skill. The skill installs what each automation needs (uv → Python, Node, Playwright, Violentmonkey) only when needed, and asks first.
</details>

---

## ✨ What it does

You say *"every Monday I download a report and paste it into a spreadsheet"* — or you say nothing, and Claude notices while helping you with something else. The skill then:

| Step | What happens | You see |
|-|-|-|
| **0b. Audit** | Already have a script, macro or flow? Reads and runs it once, lists the shortcuts that will hurt (login every run, sleeps, no dedupe, silent failures), fixes one at a time with your yes. | *"It logs in with your password every hour; one day the portal locks you out. I can make it reuse the session — 20 minutes."* |
| **0. Capability check** | Probes your computer. Tells you what's missing and what each thing would unlock. Installs it for you. | *"If I install Python (2 min), I can make this run every morning by itself. Install?"* |
| **1. Discovery** | Five questions about your day. Watches you do the task once (recorded). Looks at Downloads, recent files, bookmarks. | A ranked list of things worth automating — **including ones you didn't mention** |
| **2. Observe** | Finds the request behind every click in the recording and replays it. No clicking, no fragile "find the button". | Nothing yet — this is the engineering |
| **3. Build** | A button on the page, a script, a scheduled service, or a one-button window. Idempotent, logged, fails loudly once. | *"3 new, 12 skipped, 0 errors"* |
| **4. Install** | Timer/service on Windows, macOS or Linux. Desktop shortcut. | It runs without you |
| **5. Handoff** | A README in your language: how to run, how to know it worked, what to do if it fails, how to stop it. | A folder you own |

And when you say **"that one is impossible"** — *"it asks a code on my phone"*, *"there's a captcha"*, *"it only works in the app"*, *"it's a scanned PDF"* — the skill shows you the way around it and what it costs. Most walls are not walls.

## 🧠 How it thinks

- **It notices, you don't have to ask.** Say *"get me the list from site X"* or *"check if that page changed"* and it does it — then, if it looks like something you will do again, it offers once to make it run by itself. You never need to know the word "automation".
- **Requests over clicks.** Every click is an HTTP request. Replaying it is 10–100× faster and survives redesigns. A real browser is driven only when nothing else works, and the README says why.
- **No LLM at runtime.** The deliverable works with Claude closed. A model is called only for genuinely free-text steps, behind a rule-based fast path, cached, and you are told it costs money.
- **Your language, no jargon.** *"The page asks the server for the list"* — not *"the XHR returns JSON"*. You never open a terminal after handoff.
- **Building blocks.** Logic lives in `core/`; surfaces are thin: command line, window, local API for page buttons, and an **MCP server** so Claude can call your tools directly (*"what came in today?"*). The second automation reuses the first.
- **Learned the hard way.** `references/gotchas.md` is a list of traps that each cost a day on real systems: sessions that expire with a 200 and a login page, POSTs that fail on old sessions while every GET works, tables loaded by a second AJAX call, one-time-use 2FA codes, dedupe keys that re-notify the whole history, bot managers that punish copied cookies. Nothing site-specific — only the rules.
- **Your account, your data.** It automates only what you may do by hand. Destructive actions (send, pay, delete) keep a human "confirm" step.

## 📦 What's inside

```
automate-my-work/
├── SKILL.md                     the workflow Claude follows (5 steps + guardrails)
├── references/
│   ├── setup.md                 probe → nudge → install → verify, per OS; keep the skill updated
│   ├── audit.md                 checklist for automations they already have: shortcuts, ranking, safe fixes
│   ├── discovery.md             interview, recording, opportunity heuristics
│   ├── network-first.md         find and replay the request behind the click
│   ├── delivery-forms.md        userscript / extension / script / service / GUI / shortcut
│   ├── scheduling.md            systemd · launchd · Task Scheduler · browser alarms
│   ├── gotchas.md               the hard-won traps + when an LLM is allowed
│   ├── unblockers.md            OTP from the QR, captcha ladder, app-only data, PDFs/OCR
│   ├── composability.md         core/surfaces, local API, MCP server, LLM-ready output
│   └── handoff.md               README template + the walkthrough
└── templates/
    ├── record_session.py        Playwright: HAR + storage state + screenshots
    ├── har_digest.py            "which request has the value I saw on screen?"
    ├── fetch_job.py             unattended HTTP job: 3 failure bins, state, lock, notify
    ├── userscript.user.js       one button on the page (Violentmonkey/Tampermonkey)
    ├── extension/               Manifest V3: alarms + storage + content script
    ├── gui_tk.py                one-window app, zero dependencies
    ├── otp_from_qr.py           2FA secret from the QR → .env → codes
    ├── api_server.py            localhost FastAPI with token
    ├── mcp_server.py            the same functions as Claude tools
    └── service/                 systemd, launchd, PowerShell task, run.sh/.bat/.command
```

## ❓ FAQ

**Do I need to know how to program?** No. That is the point. You describe your day; Claude builds, installs and explains.

**Will it change how my computer works?** No. Tools are installed per project (`uv`) or as a browser extension; everything lives in one folder per automation and can be deleted.

**Where do my passwords go?** In a local `.env` file inside the automation folder. Never in code, never in the README, never sent anywhere.

**What about 2FA?** You re-create the authenticator on the site, scan the QR into an exportable app (2FAS, Aegis, Ente) *and* show the same QR to Claude. The script then generates the same codes. The secret is as sensitive as a password and stays in `.env`.

**Captchas?** In order: reuse the session you logged into by hand · use the site's official API/export · a button inside your logged-in tab · a paid solving service for your own account (with the terms-of-use caveat). It never spoofs fingerprints or fights bot protection.

**Can other tools or Claude reuse what was built?** Yes — that is step 3b. Local API for page buttons, MCP server for Claude, outputs shaped for an LLM to read.

## 🤝 Contributing

Gotchas are welcome when they are **general** (a pattern, not a site) and **measured** (what you saw, what fixed it). Open an issue with the incident in three lines: symptom, cause, fix.

## 📄 License

MIT
