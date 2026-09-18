# Discovery — find the work the user does not know is automatable

People describe the last annoying thing, not their day. Your job is to map
the day. Two sources: what they say, and what the machine shows.

## 1. Interview (one question at a time, in their language, 5 max)

1. "Walk me through yesterday morning, from opening the computer. Which
   windows did you open, in what order?" (routines surface here)
2. "What do you copy from one place and paste into another?" (the #1
   automation candidate; ask where from, where to, how often)
3. "What do you download, and what do you do with the file afterwards?"
4. "What do you check 'just to see if something changed'?" (polling →
   scheduled watcher with notification)
5. "What would you hate to do this Friday?" (the emotional one; often a
   monthly report or reconciliation)

For each answer, capture: **trigger** (time / event / someone asks),
**systems** (URLs, apps, files), **input**, **output**, **frequency**,
**minutes per pass**, **what makes it annoying** (waiting, retyping,
finding things). Do not propose solutions yet.

## 2. Watch one real pass (Playwright recorder)

Run `templates/record_session.py` (needs Playwright). It opens their normal
browser profile copy, records a **HAR with bodies**, a screenshot per
navigation, and saves `storage_state.json` at the end. Ask them to do the
task exactly as always, narrating out loud; you write the step list.

If Playwright is not installed: nudge (setup.md), and meanwhile use the
browser DevTools "Network → Export HAR" or, in Claude Desktop with the
Chrome MCP, drive their browser and read the network log.

Without any recording ability, fall back to screenshots per step + asking
them to right-click → "Copy as cURL" on the row that changes (last resort).

## 3. Look at the machine (with permission, read-only)

- Downloads folder: names with dates/numbers = recurring exports.
- Recent files (Office recent list, `~/Documents` mtime): spreadsheets
  updated weekly are candidates for "fill from source automatically".
- Bookmarks bar: the systems they live in. Open tabs: the daily loop.
- Desktop shortcuts and `.bat`/`.command` files: someone already tried.
- Email rules/labels: what they triage by hand.
- Calendar: recurring "do X" events are cron jobs in disguise.

## 4. Opportunity map (write it, show it)

Rank by `minutes_saved_per_week × determinism`. Determinism: does the same
input always produce the same steps? High = script; medium = script +
"review before send" step; low = leave to the human, maybe assist.

Categories that are almost always worth it:

| Pattern they describe | What to build |
|-|-|
| "I open X every morning to see if there is something new" | scheduled watcher (requests) → notification only when new |
| "I download the report and paste it into the spreadsheet" | scheduled fetch → writes the sheet (openpyxl / Google Sheets API) |
| "I type the same thing into the form for each row" | userscript button: read the row, POST the form N times |
| "I search each client one by one in site Y" | userscript/script: loop over the list, one request each, table out |
| "I forward these emails to Z" | mail rule if the client supports it; else IMAP script |
| "I rename/move files after downloading" | watcher on the Downloads folder (watchdog) |
| "I check three systems and write a summary" | scheduled fetch × 3 → one page/e-mail/Telegram message |
| "I fill in the same PDF/DOCX with data from…" | template + script (docxtpl / pypdf) |

Present max 5 opportunities, ranked, one line each with the estimated
minutes saved per week and the shape ("button on the page", "runs every
morning", "drag file here"). Include at least one they did not mention.
Let them pick; start with the one that is both valuable and deterministic.

## 5. Write the spec (5 lines, agree before building)

```
Task: <name>
Trigger: <button on page X | every day 08:00 | file dropped in folder>
Reads: <system/URL/file>
Writes: <file/system/message>
Done when: <observable result the user checks>
Never: <the destructive action it must not do without confirmation>
```
