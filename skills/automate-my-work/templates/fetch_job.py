"""Skeleton for an unattended HTTP job. Copy, rename, fill the three TODOs.

    uv init --app && uv add requests python-dotenv beautifulsoup4
    uv run python run.py --dry-run

Structure (do not remove pieces): config → lock → session → fetch → classify →
transform → write (idempotent) → notify → exit code.
Exit codes: 0 ok · 1 blocked/unavailable (retry later) · 2 needs the human
(login/config) · 3 bug.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import pathlib
import random
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent
DATA, LOGS = ROOT / "data", ROOT / "logs"
STATE = DATA / "state.json"
JAR = DATA / "cookies.json"
DEBUG_DIR = DATA / "debug"
LOCK = DATA / ".lock"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"


# ---------- three bins of failure (gotchas §1) ----------
class NotFound(Exception):  # legitimate answer: stop, no retry
    pass


class Blocked(Exception):  # non-200 / captcha / error page / transport → retry, then report
    pass


class SessionExpired(Blocked):  # re-login once, then retry
    pass


class NeedsHuman(Exception):  # bad credentials, 2FA, config missing → exit 2
    pass


# ---------- logging: one human file, one debug file ----------
def setup_logging(verbose: bool) -> logging.Logger:
    LOGS.mkdir(exist_ok=True)
    log = logging.getLogger("job")
    log.setLevel(logging.DEBUG)
    human = RotatingFileHandler(LOGS / "run.log", maxBytes=512_000, backupCount=3, encoding="utf-8")
    human.setLevel(logging.INFO)
    human.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%Y-%m-%d %H:%M"))
    debug = RotatingFileHandler(LOGS / "debug.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    debug.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    con = logging.StreamHandler()
    con.setLevel(logging.DEBUG if verbose else logging.INFO)
    for h in (human, debug, con):
        log.addHandler(h)
    return log


log = logging.getLogger("job")


# ---------- state (idempotence) ----------
def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"seen": [], "last_run": None}


def save_state(state: dict) -> None:
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    tmp.replace(STATE)  # atomic


# ---------- session with cookie jar + one request helper ----------
def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    if JAR.exists():
        s.cookies.update(json.loads(JAR.read_text()))
    return s


def save_jar(s: requests.Session) -> None:
    JAR.write_text(json.dumps(s.cookies.get_dict()))


def request(s: requests.Session, method: str, url: str, **kw) -> requests.Response:
    """Every network call goes through here: transport → Blocked, throttles → backoff."""
    kw.setdefault("timeout", 30)
    for attempt, delay in enumerate((0, 20, 45)):
        if delay:
            log.debug("backoff %ss before retry %s", delay, attempt)
            time.sleep(delay)
        try:
            r = s.request(method, url, **kw)
        except requests.RequestException as exc:  # transport → same path as blocked
            last = Blocked(f"{url} did not answer ({exc.__class__.__name__})")
            continue
        if r.status_code in (429, 502, 503, 504):
            last = Blocked(f"{url} answered {r.status_code}")
            continue
        if is_login_page(r):
            raise SessionExpired(url)
        return r
    raise last


def is_login_page(r: requests.Response) -> bool:
    """200 with the login form as body counts as expired (gotchas §2). TODO: markers of YOUR site."""
    if "text/html" not in r.headers.get("Content-Type", ""):
        return False
    body = r.text[:20000].lower()
    markers = ('id="frmlogin"', 'name="username"', 'type="password"')  # TODO
    return sum(m in body for m in markers) >= 2


def save_debug(name: str, r: requests.Response) -> pathlib.Path:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    p = DEBUG_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-{name}.html"
    p.write_bytes(r.content)
    return p


def login(s: requests.Session) -> None:
    """TODO: replay the login you observed in the HAR. Raise NeedsHuman when creds/2FA fail."""
    user, pwd = os.environ.get("SITE_USER"), os.environ.get("SITE_PASSWORD")
    if not user or not pwd:
        raise NeedsHuman("SITE_USER/SITE_PASSWORD missing in .env")
    raise NeedsHuman("login() not implemented")  # replace


# ---------- the work ----------
def fetch(s: requests.Session) -> list[dict]:
    """TODO: the request(s) behind the click. Return a list of records, each with a stable 'key'."""
    r = request(s, "GET", os.environ["SITE_URL"])
    if r.status_code == 404:
        raise NotFound(r.url)
    if r.status_code != 200:
        save_debug("unexpected", r)
        raise Blocked(f"{r.url} answered {r.status_code}")
    # parse r.json() or BeautifulSoup(r.text, "html.parser")
    return []


def write(new: list[dict], dry: bool) -> None:
    """TODO: spreadsheet / file / API. Must be safe to call with the same records twice."""
    if dry:
        log.info("dry-run: would write %d record(s)", len(new))
        return


def notify(text: str, dry: bool) -> None:
    """Failure channel the user already reads. Telegram shown; swap for e-mail/toast."""
    tok, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if dry or not tok or not chat:
        log.debug("notify skipped: %s", text)
        return
    try:
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", json={"chat_id": chat, "text": text[:4000]}, timeout=15)
    except requests.RequestException as exc:
        log.warning("notification failed: %s", exc)


# ---------- main ----------
def run(dry: bool) -> int:
    state = load_state()
    seen = set(state["seen"])
    s = session()
    time.sleep(random.uniform(0.5, 2))  # politeness jitter
    try:
        try:
            records = fetch(s)
        except SessionExpired:
            log.info("session expired, logging in again")
            login(s)
            save_jar(s)
            records = fetch(s)
    except NotFound as exc:
        log.info("nothing there (%s)", exc)
        return 0
    except Blocked as exc:
        log.info("site unavailable, will try again next run: %s", exc)
        return 1
    except NeedsHuman as exc:
        log.info("NEEDS YOU: %s", exc)
        notify(f"Automation needs you: {exc}", dry)
        return 2

    new = [r for r in records if r["key"] not in seen]
    write(new, dry)
    if not dry:
        state["seen"] = sorted(seen | {r["key"] for r in new})[-5000:]
        state["last_run"] = time.strftime("%Y-%m-%d %H:%M")
        save_state(state)
        save_jar(s)
    log.info("%d new, %d skipped, 0 errors", len(new), len(records) - len(new))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    load_dotenv(ROOT / ".env")
    DATA.mkdir(exist_ok=True)
    setup_logging(a.verbose)
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime < 3600:
        log.info("already running, skipping")
        sys.exit(0)
    LOCK.touch()
    try:
        code = run(a.dry_run)
    except Exception:
        log.exception("bug")
        notify("Automation crashed — send logs/debug.log", a.dry_run)
        code = 3
    finally:
        LOCK.unlink(missing_ok=True)
    sys.exit(code)


if __name__ == "__main__":
    main()
