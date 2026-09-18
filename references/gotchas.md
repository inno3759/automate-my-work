# Gotchas — traps that cost whole days, generalized

Each of these was learned the hard way on real systems. They are stated as
rules; the incident that taught them is one line each. Nothing here is
site-specific.

## 1. Classify every failure in THREE bins, never two

| Bin | Means | Do |
|-|-|-|
| **Legitimate "not found" / "nothing new"** | the server answered and this is the true state | stop, no retry, no fallback (a browser would see the same) |
| **Blocked / unavailable** | non-200, captcha, bot manager page, HTML error page, "too many requests" | retry with backoff, then fallback, then report |
| **Transport** | connection dropped, timeout, DNS, TLS, browser died | translate into the SAME domain error as "blocked" and go down the SAME retry path |

Never let a non-200 or a parse failure be recorded as "nothing new": that
silently deletes work, overwrites good data with partial data, and stamps
"checked" on something that was never checked. *Incident: an outage was
parsed as "not found" for 3 days; every record was marked checked.*

Transport exceptions differ per library and are **unrelated classes**:
`requests.RequestException`, `curl_cffi.requests.exceptions.RequestException`
(derives from `OSError`), `httpx.HTTPError`, Playwright `TimeoutError`. Wrap
every network call in one helper per project that converts them. *Incident:
a bot manager dropped the TCP connection (`HTTP/2 stream not closed
cleanly`); the raw exception escaped the retry `except` and killed the job
on the first try.*

Cascade in the caller: `except NotFound: raise` (definitive) **before**
`except Exception` (fallback). Iterating candidate URLs: a transport error
on URL 1 says nothing about URL 2 — remember `last_error`, continue.

## 2. Session expiry does not always look like expiry

- Some servers **redirect to login** (easy: check the final URL).
- Others return **200 with the login page as body**. Your parser then
  fails with "table not found" — a parse error that never triggers
  re-login, so the job fails forever with a useless message. Detect the
  login page by content (2 of 3 markers: form id, username field,
  password field) on every entry request and raise `SessionExpired`.
  *Incident: a 4-week-old cookie jar; every run "parse error" for a month.*
- An **old session can pass every GET and still fail the POST** that
  changes state, returning a page with an error code and nothing done.
  Validate the *body* of state-changing responses ("scheduled", "saved",
  an id came back), not the status. On an error body: refresh session,
  retry once. *Incident: a poll loop waited 10 min for a job the server
  never accepted.*
- Re-login once per failure, under a lock (parallel workers must not
  all re-login at the same time), and never in a loop.

## 3. The HTML you fetched is not what the user sees

- Tables are often **loaded by a second AJAX request** after the page.
  Symptom: page parses fine, list is empty or short. Look for an element
  like `<div data-url=…>`, `data-cursor`, a `load more` link with
  `data-mode="ajax"`, or the XHR in the HAR. The AJAX endpoint uses the
  same cookie jar and often no CSRF.
- The AJAX may be **intermittent** (server decides per request to inline
  or lazy-load). Handle both: parse inline rows AND, if a lazy marker
  exists, fetch and **add** the AJAX rows. *Incident: a week of records
  flip-flopping between "OK" and "not found" every run.*
- **Signed/dynamic URLs** live in `data-*` attributes or inline JS
  (`data-action="…&hash=…"`). Read them from the page you just fetched;
  never hard-code them.
- `<br>` is a line break; every other whitespace run collapses. Match
  the browser's `innerText` when you derive text keys.
- Forms: send every **hidden input**, skip **`disabled`** fields (the
  browser does not send them), include the submit button's name/value
  only if the button is the one clicked, and note `<button form="id">`
  outside the `<form>`. A wrong hidden token often **re-renders the form
  silently** with 200 — treat "I got the form back" as failure.

## 4. Two-step downloads and polling

- A "document" endpoint often returns an HTML **shell** with the real
  link; follow the link, then check `Content-Type` before saving.
- Some resources only respond after a **warm-up** request set a cookie
  (open the record page first, then the file). Replay the sequence, once
  per session, and remember you did.
- "Generate → poll → download" pages have at least FOUR states: ready,
  pending, form (nothing scheduled yet), and error (server-side job
  failed). Classify all four, case-insensitively. Re-submitting while
  pending = double scheduling. Cap the poll (attempts × interval) and
  report which state you were stuck in.
- The server that serves files may be down while the site is up. Make
  that its own error so the rest of the run continues.

## 5. Logins with 2FA

