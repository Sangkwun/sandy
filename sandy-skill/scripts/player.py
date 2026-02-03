"""
Sandy Scenario Player

Executes scenarios by calling MCP tools directly (no LLM).
Supports variable substitution and output extraction.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Callable, Literal

from jsonpath_ng import parse as jsonpath_parse


__all__ = [
    # Data classes
    "StepResult",
    "PlayResult",
    "PlayerOptions",
    # Classes
    "ScenarioPlayer",
    # Functions
    "play_scenario",
]


@lru_cache(maxsize=128)
def _cached_jsonpath_parse(path: str):
    """Cache parsed JSONPath expressions"""
    return jsonpath_parse(path)

try:
    from .scenario import Scenario, Step, parse_tool_name, VAR_PATTERN
    from .config import Config, get_server_config
    from .clients import MCPClient, create_client
except ImportError:
    from scenario import Scenario, Step, parse_tool_name, VAR_PATTERN
    from config import Config, get_server_config
    from clients import MCPClient, create_client


@dataclass
class StepResult:
    """Result of a single step execution"""
    step: int
    tool: str
    success: bool
    duration: float
    params: dict[str, Any] = field(default_factory=dict)  # Actual params used
    result: Any = None  # MCP tool raw result
    description: str | None = None
    error: str | None = None
    retries: int = 0
    skipped: bool = False


@dataclass
class PlayResult:
    """Result of scenario execution"""
    scenario_name: str
    success: bool
    total_steps: int
    passed_steps: int
    failed_step: int | None
    duration: float
    step_results: list[StepResult] = field(default_factory=list)  # MCP raw results

    completed_steps: list[int] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)  # JSONPath extracted values
    context: dict[str, Any] = field(default_factory=dict)  # Debug info
    error: str | None = None  # Top-level error message

    @property
    def summary(self) -> str:
        """Generate summary string"""
        status = "PASSED" if self.success else "FAILED"
        return (
            f"{status}: {self.passed_steps}/{self.total_steps} steps "
            f"in {self.duration:.2f}s"
        )

    # Backward compatibility alias
    @property
    def steps(self) -> list[StepResult]:
        """Alias for step_results (backward compatibility)"""
        return self.step_results


@dataclass
class PlayerOptions:
    """Player configuration options"""
    variables: dict[str, str] = field(default_factory=dict)
    start: int | None = None  # Start from step N (inclusive)
    end: int | None = None    # End at step N (inclusive)
    dry_run: bool = False
    debug: bool = False
    default_delay: float = 0.0

    # Result inclusion mode (token optimization)
    # - False (default): Don't include MCP raw results (outputs only)
    # - True: Always include MCP raw results
    # - "on_failure": Only include results when step fails
    include_results: bool | Literal["on_failure"] = False

    # Callbacks
    on_step_start: Callable[[int, int, str], None] | None = None
    on_step_complete: Callable[[StepResult], None] | None = None

    # Backward compatibility alias
    @property
    def resume_from(self) -> int | None:
        """Alias for start (backward compatibility)"""
        return self.start

    @resume_from.setter
    def resume_from(self, value: int | None) -> None:
        self.start = value


class ScenarioPlayer:
    """
    Executes Sandy scenarios

    Features:
    - Variable substitution ({{VAR}} and {{step_id.field}})
    - Output extraction via JSONPath
    - Error handling with retry/skip/stop
    - Resume from specific step
    """

    def __init__(
        self,
        scenario: Scenario,
        config: Config,
        options: PlayerOptions | None = None,
    ):
        self.scenario = scenario
        self.config = config
        self.options = options or PlayerOptions()

        # Merge variables: scenario defaults + options override
        self.variables = {**scenario.variables, **self.options.variables}

        # Step outputs for runtime references
        self.step_outputs: dict[str, dict[str, Any]] = {}

        # MCP clients (lazy-loaded per server)
        self._clients: dict[str, MCPClient] = {}

    async def execute(self) -> PlayResult:
        """
        Execute steps in the scenario

        Supports partial execution via start/end options:
        - start: Begin from step N (inclusive)
        - end: Stop at step N (inclusive)

        Returns:
            PlayResult with execution details
        """
        start_time = time.time()
        results: list[StepResult] = []
        failed_step: int | None = None

        try:
            for step in self.scenario.steps:
                # Skip steps before start point
                if self.options.start and step.step < self.options.start:
                    continue

                # Stop after end point
                if self.options.end and step.step > self.options.end:
                    break

                # Execute step
                step_start = time.time()

                # Notify step start
                if self.options.on_step_start:
                    self.options.on_step_start(
                        step.step,
                        len(self.scenario.steps),
                        step.description or step.tool
                    )

                result = await self._execute_step(step)
                result.duration = time.time() - step_start

                # Apply include_results policy
                self._apply_result_policy(result)

                results.append(result)

                # Notify step complete
                if self.options.on_step_complete:
                    self.options.on_step_complete(result)

                # Handle failure
                if not result.success and not result.skipped:
                    on_error = step.on_error or "stop"
                    if on_error == "stop":
                        failed_step = step.step
                        break
                    # "skip" continues to next step

                # Wait after step
                if step.wait_after:
                    await asyncio.sleep(step.wait_after)
                elif self.options.default_delay > 0:
                    await asyncio.sleep(self.options.default_delay)

        finally:
            # Close all clients
            await self._close_clients()

        duration = time.time() - start_time
        passed = sum(1 for r in results if r.success)
        completed = [r.step for r in results if r.success]

        # Build context and error for debugging
        context: dict[str, Any] = {}
        error: str | None = None
        if failed_step is not None:
            failed_result = next((r for r in results if r.step == failed_step), None)
            if failed_result:
                error = failed_result.error
                context["failed_step_error"] = failed_result.error
                context["failed_step_result"] = failed_result.result

        return PlayResult(
            scenario_name=self.scenario.metadata.name,
            success=failed_step is None and passed == len(results),
            total_steps=len(self.scenario.steps),
            passed_steps=passed,
            failed_step=failed_step,
            duration=duration,
            step_results=results,
            completed_steps=completed,
            outputs=dict(self.step_outputs),  # JSONPath extracted values
            context=context,
            error=error,
        )

    async def _execute_step(self, step: Step) -> StepResult:
        """Execute a single step"""
        # Substitute variables in params early for recording
        substituted_params = self._substitute_variables(step.params)

        step_result = StepResult(
            step=step.step,
            tool=step.tool,
            success=False,
            duration=0,
            params=substituted_params,  # Record actual params used
            description=step.description,
        )

        # Check condition
        if step.condition and not self._evaluate_condition(step.condition):
            step_result.success = True
            step_result.skipped = True
            return step_result

        # Dry run mode
        if self.options.dry_run:
            step_result.success = True
            step_result.result = {"dry_run": True}
            if self.options.debug:
                print(f"  [DRY RUN] {step.tool}")
                print(f"    params: {json.dumps(substituted_params, indent=2)}")
            return step_result

        # Handle Sandy internal tools (no MCP call)
        if step.tool.startswith("sandy__"):
            return await self._execute_internal_tool(step, substituted_params, step_result)

        # Get retry settings
        max_retries = 1
        retry_delay = 0.5
        if step.on_error == "retry":
            retry_config = step.retry or {}
            max_retries = retry_config.get("count", 3)
            retry_delay = retry_config.get("delay", 500) / 1000.0

        # Execute with retries
        for attempt in range(1, max_retries + 1):
            try:
                data = await self._call_tool(step, substituted_params)
                step_result.success = True
                step_result.result = data

                # Extract outputs
                if step.id and step.output:
                    self._extract_output(step.id, step.output, data)

                if attempt > 1:
                    step_result.retries = attempt - 1

                return step_result

            except Exception as e:
                step_result.error = str(e)

                if self.options.debug:
                    print(f"  [ERROR] Attempt {attempt}/{max_retries}: {e}")

                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)

        return step_result

    async def _call_tool(self, step: Step, params: dict[str, Any]) -> Any:
        """Call the MCP tool for a step"""
        # Parse tool name to get server and tool
        server_name, tool_name = parse_tool_name(step.tool)

        # Get or create client
        client = await self._get_client(server_name)

        if self.options.debug:
            print(f"  Calling {server_name}.{tool_name}")
            print(f"    params: {json.dumps(params, indent=2)}")

        # Call tool
        tool_result = await client.call_tool(tool_name, params)

        if not tool_result.success:
            raise Exception(tool_result.error or "Tool call failed")

        if self.options.debug:
            data_str = json.dumps(tool_result.data, indent=2, default=str)
            if len(data_str) > 500:
                data_str = data_str[:500] + "..."
            print(f"    result: {data_str}")

        return tool_result.data

    async def _execute_internal_tool(
        self,
        step: Step,
        params: dict[str, Any],
        step_result: StepResult,
    ) -> StepResult:
        """
        Execute Sandy internal tools (no MCP call)

        Supported tools:
        - sandy__wait: Wait for specified duration (seconds)
        - sandy__log: Log a message (debug)
        """
        tool_name = step.tool.removeprefix("sandy__")

        try:
            if tool_name == "wait":
                duration = params.get("duration", 0)
                if self.options.debug:
                    print(f"  [INTERNAL] wait {duration}s")
                await asyncio.sleep(duration)
                step_result.success = True
                step_result.result = {"waited": duration}

            elif tool_name == "log":
                message = params.get("message", "")
                print(f"  [LOG] {message}")
                step_result.success = True
                step_result.result = {"logged": message}

            else:
                step_result.success = False
                step_result.error = f"Unknown internal tool: {step.tool}"

        except Exception as e:
            step_result.success = False
            step_result.error = str(e)

        return step_result

    async def _get_client(self, server_name: str) -> MCPClient:
        """Get or create MCP client for server"""
        if server_name not in self._clients:
            server_config = get_server_config(self.config, server_name)
            client = await create_client(server_config)
            await client.connect()
            self._clients[server_name] = client

        return self._clients[server_name]

    async def _close_clients(self) -> None:
        """Close all MCP clients"""
        # Note: Sequential closing required due to MCP SDK's anyio cancel scope
        # which has task affinity and doesn't work well with asyncio.gather
        for client in self._clients.values():
            try:
                await client.disconnect()
            except Exception:
                pass  # Ignore errors during cleanup
        self._clients.clear()

    def _substitute_variables(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Substitute variables in params

        Supports:
        - {{VAR}} - Static variable from scenario.variables
        - {{step_id.field}} - Runtime result reference
        """
        return self._substitute_in_value(params)

    def _substitute_in_value(self, value: Any) -> Any:
        """Recursively substitute variables in a value"""
        if isinstance(value, str):
            # Check if entire string is a single variable reference
            match = VAR_PATTERN.fullmatch(value)
            if match:
                # Return the raw value (preserves type: int, bool, dict, etc.)
                return self._get_variable_value(match.group(1))
            return self._substitute_string(value)
        elif isinstance(value, dict):
            return {k: self._substitute_in_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._substitute_in_value(v) for v in value]
        return value

    def _resolve_variable(self, var_ref: str) -> tuple[Any, bool]:
        """
        Resolve a variable reference to its value.

        Args:
            var_ref: Variable reference (e.g., "VAR" or "step_id.field")

        Returns:
            Tuple of (value, found) where found indicates if variable exists
        """
        # Check for step output reference (contains dot)
        if "." in var_ref:
            step_id, field = var_ref.split(".", 1)
            if step_id in self.step_outputs and field in self.step_outputs[step_id]:
                return self.step_outputs[step_id][field], True
            return None, False

        # Check for static variable
        if var_ref in self.variables:
            return self.variables[var_ref], True

        # Check for full step output
        if var_ref in self.step_outputs:
            return self.step_outputs[var_ref], True

        return None, False

    def _get_variable_value(self, var_ref: str) -> Any:
        """Get the raw value of a variable (preserves type)"""
        value, found = self._resolve_variable(var_ref)
        return value if found else ""

    def _substitute_string(self, text: str) -> str:
        """Substitute variables in a string"""
        def replace(match: re.Match[str]) -> str:
            var_ref = match.group(1)
            value, found = self._resolve_variable(var_ref)

            if not found:
                return ""

            # Convert to string appropriately
            if value is None:
                return ""
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return str(value)

        return VAR_PATTERN.sub(replace, text)

    def _extract_output(
        self,
        step_id: str,
        output_spec: dict[str, str],
        data: Any,
    ) -> None:
        """
        Extract output values from tool result

        Args:
            step_id: Step identifier for storing output
            output_spec: Mapping of name -> JSONPath
            data: Tool result data
        """
        extracted: dict[str, Any] = {}

        for name, path in output_spec.items():
            if path == "$":
                # Full result
                extracted[name] = data
            else:
                # JSONPath extraction (cached)
                try:
                    expr = _cached_jsonpath_parse(path)
                    matches = expr.find(data)
                    if matches:
                        extracted[name] = matches[0].value
                    else:
                        extracted[name] = None
                except Exception:
                    extracted[name] = None

        self.step_outputs[step_id] = extracted

        if self.options.debug:
            print(f"  Extracted outputs for '{step_id}': {extracted}")

    def _evaluate_condition(self, condition: str) -> bool:
        """
        Evaluate a condition expression

        Simple implementation supporting:
        - {{step_id.field}} != ""
        - {{VAR}} == "value"
        """
        # Substitute variables first
        evaluated = self._substitute_string(condition)

        # Simple equality checks
        if "==" in evaluated:
            left, right = evaluated.split("==", 1)
            return left.strip().strip('"') == right.strip().strip('"')
        elif "!=" in evaluated:
            left, right = evaluated.split("!=", 1)
            return left.strip().strip('"') != right.strip().strip('"')

        # Non-empty check
        return bool(evaluated.strip())

    def _apply_result_policy(self, result: StepResult) -> None:
        """
        Apply include_results policy to step result.

        Modes:
        - False (default): Clear result to save tokens (outputs are preserved)
        - True: Keep full MCP raw result
        - "on_failure": Only keep result when step failed
        """
        include = self.options.include_results

        if include is True:
            # Keep result as is
            return

        if include == "on_failure":
            # Keep result only if step failed
            if result.success:
                result.result = None
            return

        # Default (False): Clear result to save tokens
        result.result = None


async def play_scenario(
    scenario: Scenario,
    config: Config,
    options: PlayerOptions | None = None,
) -> PlayResult:
    """
    Convenience function to play a scenario

    Args:
        scenario: Loaded scenario
        config: MCP configuration
        options: Player options

    Returns:
        PlayResult with execution details
    """
    player = ScenarioPlayer(scenario, config, options)
    return await player.execute()
