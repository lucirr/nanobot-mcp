"""MCP tool wrapper that adapts MCP tools to nanobot's Tool interface."""

from typing import Any, TYPE_CHECKING
from loguru import logger
from nanobot.agent.tools.base import Tool

if TYPE_CHECKING:
    from nanobot.mcp.client import MCPClient


class MCPToolWrapper(Tool):
    """Wraps an MCP tool as a nanobot Tool."""

    def __init__(
        self,
        mcp_client: "MCPClient",
        tool_definition: dict[str, Any]
    ):
        self._client = mcp_client
        self._definition = tool_definition
        self._tool_name = tool_definition["name"]
        self._server_name = mcp_client.server_name

    @property
    def name(self) -> str:
        """Tool name with server prefix to avoid conflicts."""
        return f"mcp_{self._server_name}_{self._tool_name}"

    @property
    def description(self) -> str:
        """Tool description annotated with server name."""
        desc = self._definition.get("description", "")
        return f"[MCP:{self._server_name}] {desc}"

    @property
    def parameters(self) -> dict[str, Any]:
        """Tool parameters in JSON Schema format."""
        # MCP uses JSON Schema - directly compatible with nanobot!
        return self._definition.get("inputSchema", {
            "type": "object",
            "properties": {}
        })

    async def execute(self, **kwargs: Any) -> str:
        """Execute the MCP tool and return string result."""
        try:
            logger.debug(f"Executing MCP tool {self._tool_name} with args: {kwargs}")

            # Call MCP server
            result = await self._client.call_tool(self._tool_name, kwargs)

            # Convert MCP result to string
            return self._format_result(result)

        except Exception as e:
            error_msg = f"Error calling MCP tool {self._tool_name}: {e}"
            logger.error(error_msg)
            return error_msg

    def _format_result(self, result: Any) -> str:
        """Format MCP result to string."""
        # MCP call_tool returns a CallToolResult object with content array
        if hasattr(result, 'content'):
            # Format content array
            parts = []
            for item in result.content:
                if hasattr(item, 'type') and item.type == 'text':
                    parts.append(item.text)
                elif hasattr(item, 'text'):
                    # Fallback if type is not explicitly set
                    parts.append(item.text)
            return "\n".join(parts) if parts else str(result)

        # Fallback to string conversion
        return str(result)
