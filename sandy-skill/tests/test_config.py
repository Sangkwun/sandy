"""
Tests for config.py
"""

import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from config import (
    load_sandy_config,
    parse_claude_desktop_config,
    parse_cursor_config,
    load_config_from_path,
    expand_env_vars,
    get_server_config,
    ServerConfig,
    ConfigNotFoundError,
    ConfigParseError,
)


class TestLoadSandyConfig:
    """Tests for load_sandy_config function"""

    def test_load_valid_config(self, tmp_path):
        """Should load valid Sandy config"""
        config_data = {
            "servers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@mcp/server-github"],
                    "env": {"TOKEN": "abc123"}
                },
                "supabase": {
                    "endpoint": "http://localhost:3000/sse"
                }
            }
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        config = load_sandy_config(config_file)

        assert len(config.servers) == 2
        assert "github" in config.servers
        assert "supabase" in config.servers

        github = config.servers["github"]
        assert github.command == "npx"
        assert github.args == ["-y", "@mcp/server-github"]
        assert github.env == {"TOKEN": "abc123"}
        assert github.transport_type == "stdio"

        supabase = config.servers["supabase"]
        assert supabase.endpoint == "http://localhost:3000/sse"
        assert supabase.transport_type == "sse"

    def test_load_invalid_json(self, tmp_path):
        """Should raise ConfigParseError for invalid JSON"""
        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid }")

        with pytest.raises(ConfigParseError, match="Invalid JSON"):
            load_sandy_config(config_file)


class TestParseClaudeDesktopConfig:
    """Tests for parse_claude_desktop_config function"""

    def test_parse_valid_config(self, tmp_path):
        """Should parse Claude Desktop config format"""
        config_data = {
            "mcpServers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@mcp/server-github"],
                    "env": {"TOKEN": "abc"}
                }
            }
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        config = parse_claude_desktop_config(config_file)

        assert "github" in config.servers
        assert config.servers["github"].command == "npx"

    def test_empty_mcp_servers(self, tmp_path):
        """Should handle empty mcpServers"""
        config_data = {"mcpServers": {}}

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        config = parse_claude_desktop_config(config_file)

        assert len(config.servers) == 0


class TestParseCursorConfig:
    """Tests for parse_cursor_config function"""

    def test_parse_valid_config(self, tmp_path):
        """Should parse Cursor config format"""
        config_data = {
            "mcpServers": {
                "notion": {
                    "command": "notion-mcp",
                    "args": []
                }
            }
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        config = parse_cursor_config(config_file)

        assert "notion" in config.servers


class TestLoadConfigFromPath:
    """Tests for load_config_from_path function"""

    def test_auto_detect_sandy_format(self, tmp_path):
        """Should auto-detect Sandy format (servers key)"""
        config_data = {
            "servers": {
                "test": {"command": "test-cmd"}
            }
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        config = load_config_from_path(config_file)
        assert "test" in config.servers

    def test_auto_detect_claude_format(self, tmp_path):
        """Should auto-detect Claude Desktop format (mcpServers key)"""
        config_data = {
            "mcpServers": {
                "test": {"command": "test-cmd"}
            }
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        config = load_config_from_path(config_file)
        assert "test" in config.servers

    def test_unknown_format(self, tmp_path):
        """Should raise ConfigParseError for unknown format"""
        config_data = {"unknown_key": {}}

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ConfigParseError, match="Unknown config format"):
            load_config_from_path(config_file)

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing file"""
        with pytest.raises(FileNotFoundError):
            load_config_from_path("/nonexistent/config.json")


class TestExpandEnvVars:
    """Tests for expand_env_vars function"""

    def test_expand_env_var(self):
        """Should expand ${VAR} references"""
        with patch.dict(os.environ, {"MY_TOKEN": "secret123"}):
            result = expand_env_vars({"TOKEN": "${MY_TOKEN}"})
            assert result["TOKEN"] == "secret123"

    def test_missing_env_var(self):
        """Should leave unset env vars as-is (unexpanded)"""
        result = expand_env_vars({"TOKEN": "${NONEXISTENT_VAR_12345}"})
        # os.path.expandvars leaves undefined vars as-is
        assert result["TOKEN"] == "${NONEXISTENT_VAR_12345}"

    def test_none_input(self):
        """Should handle None input"""
        result = expand_env_vars(None)
        assert result == {}

    def test_empty_dict(self):
        """Should handle empty dict"""
        result = expand_env_vars({})
        assert result == {}


class TestGetServerConfig:
    """Tests for get_server_config function"""

    def test_get_existing_server(self, tmp_path):
        """Should return config for existing server"""
        config_data = {
            "servers": {
                "github": {"command": "gh-mcp"}
            }
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        config = load_sandy_config(config_file)
        server_config = get_server_config(config, "github")

        assert server_config.name == "github"
        assert server_config.command == "gh-mcp"

    def test_get_nonexistent_server(self, tmp_path):
        """Should raise KeyError for missing server"""
        config_data = {
            "servers": {
                "github": {"command": "gh-mcp"}
            }
        }

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        config = load_sandy_config(config_file)

        with pytest.raises(KeyError, match="not found"):
            get_server_config(config, "nonexistent")


class TestServerConfigTransportType:
    """Tests for ServerConfig.transport_type property"""

    def test_stdio_transport(self):
        """Should return stdio when command is set"""
        config = ServerConfig(name="test", command="test-cmd")
        assert config.transport_type == "stdio"

    def test_sse_transport(self):
        """Should return sse for http endpoint"""
        config = ServerConfig(name="test", endpoint="http://localhost:3000/sse")
        assert config.transport_type == "sse"

    def test_websocket_transport(self):
        """Should return websocket for ws endpoint"""
        config = ServerConfig(name="test", endpoint="ws://localhost:9222")
        assert config.transport_type == "websocket"

    def test_websocket_secure_transport(self):
        """Should return websocket for wss endpoint"""
        config = ServerConfig(name="test", endpoint="wss://localhost:9222")
        assert config.transport_type == "websocket"
