# Network first — find the request behind the click and replay it

A browser click is sugar on top of an HTTP request. Replaying the request
is 10-100× faster, has no window to break, needs no browser installed on
the schedule machine, and survives redesigns of the page better than
selectors do. Drive a browser only when the decision rule at the end says so.

## 1. Capture

From the HAR recorded in discovery (or DevTools → Network with "Preserve
log" + "Disable cache"), for each step of the task:

1. Filter by **Fetch/XHR** and **Doc** first; ignore images/fonts/analytics.
2. Find the request whose response contains the data the user looked at or
   whose timing matches the click. Search the HAR for a value you saw on
   screen (a name, an amount) — the request whose response body contains it
   is the one.
3. Note: method, URL (with query), **request headers that are not default**
   (Authorization, X-CSRF-*, X-Requested-With, Accept, Content-Type,
   Referer/Origin), cookies, body (form vs JSON vs multipart), response
   type (JSON / HTML fragment / file / redirect).
4. Note the **sequence**: which earlier request set the cookie or issued
   the token the later one needs. The click is rarely a single request.

Tools: `templates/har_digest.py` prints a compact table of the
non-asset requests with sizes and a body preview — read that, not the raw
HAR.

## 2. Replay by hand before writing any code

Right-click → "Copy as cURL" from DevTools, or build it from the HAR. Run
it. Compare the body to what the browser got (same count of rows? same
first row?). Then **remove headers one at a time** until it breaks — keep
only what is required. Then run it again 60 seconds later and after
closing the browser: does it still work? That tells you what the session
is bound to.

Three outcomes:
- **Works with cookies only** → replay with a stored cookie jar; refresh
  the jar by logging in (form POST) or by a browser login once (export
  `storage_state`) when it expires.
- **Works with a bearer/API key** → best case; store the token, learn how
  it is renewed (refresh endpoint, login response), renew before expiry.
- **Only works inside the page** (token in JS memory, signed URL per
  render, WebSocket) → userscript/extension running in the tab, calling
  `fetch()` with `credentials: 'include'`. The browser owns the session;
  your code just fires the requests.

## 2b. Trace the chain backwards — the request is rarely alone

The request that does the work usually needs values that earlier requests
produced: a record id from a search, a token from the page HTML, a cookie
from a warm-up GET, a signed URL from a JSON response. Replaying only the
last request works today (the values are still valid) and breaks tomorrow.

Method — start from the final request and walk backwards:

1. List every **non-constant value** in it: path segments, query params,
   body fields, headers, cookies. Ignore what is obviously static.
2. For each value, find the **earliest response** in the HAR that contains
   it (`har_digest.py --trace VALUE` prints where it first appeared and
   every request that later sent it). Three outcomes:
   - it came from a response → that request is a **dependency**; repeat
     step 1 on it;
   - it came from the user (what they typed, chose, uploaded) → it is an
     **input** of the tool;
   - it appears nowhere earlier → it is computed in the page's JS
     (timestamp, hash, signature). If it looks like a timestamp/uuid,
     generate it; if it looks like a signature, that is the sign to move
     the automation into the tab (userscript) rather than reverse the JS.
3. The dependencies form a small tree with the login/entry page at the
   root. **Replay only that tree, in order**, carrying the values forward.
   Everything else in the HAR (assets, analytics, prefetches, the 40
   requests the page fires for its own UI) is not needed.
4. Write the chain down in the script as named steps (`entry → search →
   detail → download`) so the next reader sees the shape without a HAR.

Signs you missed a dependency: it works right after recording and fails
an hour/a day later; it works in the browser but not in curl with the
same headers; the server answers with an empty or generic page instead of
an error. Re-record and trace again.

## 3. Authentication patterns, from easiest to hardest

| Pattern | How to replay |
|-|-|
| Public GET | just do it; add a UA and a Referer if it 403s |
| Cookie session, form login | POST the login form (copy hidden inputs from the GET), keep the jar, detect "session expired" (see gotchas §2), re-login once |
| Bearer token from a login JSON | POST creds → token; keep expiry; refresh route if any |
| CSRF token in the page/meta/cookie | GET page → parse token → send in header/body of POST; **same jar** |
| SSO / 2FA / captcha at login | log in ONCE in a real browser (Playwright persistent profile or their own), export cookies, replay by HTTP; refresh when expired. TOTP can be automated only if the user gives their own secret — one code per 30-s window (gotchas §5) |
| Token only exists in the tab (JS-generated, per-render signatures) | userscript in the tab; do not try to reproduce the JS |
| Bot manager that drops connections (Akamai, Cloudflare Turnstile) | do not fight it. Userscript inside the logged-in tab or stop. Copying browser cookies into curl usually makes it WORSE (cookie bound to TLS fingerprint) |

## 4. Reading the responses

- JSON: use it as-is. Map fields by looking at what the UI shows.
- HTML page: parse with BeautifulSoup/`lxml`; select by stable attributes
  (ids, `name=`, `data-*`) over classes. Save the raw HTML on any parse
  failure (`data/debug/<ts>.html`) — you will need it.
- HTML fragment via AJAX: the "page" you got may show an **empty table**
  that the browser fills later — the real data is a second request
  (gotchas §3).
- File download: often a 2-step — an endpoint returns an HTML *shell* with
  a link to the actual file, or a "generate" POST followed by polling until
  ready (gotchas §4). Stream to disk; check `Content-Type` before saving as
  PDF.
- Pagination: cursor/keyset (`data-cursor`, `nextPageToken`) or offset.
  Loop until the "has more" flag is false; **dedupe across page
  boundaries** (gotchas §6).
- Dates: servers speak UTC or local silently. Check one known row against
  the UI before trusting a timezone.

## 5. Decision rule — HTTP replay vs userscript vs browser automation

```
Can the request be replayed with curl outside the browser (after removing
optional headers) AND the login can be renewed without a human?
  yes → Python script (requests / httpx). Schedule it.
  no  → Is the user on that site when the task happens, or can they be?
          yes → Userscript / extension (fetch inside the tab).
          no  → Playwright with a persistent profile (login once by hand,
                cookies survive). Document WHY in the README; check the
                site's outage/anti-bot behavior before promising a schedule.
```
Playwright is also fine as the **login step only**: log in headed once,
`context.storage_state(path=…)`, then everything else by HTTP. Renew the
state when a request comes back as a login page.

## 6. Being a good citizen

- One session per site, sequential requests, 0.5–2 s jitter between them,
  `Accept-Encoding: gzip`. Never parallelize against a small site.
- Honour a 429/`Retry-After`; back off 20 s → 45 s → give up and report.
- Cache what does not change (lookup tables, the first page) to disk.
- Identify honestly where a UA is needed: a normal browser UA is fine; do
  not impersonate a specific person.
- If the site publishes an API or export (CSV, iCal, RSS, OData), use it
  instead of scraping the UI — check `/api`, `/export`, `?format=json`,
  robots.txt, the footer, the "integrations" page.
