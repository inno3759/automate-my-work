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

## 4b. Is it worth automating? (run every candidate through this filter)

Bad automation does not feel broken; it feels productive. Things move,
tasks disappear, dashboards look nicer — and a week later the user is
reviewing output that did not need to exist, or trusting something they
should not. Before a candidate goes on the map, answer these; a "no" on
any of the first three means **leave it manual, on purpose, and say why**.

Two overrides, in this order:

- **The user explicitly asked to automate it → automate it.** The filter
  is for candidates *you* propose, not a gate on their request. If a test
  fails, build it anyway with the safety it implies (a "review before
  send" step, `--dry-run`, an undo), say in one line what you added and
  why, and move on. Never refuse or stall a clear request with this table.
- **Recurrence is the trigger, not a count.** Nothing below is a hard
  threshold. If it happens every month, every quarter, every time a
  client arrives, or if you can reasonably presume they will do it again
  ("todo mês eu faço isso", the same site as an earlier request, a date
  in a file name, a task that is obviously part of their job) — offer
  the automation. Monthly and painful beats daily and trivial.

| Test | Ask | Automate when |
|-|-|-|
| **Flow, not decision** | Is the step "if A → do B", or does it need context, nuance, accountability? | clear path, few surprises, mistakes cheap, output easy to verify. Data moving, reminders, statuses, syncing, "draft-level" tags/priority: yes. Judgment calls: no — or produce a draft the human approves. |
| **Silent failure** | If this ran wrong silently, how fast would they notice, and how bad is it? | "quickly" and "cheap". If "not quickly" or "pretty bad": keep a human checkpoint (`--dry-run`, "review before send"). |
| **Reversible** | Can a person spot a wrong move and undo it? | yes. If not, the tool prepares and the human presses "send". |
| **Leverage** | Does it shorten a cycle (lead → meeting → payment), cut losses (missed calls, forgotten follow-ups), or raise quality — or does it save 3 clicks and add a layer of checking? | leverage. A "looks nice" automation that creates review work is clean-looking chaos. |
| **Still wanted** | "If this ran perfectly, would you still want the output?" | yes. If the honest answer is "I would not read it", drop it. |
| **Recurrence × pain** | Will it happen again — daily, weekly, monthly, every new client? Does it feel like a chore? Acceptable deviation if done by hand? | it recurs, on any cadence, or you can presume it will; more so if it is a chore or must come out identical every time. |
| **Maintenance** | Who fixes it when the site changes next month? | the gain covers the upkeep; otherwise a userscript button (cheap to fix) beats a service. |

Guard the thinking, not the effort: a step that exists to catch bad
inputs, validate an assumption or force a decision must stay where a
human sees it. Automating it hides the problem instead of solving it.
The good automations move human effort to the exact point where it
matters and are boringly reliable, not impressive.

## 5. Write the spec (5 lines, agree before building)

```
Task: <name>
Trigger: <button on page X | every day 08:00 | file dropped in folder>
Reads: <system/URL/file>
Writes: <file/system/message>
Done when: <observable result the user checks>
Never: <the destructive action it must not do without confirmation>
```

## 6. Process mining, the cheap version (when the day is too big to map by hand)

Enterprises pay for "process mining": collect timestamps of events from
the tools a team uses, and let the data draw the process and point at the
bottleneck. The same idea costs nothing and is the right first move when
the user (or their team) has **many routines, several systems, or cannot
say where the time goes** — a judgment call, not a count. Offer it in their words: "instead of
guessing, we log for one week what happens when, and the log tells us
what to automate first".

How, with what is already there:

1. **Pull event logs you already have**, read-only: e-mail headers
   (sent/received time, subject), calendar, ticket/CRM history exports
   (status changes with timestamps), the system's own audit/history tab,
   file mtimes in Downloads/Documents, browser history export. Each row
   becomes `case_id, activity, timestamp, who, system`.
2. **Where no log exists, add a one-key logger** for one week: a
   userscript button "started/finished X" on the pages they use, or a
   tiny GUI (`templates/gui_tk.py`) with 5 buttons that appends a line to
   a CSV. Thirty seconds of the user's time per day.
3. **Analyze with pandas** (or a spreadsheet pivot): per case, the
   sequence of activities and the wait between them. Output three lists:
   most frequent paths (the real process, not the described one), longest
   waits between steps (the bottleneck — usually a hand-off or a
   "check if something arrived"), and rework loops (the same activity
   repeated per case). `pm4py` draws the process graph if a picture helps.
4. **Feed §4 with numbers**: minutes per week now come from the log, not
   from memory. The top waits become the top candidates — typically
   watchers ("tell me when it arrives") and hand-offs ("move it to the
   next system"), which are also the most deterministic.

Keep it read-only, anonymous (`who` = role, not name) and time-boxed
(one or two weeks). It is a discovery tool, not a monitoring system: say
so, and delete the logger when the map is done.
