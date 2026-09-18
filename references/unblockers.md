# Unblockers — what the user thinks is impossible, and how it is not

Non-technical people give up at the first wall: "it asks a code on my
phone", "there is a captcha", "it only works in the app", "it is a PDF".
Every one of these has a known workaround. **Always tell them the wall is
passable, what it costs, and offer to do it** — they cannot ask for what
they do not know exists.

Rule for every item: their own account, their own data, a site they already
use by hand. Say when a workaround may conflict with a site's terms of use
and let them decide. Prefer an official API/export when one exists.

## "It asks a code from my phone" (2FA / OTP)

The code is generated from a **secret** that the site showed once as a QR
code. If we have the secret, the script generates the same codes.

Tell them:
1. Go to the site's security settings → "reset / re-configure the
   authenticator app". A new QR appears.
2. **Scan it with an exportable authenticator** (2FAS, Aegis, Ente Auth,
   Bitwarden) so THEY keep working as before — and take a screenshot of
   the same QR (or press "can't scan? show the key").
3. Give the screenshot/key to Claude. `templates/otp_from_qr.py` decodes
   the QR (`otpauth://totp/...?secret=...`) and stores the secret in
   `.env` as `SITE_TOTP_SECRET`. From then on `pyotp.TOTP(secret).now()`
   is the code.
4. Gotchas §5 apply: one code per 30-s window; keep a consumed-window
   registry.

Say clearly: the secret is as sensitive as the password; it lives only in
`.env`; anyone with it can generate codes. If the site allows several
authenticators, do not reset — add one.

SMS/e-mail codes: read the mailbox via IMAP/Graph (the code arrives as
text); SMS needs an Android forwarding app or a virtual number — offer it,
mark it fragile.

## "There is a captcha"

Order of attempts:
1. **Is the captcha really needed?** Often only the login has one and the
   session then lasts days/weeks → log in by hand once (Playwright headed
   or their own browser), export cookies, automate the rest by HTTP.
   Renew when expired. This solves most cases with zero cost.
2. **Does the site offer an API, export, RSS, e-mail digest?** Use that.
3. **Userscript inside their logged-in tab** — the captcha was already
   solved by the human; the automation runs after.
4. **Captcha-solving services** (2Captcha, CapSolver, Anti-Captcha and
   similar: an API that returns the token for reCAPTCHA/hCaptcha/
   Turnstile/image captchas, ~US$1–3 per 1000). Offer it when 1–3 do not
   apply and the task is worth it. Say: paid, may violate the site's
   terms, only for their own account, can stop working when the site
   changes. Implement as a pluggable function
   `solve_captcha(site_key, url) -> token` posted in the same field the
   browser would send.
5. If the site actively fights automation (bot manager dropping
   connections, fingerprint challenges), say so and stop at 3. Do not
   escalate through fingerprint spoofing.

## "It only works inside the app / desktop program"

- Most desktop apps talk to a server: capture with a proxy (mitmproxy,
  `HTTP_PROXY`, or Wireshark for non-HTTP) → replay. Ask before doing
  this on a work machine.
- Many store data locally: SQLite/Access/CSV under `%APPDATA%`/
  `~/Library/Application Support` → read the file directly (read-only).
- Office apps: automate with their own object model (`win32com` Excel/
  Outlook, AppleScript/JXA for Mail/Numbers) — no clicking.
- Truly click-only legacy apps: `pyautogui` + image matching, last resort;
  label it fragile; keep the window layout fixed.

## "It is a PDF / a scan / an image"

- Text PDF: `pypdf`/`pdfplumber` → text/tables. Bookmarks/outline give
  the document structure.
- Scanned: OCR (`tesseract` + language pack; `ocrmypdf` for whole files).
  Threshold: page with <40 chars of text = image page. Cache OCR results
  per file; never OCR twice.
- Photos of documents: same, after deskew; expect ~95 % words, verify
  numbers with check digits when they have them.

## "It is a spreadsheet someone e-mails me" / "it is in Google Sheets"

- Attachments: IMAP/Graph fetch by rule → `openpyxl`/`pandas`.
- Google Sheets: official API with a service account (share the sheet
  with it) → read/write ranges; no browser.
- Excel on a shared drive: read/write the file directly; write to a copy,
  then replace atomically; never while the user has it open (lock file
  `~$name.xlsx` present = skip).

## "The site logs me out all the time"

Session bound to something. Measure which (network-first §2): cookie
only, UA, IP, TLS fingerprint. Refresh strategy per finding: re-login by
HTTP, or keep a persistent browser profile and re-export. Detect expiry
by content (gotchas §2), never by waiting for a parse error.

## "I have to be at the office computer"

- The script can run there on a schedule (Task Scheduler) and send the
  result to their phone (Telegram/e-mail).
- Or move it to a small always-on machine (a mini PC, a Raspberry Pi, a
  US$5 VPS) — offer when the office PC sleeps or is shared. VPN/IP
  restrictions: the office machine remains the runner; the result travels.

## "It is a WhatsApp / Telegram / Slack message"

Telegram: a bot is 5 minutes (token from @BotFather) — best notification
channel for these tools. WhatsApp: Cloud API needs a Meta business setup
(offer; more paperwork), Slack/Teams: incoming webhooks in 2 minutes.

## "Someone has to check it before sending"

Build the tool to **prepare** and stop: a draft, a preview page, a
"Send" button. The human approves in one click. This is not a
limitation; it is how most automation should ship.

## "It changes every month"

Selectors change; APIs rarely do. That is another reason for network-first.
Log the shape of what you parse (counts, first row) so drift is visible
before it hurts; alert on "0 rows" when yesterday had 50.
