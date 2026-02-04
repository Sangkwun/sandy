"""
Claude Code Native Tool Implementations

Provides Python implementations of Claude Code's native tools,
allowing scenarios to execute without LLM inference.

Supported tools:
- claude__read: Read file contents
- claude__write: Write file contents
- claude__edit: Edit file with string replacement
- claude__glob: Find files by pattern
- claude__grep: Search file contents with regex
- claude__bash: Execute shell commands
- claude__web_fetch: Fetch URL contents
- claude__notebook_edit: Edit Jupyter notebooks
"""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    data: Any = None
    error: str | None = None


class ClaudeTools:
    """
    Claude Code native tool implementations.

    All methods are static and can be called directly.
    Tool names use snake_case internally but map to Claude's tool names.
    """

    # Supported tool names
    TOOLS = {"read", "write", "edit", "glob", "grep", "bash", "web_fetch", "notebook_edit"}

    @classmethod
    async def execute(cls, tool_name: str, params: dict[str, Any]) -> ToolResult:
        """
        Execute a Claude tool by name.

        Args:
            tool_name: Tool name without prefix (e.g., "read", "write")
            params: Tool parameters

        Returns:
            ToolResult with success status and data/error
        """
        if tool_name not in cls.TOOLS:
            return ToolResult(
                success=False,
                error=f"Unknown Claude tool: claude__{tool_name}"
            )

        method = getattr(cls, tool_name)
        try:
            # Check if method is async
            if inspect.iscoroutinefunction(method):
                result = await method(**params)
            else:
                result = method(**params)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    def read(
        file_path: str,
        offset: int | None = None,
        limit: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Read file contents.

        Args:
            file_path: Absolute path to the file
            offset: Line number to start reading from (1-based)
            limit: Number of lines to read

        Returns:
            Dict with content and metadata
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Read file content
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        # Apply offset and limit
        start_line = 1
        if offset is not None:
            start_line = max(1, offset)
            lines = lines[start_line - 1:]

        if limit is not None:
            lines = lines[:limit]

        # Format with line numbers (cat -n style)
        formatted_lines = []
        for i, line in enumerate(lines, start=start_line):
            # Remove trailing newline for consistent formatting
            line_content = line.rstrip('\n\r')
            formatted_lines.append(f"{i:6}\t{line_content}")

        return {
            "content": "\n".join(formatted_lines),
            "total_lines": total_lines,
            "start_line": start_line,
            "lines_read": len(lines),
        }

    @staticmethod
    def write(
        file_path: str,
        content: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Write content to a file.

        Args:
            file_path: Absolute path to the file
            content: Content to write

        Returns:
            Dict with write status
        """
        path = Path(file_path)

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        path.write_text(content, encoding="utf-8")

        return {
            "path": str(path),
            "bytes_written": len(content.encode("utf-8")),
        }

    @staticmethod
    def edit(
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Edit file by replacing string.

        Args:
            file_path: Absolute path to the file
            old_string: Text to replace
            new_string: Replacement text
            replace_all: Replace all occurrences (default: False)

        Returns:
            Dict with edit status
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")

        # Check if old_string exists
        if old_string not in content:
            raise ValueError(f"old_string not found in file: {file_path}")

        # Check for uniqueness if not replace_all
        if not replace_all:
            count = content.count(old_string)
            if count > 1:
                raise ValueError(
                    f"old_string appears {count} times in file. "
                    "Use replace_all=true or provide more context."
                )

        # Perform replacement
        if replace_all:
            new_content = content.replace(old_string, new_string)
            replacements = content.count(old_string)
        else:
            new_content = content.replace(old_string, new_string, 1)
            replacements = 1

        # Write back
        path.write_text(new_content, encoding="utf-8")

        return {
            "path": str(path),
            "replacements": replacements,
        }

    @staticmethod
    def glob(
        pattern: str,
        path: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Find files matching glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.py")
            path: Directory to search in (default: current directory)

        Returns:
            Dict with matching files
        """
        base_path = Path(path) if path else Path.cwd()

        if not base_path.exists():
            raise FileNotFoundError(f"Directory not found: {base_path}")

        # Use glob to find matches
        matches = list(base_path.glob(pattern))

        # Sort by modification time (newest first)
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Convert to strings
        files = [str(m) for m in matches if m.is_file()]

        return {
            "files": files,
            "count": len(files),
        }

    @staticmethod
    def grep(
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
        output_mode: Literal["content", "files_with_matches", "count"] = "files_with_matches",
        context: int | None = None,
        head_limit: int | None = None,
        case_insensitive: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Search file contents with regex.

        Args:
            pattern: Regex pattern to search for
            path: File or directory to search in
            glob: Glob pattern to filter files
            output_mode: Output format (content, files_with_matches, count)
            context: Lines of context around matches
            head_limit: Limit number of results
            case_insensitive: Case insensitive search (-i flag)

        Returns:
            Dict with search results
        """
        # Handle -i parameter alias
        if kwargs.get("-i"):
            case_insensitive = True

        base_path = Path(path) if path else Path.cwd()

        # Compile regex
        flags = re.IGNORECASE if case_insensitive else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        # Collect files to search
        if base_path.is_file():
            files = [base_path]
        else:
            if glob:
                files = list(base_path.glob(glob))
            else:
                files = list(base_path.rglob("*"))
            files = [f for f in files if f.is_file()]

        results: list[dict[str, Any]] = []
        files_matched: list[str] = []
        total_matches = 0

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()

                file_matches: list[dict[str, Any]] = []

                file_has_match = False
                for line_num, line in enumerate(lines, start=1):
                    if regex.search(line):
                        total_matches += 1
                        file_has_match = True

                        if output_mode == "content":
                            match_info = {
                                "file": str(file_path),
                                "line_num": line_num,
                                "line": line,
                            }

                            # Add context if requested
                            if context:
                                start = max(0, line_num - context - 1)
                                end = min(len(lines), line_num + context)
                                match_info["context_before"] = lines[start:line_num-1]
                                match_info["context_after"] = lines[line_num:end]

                            file_matches.append(match_info)

                if file_has_match:
                    files_matched.append(str(file_path))
                    results.extend(file_matches)

            except Exception:
                continue  # Skip files that can't be read

        # Apply head_limit
        if head_limit:
            if output_mode == "content":
                results = results[:head_limit]
            elif output_mode == "files_with_matches":
                files_matched = files_matched[:head_limit]

        if output_mode == "content":
            return {
                "matches": results,
                "total_matches": total_matches,
            }
        elif output_mode == "count":
            return {
                "count": total_matches,
                "files_count": len(files_matched),
            }
        else:  # files_with_matches
            return {
                "files": files_matched,
                "count": len(files_matched),
            }

    @staticmethod
    async def bash(
        command: str,
        timeout: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute a shell command.

        Args:
            command: Command to execute
            timeout: Timeout in milliseconds (default: 120000)

        Returns:
            Dict with command output
        """
        # Convert timeout from ms to seconds
        timeout_sec = (timeout or 120000) / 1000

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_sec,
            )

            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Truncate if too long
            max_len = 30000
            if len(stdout_str) > max_len:
                stdout_str = stdout_str[:max_len] + "\n... (truncated)"
            if len(stderr_str) > max_len:
                stderr_str = stderr_str[:max_len] + "\n... (truncated)"

            return {
                "stdout": stdout_str,
                "stderr": stderr_str,
                "exit_code": process.returncode,
            }

        except asyncio.TimeoutError:
            raise TimeoutError(f"Command timed out after {timeout_sec}s")

    @staticmethod
    async def web_fetch(
        url: str,
        prompt: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Fetch content from a URL.

        Args:
            url: URL to fetch
            prompt: Not used (kept for API compatibility)

        Returns:
            Dict with fetched content
        """
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx is required for web_fetch. Install with: pip install httpx")

        try:
            from markdownify import markdownify as md
        except ImportError:
            md = None

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            content = response.text

            # Convert HTML to markdown if possible
            if "text/html" in content_type and md:
                content = md(content)

            # Truncate if too long
            max_len = 50000
            if len(content) > max_len:
                content = content[:max_len] + "\n... (truncated)"

            return {
                "url": str(response.url),
                "status_code": response.status_code,
                "content": content,
                "content_type": content_type,
            }

    @staticmethod
    def notebook_edit(
        notebook_path: str,
        new_source: str,
        cell_id: str | None = None,
        cell_type: Literal["code", "markdown"] | None = None,
        edit_mode: Literal["replace", "insert", "delete"] = "replace",
        **kwargs,
    ) -> dict[str, Any]:
        """
        Edit a Jupyter notebook cell.

        Args:
            notebook_path: Absolute path to the notebook
            new_source: New source content for the cell
            cell_id: Cell ID to edit (for replace/delete) or insert after
            cell_type: Cell type (code or markdown), required for insert
            edit_mode: Edit mode (replace, insert, delete)

        Returns:
            Dict with edit status
        """
        try:
            import nbformat
        except ImportError:
            raise ImportError("nbformat is required for notebook_edit. Install with: pip install nbformat")

        path = Path(notebook_path)

        if not path.exists():
            raise FileNotFoundError(f"Notebook not found: {notebook_path}")

        # Read notebook
        with open(path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        cells = nb.get("cells", [])

        if edit_mode == "insert":
            if not cell_type:
                raise ValueError("cell_type is required for insert mode")

            # Create new cell
            if cell_type == "code":
                new_cell = nbformat.v4.new_code_cell(new_source)
            else:
                new_cell = nbformat.v4.new_markdown_cell(new_source)

            # Find insert position
            if cell_id:
                insert_idx = None
                for i, cell in enumerate(cells):
                    if cell.get("id") == cell_id:
                        insert_idx = i + 1
                        break
                if insert_idx is None:
                    raise ValueError(f"Cell with id '{cell_id}' not found")
                cells.insert(insert_idx, new_cell)
            else:
                cells.insert(0, new_cell)

            action = "inserted"

        elif edit_mode == "delete":
            if not cell_id:
                raise ValueError("cell_id is required for delete mode")

            delete_idx = None
            for i, cell in enumerate(cells):
                if cell.get("id") == cell_id:
                    delete_idx = i
                    break

            if delete_idx is None:
                raise ValueError(f"Cell with id '{cell_id}' not found")

            del cells[delete_idx]
            action = "deleted"

        else:  # replace
            if not cell_id:
                raise ValueError("cell_id is required for replace mode")

            found = False
            for cell in cells:
                if cell.get("id") == cell_id:
                    cell["source"] = new_source
                    if cell_type:
                        cell["cell_type"] = cell_type
                    found = True
                    break

            if not found:
                raise ValueError(f"Cell with id '{cell_id}' not found")

            action = "replaced"

        # Write notebook back
        nb["cells"] = cells
        with open(path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        return {
            "path": str(path),
            "action": action,
            "cell_id": cell_id,
        }
