# Composability — make the tools reusable by people, by scripts, and by Claude

A one-off script is fine. But after the second automation, the user has a
**toolbox**. Design for that from the start, and tell the user it exists:
"the part that logs into X and fetches Y is now a function; the next tool
that needs X reuses it, and Claude can call it directly".

## 1. Core / surfaces split

```
~/Automations/<name>/
├── core/            pure functions: login(), fetch_items(), write_sheet()  — no printing, no CLI
├── run.py           CLI surface (schedule, shortcut)
├── gui.py           window surface (optional)
├── api.py           HTTP surface (optional): FastAPI on localhost
└── mcp_server.py    Claude surface (optional): the same functions as MCP tools
```
Surfaces never contain logic. Shared pieces across automations go to
`~/Automations/_shared/` as a small local package (`uv add --editable
../_shared`): the site session, notifications, the state store, OCR.

## 2. Local API endpoints (`templates/api_server.py`)

When two tools need the same capability, or a userscript/extension in the
browser needs something only Python can do (files, OCR, a desktop app),
expose it on `http://127.0.0.1:<port>`:

- FastAPI, bound to localhost only, a random token in `.env` checked on
  every call (`X-Token`), CORS restricted to the site's origin when a
  userscript will call it.
- One endpoint per capability, JSON in/out, idempotent where possible.
- Run it as a user service (`scheduling.md`) with `Restart=on-failure`.
- The userscript then does `fetch('http://127.0.0.1:8765/ocr', …)` — the
  browser button now reaches the whole machine.

## 3. MCP server (`templates/mcp_server.py`) — give the tools to Claude

Once a capability exists as a function, wrap it as an MCP tool so Claude
(Desktop or Code) can call it in conversation: "get today's items from X
and draft the replies". Offer this whenever the user does a task that is
part automatic (fetch/transform) and part judgment (write, decide).

- `mcp` package (FastMCP): each function becomes `@mcp.tool()` with a
  docstring that says exactly what it returns. Type hints = the schema.
- Read-only by default; tools that write take an explicit `confirm: bool`.
- Register in Claude Desktop (`claude_desktop_config.json` →
  `mcpServers.<name>.command = "uv", args = ["run", "--directory",
  "<folder>", "mcp_server.py"]`) or Claude Code (`claude mcp add`). Do
  the registration for them and verify the tool shows up.
- The nudge (setup.md) applies: "if I register this as an MCP, you can
  just ask me 'what came in today?' and I answer from the real data."

## 4. Outputs made for an LLM to read

When the user will paste (or Claude will read) the tool's output, shape
it for a model, not for a human:

- One file per run, Markdown or JSON, deterministic order, stable keys.
- Header with: source, timestamp, count, what changed since last run.
- Full identifiers (ids, dates ISO, amounts with currency), no truncation
  the human would tolerate.
- Long content: `summary.md` (< 2k tokens) + `full/` folder with one file
  per item; the summary links the files.
- Include the *question the tool cannot answer* explicitly ("3 items
  could not be classified: …"). That is where the LLM/human steps in.
- Also useful for humans: the same JSON feeds the spreadsheet.

## 5. When to suggest each

| The user says | Offer |
|-|-|
| "now I want the same for site B" | move session/state/notify to `_shared`, second tool reuses |
| "the button on the page should also …(something needing files/OCR)" | local API + userscript |
| "then I read it and decide" | MCP server → decide in the chat with Claude |
| "I paste the result into ChatGPT/Claude" | LLM-ready output (§4) — and an MCP if they do it daily |
| "my colleague needs it too" | API on the LAN with token, or a shared folder output; never share `.env` |

Tell them what they gained each time: "this is now a building block".
