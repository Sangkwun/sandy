"""
Tests for Claude native tools (builtins/claude_tools.py)
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from native_tools.claude_tools import ClaudeTools, ToolResult


class TestClaudeToolsRead:
    """Tests for claude__read tool"""

    def test_read_file_content(self):
        """Should read file content with line numbers"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            temp_path = f.name

        try:
            result = ClaudeTools.read(file_path=temp_path)

            assert "content" in result
            assert "line1" in result["content"]
            assert result["total_lines"] == 3
            assert result["lines_read"] == 3
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_read_with_offset(self):
        """Should read from specified offset"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\nline5\n")
            temp_path = f.name

        try:
            result = ClaudeTools.read(file_path=temp_path, offset=3)

            assert result["start_line"] == 3
            assert "line3" in result["content"]
            assert "line1" not in result["content"]
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_read_with_limit(self):
        """Should limit number of lines read"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\nline5\n")
            temp_path = f.name

        try:
            result = ClaudeTools.read(file_path=temp_path, limit=2)

            assert result["lines_read"] == 2
            assert "line1" in result["content"]
            assert "line2" in result["content"]
            assert "line3" not in result["content"]
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_read_nonexistent_file(self):
        """Should raise error for nonexistent file"""
        with pytest.raises(FileNotFoundError):
            ClaudeTools.read(file_path="/nonexistent/path/file.txt")

    def test_read_directory(self):
        """Should raise error when reading directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(ValueError) as exc_info:
                ClaudeTools.read(file_path=temp_dir)
            assert "Not a file" in str(exc_info.value)


class TestClaudeToolsWrite:
    """Tests for claude__write tool"""

    def test_write_file(self):
        """Should write content to file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "output.txt"

            result = ClaudeTools.write(
                file_path=str(file_path),
                content="Hello, World!"
            )

            assert result["path"] == str(file_path)
            assert file_path.read_text() == "Hello, World!"

    def test_write_creates_parent_dirs(self):
        """Should create parent directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "a" / "b" / "c" / "file.txt"

            ClaudeTools.write(
                file_path=str(nested_path),
                content="nested content"
            )

            assert nested_path.exists()
            assert nested_path.read_text() == "nested content"

    def test_write_overwrites_existing(self):
        """Should overwrite existing file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("old content")
            temp_path = f.name

        try:
            ClaudeTools.write(file_path=temp_path, content="new content")
            assert Path(temp_path).read_text() == "new content"
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestClaudeToolsEdit:
    """Tests for claude__edit tool"""

    def test_edit_replace_single(self):
        """Should replace single occurrence"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def old_name():\n    pass\n")
            temp_path = f.name

        try:
            result = ClaudeTools.edit(
                file_path=temp_path,
                old_string="old_name",
                new_string="new_name"
            )

            assert result["replacements"] == 1
            content = Path(temp_path).read_text()
            assert "new_name" in content
            assert "old_name" not in content
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_edit_replace_all(self):
        """Should replace all occurrences with replace_all=True"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("foo bar foo baz foo\n")
            temp_path = f.name

        try:
            result = ClaudeTools.edit(
                file_path=temp_path,
                old_string="foo",
                new_string="qux",
                replace_all=True
            )

            assert result["replacements"] == 3
            content = Path(temp_path).read_text()
            assert content == "qux bar qux baz qux\n"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_edit_fails_on_multiple_without_replace_all(self):
        """Should fail when old_string appears multiple times without replace_all"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("foo bar foo\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                ClaudeTools.edit(
                    file_path=temp_path,
                    old_string="foo",
                    new_string="baz"
                )
            assert "appears" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_edit_fails_on_not_found(self):
        """Should fail when old_string not found"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                ClaudeTools.edit(
                    file_path=temp_path,
                    old_string="nonexistent",
                    new_string="replacement"
                )
            assert "not found" in str(exc_info.value)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestClaudeToolsGlob:
    """Tests for claude__glob tool"""

    def test_glob_find_files(self):
        """Should find files matching pattern"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            (Path(temp_dir) / "test1.py").write_text("# test1")
            (Path(temp_dir) / "test2.py").write_text("# test2")
            (Path(temp_dir) / "readme.md").write_text("# readme")

            result = ClaudeTools.glob(pattern="*.py", path=temp_dir)

            assert result["count"] == 2
            assert all(".py" in f for f in result["files"])

    def test_glob_recursive(self):
        """Should find files recursively with **"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested structure
            (Path(temp_dir) / "a").mkdir()
            (Path(temp_dir) / "a" / "b").mkdir()
            (Path(temp_dir) / "test.py").write_text("")
            (Path(temp_dir) / "a" / "test.py").write_text("")
            (Path(temp_dir) / "a" / "b" / "test.py").write_text("")

            result = ClaudeTools.glob(pattern="**/*.py", path=temp_dir)

            assert result["count"] == 3

    def test_glob_no_matches(self):
        """Should return empty list when no matches"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ClaudeTools.glob(pattern="*.xyz", path=temp_dir)

            assert result["count"] == 0
            assert result["files"] == []


class TestClaudeToolsGrep:
    """Tests for claude__grep tool"""

    def test_grep_find_pattern(self):
        """Should find files matching pattern"""
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "file1.py").write_text("def hello():\n    pass\n")
            (Path(temp_dir) / "file2.py").write_text("def world():\n    pass\n")
            (Path(temp_dir) / "file3.txt").write_text("no functions here")

            result = ClaudeTools.grep(
                pattern=r"def \w+\(",
                path=temp_dir,
                glob="*.py"
            )

            assert result["count"] == 2

    def test_grep_content_mode(self):
        """Should return matching lines in content mode"""
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "test.py").write_text("line1\nTARGET line\nline3\n")

            result = ClaudeTools.grep(
                pattern="TARGET",
                path=temp_dir,
                output_mode="content"
            )

            assert len(result["matches"]) == 1
            assert "TARGET" in result["matches"][0]["line"]

    def test_grep_count_mode(self):
        """Should return count in count mode"""
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "test.py").write_text("foo\nfoo\nbar\nfoo\n")

            result = ClaudeTools.grep(
                pattern="foo",
                path=temp_dir,
                output_mode="count"
            )

            assert result["count"] == 3

    def test_grep_case_insensitive(self):
        """Should support case insensitive search"""
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "test.txt").write_text("Hello\nHELLO\nhello\n")

            result = ClaudeTools.grep(
                pattern="hello",
                path=temp_dir,
                output_mode="count",
                case_insensitive=True
            )

            assert result["count"] == 3


class TestClaudeToolsBash:
    """Tests for claude__bash tool"""

    def test_bash_simple_command(self):
        """Should execute simple command"""
        async def run_test():
            result = await ClaudeTools.bash(command="echo 'hello world'")

            assert result["exit_code"] == 0
            assert "hello world" in result["stdout"]

        asyncio.run(run_test())

    def test_bash_capture_stderr(self):
        """Should capture stderr"""
        async def run_test():
            result = await ClaudeTools.bash(command="echo 'error' >&2")

            assert "error" in result["stderr"]

        asyncio.run(run_test())

    def test_bash_nonzero_exit(self):
        """Should capture non-zero exit code"""
        async def run_test():
            result = await ClaudeTools.bash(command="exit 42")

            assert result["exit_code"] == 42

        asyncio.run(run_test())

    def test_bash_timeout(self):
        """Should timeout long-running command"""
        async def run_test():
            with pytest.raises(TimeoutError):
                await ClaudeTools.bash(
                    command="sleep 10",
                    timeout=100  # 100ms
                )

        asyncio.run(run_test())


class TestClaudeToolsExecute:
    """Tests for ClaudeTools.execute dispatcher"""

    def test_execute_read(self):
        """Should dispatch to read tool"""
        async def run_test():
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("test content")
                temp_path = f.name

            try:
                result = await ClaudeTools.execute("read", {"file_path": temp_path})

                assert result.success is True
                assert "test content" in result.data["content"]
            finally:
                Path(temp_path).unlink(missing_ok=True)

        asyncio.run(run_test())

    def test_execute_unknown_tool(self):
        """Should return error for unknown tool"""
        async def run_test():
            result = await ClaudeTools.execute("unknown_tool", {})

            assert result.success is False
            assert "Unknown" in result.error

        asyncio.run(run_test())

    def test_execute_handles_exception(self):
        """Should handle exceptions gracefully"""
        async def run_test():
            result = await ClaudeTools.execute("read", {"file_path": "/nonexistent/file"})

            assert result.success is False
            assert result.error is not None

        asyncio.run(run_test())


class TestClaudeToolsIntegration:
    """Integration tests for claude tools in player"""

    def test_player_executes_claude_tool(self):
        """Should execute claude__ tools in player"""
        from scenario import parse_scenario
        from player import ScenarioPlayer, PlayerOptions

        async def run_test():
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("integration test content\n")
                temp_path = f.name

            try:
                scenario = parse_scenario({
                    "version": "2.1",
                    "metadata": {"name": "Claude Tool Test"},
                    "variables": {},
                    "steps": [
                        {
                            "step": 1,
                            "id": "read_file",
                            "tool": "claude__read",
                            "params": {"file_path": temp_path},
                            "output": {"content": "$.content"}
                        }
                    ]
                })

                class MockConfig:
                    servers = {}
                    source = "test"

                player = ScenarioPlayer(scenario, MockConfig(), PlayerOptions())
                result = await player.execute()

                assert result.success is True
                assert result.passed_steps == 1
                assert "content" in player.step_outputs.get("read_file", {})
            finally:
                Path(temp_path).unlink(missing_ok=True)

        asyncio.run(run_test())

    def test_player_chains_claude_tools(self):
        """Should chain multiple claude tools with variable references"""
        from scenario import parse_scenario
        from player import ScenarioPlayer, PlayerOptions

        async def run_test():
            with tempfile.TemporaryDirectory() as temp_dir:
                input_path = Path(temp_dir) / "input.txt"
                output_path = Path(temp_dir) / "output.txt"
                input_path.write_text("original content")

                scenario = parse_scenario({
                    "version": "2.1",
                    "metadata": {"name": "Chain Test"},
                    "variables": {
                        "INPUT": str(input_path),
                        "OUTPUT": str(output_path)
                    },
                    "steps": [
                        {
                            "step": 1,
                            "id": "read",
                            "tool": "claude__read",
                            "params": {"file_path": "{{INPUT}}"},
                            "output": {"lines": "$.lines_read"}
                        },
                        {
                            "step": 2,
                            "tool": "claude__write",
                            "params": {
                                "file_path": "{{OUTPUT}}",
                                "content": "Lines read: {{read.lines}}"
                            }
                        }
                    ]
                })

                class MockConfig:
                    servers = {}
                    source = "test"

                player = ScenarioPlayer(scenario, MockConfig(), PlayerOptions())
                result = await player.execute()

                assert result.success is True
                assert output_path.exists()
                assert "Lines read: 1" in output_path.read_text()

        asyncio.run(run_test())
