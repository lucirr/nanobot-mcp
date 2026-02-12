# MCP (Model Context Protocol) Integration Guide

nanobot now supports MCP (Model Context Protocol) client functionality, allowing you to connect to external MCP servers and use their tools within your agent.

## Features

- ✅ **HTTP** transport support (default, recommended)
- ✅ **SSE** (Server-Sent Events) transport support
- ✅ Multiple MCP servers simultaneously
- ✅ Automatic tool discovery and registration
- ✅ Graceful error handling
- ✅ Python MCP SDK integration (for SSE)

## Installation

### For HTTP Transport (Recommended)

HTTP transport is built-in and requires no additional dependencies:

```bash
# If using source install
pip install -e .

# Or reinstall from PyPI after next release
pip install --upgrade nanobot-ai
```

### For SSE Transport (Optional)

If you want to use SSE transport, install the MCP SDK:

```bash
pip install mcp
```

## Configuration

Add MCP server configuration to your `~/.nanobot/config.json`:

### HTTP Transport (Recommended)

```json
{
  "tools": {
    "mcp": {
      "enabled": true,
      "servers": {
        "filesystem": {
          "enabled": true,
          "transport": "http",
          "url": "http://localhost:8080",
          "timeout": 30
        },
        "github": {
          "enabled": true,
          "transport": "http",
          "url": "http://localhost:8081",
          "headers": {
            "Authorization": "Bearer ghp_your_github_token"
          },
          "timeout": 30
        }
      }
    }
  }
}
```

### SSE Transport (Alternative)

```json
{
  "tools": {
    "mcp": {
      "enabled": true,
      "servers": {
        "filesystem": {
          "enabled": true,
          "transport": "sse",
          "url": "http://localhost:8080/sse",
          "timeout": 30,
          "auto_reconnect": true
        }
      }
    }
  }
}
```

### Configuration Options

**Global MCP Config:**
- `enabled` (bool): Enable/disable MCP functionality (default: false)
- `servers` (dict): Dictionary of MCP server configurations

**Per-Server Config:**
- `enabled` (bool): Enable/disable this specific server (default: true)
- `transport` (string): Transport type - "http" (default) or "sse" (required)
- `url` (string): Server URL (required)
  - For HTTP: `http://localhost:8080`
  - For SSE: `http://localhost:8080/sse`
- `timeout` (int): Connection timeout in seconds (default: 30)
- `headers` (dict): Custom HTTP headers for authentication (optional)
- `auto_reconnect` (bool): Automatically reconnect on connection loss for SSE (default: true)

## Usage

### 1. Start Your MCP Server

Example using a fictional MCP server:

```bash
# Start an MCP server with SSE transport
python -m mcp.server.sse --port 8080
```

### 2. Start nanobot

Start nanobot normally. MCP tools will be automatically discovered and registered:

```bash
# Gateway mode (for chat channels)
nanobot gateway

# Interactive mode
nanobot agent

# Single command
nanobot agent -m "Use MCP tools to help me"
```

### 3. Use MCP Tools

MCP tools are automatically prefixed with `mcp_{server_name}_` to avoid naming conflicts:

```bash
nanobot agent -m "List available tools"
```

The agent will see MCP tools with descriptions like:
- `mcp_filesystem_read_file` - [MCP:filesystem] Read a file from the filesystem
- `mcp_github_create_issue` - [MCP:github] Create a new GitHub issue

## Example MCP Servers

### Official MCP Servers

You can find official MCP server implementations at:
- Filesystem: `@modelcontextprotocol/server-filesystem`
- GitHub: `@modelcontextprotocol/server-github`
- And more at: https://github.com/modelcontextprotocol

### Custom MCP Server

Create your own MCP server following the official specification:
https://modelcontextprotocol.io/

## Troubleshooting

### MCP SDK Not Installed

If you see this warning:
```
MCP SDK not installed. Install with: pip install mcp
```

Run:
```bash
pip install mcp
```

### Connection Failed

If MCP server connection fails:

1. **Check the URL**: Ensure the MCP server is running and accessible
2. **Check logs**: Run with `--logs` to see detailed error messages:
   ```bash
   nanobot agent --logs -m "test"
   ```
3. **Test connectivity**: Use curl to test the SSE endpoint:
   ```bash
   curl -N http://localhost:8080/sse
   ```

### No Tools Discovered

If MCP connects but no tools appear:

1. Check that the MCP server implements the `tools/list` capability
2. Verify the server returns valid tool definitions
3. Check nanobot logs for tool registration messages

### Tool Execution Errors

If MCP tools fail during execution:

1. Check tool parameter validation
2. Verify MCP server is responding
3. Check authentication headers if required
4. Review MCP server logs for errors

## Architecture

```
nanobot Agent
    ↓
MCPManager (manages multiple servers)
    ↓
MCPClient (connects via SSE)
    ↓
MCP Server (external)
    ↓
MCPToolWrapper (exposes as nanobot tool)
    ↓
AgentLoop (LLM uses tool)
```

## Transport Comparison

| Feature | HTTP | SSE |
|---------|------|-----|
| **Simplicity** | ✅ Very simple | ⚠️ Requires MCP SDK |
| **Stateless** | ✅ Yes | ❌ No (maintains connection) |
| **Firewall-friendly** | ✅ Very | ✅ Yes |
| **Latency** | ⚠️ Request per call | ✅ Persistent connection |
| **Reconnection** | ✅ Automatic | ⚠️ Requires auto_reconnect |
| **Dependencies** | ✅ None (httpx built-in) | ⚠️ Requires `mcp` package |

**Recommendation:** Use HTTP transport unless you need persistent connections or streaming.

## Limitations

- Tools only (Resources and Prompts support planned)
- No streaming responses yet for HTTP transport
- stdio transport not yet supported (planned)

## Future Enhancements

- [ ] stdio transport support (for local servers)
- [ ] Resources support
- [ ] Prompts support
- [ ] Streaming responses for HTTP
- [ ] Connection pooling for HTTP
- [ ] Health checks
- [ ] Metrics and monitoring
- [ ] Dynamic tool reload

## Contributing

To add new MCP transport types or features, see the implementation in:
- `nanobot/mcp/client.py` - Client implementation
- `nanobot/mcp/manager.py` - Server management
- `nanobot/mcp/tool_wrapper.py` - Tool adaptation

## Learn More

- MCP Specification: https://modelcontextprotocol.io/
- Python MCP SDK: https://github.com/modelcontextprotocol/python-sdk
- nanobot Documentation: https://github.com/HKUDS/nanobot
