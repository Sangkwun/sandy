"""
Sandy Config Auto-Detection

Automatically detects MCP configuration from various sources:
1. $SANDY_CONFIG environment variable
2. .sandy/config.json (project local)
3. Claude Desktop config
4. Cursor MCP config
5. ~/.sandy/config.json (global)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


__all__ = [
    # Data classes
    "ServerConfig",
    "Config",
    # Exceptions
    "ConfigNotFoundError",
    "ConfigParseError",
    # Functions
    "detect_config",
    "get_server_config",
    "load_config_from_path",
]


@dataclass
class ServerConfig:
    """MCP Server configuration"""
    name: str
    endpoint: str | None = None  # SSE/WebSocket endpoint
    command: str | None = None   # stdio command
    args: list[str] | None = None
    env: dict[str, str] | None = None

    @property
    def transport_type(self) -> str:
        """Determine transport type"""
        if self.endpoint:
            if self.endpoint.startswith("ws://") or self.endpoint.startswith("wss://"):
                return "websocket"
            return "sse"
        return "stdio"


@dataclass
class Config:
    """Sandy configuration"""
    servers: dict[str, ServerConfig]
    source: str  # Where config was loaded from


class ConfigNotFoundError(Exception):
    """Raised when no config can be found"""
    pass


class ConfigParseError(Exception):
    """Raised when config parsing fails"""
    pass


def detect_config() -> Config:
    """
    Auto-detect MCP configuration

    Priority order:
    1. $SANDY_CONFIG environment variable
    2. .sandy/config.json (project local)
    3. Claude Desktop config
    4. Cursor config
    5. ~/.sandy/config.json (global)

    Returns:
        Detected Config object

    Raises:
        ConfigNotFoundError: If no config found
    """
    # 1. Environment variable
    if env_path := os.getenv("SANDY_CONFIG"):
        path = Path(env_path)
        if path.exists():
            return load_sandy_config(path)
        raise ConfigNotFoundError(f"SANDY_CONFIG path not found: {env_path}")

    # 2. Project local config
    local_config = Path.cwd() / ".sandy" / "config.json"
    if local_config.exists():
        return load_sandy_config(local_config)

    # 3. Claude Desktop config
    claude_config = get_claude_desktop_config_path()
    if claude_config and claude_config.exists():
        return parse_claude_desktop_config(claude_config)

    # 4. Cursor config
    cursor_config = Path.home() / ".cursor" / "mcp.json"
    if cursor_config.exists():
        return parse_cursor_config(cursor_config)

    # 5. Global Sandy config
    sandy_global = Path.home() / ".sandy" / "config.json"
    if sandy_global.exists():
        return load_sandy_config(sandy_global)

    raise ConfigNotFoundError(
        "No MCP config found. Checked:\n"
        "  - $SANDY_CONFIG environment variable\n"
        "  - .sandy/config.json (project local)\n"
        "  - Claude Desktop config\n"
        "  - ~/.cursor/mcp.json (Cursor)\n"
        "  - ~/.sandy/config.json (global)"
    )


def get_claude_desktop_config_path() -> Path | None:
    """Get Claude Desktop config path based on platform"""
    import platform

    system = platform.system()

    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

    return None


def load_sandy_config(path: Path) -> Config:
    """
    Load Sandy-native config format

    Expected format:
    {
        "servers": {
            "server-name": {
                "endpoint": "http://...",  // or
                "command": "...",
                "args": [...],
                "env": {...}
            }
        }
    }
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigParseError(f"Invalid JSON in {path}: {e}")

    return _parse_sandy_format(data, str(path))


def _parse_sandy_format(data: dict, source: str) -> Config:
    """Parse Sandy config from already-loaded data"""
    servers = {}
    for name, server_data in data.get("servers", {}).items():
        servers[name] = ServerConfig(
            name=name,
            endpoint=server_data.get("endpoint"),
            command=server_data.get("command"),
            args=server_data.get("args"),
            env=expand_env_vars(server_data.get("env", {})),
        )

    return Config(servers=servers, source=source)


def _parse_mcp_servers_config(path: Path) -> Config:
    """
    Parse config with mcpServers format (Claude Desktop, Cursor)

    Expected format:
    {
        "mcpServers": {
            "server-name": {
                "command": "...",
                "args": [...],
                "env": {...}
            }
        }
    }
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigParseError(f"Invalid JSON in {path}: {e}")

    return _parse_mcp_servers_format(data, str(path))


def _parse_mcp_servers_format(data: dict, source: str) -> Config:
    """Parse mcpServers config from already-loaded data"""
    servers = {}
    for name, server_data in data.get("mcpServers", {}).items():
        servers[name] = ServerConfig(
            name=name,
            command=server_data.get("command"),
            args=server_data.get("args"),
            env=expand_env_vars(server_data.get("env", {})),
        )

    return Config(servers=servers, source=source)


# Aliases for compatibility
parse_claude_desktop_config = _parse_mcp_servers_config
parse_cursor_config = _parse_mcp_servers_config


def expand_env_vars(env_dict: dict[str, str] | None) -> dict[str, str]:
    """
    Expand environment variable references in env dict

    Supports ${VAR} syntax
    """
    if not env_dict:
        return {}

    result = {}
    for key, value in env_dict.items():
        if isinstance(value, str):
            # Expand ${VAR} references
            result[key] = os.path.expandvars(value)
        else:
            result[key] = str(value)

    return result


def get_server_config(config: Config, server_name: str) -> ServerConfig:
    """
    Get configuration for a specific server

    Args:
        config: Config object
        server_name: Name of the MCP server

    Returns:
        ServerConfig for the server

    Raises:
        KeyError: If server not found
    """
    # Special case: claude-in-chrome uses Unix socket, no config needed
    if server_name == "claude-in-chrome":
        return ServerConfig(name="claude-in-chrome")

    if server_name not in config.servers:
        available = ", ".join(config.servers.keys()) or "(none)"
        raise KeyError(
            f"Server '{server_name}' not found in config.\n"
            f"Available servers: {available}\n"
            f"Config source: {config.source}"
        )

    return config.servers[server_name]


def load_config_from_path(path: str | Path) -> Config:
    """
    Load config from explicit path

    Auto-detects format based on content
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigParseError(f"Invalid JSON in {path}: {e}")

    # Detect format and parse from already-loaded data (avoid double read)
    if "mcpServers" in data:
        return _parse_mcp_servers_format(data, str(path))
    elif "servers" in data:
        return _parse_sandy_format(data, str(path))
    else:
        raise ConfigParseError(
            f"Unknown config format in {path}. "
            "Expected 'servers' (Sandy format) or 'mcpServers' (Claude/Cursor format)"
        )
