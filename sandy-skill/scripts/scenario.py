"""
Sandy Scenario Loader and Validator

Supports scenario format v2.1 with:
- MCP Tool calls (tool field instead of action)
- Runtime result references (id, output fields)
- Variable substitution ({{VAR}}, {{step_id.field}})
- v1.1 backwards compatibility (action -> tool conversion)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


__all__ = [
    # Data classes
    "ScenarioMetadata",
    "Step",
    "Scenario",
    # Exceptions
    "ScenarioValidationError",
    # Functions
    "load_scenario",
    "parse_scenario",
    "get_required_variables",
    "parse_tool_name",
    # Constants
    "VAR_PATTERN",
]


# Pre-compiled regex pattern for variable detection
# Matches {{VAR}} and {{step_id.field}} patterns
VAR_PATTERN = re.compile(r"\{\{([^}]+)\}\}")


@dataclass
class ScenarioMetadata:
    """Scenario metadata"""
    name: str
    created_at: str | None = None
    description: str | None = None
    created_by: str | None = None


@dataclass
class Step:
    """Scenario step"""
    step: int
    tool: str
    params: dict[str, Any]
    id: str | None = None
    output: dict[str, str] | None = None
    description: str | None = None
    wait_after: float | None = None  # Delay in seconds after step completion
    on_error: str | None = None  # "stop", "skip", "retry"
    retry: dict[str, Any] | None = None
    condition: str | None = None


@dataclass
class Scenario:
    """Sandy scenario"""
    version: str
    metadata: ScenarioMetadata
    steps: list[Step]
    variables: dict[str, str] = field(default_factory=dict)


class ScenarioValidationError(Exception):
    """Raised when scenario validation fails"""
    pass


def load_scenario(file_path: str | Path) -> Scenario:
    """
    Load and parse a scenario file

    Args:
        file_path: Path to the scenario JSON file

    Returns:
        Parsed Scenario object

    Raises:
        ScenarioValidationError: If scenario is invalid
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ScenarioValidationError(f"Invalid JSON in scenario file: {e}")

    return parse_scenario(data)


def parse_scenario(data: dict[str, Any]) -> Scenario:
    """
    Parse scenario data from dict

    Args:
        data: Raw scenario dict

    Returns:
        Parsed Scenario object
    """
    validate_scenario(data)

    version = data.get("version", "2.1")

    # Parse metadata
    raw_metadata = data.get("metadata", {})
    metadata = ScenarioMetadata(
        name=raw_metadata.get("name", "Unnamed Scenario"),
        created_at=raw_metadata.get("created_at"),
        description=raw_metadata.get("description"),
        created_by=raw_metadata.get("created_by"),
    )

    # Parse steps
    steps = []
    for step_data in data.get("steps", []):
        step = parse_step(step_data, version)
        steps.append(step)

    return Scenario(
        version=version,
        metadata=metadata,
        steps=steps,
        variables=data.get("variables", {}),
    )


def parse_step(step_data: dict[str, Any], version: str) -> Step:
    """
    Parse a single step

    Supports v1.1 (action) and v2.1 (tool) formats
    """
    step_num = step_data.get("step", 0)

    # Handle v1.1 -> v2.1 conversion
    if "action" in step_data and "tool" not in step_data:
        # Convert v1.1 action to v2.1 tool format
        tool = convert_action_to_tool(step_data["action"])
    else:
        tool = step_data.get("tool", "")

    return Step(
        step=step_num,
        tool=tool,
        params=step_data.get("params", {}),
        id=step_data.get("id"),
        output=step_data.get("output"),
        description=step_data.get("description"),
        wait_after=step_data.get("wait_after"),
        on_error=step_data.get("on_error"),
        retry=step_data.get("retry"),
        condition=step_data.get("condition"),
    )


def convert_action_to_tool(action: str) -> str:
    """
    Convert v1.1 action to v2.1 tool name

    Default mapping uses chrome-devtools MCP server
    """
    action_to_tool = {
        "navigate": "mcp__chrome-devtools__navigate_page",
        "click": "mcp__chrome-devtools__click",
        "fill": "mcp__chrome-devtools__fill",
        "type": "mcp__chrome-devtools__press_key",  # character by character
        "key": "mcp__chrome-devtools__press_key",
        "screenshot": "mcp__chrome-devtools__take_screenshot",
        "wait": "mcp__chrome-devtools__evaluate_script",  # setTimeout
        "wait_for_text": "mcp__chrome-devtools__wait_for",
        "scroll": "mcp__chrome-devtools__evaluate_script",  # scrollBy
        "hover": "mcp__chrome-devtools__hover",
    }
    return action_to_tool.get(action, f"mcp__unknown__{action}")


