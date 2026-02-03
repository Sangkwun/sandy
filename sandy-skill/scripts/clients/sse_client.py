"""
Sandy MCP SSE Client

Uses MCP Python SDK to connect to MCP servers via Server-Sent Events (HTTP).
"""

from __future__ import annotations

from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client

try:
    from .base import MCPClient, ToolResult, MCPToolCallError, MCPConnectionError, extract_content_data, list_tools_from_session
except ImportError:
    from clients.base import MCPClient, ToolResult, MCPToolCallError, MCPConnectionError, extract_content_data, list_tools_from_session


class SSEClient(MCPClient):
    """
    MCP Client using SSE (Server-Sent Events) transport

    Connects to an MCP server via HTTP SSE endpoint.
    Uses the official MCP Python SDK.
    """

    def __init__(
        self,
        server_name: str,
        endpoint: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        sse_read_timeout: float = 300.0,
    ):
        """
        Initialize SSE client.

        Args:
            server_name: Name of the server
            endpoint: HTTP(S) endpoint URL for SSE connection
            headers: Optional HTTP headers
            timeout: HTTP timeout for regular operations (seconds)
            sse_read_timeout: Timeout for SSE read operations (seconds)
        """
        self._server_name = server_name
        self._endpoint = endpoint
        self._headers = headers or {}
        self._timeout = timeout
        self._sse_read_timeout = sse_read_timeout
        self._session: ClientSession | None = None
        self._sse_context: Any = None
        self._connected = False

    @property
    def transport_type(self) -> str:
        return "sse"

    @property
    def server_name(self) -> str:
        return self._server_name

    async def connect(self) -> None:
        """
        Connect to the MCP server via SSE

        Raises:
            MCPConnectionError: If connection or initialization fails
        """
        if self._connected:
            return

        try:
            # Create SSE client context
            self._sse_context = sse_client(
                url=self._endpoint,
                headers=self._headers if self._headers else None,
                timeout=self._timeout,
                sse_read_timeout=self._sse_read_timeout,
            )

            # Enter the context to get read/write streams
            read, write = await self._sse_context.__aenter__()

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
        """Close the SSE connection"""
        if not self._connected:
            return

        try:
            if self._session:
                await self._session.__aexit__(None, None, None)
                self._session = None

            if self._sse_context:
                await self._sse_context.__aexit__(None, None, None)
                self._sse_context = None

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
