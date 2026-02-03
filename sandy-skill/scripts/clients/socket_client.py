"""
Sandy MCP Socket Client for Claude-in-Chrome

Connects to existing Claude Code --chrome session via Unix socket.

Protocol (discovered from Chrome extension source):
- JSON-RPC 2.0 format
- Length-prefixed messages (4-byte little-endian length + JSON)
- method: "execute_tool"
- params: { tool: "tool_name", args: {...} }
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import struct
from pathlib import Path
from typing import Any

try:
    from .base import MCPClient, ToolResult, MCPToolCallError, MCPConnectionError
except ImportError:
    from clients.base import MCPClient, ToolResult, MCPToolCallError, MCPConnectionError


def get_socket_dir() -> Path:
    """Get the socket directory path"""
    user = os.environ.get("USER", "unknown")
    return Path(f"/tmp/claude-mcp-browser-bridge-{user}")


class ClaudeInChromeSocketClient(MCPClient):
    """
    MCP Client for claude-in-chrome via Unix socket

    Connects to an existing Claude Code --chrome session.
    """

    def __init__(self, timeout: float = 30.0):
        self._socket_path: Path | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        self._timeout = timeout
        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future[Any]] = {}
        self._tab_id: int | None = None
        self._read_task: asyncio.Task[None] | None = None

    @property
    def transport_type(self) -> str:
        return "socket"

    @property
    def server_name(self) -> str:
        return "claude-in-chrome"

    @property
    def tab_id(self) -> int | None:
        return self._tab_id

    async def connect(self) -> None:
        """
        Find and connect to Claude-in-Chrome socket

        Raises:
            MCPConnectionError: If no socket found or connection fails
        """
        if self._connected:
            return

        # Find active socket
        socket_path = await self._find_active_socket()
        if not socket_path:
            raise MCPConnectionError(
                "No Claude-in-Chrome socket found. Make sure:\n"
                "1. Claude Code is running with --chrome flag\n"
                "2. Chrome Extension is installed and connected"
            )

        try:
            # Connect to socket
            self._reader, self._writer = await asyncio.open_unix_connection(
                str(socket_path)
            )
            self._socket_path = socket_path
            self._connected = True

            # Start background read task
            self._read_task = asyncio.create_task(self._read_loop())

            # Create tab for this session
            await self._create_tab()

        except Exception as e:
            self._connected = False
            raise MCPConnectionError(f"Failed to connect to socket: {e}") from e

    async def disconnect(self) -> None:
        """Close the socket connection"""
        if not self._connected:
            return

        # Cancel read task
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
            self._read_task = None

        # Close connection
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass

        self._reader = None
        self._writer = None
        self._connected = False

        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

    async def call_tool(self, tool_name: str, params: dict[str, Any]) -> ToolResult:
        """
        Call an MCP tool via the socket

        Args:
            tool_name: Tool name (with or without mcp__claude-in-chrome__ prefix)
            params: Tool parameters

        Returns:
            ToolResult with success status and data/error
        """
        if not self._connected:
            raise MCPToolCallError("Not connected to Claude-in-Chrome socket")

        # Strip prefix if present (Python 3.9+ removeprefix)
        tool_name = tool_name.removeprefix("mcp__claude-in-chrome__")

        # Add tabId if not present and we have one
        if self._tab_id is not None and "tabId" not in params:
            params = {**params, "tabId": self._tab_id}

        try:
            result = await self._send_request(tool_name, params)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def list_tools(self) -> list[str]:
        """
        List available tools

        Returns predefined list since claude-in-chrome doesn't have list_tools
        """
        return [
            "tabs_context_mcp",
            "tabs_create_mcp",
            "navigate",
            "computer",
            "read_page",
            "find",
            "form_input",
            "get_page_text",
            "read_console_messages",
            "read_network_requests",
            "javascript_tool",
        ]

    async def _find_active_socket(self) -> Path | None:
        """Find an active socket in the socket directory"""
        socket_dir = get_socket_dir()

        if not socket_dir.exists():
            return None

        for socket_file in socket_dir.glob("*.sock"):
            if await self._test_socket(socket_file):
                return socket_file

        return None

    async def _test_socket(self, socket_path: Path) -> bool:
        """Test if a socket is responsive"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(str(socket_path)),
                timeout=1.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _create_tab(self) -> None:
        """Create a new tab for this session"""
        # First get context to ensure group exists
        await self._send_request("tabs_context_mcp", {"createIfEmpty": True})

        # Create new tab
        result = await self._send_request("tabs_create_mcp", {})

        # Extract tabId from result
        if isinstance(result, dict):
            self._tab_id = result.get("tabId")

            # Try parsing from content text if not directly available
            if self._tab_id is None and "content" in result:
                match = re.search(r"Tab ID:\s*(\d+)", str(result["content"]), re.I)
                if match:
                    self._tab_id = int(match.group(1))

        if self._tab_id is None:
            raise MCPConnectionError("Could not extract tabId from response")

    async def _send_request(self, tool: str, args: dict[str, Any]) -> Any:
        """
        Send a JSON-RPC request and wait for response

        Args:
            tool: Tool name
            args: Tool arguments

        Returns:
            Response data
        """
        if not self._writer or not self._reader:
            raise MCPToolCallError("Socket not connected")

        self._request_id += 1
        request_id = self._request_id

        message = {
            "jsonrpc": "2.0",
            "method": "execute_tool",
            "params": {
                "tool": tool,
                "args": args
            },
            "id": request_id
        }

        # Create future for response
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending_requests[request_id] = future

        try:
            # Send message with length prefix
            self._send_message(message)

            # Wait for response
            result = await asyncio.wait_for(future, timeout=self._timeout)
            return result

        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise MCPToolCallError(f"Request timeout for {tool}")

        except asyncio.CancelledError:
            self._pending_requests.pop(request_id, None)
            raise

    def _send_message(self, message: dict[str, Any]) -> None:
        """Send a length-prefixed JSON message"""
        if not self._writer:
            return

        json_bytes = json.dumps(message).encode("utf-8")
        length_bytes = struct.pack("<I", len(json_bytes))

        self._writer.write(length_bytes + json_bytes)
        # Note: we don't await drain() to allow pipelining

    async def _read_loop(self) -> None:
        """Background task to read and dispatch responses"""
        buffer = b""

        try:
            while self._connected and self._reader:
                # Read more data
                data = await self._reader.read(4096)
                if not data:
                    break

                buffer += data

                # Process complete messages
                while len(buffer) >= 4:
                    length = struct.unpack("<I", buffer[:4])[0]
                    if len(buffer) < 4 + length:
                        break

                    message_bytes = buffer[4:4 + length]
                    buffer = buffer[4 + length:]

                    try:
                        message = json.loads(message_bytes.decode("utf-8"))
                        self._handle_message(message)
                    except json.JSONDecodeError:
                        pass  # Ignore malformed messages

        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def _handle_message(self, message: dict[str, Any]) -> None:
        """Handle an incoming message"""
        request_id = message.get("id")

        # Try to find matching request
        future: asyncio.Future[Any] | None = None

        if request_id is not None and request_id in self._pending_requests:
            future = self._pending_requests.pop(request_id)
        elif self._pending_requests:
            # FIFO fallback if no id in response
            first_id = next(iter(self._pending_requests))
            future = self._pending_requests.pop(first_id)

        if not future or future.done():
            return

        # Handle error
        if "error" in message:
            error = message["error"]
            error_msg = error.get("message") or error.get("content") or "Unknown error"
            future.set_exception(MCPToolCallError(str(error_msg)))
            return

        # Extract result
        result = message.get("result")
        if result:
            content = result.get("content")
            if isinstance(content, list):
                # Find text content
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            future.set_result(json.loads(text))
                        except json.JSONDecodeError:
                            future.set_result({"content": text})
                        return

            future.set_result(result)
        else:
            future.set_result(None)
