"""Compact view of a HAR: the requests that matter, in order.

Usage: uv run python har_digest.py session.har [--grep TEXT] [--trace VALUE]
                                   [--surface] [--all] [--show-secrets]
                                   [--sensitive-value X ...]
Prints one line per non-asset request (method, status, type, size, url) and,
with --grep, marks the requests whose RESPONSE BODY contains TEXT — that is
how you find "the request behind the click": grep for a value you saw on
screen.
--trace VALUE walks the chain backwards (network-first.md §2b): it prints the
first response that CONTAINED the value (its origin) and every request that
later SENT it (url, header, cookie or body). Origin = a dependency to replay;
no origin = user input or computed in the page's JS.
--surface groups the requests by endpoint (method + host + path with ids
replaced by {n}/{uuid}/{hex}/{date}) — "the site has 6 endpoints", not 400
lines. Read this first on a big HAR.

Secrets: the printed output hides token-looking query values and
password/token fields in bodies, and blanks every --sensitive-value, so a
digest can be pasted into a chat. This touches ONLY what is printed — the
HAR, storage_state.json and the automation's own tokens are untouched.
--show-secrets prints everything (fine on the user's own machine while
building the replay).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from collections import defaultdict
from urllib.parse import urlsplit

SKIP_MIME = ("image/", "font/", "text/css", "video/", "audio/")
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".css", ".map")
NOISE = ("google-analytics", "googletagmanager", "doubleclick", "facebook.net", "hotjar", "sentry", "segment.io")
AUTH_HEADERS = ("authorization", "x-csrf-token", "x-xsrf-token", "x-requested-with")

# names whose VALUE is hidden in printed urls and bodies (case-insensitive)
SECRET_NAMES = r"(?:pass(?:word|wd)?|pwd|senha|token|secret|session|signature|auth|api[_-]?key|otp)"
_QUERY = re.compile(rf"([?&][\w\[\]\-]*{SECRET_NAMES}[\w\[\]\-]*=)[^&#]+", re.I)
_FIELD = re.compile(rf"(\"?[\w\-]*{SECRET_NAMES}[\w\-]*\"?\s*[:=]\s*\"?)[^\"&,\s]+", re.I)
_SEG = [
    (re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I), "{uuid}"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}(T[\d:.]+Z?)?$"), "{date}"),
    (re.compile(r"^\d+$"), "{n}"),
    (re.compile(r"^[0-9a-f]{16,}$", re.I), "{hex}"),
]

SHOW_SECRETS = False
SENSITIVE: list[str] = []


def scrub(text: str) -> str:
    """What gets printed. Never applied to the files on disk."""
    for v in SENSITIVE:
        text = text.replace(v, "***")
    if SHOW_SECRETS:
        return text
    text = _QUERY.sub(r"\1***", text)
    return _FIELD.sub(r"\1***", text)


def template(url: str) -> str:
    """/api/case/12345/doc/3fa8… → /api/case/{n}/doc/{hex}"""
    u = urlsplit(url)
    parts = []
    for seg in u.path.split("/"):
        for rx, name in _SEG:
            if rx.match(seg):
                seg = name
                break
        parts.append(seg)
    return f"{u.scheme}://{u.netloc}{'/'.join(parts)}"


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
            print(f"ORIGIN  #{i:4d} {req['method']} {scrub(req['url'][:100])}  ({where})")
        sent = _sent_where(req, value)
        if sent:
            print(f"SENT    #{i:4d} {req['method']} {scrub(req['url'][:100])}  in {', '.join(sent)}")
    if origin is None:
        print("no origin found: the value is user input or computed in the page's JS (network-first.md §2b)")
    else:
        print(f"→ request #{origin} is a dependency; trace ITS non-constant values next.")


def is_noise(e: dict) -> bool:
    url = e["request"]["url"]
    mime = e["response"].get("content", {}).get("mimeType", "")
    path = urlsplit(url).path.lower()
    return mime.startswith(SKIP_MIME) or path.endswith(SKIP_EXT) or any(n in url for n in NOISE)


def surface(entries: list[dict]) -> None:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in entries:
        groups[(e["request"]["method"], template(e["request"]["url"]))].append(e)
    print(f"{'calls':>5}  {'method':6s} {'status':8s} {'auth':5s} endpoint   (first seen → example)")
    for (method, tpl), es in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        statuses = ",".join(sorted({str(x["response"]["status"]) for x in es}))
        auth = "yes" if any(h["name"].lower() in AUTH_HEADERS for h in es[0]["request"]["headers"]) else ""
        print(f"{len(es):5d}  {method:6s} {statuses:8s} {auth:5s} {tpl[:100]}")
        print(f"{'':30s} e.g. {scrub(es[0]['request']['url'][:120])}")
    print("\nOne line = one endpoint; {n}/{uuid}/{hex}/{date} replace ids. Start from the ones with few calls and a body.")


def main() -> None:
    global SHOW_SECRETS, SENSITIVE
    ap = argparse.ArgumentParser()
    ap.add_argument("har")
    ap.add_argument("--grep", help="text to look for in response bodies")
    ap.add_argument("--trace", help="value to follow backwards: origin response + requests that send it")
    ap.add_argument("--surface", action="store_true", help="group by endpoint (path template) instead of listing")
    ap.add_argument("--all", action="store_true", help="include assets/noise")
    ap.add_argument("--show-secrets", action="store_true", help="print token/password values instead of ***")
    ap.add_argument("--sensitive-value", action="append", default=[], help="literal to blank in the output (repeatable)")
    args = ap.parse_args()
    SHOW_SECRETS, SENSITIVE = args.show_secrets, args.sensitive_value
    entries = json.loads(pathlib.Path(args.har).read_text(encoding="utf-8"))["log"]["entries"]
    if not args.all:
        entries_shown = [e for e in entries if not is_noise(e)]
    else:
        entries_shown = entries
    if args.trace:
        trace(entries, args.trace)
        return
    if args.surface:
        surface(entries_shown)
        return
    needle = (args.grep or "").lower()

    for i, e in enumerate(entries, 1):
        if not args.all and is_noise(e):
            continue
        req, res = e["request"], e["response"]
        body = res.get("content", {}).get("text") or ""
        hit = "  <== HIT" if needle and needle in body.lower() else ""
        kind = "xhr" if e.get("_resourceType") in ("xhr", "fetch") else e.get("_resourceType", "doc")
        extra_hdrs = [h["name"] for h in req["headers"] if h["name"].lower() in AUTH_HEADERS]
        post = req.get("postData", {}).get("text", "")
        post_preview = f" body={scrub(post[:80])!r}" if post else ""
        print(f"{i:4d} {req['method']:5s} {res['status']} {kind:5s} {len(body):7d}B {scrub(req['url'][:110])}{post_preview} {extra_hdrs or ''}{hit}")

    if needle:
        print("\nHIT = response body contains the text. Replay that request first (network-first.md §2).")
    if not SHOW_SECRETS:
        print("(*** = hidden secret; the HAR itself is intact. --show-secrets to see them.)")


if __name__ == "__main__":
    main()
