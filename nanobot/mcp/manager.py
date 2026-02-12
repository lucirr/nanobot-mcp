"""MCP manager that coordinates multiple MCP server connections."""

from typing import Dict
from loguru import logger
from nanobot.mcp.client import MCPClient, MCP_AVAILABLE
from nanobot.mcp.tool_wrapper import MCPToolWrapper
from nanobot.config.schema import MCPConfig


class MCPManager:
    """Manages multiple MCP server connections."""

    def __init__(self, config: MCPConfig):
        self.config = config
        self.clients: Dict[str, MCPClient] = {}
        self.tools: list[MCPToolWrapper] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all enabled MCP servers."""
        if not MCP_AVAILABLE:
            logger.warning(
                "MCP SDK not installed. MCP functionality disabled. "
                "Install with: pip install mcp"
            )
            return

        if not self.config.enabled:
            logger.info("MCP disabled in config")
            return

        if not self.config.servers:
            logger.info("No MCP servers configured")
            return

        logger.info(f"Initializing {len(self.config.servers)} MCP servers...")

        for server_name, server_config in self.config.servers.items():
            if not server_config.enabled:
                logger.info(f"MCP server '{server_name}' disabled, skipping")
                continue

            if not server_config.url:
                logger.warning(f"MCP server '{server_name}' has no URL, skipping")
                continue

            try:
                # Create client
                client = MCPClient(
                    server_name=server_name,
                    url=server_config.url,
                    transport=server_config.transport,
                    timeout=server_config.timeout,
                    headers=server_config.headers,
                    auto_reconnect=server_config.auto_reconnect
                )

                # Initialize connection
                await client.initialize()

                # Discover tools
                tool_defs = await client.list_tools()

                # Wrap tools
                for tool_def in tool_defs:
                    wrapper = MCPToolWrapper(client, tool_def)
                    self.tools.append(wrapper)

                self.clients[server_name] = client
                logger.info(
                    f"MCP server '{server_name}' ready: {len(tool_defs)} tools"
                )

            except Exception as e:
                logger.error(
                    f"Failed to initialize MCP server '{server_name}': {e}"
                )
                # Continue with other servers - fault tolerance

        self._initialized = True
        total_tools = len(self.tools)
        total_servers = len(self.clients)

        if total_servers > 0:
            logger.info(
                f"MCP initialization complete: {total_tools} tools from "
                f"{total_servers} servers"
            )
        else:
            logger.warning("No MCP servers successfully initialized")

    def get_tools(self) -> list[MCPToolWrapper]:
        """Get all wrapped MCP tools."""
        return self.tools

    async def close(self) -> None:
        """Close all MCP connections."""
        if not self.clients:
            return

        logger.info("Closing MCP connections...")
        for server_name, client in self.clients.items():
            try:
                await client.close()
                logger.debug(f"Closed MCP server '{server_name}'")
            except Exception as e:
                logger.error(f"Error closing MCP server '{server_name}': {e}")
