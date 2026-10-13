"""Record one real pass of a task: HAR with bodies, screenshots, storage state.

Usage:  uv run python record_session.py <start-url> [--out data/recording]
        uv run python record_session.py <start-url> --cdp http://127.0.0.1:9222
Needs:  uv add playwright && uv run playwright install chromium
        (--cdp needs no Chromium download: it attaches to a Chrome/Edge the
        user started themselves — see below)

The user does the task by hand in the window that opens. Press Enter in the
terminal (or close the window) when done. Output:
  <out>/session.har            every request/response with bodies
  <out>/storage_state.json     cookies + localStorage (reusable for HTTP replay)
  <out>/step_NN.png            screenshot per navigation
  <out>/steps.txt              URL + title per navigation
Run har_digest.py on the HAR next.

--cdp: attach to a REAL Chrome/Edge instead of launching Playwright's
Chromium. Use it when the site treats Playwright as a robot (instant logout,
challenge page, dropped connection) or when the login only exists in the
user's own browser. The user starts the browser once with a dedicated
profile folder (Chrome 136+ refuses remote debugging on the default
profile), logs in by hand, then runs this script:
  Windows  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
           --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\\Automations\\chrome"
  macOS    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
           --remote-debugging-port=9222 --user-data-dir="$HOME/Automations/chrome"
  Linux    google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/Automations/chrome"
  (Edge: msedge / "Microsoft Edge" with the same two flags.)
Put that line in a shortcut named "Browser for automations" so they never
type it. Nothing is spoofed: it is their browser, their profile, their
login; the script only listens. The logged-in profile is reusable for
Playwright `connect_over_cdp` later if the decision rule ends in "browser".
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import threading
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright


class HarWriter:
    """Minimal HAR 1.2 (enough for har_digest.py) when Playwright cannot record
    itself — i.e. when attached over CDP to a browser it did not launch."""

    def __init__(self) -> None:
        self.entries: list[dict] = []

    def on_response(self, res) -> None:  # noqa: ANN001
        req = res.request
        try:
            text = res.text()
        except Exception:  # redirect, no body, body already gone
            text = ""
        try:
            req_headers, res_headers = req.all_headers(), res.all_headers()
        except Exception:
            req_headers, res_headers = req.headers, res.headers
        post = req.post_data or ""
        self.entries.append(
            {
                "startedDateTime": datetime.now(timezone.utc).isoformat(),
                "request": {
                    "method": req.method,
                    "url": req.url,
                    "headers": [{"name": k, "value": v} for k, v in req_headers.items()],
                    "cookies": [],  # the Cookie header above carries them
                    "postData": {"text": post} if post else {},
                },
                "response": {
                    "status": res.status,
                    "headers": [{"name": k, "value": v} for k, v in res_headers.items()],
                    "content": {"mimeType": res_headers.get("content-type", ""), "text": text, "size": len(text)},
                },
                "_resourceType": req.resource_type,
            }
        )

    def save(self, path: pathlib.Path) -> None:
        har = {"log": {"version": "1.2", "creator": {"name": "record_session", "version": "1"}, "entries": self.entries}}
        path.write_text(json.dumps(har, ensure_ascii=False), encoding="utf-8")


def _wait_enter(done: threading.Event) -> None:
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass
    done.set()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="data/recording")
    ap.add_argument("--profile", default="data/profile", help="persistent profile dir (keeps logins)")
    ap.add_argument("--cdp", help="attach to a running Chrome/Edge, e.g. http://127.0.0.1:9222 (see docstring)")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    steps = (out / "steps.txt").open("w", encoding="utf-8")
    n = 0
    har_path = out / "session.har"
    writer: HarWriter | None = None

    with sync_playwright() as pw:
        if args.cdp:
            browser = pw.chromium.connect_over_cdp(args.cdp)
            ctx = browser.contexts[0]  # the user's logged-in profile
            writer = HarWriter()
            ctx.on("response", writer.on_response)
        else:
            ctx = pw.chromium.launch_persistent_context(
                args.profile,
                headless=False,
                record_har_path=str(har_path),
                record_har_content="embed",  # bodies inside the HAR
                viewport=None,
            )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        def on_nav(frame) -> None:  # noqa: ANN001
            nonlocal n
            if frame != page.main_frame:
                return
            n += 1
            try:
                page.screenshot(path=str(out / f"step_{n:02d}.png"))
                steps.write(f"{n:02d}\t{page.url}\t{page.title()}\n")
                steps.flush()
            except Exception:  # page mid-navigation
                pass

        page.on("framenavigated", on_nav)
        page.goto(args.url)
        print("Do the task as usual. Press Enter here when finished.", file=sys.stderr)
        done = threading.Event()
        ctx.on("close", lambda _: done.set())  # user closed the window
        threading.Thread(target=_wait_enter, args=(done,), daemon=True).start()
        while not done.is_set():
            try:
                page.wait_for_timeout(300)  # keeps Playwright's loop running: a blocking input() would starve it and lose events
            except Exception:  # page/window gone
                break
        try:
            ctx.storage_state(path=str(out / "storage_state.json"))
        except Exception:
            print("storage_state not saved (browser already closed)", file=sys.stderr)
        if writer:
            writer.save(har_path)  # the browser stays open: it is the user's
        else:
            ctx.close()  # flushes the HAR
    print(f"Saved to {out}/ — next: uv run python har_digest.py {har_path} --surface")


if __name__ == "__main__":
    main()
