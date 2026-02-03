"""
Sandy Result Reporter

Formats and displays execution results.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from typing import TextIO


__all__ = [
    "Reporter",
    "create_reporter",
]


try:
    from .player import PlayResult, StepResult
except ImportError:
    from player import PlayResult, StepResult


class Reporter:
    """
    Formats execution results for display

    Supports:
    - Console output with colors
    - JSON output for machine parsing
    - Callback hooks for custom formatting
    """

    # ANSI color codes
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(
        self,
        output: TextIO = sys.stdout,
        use_color: bool = True,
        verbose: bool = False,
    ):
        self.output = output
        self.use_color = use_color and output.isatty()
        self.verbose = verbose

    def _color(self, text: str, color: str) -> str:
        """Apply color if enabled"""
        if self.use_color:
            return f"{color}{text}{self.RESET}"
        return text

    def step_start(self, step_num: int, total: int, description: str) -> None:
        """Called when a step starts"""
        prefix = self._color(f"[{step_num}/{total}]", self.BLUE)
        self.output.write(f"{prefix} {description}...")
        self.output.flush()

    def step_complete(self, result: StepResult) -> None:
        """Called when a step completes"""
        if result.skipped:
            status = self._color(" SKIPPED", self.YELLOW)
        elif result.success:
            status = self._color(" OK", self.GREEN)
            if result.retries > 0:
                status += self._color(f" (retry x{result.retries})", self.YELLOW)
        else:
            status = self._color(" FAILED", self.RED)

        duration = self._color(f" ({result.duration:.2f}s)", self.GRAY)
        self.output.write(f"{status}{duration}\n")

        # Show error in verbose mode
        if not result.success and result.error:
            error_text = self._color(f"    Error: {result.error}", self.RED)
            self.output.write(f"{error_text}\n")

        self.output.flush()

    def print_result(self, result: PlayResult) -> None:
        """Print final execution result"""
        self.output.write("\n")
        self.output.write("=" * 60 + "\n")

        # Header
        if result.success:
            status = self._color("PASSED", self.GREEN)
        else:
            status = self._color("FAILED", self.RED)

        header = f"{self.BOLD}Result: {status}{self.RESET}"
        if not self.use_color:
            header = f"Result: {'PASSED' if result.success else 'FAILED'}"

        self.output.write(f"{header}\n")
        self.output.write("-" * 60 + "\n")

        # Summary
        self.output.write(f"Scenario: {result.scenario_name}\n")
        self.output.write(f"Steps: {result.passed_steps}/{result.total_steps} passed\n")
        self.output.write(f"Duration: {result.duration:.2f}s\n")

        if result.failed_step:
            self.output.write(
                self._color(f"Failed at step: {result.failed_step}\n", self.RED)
            )

        # Verbose: show all step results
        if self.verbose:
            self.output.write("\n")
            self.output.write("Step Details:\n")
            for step_result in result.step_results:
                self._print_step_detail(step_result)

        self.output.write("=" * 60 + "\n")
        self.output.flush()

    def _print_step_detail(self, result: StepResult) -> None:
        """Print detailed step result"""
        if result.skipped:
            status = self._color("SKIP", self.YELLOW)
        elif result.success:
            status = self._color("PASS", self.GREEN)
        else:
            status = self._color("FAIL", self.RED)

        self.output.write(f"  [{status}] Step {result.step}: {result.tool}\n")

        if result.description:
            self.output.write(f"        {result.description}\n")

        if result.error:
            self.output.write(self._color(f"        Error: {result.error}\n", self.RED))

        self.output.write(f"        Duration: {result.duration:.2f}s\n")

    def print_json(self, result: PlayResult) -> None:
        """Print result as JSON"""
        data = asdict(result)
        self.output.write(json.dumps(data, indent=2))
        self.output.write("\n")
        self.output.flush()


def create_reporter(
    verbose: bool = False,
    json_output: bool = False,
    output: TextIO | None = None,
) -> Reporter:
    """
    Create a reporter instance

    Args:
        verbose: Show detailed step information
        json_output: Output as JSON (disables colors)
        output: Output stream (default: stdout)

    Returns:
        Configured Reporter instance
    """
    return Reporter(
        output=output or sys.stdout,
        use_color=not json_output,
        verbose=verbose,
    )