def validate_scenario(data: dict[str, Any]) -> None:
    """
    Validate scenario structure

    Raises:
        ScenarioValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ScenarioValidationError("Scenario must be a JSON object")

    # Version check
    version = data.get("version")
    if not version:
        raise ScenarioValidationError("Scenario missing 'version' field")

    # Metadata check
    metadata = data.get("metadata")
    if not metadata:
        raise ScenarioValidationError("Scenario missing 'metadata' field")

    if not metadata.get("name"):
        raise ScenarioValidationError("Scenario missing 'metadata.name' field")

    # Steps check
    steps = data.get("steps")
    if not steps or not isinstance(steps, list):
        raise ScenarioValidationError("Scenario missing 'steps' array")

    if len(steps) == 0:
        raise ScenarioValidationError("Scenario must have at least one step")

    # Validate each step
    step_ids: set[str] = set()
    for i, step in enumerate(steps):
        validate_step(step, i, step_ids)


def validate_step(step: dict[str, Any], index: int, step_ids: set[str]) -> None:
    """
    Validate a single step

    Args:
        step: Step data
        index: Step index (for error messages)
        step_ids: Set of seen step IDs (for duplicate checking)
    """
    if not isinstance(step, dict):
        raise ScenarioValidationError(f"Step {index + 1}: must be an object")

    # Step number
    if "step" not in step:
        raise ScenarioValidationError(f"Step {index + 1}: missing 'step' number")

    step_num = step["step"]

    # Tool or action required
    if "tool" not in step and "action" not in step:
        raise ScenarioValidationError(f"Step {step_num}: missing 'tool' or 'action' field")

    # Params required
    if "params" not in step:
        raise ScenarioValidationError(f"Step {step_num}: missing 'params' field")

    if not isinstance(step["params"], dict):
        raise ScenarioValidationError(f"Step {step_num}: 'params' must be an object")

    # ID uniqueness check
    if "id" in step:
        step_id = step["id"]
        if step_id in step_ids:
            raise ScenarioValidationError(f"Step {step_num}: duplicate id '{step_id}'")
        step_ids.add(step_id)

    # Output validation (requires id)
    if "output" in step:
        if "id" not in step:
            raise ScenarioValidationError(
                f"Step {step_num}: 'output' requires 'id' field for result reference"
            )
        if not isinstance(step["output"], dict):
            raise ScenarioValidationError(f"Step {step_num}: 'output' must be an object")

    # on_error validation
    if "on_error" in step:
        valid_behaviors = {"stop", "skip", "retry"}
        if step["on_error"] not in valid_behaviors:
            raise ScenarioValidationError(
                f"Step {step_num}: 'on_error' must be one of {valid_behaviors}"
            )

    # retry validation
    if "retry" in step:
        retry = step["retry"]
        if not isinstance(retry, dict):
            raise ScenarioValidationError(f"Step {step_num}: 'retry' must be an object")


def get_required_variables(scenario: Scenario) -> list[str]:
    """
    Get list of variables that need to be provided

    Variables are required if:
    1. Defined in variables but with empty value
    2. Referenced in steps but not defined

    Returns:
        List of required variable names
    """
    required: set[str] = set()
    defined = set(scenario.variables.keys())

    # Check for empty-valued definitions
    for key, value in scenario.variables.items():
        if not value:
            required.add(key)

    # Find variable references in steps
    for step in scenario.steps:
        params_str = json.dumps(step.params)
        matches = VAR_PATTERN.findall(params_str)
        for var_name in matches:
            # Skip step output references (contain dots when used)
            if "." not in var_name and var_name not in defined:
                required.add(var_name)

    return sorted(required)


def parse_tool_name(tool: str) -> tuple[str, str]:
    """
    Parse MCP tool name into server and tool parts

    Args:
        tool: Tool name like "mcp__server__tool_name"

    Returns:
        Tuple of (server_name, tool_name)
    """
    if not tool.startswith("mcp__"):
        raise ValueError(f"Invalid tool name format: {tool}")

    parts = tool[5:].split("__", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid tool name format: {tool}")

    return parts[0], parts[1]
