# Install sarvam-mcp

Read this when MCP is missing, the user asks to set up Sarvam, or a client needs a config path.

Server is local **stdio** — the client spawns it. Full canonical docs: [sarvam-mcp INSTALLATION.md](https://github.com/sarvamai/sarvam-mcp/blob/main/docs/INSTALLATION.md).

## Setup checklist

```
- [ ] API key from https://dashboard.sarvam.ai/key-management (`sk_...`)
- [ ] Runner: uvx (preferred) or pip install sarvam-mcp (Python 3.11+)
- [ ] Auth in client env OR ~/.sarvam/credentials
- [ ] Client config added / reloaded
- [ ] Verify with a live translate or /mcp / tools list
```

### Auth (pick one)

**A. Credentials file** (works across clients; omit `env` from JSON):

```ini
# ~/.sarvam/credentials
api_key = sk_...
```

**B. Client env:** `"env": { "SARVAM_API_KEY": "sk_..." }` — wins if both set.

> **Watch where the key lands.** `.cursor/mcp.json` and `.vscode/mcp.json` are project-local — they live inside the repo. If the key goes there instead of a user-global path, add the file to `.gitignore` *before* writing it, or `git add .` ships a live `SARVAM_API_KEY`. When in doubt, use Option A (`~/.sarvam/credentials`) or a user-global config path (`~/.cursor/mcp.json`, `~/.codex/config.toml`, etc.) instead.

### Runner

| Method | `command` / args | Need |
|--------|------------------|------|
| uvx | `"command": "uvx", "args": ["sarvam-mcp"]` | [uv](https://docs.astral.sh/uv/) |
| pip | `"command": "sarvam-mcp"` | `pip install sarvam-mcp` |

## Shared config (most clients)

```json
{
  "mcpServers": {
    "sarvam": {
      "command": "uvx",
      "args": ["sarvam-mcp"],
      "env": { "SARVAM_API_KEY": "sk_..." }
    }
  }
}
```

## Per client

| Client | Where / how |
|--------|-------------|
| **Cursor** | One-click: [Add to Cursor](https://cursor.com/install-mcp?name=sarvam&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyJzYXJ2YW0tbWNwIl19). Manual: `~/.cursor/mcp.json` or `.cursor/mcp.json`. Verify: Settings → MCP → green **sarvam**. |
| **Claude Code** | `claude mcp add --scope user sarvam --env SARVAM_API_KEY=sk_... -- uvx sarvam-mcp` → verify `/mcp` |
| **Claude Desktop** | macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`. Windows: `%APPDATA%\Claude\claude_desktop_config.json`. Same JSON; full quit/reopen. |
| **VS Code Copilot** | `code --add-mcp '{"name":"sarvam","command":"uvx","args":["sarvam-mcp"],"env":{"SARVAM_API_KEY":"sk_..."}}'` **or** `.vscode/mcp.json` with top-level key `servers` (not `mcpServers`) |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` → Refresh Cascade MCP |
| **Zed** | `settings.json` → `context_servers.sarvam.command` = `{ "path": "uvx", "args": ["sarvam-mcp"], "env": { "SARVAM_API_KEY": "sk_..." } }` |
| **Codex CLI** | `codex mcp add sarvam --env SARVAM_API_KEY=sk_... -- uvx sarvam-mcp` or `~/.codex/config.toml` `[mcp_servers.sarvam]` |
| **Gemini CLI** | `gemini mcp add sarvam -e SARVAM_API_KEY=sk_... uvx sarvam-mcp` |
| **Cline / Roo** | Extension MCP settings → shared JSON above |
| **Continue** | `~/.continue/config.yaml` → `mcpServers` list with `command: uvx`, `args: [sarvam-mcp]` |
| **LM Studio** | Program → Install → Edit mcp.json → shared JSON → enable |

### VS Code `servers` shape

```json
{
  "servers": {
    "sarvam": {
      "command": "uvx",
      "args": ["sarvam-mcp"],
      "env": { "SARVAM_API_KEY": "sk_..." }
    }
  }
}
```

### Codex TOML

```toml
[mcp_servers.sarvam]
command = "uvx"
args = ["sarvam-mcp"]
env = { SARVAM_API_KEY = "sk_..." }
```

### Continue YAML

```yaml
mcpServers:
  - name: sarvam
    command: uvx
    args: [sarvam-mcp]
    env:
      SARVAM_API_KEY: sk_...
```

## Verify

Ask: *Translate "good morning" to Hindi using Sarvam.*

Or: `npx @modelcontextprotocol/inspector uvx sarvam-mcp`

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `uvx` / `sarvam-mcp` not found | Install uv, or absolute path from `pip show -f sarvam-mcp`; restart client |
| Auth errors | Check env or `~/.sarvam/credentials`; then `sarvam_tools_set_api_key` |
| Server "hangs" in a terminal | Expected for stdio — let the client spawn it |
| Slow first uvx run | Cold download; `uv tool install sarvam-mcp` |
| Stale package | `uvx sarvam-mcp@latest` or `pip install -U sarvam-mcp` |
