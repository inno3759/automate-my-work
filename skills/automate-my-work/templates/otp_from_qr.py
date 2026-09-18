"""Extract the TOTP secret from a QR screenshot or an otpauth:// URL, store it in .env, print a test code.

    uv add pyotp pyzbar pillow    (Linux: sudo apt-get install -y libzbar0; macOS: brew install zbar)
    uv run python otp_from_qr.py qr.png --env-key SITE_TOTP_SECRET
    uv run python otp_from_qr.py "otpauth://totp/Site:user?secret=ABC...&issuer=Site"

The user scans the SAME QR into an exportable authenticator (2FAS, Aegis, Ente)
so they keep receiving codes; this script gives the automation the same secret.
The secret is as sensitive as a password: .env only, never logged.
"""

from __future__ import annotations

import pathlib
import sys
from urllib.parse import parse_qs, unquote, urlsplit

import pyotp


def secret_from_url(url: str) -> tuple[str, str]:
    u = urlsplit(url)
    if u.scheme != "otpauth" or u.netloc != "totp":
        raise SystemExit("not a TOTP otpauth:// URL (HOTP/other not supported)")
    q = parse_qs(u.query)
    label = unquote(u.path.lstrip("/"))
    return q["secret"][0].replace(" ", "").upper(), q.get("issuer", [label])[0]


def secret_from_image(path: str) -> tuple[str, str]:
    from PIL import Image
    from pyzbar.pyzbar import decode

    codes = [c.data.decode() for c in decode(Image.open(path))]
    for c in codes:
        if c.startswith("otpauth://"):
            return secret_from_url(c)
    raise SystemExit(f"no otpauth QR found in {path} (found: {codes or 'nothing'}) — try a sharper screenshot")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = sys.argv[1]
    key = sys.argv[sys.argv.index("--env-key") + 1] if "--env-key" in sys.argv else "SITE_TOTP_SECRET"
    secret, issuer = secret_from_url(src) if src.startswith("otpauth://") else secret_from_image(src)
    code = pyotp.TOTP(secret).now()  # validates the base32 too
    env = pathlib.Path(".env")
    lines = [ln for ln in env.read_text().splitlines() if not ln.startswith(key + "=")] if env.exists() else []
    env.write_text("\n".join([*lines, f"{key}={secret}"]) + "\n")
    print(f"{issuer}: secret saved to .env as {key}. Current code {code} — compare with the phone app.")


if __name__ == "__main__":
    main()
