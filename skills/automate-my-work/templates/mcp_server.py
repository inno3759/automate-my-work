"""Expose the automation's core functions to Claude as MCP tools.

    uv add "mcp[cli]"
    Claude Desktop → claude_desktop_config.json:
      "mcpServers": {"NAME": {"command": "uv", "args": ["run", "--directory", "<this folder>", "mcp_server.py"]}}
    Claude Code → claude mcp add NAME -- uv run --directory <this folder> mcp_server.py

Rules: read-only tools by default; a tool that writes takes confirm=True;
docstrings say exactly what comes back (the model reads them).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("NAME")


@mcp.tool()
def list_items(since: str | None = None, limit: int = 50) -> list[dict]:
    """Items fetched by the automation, newest first.

    since: ISO date (YYYY-MM-DD) to filter; limit: max rows.
    Returns dicts with key, date (ISO), title, status, url.
    """
    # from core import fetch_items; return fetch_items(since=since)[:limit]
    return []


@mcp.tool()
def run_now(dry_run: bool = True) -> str:
    """Run the automation once. dry_run=True only reports what WOULD change.

    Returns the human log line ("3 new, 12 skipped, 0 errors").
    """
    # from core import run; return run(dry=dry_run)
    return "not implemented"


@mcp.tool()
def send(key: str, confirm: bool = False) -> str:
    """Send/submit the item identified by key. Does nothing unless confirm=True."""
    if not confirm:
        return f"Would send {key}. Call again with confirm=True."
    return f"sent {key}"


if __name__ == "__main__":
    mcp.run()
