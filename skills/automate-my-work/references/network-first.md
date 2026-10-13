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
HAR. On a big HAR start with `--surface`: one line per **endpoint** (ids
in the path collapsed to `{n}`/`{uuid}`/`{hex}`/`{date}`, call count,
whether it carries an auth header), so 400 requests read as "6 endpoints".
The digest hides token-looking query values and password/token body fields
(`***`) so it can be pasted into a chat; add `--sensitive-value X` for
anything else the user showed you. This only changes what is printed — the
HAR, `storage_state.json` and the tokens the automation will use are
intact; `--show-secrets` when you need the values to build the replay.

## 1b. When it isn't a browser — capture one layer down

DevTools/HAR only see a browser. A desktop program, a phone app on the
same Wi-Fi, or a 40-year-old client shows nothing there. Capture below the
app. Three cases, **different answers — do not treat them the same**:

| What it is | Observe with | Replay |
|-|-|-|
| **Electron** desktop app (Slack/Discord/Notion-style; "Chrome in a box": `resources/app.asar` next to the .exe) | **unpack and read, no capture**: `npx @electron/asar extract app.asar out/` → grep the JS for `fetch(`, `axios`, `baseURL`, `"/api/`, `Authorization` — endpoints, header names and the login flow are in plain text. Token at runtime: `%APPDATA%/<app>/Local Storage` / `Cookies` (SQLite) or the app's own config file. Only if that is not enough, the mitmproxy row below | ordinary HTTP — §2–§4 unchanged. Best case, 2 minutes. |
| Desktop/mobile app over HTTPS (most business software) | system proxy → **mitmproxy** (`mitmweb`) + install its CA cert so TLS decodes; save a flow, `har_digest.py` reads it like any HAR | ordinary HTTP once decoded — §2–§4 unchanged. |
| Non-HTTP / binary protocol (custom TCP port, DB wire, message bus) | **Wireshark** to see the bytes and reconstruct the exchange | case by case; sometimes you learn enough to script the calls, sometimes you stop and say so |
| Green-screen / terminal (COBOL, 3270, AS/400, DOS-era client, telnet/SSH TUI) | it is a **character stream, not requests** — never packet-replay a stateful session | terminal scripting, not HTTP → unblockers.md §"It's an old green-screen / DOS / mainframe app" |

Rules:
- **mitmproxy needs its CA cert on the machine, and certificate pinning
  defeats it.** If the app refuses to connect through the proxy, it is
  pinned — fall back to its local data files or UI automation
  (unblockers.md §desktop), do not fight it. Same posture as the bot-manager
  row in §3.
- The user never runs these tools. Claude sets the proxy, reads the
  capture, builds the replay — the "user never opens a terminal" promise
  holds.
- Their machine, their account, their traffic — same boundary as
  everything else. Ask first on a work machine.

Once you have the request, §5's decision rule applies as written.

## 1c. Endpoints hiding in the JavaScript — read the code, no click needed

The HAR shows what the user clicked. The site's JavaScript shows
**everything the page can ask for**, including the export, the bulk
endpoint and the pagination parameter the UI never exposes. Use it when
the click did not show up in the HAR (lazy, debounced, behind a feature
flag), when you suspect a better endpoint than the one the UI uses, or
before recording at all on a site you will automate deeply.

1. Take the script URLs from the HAR (`har_digest.py --all`, the `.js`
   lines) or DevTools → Sources. Download them once; pretty-print
   (`npx prettier`, or the `{}` button in DevTools) — bundles are one line.
2. Grep for the request primitives and the strings next to them:
   `fetch(`, `axios`, `XMLHttpRequest`, `\.open\(`, `baseURL`, `"/api/`,
   `graphql`, `Authorization`, `X-CSRF`, `credentials`. Each hit is an
   endpoint candidate with its method and the header names it sends.
3. Treat what you find as a **candidate, not a fact**: a URL in the code
   proves the page *can* call it, not that it does, nor with which values.
   Confirm by calling it once from the recorded session (§2). Minified
   names and string concatenation hide some endpoints; the HAR remains
   the ground truth for what actually fired.
4. Source maps (`//# sourceMappingURL=`) when present give the original
   file names — the endpoint list reads like documentation then.

Never run the site's JS to "see what it does"; read it as text. If the
request's values come from code you cannot follow (signatures, obfuscated
hashing), that is the sign to move into the tab (§2b, outcome 3), not to
reverse the function.

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
| Bot manager that drops connections (Akamai, Cloudflare Turnstile) | do not fight it. Userscript inside the logged-in tab, or Playwright **attached to the user's own Chrome** (`record_session.py --cdp`, unblockers.md §"The site knows it's a robot") — their real browser, nothing spoofed. Copying browser cookies into curl usually makes it WORSE (cookie bound to TLS fingerprint) |

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
If Playwright's own Chromium gets treated as a robot, drive the user's
real Chrome instead: they start it with `--remote-debugging-port` and a
dedicated profile, the script does `connect_over_cdp` (recipe in
`record_session.py`). Same browser the human uses; no flags, no spoofing.

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
