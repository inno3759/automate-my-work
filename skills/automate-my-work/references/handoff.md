# Handoff — the user must be able to operate it alone

Deliver one folder, one README in their language, one way to run, one way
to stop, one place to look when it fails. Then do a real run together.

## README template (fill every line; plain words; no jargon)

```
# <Name of the automation>

## What it does
One paragraph: "Every weekday at 08:00 it opens <system>, gets the new
<things>, saves them in <folder/spreadsheet> and sends you a message on
<channel> only if something needs your attention."

## How to run it by hand
Double-click "<shortcut name>" on the Desktop.   (or: the button "<label>" on the page <site>)

## How to know it worked
Open logs/run.log — the last line says "<date>: 3 new, 12 skipped, 0 errors".
(or: the message on <channel> / the new rows in <spreadsheet>)

## When it fails
- "needs you to log in again": run "<shortcut> — Log in" and log in once.
- "<site> did not answer": nothing to do, it retries at the next run.
- anything else: send me logs/debug.log.

## How to stop or pause it
<the one command or the checkbox in Task Scheduler / Violentmonkey toggle>

## Where things are
Folder: ~/Automations/<name>/   Settings: .env (never share)   Log: logs/

## Ideas for later (things you did not pick this time)
- <opportunity 2> — would save ~N min/week
- <opportunity 3>
- Installing <tool/MCP> would let Claude <benefit>.
```

## The walkthrough (do it, do not just write it)

1. Run it with them watching (`--dry-run` first, then real).
2. Run it again: show "0 new" — explain "it remembers what it already did".
3. Show them the log line and where the output landed.
4. Trigger the schedule (or press the page button) once for real.
5. Break it on purpose once (turn off Wi-Fi / log out) and show the
   message they will get. Restore.
6. Read the README aloud with them; fix any sentence they do not get.

## What NOT to leave behind

- Terminal instructions as the only way to run something.
- Credentials in code, in the README, in a screenshot.
- Their name, e-mail, company or hostname inside the code or file names.
- A fallback path you did not test ("should work if…"). Remove it and
  write what you measured instead.
- A schedule you did not see fire.
