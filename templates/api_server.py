"""Local HTTP surface for the core functions — for userscripts/extensions/other tools.

    uv add fastapi uvicorn python-dotenv
    uv run python api_server.py            # http://127.0.0.1:8765
Token in .env: API_TOKEN=<random>; every call sends header X-Token.
Bound to localhost; CORS only for the site origin that will call it.
"""

from __future__ import annotations

import os
import secrets

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()
TOKEN = os.environ.get("API_TOKEN") or secrets.token_urlsafe(24)
ALLOWED_ORIGINS = [o for o in os.environ.get("API_ORIGINS", "").split(",") if o]  # e.g. https://example.com

app = FastAPI(title="automation api")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["*"], allow_headers=["*"])


def auth(x_token: str | None) -> None:
    if not x_token or not secrets.compare_digest(x_token, TOKEN):
        raise HTTPException(401, "bad token")


class Item(BaseModel):
    key: str
    text: str


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/process")
def process(item: Item, x_token: str | None = Header(default=None)) -> dict:
    """TODO: call core.process(item). Idempotent: same key twice → same answer."""
    auth(x_token)
    return {"key": item.key, "done": True}


if __name__ == "__main__":
    if not os.environ.get("API_TOKEN"):
        print(f"No API_TOKEN in .env — using a temporary one: {TOKEN}")
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("API_PORT", "8765")))