- A TOTP code is valid for one use per 30-s window on many servers.
  Login + a second action in the same window (unlock, confirm) fails
  with a misleading "invalid code". Keep a consumed-window registry;
  sleep into the next window when the current one is used or has <5 s
  left. *Incident: retry after re-login failed 100% of the time.*
- Per-service secret; never fall back to another service's secret (the
  wrong code sends you debugging the wrong thing).
- Only with the user's own secret, given knowingly. Never bypass.

## 6. Dedupe: the key must never change for stored rows

If you dedupe by `(date, title)` and later "improve" the key to include a
field older rows did not store, every old row looks new and the user is
**re-notified with the entire history**. Before touching a key, ask: *for a
row already stored, does the new key compute the same value?* If not, keep
a legacy-key guard. Normalize whitespace and case in the key. Use a
partial unique index / `INSERT … ON CONFLICT DO NOTHING` so one collision
does not abort the batch. *Incident: whitespace change → the whole office
got 200 old notifications.*

Pagination by cursor can repeat the boundary row when two rows tie on the
sort key; dedupe across pages, and do not "trim duplicates" blindly — real
consecutive identical rows exist.

## 7. Outages, throttles, bot managers

- One 5xx is a hint, not proof. Before declaring "site down" (and skipping
  all work), probe one URL you know is fine. During a confirmed outage,
  **do not stamp anything** as checked/not-found.
- "Too many simultaneous queries" → back off 20 s/45 s and retry the SAME
  URL; serialize with a lock; one session per site.
- Bot managers bind cookies to the TLS/HTTP2 fingerprint of the client
  that obtained them. Copying browser cookies into curl can make it worse.
  `curl_cffi` with `impersonate="chrome"` sometimes helps for plain
  fingerprint checks; if it does not, do not keep a fallback that "should
  work" — remove it and write down what was measured, or the next
  session repeats the experiment. A fallback that only *detects* ("there
  is something new, I could not read it") is still valuable — as long as
  it does not write.

## 8. Browser automation specifics

- Prefer a **persistent profile** (`launch_persistent_context`) so a
  human login survives; keep one process at a time (lock) — a second
  launch on the same profile fails or corrupts it.
- Export `storage_state` + the UA right after login and use HTTP for the
  rest. Include the UA: some sessions are UA-bound.
- Sync Playwright inside an asyncio loop poisons the worker thread for
  every later call ("Sync API inside asyncio loop"): use the async API
  under asyncio, or run sync in a dedicated thread with its own loop.
- Restarting is not optional after changing code that a long-running
  process imported; a bind-mount or file edit does not reload modules.
- Wait for the network response you need (`expect_response`), not for a
  timeout. Dropdowns/selects populated by XHR need the response first.
- Capture `page.on("request")` to get the **exact** body the site sends;
  that is your spec for the HTTP replay.

## 9. Data hygiene

- `now()` on the server is often UTC; the user thinks local. Decide once,
  store aware datetimes, display local.
- Titles/keys: strip, collapse spaces, NFKC-normalize, drop accents only
  for matching, never for display.
- Money: integers in cents. Documents (tax ids): validate check digits,
  compare only the digits — and know that some ids are alphanumeric.
- Save every unexpected page under `data/debug/` with a timestamp; delete
  older than 14 days.

## 10. Process rules

- **Test in the real medium.** Mocks and memory both lied in the same
  task (a message size limit that turned out to be different for the API
  used). Run against the real site with `--dry-run` / `notify=False`.
- **Prove idempotence**: second run right after the first → `new = 0`.
- **Notify first, enrich later.** If a slow step (summary, download)
  fails, the basic notification must already be out.
- **Restart, then verify** after changes to anything a daemon imports.
- **Logs are for the user**: one human line per run ("3 new, 12 skipped,
  0 errors") + a technical debug file.

## When an LLM is allowed at runtime

Only for a step whose input is free text and whose rule cannot be written:
"which of these 6 folders does this e-mail belong to", "summarize this
PDF". Always:

1. A deterministic fast path first (an id/regex/lookup that resolves 80 %
   of cases with zero LLM calls).
2. Small, cheap model; strict JSON output; validated; fallback to "ask the
   human" when confidence is low.
3. Cache results by input hash; never call twice for the same input.
4. The pipeline must still work (degraded) when the LLM is down.
5. Tell the user this step costs money and can be wrong.

Everything else — navigation, parsing, transformation, scheduling — is
code. If you find yourself asking a model to "click the button", stop and
find the request.
