"""
Tests for scenario.py
"""

import json
import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scenario import (
    load_scenario,
    parse_scenario,
    validate_scenario,
    parse_tool_name,
    get_required_variables,
    convert_action_to_tool,
    ScenarioValidationError,
)


class TestLoadScenario:
    """Tests for load_scenario function"""

    def test_load_valid_scenario(self, tmp_path):
        """Should load a valid v2.1 scenario"""
        scenario_data = {
            "version": "2.1",
            "metadata": {"name": "Test Scenario"},
            "variables": {"VAR1": "value1"},
            "steps": [
                {
                    "step": 1,
                    "tool": "mcp__test__action",
                    "params": {"key": "{{VAR1}}"},
                }
            ],
        }

        scenario_file = tmp_path / "test.json"
        scenario_file.write_text(json.dumps(scenario_data))

        scenario = load_scenario(scenario_file)

        assert scenario.version == "2.1"
        assert scenario.metadata.name == "Test Scenario"
        assert scenario.variables == {"VAR1": "value1"}
        assert len(scenario.steps) == 1
        assert scenario.steps[0].tool == "mcp__test__action"

    def test_load_nonexistent_file(self):
        """Should raise FileNotFoundError for missing file"""
        with pytest.raises(FileNotFoundError):
            load_scenario("/nonexistent/path/scenario.json")

    def test_load_invalid_json(self, tmp_path):
        """Should raise ScenarioValidationError for invalid JSON"""
        scenario_file = tmp_path / "invalid.json"
        scenario_file.write_text("{ invalid json }")

        with pytest.raises(ScenarioValidationError, match="Invalid JSON"):
            load_scenario(scenario_file)


class TestValidateScenario:
    """Tests for validate_scenario function"""

    def test_missing_version(self):
        """Should reject scenario without version"""
        with pytest.raises(ScenarioValidationError, match="version"):
            validate_scenario({"metadata": {"name": "Test"}, "steps": []})

    def test_missing_metadata(self):
        """Should reject scenario without metadata"""
        with pytest.raises(ScenarioValidationError, match="metadata"):
            validate_scenario({"version": "2.1", "steps": []})

    def test_missing_metadata_name(self):
        """Should reject scenario without metadata.name"""
        with pytest.raises(ScenarioValidationError, match="metadata.name"):
            validate_scenario({
                "version": "2.1",
                "metadata": {"description": "has desc but no name"},
                "steps": [{"step": 1, "tool": "mcp__t__t", "params": {}}]
            })

    def test_missing_steps(self):
        """Should reject scenario without steps"""
        with pytest.raises(ScenarioValidationError, match="steps"):
            validate_scenario({
                "version": "2.1",
                "metadata": {"name": "Test"}
            })

    def test_empty_steps(self):
        """Should reject scenario with empty steps array"""
        with pytest.raises(ScenarioValidationError, match="steps"):
            validate_scenario({
                "version": "2.1",
                "metadata": {"name": "Test"},
                "steps": []
            })

    def test_step_missing_tool_and_action(self):
        """Should reject step without tool or action"""
        with pytest.raises(ScenarioValidationError, match="tool.*action"):
            validate_scenario({
                "version": "2.1",
                "metadata": {"name": "Test"},
                "steps": [{"step": 1, "params": {}}]
            })

    def test_step_missing_params(self):
        """Should reject step without params"""
        with pytest.raises(ScenarioValidationError, match="params"):
            validate_scenario({
                "version": "2.1",
                "metadata": {"name": "Test"},
                "steps": [{"step": 1, "tool": "mcp__test__action"}]
            })

    def test_duplicate_step_id(self):
        """Should reject duplicate step IDs"""
        with pytest.raises(ScenarioValidationError, match="duplicate id"):
            validate_scenario({
                "version": "2.1",
                "metadata": {"name": "Test"},
                "steps": [
                    {"step": 1, "id": "same_id", "tool": "mcp__test__a", "params": {}},
                    {"step": 2, "id": "same_id", "tool": "mcp__test__b", "params": {}},
                ]
            })

    def test_output_without_id(self):
        """Should reject output field without id"""
        with pytest.raises(ScenarioValidationError, match="output.*requires.*id"):
            validate_scenario({
                "version": "2.1",
                "metadata": {"name": "Test"},
                "steps": [
                    {
                        "step": 1,
                        "tool": "mcp__test__action",
                        "params": {},
                        "output": {"field": "$.value"}
                    }
                ]
            })

    def test_invalid_on_error(self):
        """Should reject invalid on_error value"""
        with pytest.raises(ScenarioValidationError, match="on_error"):
            validate_scenario({
                "version": "2.1",
                "metadata": {"name": "Test"},
                "steps": [
                    {
                        "step": 1,
                        "tool": "mcp__test__action",
                        "params": {},
                        "on_error": "invalid"
                    }
                ]
            })

    def test_valid_scenario(self):
        """Should accept valid scenario"""
        validate_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "steps": [
                {
                    "step": 1,
                    "id": "step1",
                    "tool": "mcp__test__action",
                    "params": {"key": "value"},
                    "output": {"result": "$.data"},
                    "on_error": "retry"
                }
            ]
        })


