"""Compact view of a HAR: the requests that matter, in order.

Usage: uv run python har_digest.py session.har [--grep TEXT] [--trace VALUE] [--all]
Prints one line per non-asset request (method, status, type, size, url) and,
with --grep, marks the requests whose RESPONSE BODY contains TEXT — that is
how you find "the request behind the click": grep for a value you saw on
screen.
--trace VALUE walks the chain backwards (network-first.md §2b): it prints the
first response that CONTAINED the value (its origin) and every request that
later SENT it (url, header, cookie or body). Origin = a dependency to replay;
no origin = user input or computed in the page's JS.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from urllib.parse import urlsplit

SKIP_MIME = ("image/", "font/", "text/css", "video/", "audio/")
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".css", ".map")
NOISE = ("google-analytics", "googletagmanager", "doubleclick", "facebook.net", "hotjar", "sentry", "segment.io")


def _sent_where(req: dict, value: str) -> list[str]:
    """Places in a request where the value is sent."""
    places = []
    if value in req["url"]:
        places.append("url")
    for h in req.get("headers", []):
        if value in h["value"]:
            places.append(f"header {h['name']}")
    for c in req.get("cookies", []):
        if value in c.get("value", ""):
            places.append(f"cookie {c['name']}")
    if value in (req.get("postData", {}).get("text") or ""):
        places.append("body")
    return places


def trace(entries: list[dict], value: str) -> None:
    origin = None
    for i, e in enumerate(entries, 1):
        req, res = e["request"], e["response"]
        body = res.get("content", {}).get("text") or ""
        set_cookie = " ".join(h["value"] for h in res.get("headers", []) if h["name"].lower() == "set-cookie")
        if origin is None and (value in body or value in set_cookie):
            origin = i
            where = "set-cookie" if value in set_cookie else "response body"
            print(f"ORIGIN  #{i:4d} {req['method']} {req['url'][:100]}  ({where})")
        sent = _sent_where(req, value)
        if sent:
            print(f"SENT    #{i:4d} {req['method']} {req['url'][:100]}  in {', '.join(sent)}")
    if origin is None:
        print("no origin found: the value is user input or computed in the page's JS (network-first.md §2b)")
    else:
        print(f"→ request #{origin} is a dependency; trace ITS non-constant values next.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("har")
    ap.add_argument("--grep", help="text to look for in response bodies")
    ap.add_argument("--trace", help="value to follow backwards: origin response + requests that send it")
    ap.add_argument("--all", action="store_true", help="include assets/noise")
    args = ap.parse_args()
    entries = json.loads(pathlib.Path(args.har).read_text(encoding="utf-8"))["log"]["entries"]
    if args.trace:
        trace(entries, args.trace)
        return
    needle = (args.grep or "").lower()

    for i, e in enumerate(entries, 1):
        req, res = e["request"], e["response"]
        url = req["url"]
        mime = res.get("content", {}).get("mimeType", "")
        path = urlsplit(url).path.lower()
        if not args.all and (mime.startswith(SKIP_MIME) or path.endswith(SKIP_EXT) or any(n in url for n in NOISE)):
            continue
        body = res.get("content", {}).get("text") or ""
        hit = "  <== HIT" if needle and needle in body.lower() else ""
        kind = "xhr" if e.get("_resourceType") in ("xhr", "fetch") else e.get("_resourceType", "doc")
        extra_hdrs = [h["name"] for h in req["headers"] if h["name"].lower() in ("authorization", "x-csrf-token", "x-xsrf-token", "x-requested-with")]
        post = req.get("postData", {}).get("text", "")
        post_preview = f" body={post[:80]!r}" if post else ""
        print(f"{i:4d} {req['method']:5s} {res['status']} {kind:5s} {len(body):7d}B {url[:110]}{post_preview} {extra_hdrs or ''}{hit}")

    if needle:
        print("\nHIT = response body contains the text. Replay that request first (network-first.md §2).")


if __name__ == "__main__":
    main()
