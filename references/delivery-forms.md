# Delivery forms — pick the surface, then follow its checklist

## Decision table

| Signal | Form | Why |
|-|-|-|
| Task happens on ONE site while the user is logged in; single action | **Userscript** (Violentmonkey) | zero install beyond the extension; runs with the tab's session; a button appears on the page |
| Needs several tabs/sites, persistent storage, popup UI, context menu, alarms, or must run when no tab of the site is open | **Browser extension** (MV3) | background service worker + `chrome.storage` + `alarms`; still uses the browser's login |
| Files, spreadsheets, e-mail, APIs, anything unattended | **Python script** (uv project) | headless, schedulable, testable |
| "every morning / every hour / at 18:00" | Python script **+ timer/service** | see scheduling.md |
| A human must choose/enter something and hates terminals | **Tiny GUI** (Tkinter — zero deps) or a **shortcut** with a dialog | one window, one button |
| "when a file lands in this folder" | Python **folder watcher** (watchdog) as a service | |
| Rendered page required (canvas, WebSocket-only, JS-signed per render) and the user is not there | **Playwright persistent profile** | last resort; document why |

Combine freely: a userscript that POSTs to a local Python service; a
scheduled script that writes a spreadsheet the user opens; an extension
that stores a list the scheduled script reads.

## Userscript checklist (`templates/userscript.user.js`)

- `@match` only the exact pages; `@grant GM_xmlhttpRequest` only if
  cross-origin is needed (else plain `fetch` with `credentials:'include'`).
- Inject ONE visible button (fixed position, high z-index, your prefix in
  the id/class — never "ad", "banner", "sponsor": ad blockers hide those).
- Read the data from the DOM or from the same API the page uses (look at
  the HAR); never re-implement the page's JS.
- Progress and errors in a small status box on the page, not `alert()`
  storms. `console.log` prefixed with the script name.
- Idempotent: mark done items (`GM_setValue` / `localStorage`) so a second
  click skips them.
- Install: Violentmonkey → "+" → "Install from URL/file". Update = same
  path; keep `@version` bumped.
- Store the script in the automation folder AND in the dashboard.

## Extension checklist (`templates/extension/`)

- Manifest V3; permissions minimal (`activeTab`, `storage`, `alarms`,
  host permissions only for the sites used).
- `background.js` = service worker: alarms, fetches, storage. Content
  script = DOM only. Message passing between them.
- Popup only if the user needs to see state; otherwise a badge count.
- No build step unless you truly need one; plain JS keeps handoff simple.
- Load unpacked: `chrome://extensions` → Developer mode → Load unpacked →
  the folder. Pin the icon. Same in Edge/Brave; Firefox: `about:debugging`
  → temporary (or sign it for permanence).
- Updates: edit files, click "reload" on the card. Put that in the README.

## Python script checklist (`templates/fetch_job.py`)

- `uv init --app`, `uv add requests python-dotenv` (+ `beautifulsoup4`,
  `openpyxl`, `watchdog` as needed). Python ≥3.12. Type hints; `ruff`.
- Structure: `load config → acquire lock → fetch → classify → transform →
  write (idempotent) → notify → exit code`. One `_request()` helper that
  converts transport errors (gotchas §1).
- Flags: `--dry-run` (no writes, no notifications), `--once`,
  `--verbose`, `--since`.
- State in `data/state.json` (seen ids, last run). Atomic writes
  (`tmp` + rename).
- Logs: `logs/run.log` (one human line per run, rotating) and
  `logs/debug.log` (everything). Raw HTML of surprises in `data/debug/`.
- Notifications on failure only, through something the user already reads:
  Telegram bot (simplest), e-mail (SMTP), desktop toast (`plyer`/
  `osascript`/`BurntToast`). Success = a line in the log, not a ping,
  unless they asked.
- Wrapper: `run.bat` / `run.command` / `run.sh` doing `cd` to the folder
  and `uv run python run.py "$@"`; shortcuts point at the wrapper.
- Exit codes: 0 ok, 1 blocked/unavailable (retry later), 2 config/auth
  (needs the human), 3 bug.

## GUI checklist (`templates/gui_tk.py`)

- Tkinter (built in). One window: a short sentence of what it does, an
  input if needed (file picker / text), one big button, a log box, a
  status line. Disable the button while running; run the work in a thread.
- Errors in the log box in plain words, plus "details saved to debug.log".
- Shortcut on the desktop launches it (`pythonw`/`.command`). Never a
  console window on Windows (`pythonw.exe` or `.pyw`).
- If the user has a browser open anyway, a local NiceGUI page is a fine
  alternative — but Tkinter needs nothing installed.

## Shortcut / one-click checklist

- Windows: `run.bat` → right-click → Send to → Desktop (create shortcut);
  set an icon; for GUIs use `start "" pythonw …`.
- macOS: `run.command` (`chmod +x`), or an Automator "Application" that
  runs the shell script (no Terminal window, dock icon).
- Linux: `~/.local/share/applications/<name>.desktop` with `Exec=` and
  `Terminal=false`.
- Drag-and-drop: `.bat`/`.command` receives the dropped path as `%1`/`$1`.

## Playwright (last resort) checklist

- `launch_persistent_context(user_data_dir=…, headless=False)` for the
  first login; headless afterwards only if the site allows it.
- Lock file so two runs never share the profile.
- After login, `context.storage_state()` → do the rest by HTTP if at all
  possible.
- Explicit waits for the response you need; screenshots on failure into
  `data/debug/`.
- README must say: "this one opens a browser window; if it stops working
  after a site update, run it once with `--login` to log in again".