class TestParseToolName:
    """Tests for parse_tool_name function"""

    def test_valid_tool_name(self):
        """Should parse valid tool name"""
        server, tool = parse_tool_name("mcp__github__create_issue")
        assert server == "github"
        assert tool == "create_issue"

    def test_tool_with_dashes(self):
        """Should handle server names with dashes"""
        server, tool = parse_tool_name("mcp__chrome-devtools__click")
        assert server == "chrome-devtools"
        assert tool == "click"

    def test_tool_with_underscores(self):
        """Should handle tool names with underscores"""
        server, tool = parse_tool_name("mcp__server__tool_name_here")
        assert server == "server"
        assert tool == "tool_name_here"

    def test_invalid_prefix(self):
        """Should reject tool without mcp__ prefix"""
        with pytest.raises(ValueError, match="Invalid tool name"):
            parse_tool_name("invalid__server__tool")

    def test_missing_tool_part(self):
        """Should reject tool without tool part"""
        with pytest.raises(ValueError, match="Invalid tool name"):
            parse_tool_name("mcp__server")


class TestConvertActionToTool:
    """Tests for convert_action_to_tool function"""

    def test_navigate_action(self):
        """Should convert navigate to chrome-devtools tool"""
        tool = convert_action_to_tool("navigate")
        assert tool == "mcp__chrome-devtools__navigate_page"

    def test_click_action(self):
        """Should convert click to chrome-devtools tool"""
        tool = convert_action_to_tool("click")
        assert tool == "mcp__chrome-devtools__click"

    def test_fill_action(self):
        """Should convert fill to chrome-devtools tool"""
        tool = convert_action_to_tool("fill")
        assert tool == "mcp__chrome-devtools__fill"

    def test_unknown_action(self):
        """Should handle unknown action"""
        tool = convert_action_to_tool("unknown_action")
        assert tool == "mcp__unknown__unknown_action"


class TestGetRequiredVariables:
    """Tests for get_required_variables function"""

    def test_empty_value_is_required(self):
        """Should detect empty-valued variables as required"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": {"VAR1": "", "VAR2": "has_value"},
            "steps": [{"step": 1, "tool": "mcp__t__t", "params": {}}]
        })

        required = get_required_variables(scenario)
        assert "VAR1" in required
        assert "VAR2" not in required

    def test_undefined_variable_in_params(self):
        """Should detect undefined variables in params"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": {},
            "steps": [
                {
                    "step": 1,
                    "tool": "mcp__t__t",
                    "params": {"key": "{{UNDEFINED_VAR}}"}
                }
            ]
        })

        required = get_required_variables(scenario)
        assert "UNDEFINED_VAR" in required

    def test_defined_variable_not_required(self):
        """Should not mark defined variables as required"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": {"DEFINED": "value"},
            "steps": [
                {
                    "step": 1,
                    "tool": "mcp__t__t",
                    "params": {"key": "{{DEFINED}}"}
                }
            ]
        })

        required = get_required_variables(scenario)
        assert "DEFINED" not in required


class TestV11Compatibility:
    """Tests for v1.1 backward compatibility"""

    def test_action_converted_to_tool(self):
        """Should convert action field to tool"""
        scenario = parse_scenario({
            "version": "1.1",
            "metadata": {"name": "Test"},
            "variables": {},
            "steps": [
                {
                    "step": 1,
                    "action": "navigate",
                    "params": {"url": "https://example.com"}
                }
            ]
        })

        assert scenario.steps[0].tool == "mcp__chrome-devtools__navigate_page"

    def test_mixed_action_and_tool(self):
        """Should prefer tool over action when both present"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": {},
            "steps": [
                {
                    "step": 1,
                    "tool": "mcp__custom__tool",
                    "action": "navigate",  # Should be ignored
                    "params": {}
                }
            ]
        })

        assert scenario.steps[0].tool == "mcp__custom__tool"
