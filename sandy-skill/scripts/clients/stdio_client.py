"""
Sandy MCP stdio Client

Uses MCP Python SDK to spawn and communicate with MCP servers via stdio.
"""

from __future__ import annotations

import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

try:
    from .base import MCPClient, ToolResult, MCPToolCallError, MCPConnectionError, extract_content_data, list_tools_from_session
except ImportError:
    from clients.base import MCPClient, ToolResult, MCPToolCallError, MCPConnectionError, extract_content_data, list_tools_from_session


class StdioClient(MCPClient):
    """
    MCP Client using stdio transport

    Spawns the MCP server as a subprocess and communicates via stdin/stdout.
    Uses the official MCP Python SDK.
    """

    def __init__(
        self,
        server_name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ):
        self._server_name = server_name
        self._command = command
        self._args = args or []
        self._env = env or {}
        self._session: ClientSession | None = None
        self._stdio_context: Any = None
        self._connected = False

    @property
    def transport_type(self) -> str:
        return "stdio"

    @property
    def server_name(self) -> str:
        return self._server_name

    async def connect(self) -> None:
        """
        Spawn the MCP server and establish connection

        Raises:
            MCPConnectionError: If spawn or initialization fails
        """
        if self._connected:
            return

        try:
            # Merge environment variables
            env = {**os.environ, **self._env}

            # Create server parameters
            server_params = StdioServerParameters(
                command=self._command,
                args=self._args,
                env=env,
            )

            # Create stdio client context
            self._stdio_context = stdio_client(server_params)

            # Enter the context to get read/write streams
            read, write = await self._stdio_context.__aenter__()

            # Create and initialize session
            self._session = ClientSession(read, write)
            await self._session.__aenter__()

            # Initialize the session
            await self._session.initialize()

            self._connected = True

        except Exception as e:
            self._connected = False
            raise MCPConnectionError(
                f"Failed to connect to MCP server '{self._server_name}': {e}"
            ) from e

    async def disconnect(self) -> None:
        """Close the connection and terminate the subprocess"""
        if not self._connected:
            return

        try:
            if self._session:
                await self._session.__aexit__(None, None, None)
                self._session = None

            if self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)
                self._stdio_context = None

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
