"""
Sandy MCP Client Base

Abstract base class for MCP clients with different transports.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


def extract_content_data(content_list: list[Any]) -> Any:
    """
    Extract data from MCP content blocks.

    MCP returns content as a list of content blocks. This utility
    extracts the data from each block and returns it in a usable format.

    Args:
        content_list: List of MCP content blocks

    Returns:
        Single item if only one content block, otherwise list of items
    """
    if not content_list:
        return None

    content_data = []
    for content in content_list:
        if hasattr(content, "text"):
            # Try to parse as JSON
            try:
                content_data.append(json.loads(content.text))
            except (json.JSONDecodeError, AttributeError):
                content_data.append(content.text)
        elif hasattr(content, "data"):
            content_data.append(content.data)
        else:
            content_data.append(str(content))

    # Return single item if only one, otherwise list
    return content_data[0] if len(content_data) == 1 else content_data


async def list_tools_from_session(session: Any) -> list[str]:
    """
    Helper to extract tool names from MCP ClientSession.

    Args:
        session: MCP ClientSession with list_tools() method

    Returns:
        List of tool names
    """
    result = await session.list_tools()
    return [tool.name for tool in result.tools]


@dataclass
class ToolResult:
    """Result from a tool call"""
    success: bool
    data: Any = None
    error: str | None = None


class MCPClient(ABC):
    """
    Abstract base class for MCP clients

    Implementations handle different transport mechanisms:
    - stdio: Spawn and communicate via stdin/stdout
    - SSE: Server-Sent Events over HTTP
    - WebSocket: WebSocket connection
    - Socket: Unix domain socket (claude-in-chrome)
    """

    @property
    @abstractmethod
    def transport_type(self) -> str:
        """Return transport type: 'stdio', 'sse', 'websocket', 'socket'"""
        pass

    @property
    @abstractmethod
    def server_name(self) -> str:
        """Return the MCP server name"""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the MCP server

        Raises:
            MCPConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection"""
        pass

    @abstractmethod
    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> ToolResult:
        """
        Call an MCP tool

        Args:
            tool_name: Name of the tool (without mcp__server__ prefix)
            params: Tool parameters

        Returns:
            ToolResult with success status and data/error
        """
        pass

    @abstractmethod
    async def list_tools(self) -> list[str]:
        """
        List available tools on this server

        Returns:
            List of tool names
        """
        pass

    async def __aenter__(self) -> MCPClient:
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.disconnect()


class MCPClientError(Exception):
    """Base exception for MCP client errors"""
    pass


class MCPConnectionError(MCPClientError):
    """Raised when connection to MCP server fails"""
    pass


class MCPToolCallError(MCPClientError):
    """Raised when a tool call fails"""
    pass
