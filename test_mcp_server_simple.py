#!/usr/bin/env python3
"""
Minimal HTTP-based MCP server without external dependencies.

This version uses only Python standard library (http.server).
Use this if you don't want to install FastAPI/uvicorn.

Usage:
    python test_mcp_server_simple.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
from typing import Any, Dict, List


# Available tools
TOOLS = [
    {
        "name": "echo",
        "description": "Echo back the input message",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message to echo back"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "add",
        "description": "Add two numbers together",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "get_time",
        "description": "Get the current server time",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def execute_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute a tool and return results."""
    if name == "echo":
        message = arguments.get("message", "")
        return [{"type": "text", "text": f"Echo: {message}"}]

    elif name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a + b
        return [{"type": "text", "text": f"The sum of {a} and {b} is {result}"}]

    elif name == "get_time":
        now = datetime.now().isoformat()
        return [{"type": "text", "text": f"Current server time: {now}"}]

    else:
        raise ValueError(f"Unknown tool: {name}")


class MCPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP protocol."""

    def do_GET(self):
        """Handle GET requests (health check)."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        response = {
            "status": "running",
            "server": "test-mcp-server-simple",
            "version": "1.0.0",
            "tools_count": len(TOOLS),
            "tools": [tool["name"] for tool in TOOLS]
        }

        self.wfile.write(json.dumps(response, indent=2).encode())

    def do_POST(self):
        """Handle POST requests (JSON-RPC)."""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            request_data = json.loads(body)

            # Extract JSON-RPC fields
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")

            print(f"📨 Received: {method}")

            # Handle methods
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "test-mcp-server-simple",
                        "version": "1.0.0"
                    }
                }
                print(f"✅ Initialized")

            elif method == "tools/list":
                result = {"tools": TOOLS}
                print(f"✅ Listed {len(TOOLS)} tools")

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                print(f"🔧 Calling '{tool_name}' with {arguments}")

                content = execute_tool(tool_name, arguments)
                result = {"content": content}
                print(f"✅ Tool executed")

            else:
                # Method not found
                self.send_error_response(-32601, f"Method not found: {method}", request_id)
                return

            # Send success response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response = {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }

            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            print(f"❌ Error: {e}")
            self.send_error_response(-32700, f"Parse error: {str(e)}", None)

    def send_error_response(self, code: int, message: str, request_id):
        """Send JSON-RPC error response."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        response = {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": request_id
        }

        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server(port=8080):
    """Start the HTTP server."""
    server = HTTPServer(("0.0.0.0", port), MCPHandler)

    print("=" * 60)
    print("🚀 Starting Simple MCP Server (stdlib only)")
    print("=" * 60)
    print(f"Tools: {len(TOOLS)} available")
    print("  - " + "\n  - ".join(tool["name"] for tool in TOOLS))
    print(f"\n📍 Server: http://localhost:{port}")
    print("\n⚙️  nanobot config:")
    print(f"""
{{
  "tools": {{
    "mcp": {{
      "enabled": true,
      "servers": {{
        "test": {{
          "transport": "http",
          "url": "http://localhost:{port}"
        }}
      }}
    }}
  }}
}}
    """)
    print("=" * 60)
    print(f"\n🔥 Server running on port {port}")
    print("Press CTRL+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        server.shutdown()


if __name__ == "__main__":
    run_server()
