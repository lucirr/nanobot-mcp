"""Simple MCP test server for testing the MCP client.

This server implements the MCP (Model Context Protocol) JSON-RPC 2.0 interface
and provides a few simple test tools.

Usage:
    python tests/test_mcp_server.py
    # Server will run on http://localhost:8080

Configure in nanobot:
    {
        "tools": {
            "mcp": {
                "enabled": true,
                "servers": {
                    "test-server": {
                        "enabled": true,
                        "transport": "http",
                        "url": "http://localhost:8080",
                        "timeout": 30
                    }
                }
            }
        }
    }
"""

from datetime import datetime
from typing import Any
import asyncio
from aiohttp import web


class TestMCPServer:
    """Simple MCP server for testing."""

    def __init__(self):
        self.request_id_counter = 0

    def _create_response(self, request_id: int | str, result: dict[str, Any]) -> dict:
        """Create JSON-RPC response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    def _create_error(self, request_id: int | str, code: int, message: str) -> dict:
        """Create JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    def handle_initialize(self, params: dict) -> dict:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "test-mcp-server",
                "version": "1.0.0"
            }
        }

    def handle_tools_list(self, params: dict) -> dict:
        """Return list of available tools."""
        return {
            "tools": [
                {
                    "name": "echo",
                    "description": "Echo back the input message",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Message to echo back"
                            }
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
                            "a": {
                                "type": "number",
                                "description": "First number"
                            },
                            "b": {
                                "type": "number",
                                "description": "Second number"
                            }
                        },
                        "required": ["a", "b"]
                    }
                },
                {
                    "name": "get_time",
                    "description": "Get the current server time",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "format": {
                                "type": "string",
                                "description": "Time format (iso or unix)",
                                "enum": ["iso", "unix"]
                            }
                        }
                    }
                },
                {
                    "name": "greet",
                    "description": "Generate a personalized greeting",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name to greet"
                            },
                            "language": {
                                "type": "string",
                                "description": "Language for greeting",
                                "enum": ["en", "ko", "ja", "es"]
                            }
                        },
                        "required": ["name"]
                    }
                }
            ]
        }

    def handle_tools_call(self, params: dict) -> dict:
        """Execute a tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Execute the appropriate tool
        if tool_name == "echo":
            message = arguments.get("message", "")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Echo: {message}"
                    }
                ]
            }

        elif tool_name == "add":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            result = a + b
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Result: {a} + {b} = {result}"
                    }
                ]
            }

        elif tool_name == "get_time":
            fmt = arguments.get("format", "iso")
            now = datetime.now()

            if fmt == "unix":
                time_str = str(int(now.timestamp()))
            else:
                time_str = now.isoformat()

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Current time ({fmt}): {time_str}"
                    }
                ]
            }

        elif tool_name == "greet":
            name = arguments.get("name", "friend")
            language = arguments.get("language", "en")

            greetings = {
                "en": f"Hello, {name}!",
                "ko": f"안녕하세요, {name}님!",
                "ja": f"こんにちは、{name}さん!",
                "es": f"¡Hola, {name}!"
            }

            greeting = greetings.get(language, greetings["en"])

            return {
                "content": [
                    {
                        "type": "text",
                        "text": greeting
                    }
                ]
            }

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def handle_request(self, request: web.Request) -> web.Response:
        """Handle incoming JSON-RPC request."""
        try:
            data = await request.json()

            request_id = data.get("id", 0)
            method = data.get("method", "")
            params = data.get("params", {})

            print(f"→ Request: method={method}, id={request_id}, params={params}")

            # Route to appropriate handler
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "tools/list":
                result = self.handle_tools_list(params)
            elif method == "tools/call":
                result = self.handle_tools_call(params)
            else:
                error = self._create_error(
                    request_id,
                    -32601,
                    f"Method not found: {method}"
                )
                print(f"← Error: {error}")
                return web.json_response(error, status=404)

            response = self._create_response(request_id, result)
            print(f"← Response: {response}")
            return web.json_response(response)

        except Exception as e:
            error = self._create_error(
                request_id if 'request_id' in locals() else 0,
                -32603,
                f"Internal error: {str(e)}"
            )
            print(f"← Error: {error}")
            return web.json_response(error, status=500)


async def create_app() -> web.Application:
    """Create aiohttp application."""
    server = TestMCPServer()
    app = web.Application()
    app.router.add_post("/", server.handle_request)
    return app


def main():
    """Run the test MCP server."""
    print("=" * 60)
    print("Test MCP Server")
    print("=" * 60)
    print("Starting server on http://localhost:8080")
    print("\nAvailable tools:")
    print("  - echo: Echo back a message")
    print("  - add: Add two numbers")
    print("  - get_time: Get current server time")
    print("  - greet: Generate a personalized greeting")
    print("\nConfigure in ~/.nanobot/config.json:")
    print('  "tools": {')
    print('    "mcp": {')
    print('      "enabled": true,')
    print('      "servers": {')
    print('        "test-server": {')
    print('          "enabled": true,')
    print('          "transport": "http",')
    print('          "url": "http://localhost:8080",')
    print('          "timeout": 30')
    print('        }')
    print('      }')
    print('    }')
    print('  }')
    print("\nPress Ctrl+C to stop")
    print("=" * 60)

    web.run_app(create_app(), host="localhost", port=8080)


if __name__ == "__main__":
    main()
