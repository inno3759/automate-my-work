# Audit — they already have an automation

Someone hands you a script, macro, flow, extension or "bot" that already
runs (or used to). Your job is not to rewrite it. It is to find the
shortcuts that will hurt them, rank them, fix the worst with their
agreement, and prove nothing else changed.

Triggers: "I already have a script that…", "my bot stopped working",
"can you look at my macro", a `.py`/`.js`/`.ahk`/`.bas`/`.ps1` file, a
Power Automate / Zapier / Make / n8n flow, a Tampermonkey script, an
Excel with macros — or you find one yourself during discovery
(`discovery.md` §"inspect the machine": an `Automations/`, `scripts/`
or `bot/` folder, a Task Scheduler entry, a crontab, a launchd plist).

## 1. Read before judging (15 minutes, no edits)

1. **What does it do, in one sentence, in their words?** Ask them, then
   confirm by reading the code. If the two disagree, that is finding #1.
2. **How is it started?** By hand, a shortcut, a scheduler, a `while
   True: sleep`? Read the scheduler entry, not their memory of it.
3. **Evidence of runs**: logs, output folder timestamps, the state file,
   the last 10 exit codes. No trace at all → "silent" is already a finding.
4. **Run it once yourself**, `--dry-run` if it has one, watching the
   network (`templates/record_session.py` or the browser's Network tab)
   if it drives a browser. You need to see the real mechanism to
   propose a better one.
5. **Freeze a reference**: copy the current output (files, rows, messages
   sent) somewhere read-only. Every fix is checked against it (§4).

## 2. The checklist (what a shortcut looks like)

Walk every row. Note where in the code, the incident it invites, and
whether it is cheap or expensive to fix. Skip the rows that do not apply.

| Shortcut | How to spot it | Why it hurts | Better |
|-|-|-|-|
| **Browser where a request would do** | Selenium/Playwright/pyautogui for a page that has a form, a table or an export | 10–100× slower, dies on every redesign, needs a screen | Record a pass, find the request, replay it (`network-first.md`). Keep the browser only for what §"decision rule" allows |
| **Timing by sleep** | `sleep(5)`, `WaitForSeconds`, fixed delays before reading a page | Flaky on a slow day, slow on a fast one | Wait for the condition (response, element, file exists), with a timeout |
| **Screen coordinates / image matching** | `click(812, 430)`, `locateOnScreen` | Breaks when a window moves, a font changes, a second monitor appears | Requests, then DOM, then accessibility APIs. Coordinates only for apps with none of those (`unblockers.md` §desktop apps) |
| **LLM for a deterministic step** | A model call to parse a date, pick a row, extract a number, decide "is this new?" | Costs per run, random on edge cases, cannot be unit-tested | Rule-based fast path; model only for free text, cached and validated (`gotchas.md` §"When an LLM is allowed") |
| **No dedupe key** | Appends on every run; "delete everything and rebuild" | Duplicate rows, re-sent messages, re-downloaded files | Stable key (id, date+title, hash); skip what exists. Second run = 0 new |
| **Dedupe key from a mutable field** | Key contains status, position, a display name | One upstream edit re-notifies the whole history | Key on what never changes. Never change the key once data is stored under it |
| **Failure bins collapsed** | `except: pass`, `if not rows: return`, non-200 treated as empty, `while True: retry` | An outage looks like "nothing new"; "checked" is stamped on things never checked | Three bins — nothing new / blocked / transport — each with its own action (`gotchas.md` §1) |
| **Silent** | No log the user can read; no notification on failure; runs as a scheduled task nobody looks at | They find out a month later from a client | Plain-language `run.log`, `debug.log`, one alert on failure to a channel they already use |
| **Secrets in code** | Passwords, tokens, cookies in the source, in a `.bat`, in git history, printed to the log | Leaks with every copy of the script | `.env` / keychain, `.env.example`, purge history if it was committed |
| **Identity in the artefact** | Real names, e-mails, client names in filenames, headers, comments, User-Agent | Travels with every share of the script | Anonymous by default (SKILL.md non-negotiables) |
| **Machine-specific paths** | `C:\Users\<name>\Desktop\…`, `/Users/<name>/…`, a mapped drive letter | Dies on the next computer, or for the colleague | Paths from `.env` or relative to the script; `Path.home()` |
| **Runs only while they watch** | Started by hand; a terminal must stay open; a `while True` loop | Stops on reboot, on logout, on a closed lid | Scheduler with catch-up, lock, run-as-user (`scheduling.md`); a wrapper, not `python` directly |
| **No single-instance lock** | A slow run overlaps the next scheduled run | Double processing, corrupted state file | Lock file / `flock` / scheduler "do not start a new instance" |
| **Destructive without a confirm** | Sends, deletes, pays, submits with no dry-run and no human step | One bug = one incident nobody can undo | Default to prepare; the human presses "send"; `--dry-run` |
| **Login every run** | Username+password POST each time, or a fresh browser profile | Rate limits, lockouts, 2FA prompts, bot walls | Reuse the session (`storage_state`, cookie jar, persistent profile); re-login only on the login-page signal |
| **Fights the site** | User-Agent rotation, proxies, fingerprint tricks, captcha farms not for their own account | Terms-of-use exposure, arms race they lose | Polite cadence, one session, userscript in their own tab; only their own account (SKILL.md guardrails) |
| **Monolith** | One 600-line file mixing fetching, parsing, Excel and the GUI | Second automation copies half of it; a fix lands in one copy | `core/` pure functions + thin surfaces (`composability.md`); a `_shared` package when two automations overlap |
| **Blind to drift** | Parses HTML/CSV without checking the shape | Site changes a column; the script writes garbage for weeks | Log counts and a first row; alert on "0 rows" when yesterday had 50 (`unblockers.md` §drift) |
| **Nobody else can run it** | No README, no `.env.example`, only they know the incantation | Vacation = the routine stops | Handoff README in their language (`handoff.md`) |

## 3. Rank, then propose (the user chooses)

Score each finding **risk × frequency**, then divide by effort. Show at
most **5**, in plain words, worst first, each as: *what it does today →
what happens when it bites → what I would change → how long*. Example:

> "It logs into the portal with your password every hour. One day the
> portal will lock your account for 'suspicious activity'. I can make it
> reuse the session like your browser does — 20 minutes, no visible change."

Rules:
- **Working code is the asset.** If it runs correctly and nobody suffers,
  a style opinion is not a finding. Do not rewrite for elegance.
- **One fix at a time**, each verified (§4) before the next. Never a
  big-bang rewrite of a tool people rely on tomorrow morning.
- **Ask before touching anything that changes output**, especially the
  dedupe key, filenames, columns, message wording — other people or
  other scripts may depend on them.
- Their language, no jargon. "It waits 5 seconds and hopes" beats
  "hard-coded sleep".

## 4. Prove nothing else changed

Before declaring a fix done:
1. **Same input → same output** against the frozen reference from §1.5
   (diff the files/rows; for messages, a dry-run log of what would be
   sent).
2. **Second run = 0 new** (idempotence), if the fix touched keys or state.
3. **The scheduled trigger fired once** after the change, if the
   scheduler was touched.
4. **Break it on purpose once** (wrong password, no network) and check
   the failure is loud and in plain words.
5. Update the README (or write the first one) with what changed and why.

Leave behind: the audit list with each item marked *fixed / declined /
later*, so the next person (or the next Claude) does not redo the audit.
