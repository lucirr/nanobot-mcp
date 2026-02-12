"""MCP client wrapper supporting both HTTP and SSE transports."""

from typing import Any
from loguru import logger
import httpx

try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP SDK not installed. Install with: pip install mcp")


class MCPClient:
    """MCP client wrapper supporting HTTP and SSE transports."""

    def __init__(
        self,
        server_name: str,
        url: str,
        transport: str = "http",
        timeout: int = 30,
        headers: dict[str, str] | None = None,
        auto_reconnect: bool = True
    ):
        self.server_name = server_name
        self.url = url
        self.transport = transport.lower()
        self.timeout = timeout
        self.headers = headers or {}
        self.auto_reconnect = auto_reconnect

        # For SSE transport
        self.session: "ClientSession | None" = None

        # For HTTP transport
        self._http_client: httpx.AsyncClient | None = None
        self._request_id = 0

        # Shared state
        self._tools: list[dict] = []
        self._connected = False

        # Validate transport
        if self.transport not in ("http", "sse"):
            raise ValueError(f"Invalid transport: {transport}. Must be 'http' or 'sse'")

        if self.transport == "sse" and not MCP_AVAILABLE:
            raise ImportError("MCP SDK is not installed. Install with: pip install mcp")

    async def initialize(self) -> None:
        """Connect to MCP server and perform handshake."""
        if self.transport == "sse":
            await self._initialize_sse()
        else:
            await self._initialize_http()

    async def _initialize_http(self) -> None:
        """Initialize HTTP transport."""
        try:
            logger.info(f"Connecting to MCP server '{self.server_name}' at {self.url} (HTTP)")

            # Create HTTP client
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers
            )

            # Perform MCP initialize handshake
            init_response = await self._http_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "nanobot",
                    "version": "0.1.0"
                }
            })

            logger.debug(f"MCP server '{self.server_name}' initialized: {init_response}")

            # List available tools
            tools_response = await self._http_request("tools/list", {})
            self._tools = tools_response.get("tools", [])

            self._connected = True
            logger.info(
                f"MCP server '{self.server_name}' connected (HTTP): "
                f"{len(self._tools)} tools available"
            )
        except Exception as e:
            logger.error(f"Failed to initialize MCP server '{self.server_name}': {e}")
            raise

    async def _initialize_sse(self) -> None:
        """Initialize SSE transport (original implementation)."""
        try:
            logger.info(f"Connecting to MCP server '{self.server_name}' at {self.url} (SSE)")

            # Create SSE connection
            async with sse_client(self.url) as (read, write):
                async with ClientSession(read, write) as session:
                    self.session = session

                    # Perform MCP initialize handshake
                    await session.initialize()
                    logger.debug(f"MCP server '{self.server_name}' initialized")

                    # List available tools
                    tools_result = await session.list_tools()
                    self._tools = [tool.model_dump() for tool in tools_result.tools]

                    self._connected = True
                    logger.info(
                        f"MCP server '{self.server_name}' connected (SSE): "
                        f"{len(self._tools)} tools available"
                    )
        except Exception as e:
            logger.error(f"Failed to initialize MCP server '{self.server_name}': {e}")
            raise

    async def _http_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send JSON-RPC request via HTTP."""
        self._request_id += 1

        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params
        }

        try:
            response = await self._http_client.post(
                self.url,
                json=payload
            )
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                raise RuntimeError(f"MCP error: {result['error']}")

            return result.get("result", {})

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling MCP method '{method}': {e}")
            raise

    async def list_tools(self) -> list[dict]:
        """Get cached tool definitions."""
        return self._tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool on the MCP server."""
        if not self._connected:
            raise RuntimeError(f"MCP client '{self.server_name}' not initialized")

        if self.transport == "http":
            return await self._call_tool_http(name, arguments)
        else:
            return await self._call_tool_sse(name, arguments)

    async def _call_tool_http(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call tool via HTTP transport."""
        try:
            logger.debug(f"Calling MCP tool '{name}' via HTTP with arguments: {arguments}")

            result = await self._http_request("tools/call", {
                "name": name,
                "arguments": arguments
            })

            logger.debug(f"MCP tool '{name}' returned: {result}")

            # Convert to object-like format for consistency with SSE
            class Result:
                def __init__(self, data):
                    self.content = data.get("content", [])

            return Result(result)

        except Exception as e:
            logger.error(f"Error calling MCP tool '{name}': {e}")
            raise

    async def _call_tool_sse(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call tool via SSE transport."""
        if not self.session:
            raise RuntimeError(f"MCP client '{self.server_name}' not initialized")

        try:
            logger.debug(f"Calling MCP tool '{name}' via SSE with arguments: {arguments}")
            result = await self.session.call_tool(name, arguments)
            logger.debug(f"MCP tool '{name}' returned: {result}")
            return result
        except Exception as e:
            logger.error(f"Error calling MCP tool '{name}': {e}")
            raise

    async def close(self) -> None:
        """Close MCP connection."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        if self.session:
            # SDK handles cleanup via context managers
            self.session = None

        self._connected = False
        logger.debug(f"MCP client '{self.server_name}' closed")
