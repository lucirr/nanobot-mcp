#!/usr/bin/env python3
"""
Simple HTTP-based MCP server for testing nanobot MCP client.

This server implements the MCP protocol over HTTP using JSON-RPC 2.0.
It provides several test tools for verification.

Usage:
    python test_mcp_server.py

Then configure nanobot with:
    {
      "tools": {
        "mcp": {
          "enabled": true,
          "servers": {
            "test": {
              "transport": "http",
              "url": "http://localhost:8080"
            }
          }
        }
      }
    }
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
from typing import Any, Dict, List

app = FastAPI(title="Test MCP Server")

# Server info
SERVER_INFO = {
    "name": "test-mcp-server",
    "version": "1.0.0"
}

# Available tools
TOOLS = [
    {
        "name": "echo",
        "description": "Echo back the input message",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to echo back"
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
            "properties": {},
            "required": []
        }
    },
    {
        "name": "reverse_string",
        "description": "Reverse a string",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to reverse"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "multiply",
        "description": "Multiply two numbers",
        "inputSchema": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "First number"
                },
                "y": {
                    "type": "number",
                    "description": "Second number"
                }
            },
            "required": ["x", "y"]
        }
    }
]


def execute_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute a tool and return results in MCP content format."""

    if name == "echo":
        message = arguments.get("message", "")
        return [
            {
                "type": "text",
                "text": f"Echo: {message}"
            }
        ]

    elif name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a + b
        return [
            {
                "type": "text",
                "text": f"The sum of {a} and {b} is {result}"
            }
        ]

    elif name == "get_time":
        now = datetime.now().isoformat()
        return [
            {
                "type": "text",
                "text": f"Current server time: {now}"
            }
        ]

    elif name == "reverse_string":
        text = arguments.get("text", "")
        reversed_text = text[::-1]
        return [
            {
                "type": "text",
                "text": f"Reversed: {reversed_text}"
            }
        ]

    elif name == "multiply":
        x = arguments.get("x", 0)
        y = arguments.get("y", 0)
        result = x * y
        return [
            {
                "type": "text",
                "text": f"{x} × {y} = {result}"
            }
        ]

    else:
        raise ValueError(f"Unknown tool: {name}")


@app.post("/")
async def handle_jsonrpc(request: Request):
    """Handle JSON-RPC 2.0 requests."""
    try:
        body = await request.json()

        # Extract JSON-RPC fields
        jsonrpc = body.get("jsonrpc")
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        # Validate JSON-RPC version
        if jsonrpc != "2.0":
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: jsonrpc must be '2.0'"
                },
                "id": request_id
            })

        print(f"📨 Received: {method}")

        # Handle different MCP methods
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": SERVER_INFO
            }
            print(f"✅ Initialize: {result}")

        elif method == "tools/list":
            result = {
                "tools": TOOLS
            }
            print(f"✅ Tools listed: {len(TOOLS)} tools")

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            print(f"🔧 Calling tool '{tool_name}' with args: {arguments}")

            try:
                content = execute_tool(tool_name, arguments)
                result = {
                    "content": content
                }
                print(f"✅ Tool executed successfully")
            except Exception as e:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution error: {str(e)}"
                    },
                    "id": request_id
                })

        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                },
                "id": request_id
            })

        # Return successful response
        return JSONResponse({
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            },
            "id": None
        })


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "server": SERVER_INFO,
        "protocol": "MCP over HTTP (JSON-RPC 2.0)",
        "tools_count": len(TOOLS),
        "tools": [tool["name"] for tool in TOOLS]
    }


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Test MCP Server")
    print("=" * 60)
    print(f"Server: {SERVER_INFO['name']} v{SERVER_INFO['version']}")
    print(f"Protocol: MCP over HTTP (JSON-RPC 2.0)")
    print(f"Tools: {len(TOOLS)} available")
    print("  - " + "\n  - ".join(tool["name"] for tool in TOOLS))
    print("\n📍 Endpoints:")
    print("  - Health: http://localhost:8080/")
    print("  - MCP: http://localhost:8080/ (POST)")
    print("\n⚙️  nanobot config:")
    print("""
{
  "tools": {
    "mcp": {
      "enabled": true,
      "servers": {
        "test": {
          "transport": "http",
          "url": "http://localhost:8080"
        }
      }
    }
  }
}
    """)
    print("=" * 60)
    print("\n🔥 Server starting on http://localhost:8080")
    print("Press CTRL+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
