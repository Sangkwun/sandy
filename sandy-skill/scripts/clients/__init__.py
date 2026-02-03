"""
Sandy MCP Client Factory

Creates appropriate MCP client based on server configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from .base import (
        MCPClient,
        MCPClientError,
        MCPConnectionError,
        MCPToolCallError,
    )
except ImportError:
    from clients.base import (
        MCPClient,
        MCPClientError,
        MCPConnectionError,
        MCPToolCallError,
    )

if TYPE_CHECKING:
    try:
        from ..config import ServerConfig
    except ImportError:
        from config import ServerConfig


async def create_client(server_config: "ServerConfig") -> MCPClient:
    """
    Create an MCP client based on server configuration

    Transport selection:
    - endpoint with ws:// or wss:// → WebSocket client
    - endpoint with http:// → SSE client (not yet implemented)
    - command without endpoint → stdio client
    - claude-in-chrome → socket client

    Args:
        server_config: Server configuration

    Returns:
        Connected MCPClient instance

    Raises:
        MCPClientError: If client creation fails
    """
    server_name = server_config.name

    # Special case: claude-in-chrome uses Unix socket
    if server_name == "claude-in-chrome":
        try:
            from .socket_client import ClaudeInChromeSocketClient
        except ImportError:
            from clients.socket_client import ClaudeInChromeSocketClient
        return ClaudeInChromeSocketClient()

    # Determine transport based on config
    if server_config.endpoint:
        endpoint = server_config.endpoint

        if endpoint.startswith("ws://") or endpoint.startswith("wss://"):
            # WebSocket transport
            try:
                from .websocket_client import WebSocketClient
            except ImportError:
                from clients.websocket_client import WebSocketClient
            return WebSocketClient(
                server_name=server_name,
                endpoint=endpoint,
            )
        elif endpoint.startswith("http://") or endpoint.startswith("https://"):
            # SSE transport
            try:
                from .sse_client import SSEClient
            except ImportError:
                from clients.sse_client import SSEClient
            return SSEClient(
                server_name=server_name,
                endpoint=endpoint,
            )
        else:
            raise MCPClientError(
                f"Unknown endpoint format for {server_name}: {endpoint}"
            )

    elif server_config.command:
        # stdio transport
        try:
            from .stdio_client import StdioClient
        except ImportError:
            from clients.stdio_client import StdioClient
        return StdioClient(
            server_name=server_name,
            command=server_config.command,
            args=server_config.args or [],
            env=server_config.env or {},
        )

    else:
        raise MCPClientError(
            f"Server {server_name} has neither endpoint nor command configured"
        )


__all__ = [
    "MCPClient",
    "MCPClientError",
    "MCPConnectionError",
    "MCPToolCallError",
    "create_client",
]
