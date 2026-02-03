"""
Sandy MCP WebSocket Client

Uses MCP Python SDK to connect to MCP servers via WebSocket.
"""

from __future__ import annotations

from typing import Any

from mcp import ClientSession
from mcp.client.websocket import websocket_client

try:
    from .base import MCPClient, ToolResult, MCPToolCallError, MCPConnectionError, extract_content_data, list_tools_from_session
except ImportError:
    from clients.base import MCPClient, ToolResult, MCPToolCallError, MCPConnectionError, extract_content_data, list_tools_from_session


class WebSocketClient(MCPClient):
    """
    MCP Client using WebSocket transport

    Connects to an MCP server via WebSocket (ws:// or wss://).
    Uses the official MCP Python SDK.
    """

    def __init__(
        self,
        server_name: str,
        endpoint: str,
    ):
        """
        Initialize WebSocket client.

        Args:
            server_name: Name of the server
            endpoint: WebSocket endpoint URL (ws:// or wss://)
        """
        self._server_name = server_name
        self._endpoint = endpoint
        self._session: ClientSession | None = None
        self._ws_context: Any = None
        self._connected = False

    @property
    def transport_type(self) -> str:
        return "websocket"

    @property
    def server_name(self) -> str:
        return self._server_name

    async def connect(self) -> None:
        """
        Connect to the MCP server via WebSocket

        Raises:
            MCPConnectionError: If connection or initialization fails
        """
        if self._connected:
            return

        try:
            # Create WebSocket client context
            self._ws_context = websocket_client(url=self._endpoint)

            # Enter the context to get read/write streams
            read, write = await self._ws_context.__aenter__()

            # Create and initialize session
            self._session = ClientSession(read, write)
            await self._session.__aenter__()

            # Initialize the session
            await self._session.initialize()

            self._connected = True

        except Exception as e:
            self._connected = False
            raise MCPConnectionError(
                f"Failed to connect to MCP server '{self._server_name}' at {self._endpoint}: {e}"
            ) from e

    async def disconnect(self) -> None:
        """Close the WebSocket connection"""
        if not self._connected:
            return

        try:
            if self._session:
                await self._session.__aexit__(None, None, None)
                self._session = None

            if self._ws_context:
                await self._ws_context.__aexit__(None, None, None)
                self._ws_context = None

        except Exception:
            pass  # Ignore errors during disconnect

        self._connected = False

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> ToolResult:
        """
        Call an MCP tool

        Args:
            tool_name: Name of the tool (without mcp__server__ prefix)
            params: Tool parameters

        Returns:
            ToolResult with success status and data/error
        """
        if not self._connected or not self._session:
            raise MCPToolCallError("Not connected to MCP server")

        try:
            result = await self._session.call_tool(tool_name, params)
            data = extract_content_data(result.content) if result.content else None

            # Check if MCP returned an error
            if result.isError:
                error_msg = data if isinstance(data, str) else str(data) if data else "Tool call failed"
                return ToolResult(success=False, data=data, error=error_msg)

            return ToolResult(success=True, data=data)

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def list_tools(self) -> list[str]:
        """
        List available tools on this server

        Returns:
            List of tool names
        """
        if not self._connected or not self._session:
            raise MCPToolCallError("Not connected to MCP server")

        return await list_tools_from_session(self._session)
