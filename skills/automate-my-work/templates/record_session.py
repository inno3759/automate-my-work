"""Record one real pass of a task: HAR with bodies, screenshots, storage state.

Usage:  uv run python record_session.py <start-url> [--out data/recording]
Needs:  uv add playwright && uv run playwright install chromium

The user does the task by hand in the window that opens. Press Enter in the
terminal (or close the window) when done. Output:
  <out>/session.har            every request/response with bodies
  <out>/storage_state.json     cookies + localStorage (reusable for HTTP replay)
  <out>/step_NN.png            screenshot per navigation
  <out>/steps.txt              URL + title per navigation
Run har_digest.py on the HAR next.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

from playwright.sync_api import sync_playwright


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="data/recording")
    ap.add_argument("--profile", default="data/profile", help="persistent profile dir (keeps logins)")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    steps = (out / "steps.txt").open("w", encoding="utf-8")
    n = 0

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            args.profile,
            headless=False,
            record_har_path=str(out / "session.har"),
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
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass
        ctx.storage_state(path=str(out / "storage_state.json"))
        ctx.close()  # flushes the HAR
    print(f"Saved to {out}/ — next: uv run python har_digest.py {out / 'session.har'}")


if __name__ == "__main__":
    main()
