"""
Tests for player.py
"""

import json
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scenario import parse_scenario
from config import load_sandy_config
from player import ScenarioPlayer, PlayerOptions, StepResult, PlayResult


class TestVariableSubstitution:
    """Tests for variable substitution"""

    def create_player(self, steps, variables=None, options=None):
        """Helper to create a player with minimal config"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": variables or {},
            "steps": steps
        })

        # Mock config with no servers (we won't actually call tools)
        class MockConfig:
            servers = {}
            source = "test"

        return ScenarioPlayer(scenario, MockConfig(), options or PlayerOptions())

    def test_simple_variable(self):
        """Should substitute simple {{VAR}}"""
        player = self.create_player(
            steps=[{"step": 1, "tool": "mcp__t__t", "params": {"key": "{{VAR}}"}}],
            variables={"VAR": "value123"}
        )

        result = player._substitute_variables({"key": "{{VAR}}"})
        assert result["key"] == "value123"

    def test_multiple_variables(self):
        """Should substitute multiple variables in one string"""
        player = self.create_player(
            steps=[{"step": 1, "tool": "mcp__t__t", "params": {}}],
            variables={"A": "hello", "B": "world"}
        )

        result = player._substitute_variables({"msg": "{{A}} {{B}}!"})
        assert result["msg"] == "hello world!"

    def test_nested_dict(self):
        """Should substitute in nested dicts"""
        player = self.create_player(
            steps=[{"step": 1, "tool": "mcp__t__t", "params": {}}],
            variables={"VAR": "nested_value"}
        )

        result = player._substitute_variables({
            "outer": {
                "inner": "{{VAR}}"
            }
        })
        assert result["outer"]["inner"] == "nested_value"

    def test_list_values(self):
        """Should substitute in list values"""
        player = self.create_player(
            steps=[{"step": 1, "tool": "mcp__t__t", "params": {}}],
            variables={"VAR": "item"}
        )

        result = player._substitute_variables({
            "items": ["{{VAR}}", "static"]
        })
        assert result["items"] == ["item", "static"]

    def test_undefined_variable(self):
        """Should replace undefined variable with empty string"""
        player = self.create_player(
            steps=[{"step": 1, "tool": "mcp__t__t", "params": {}}],
            variables={}
        )

        result = player._substitute_variables({"key": "prefix_{{UNDEFINED}}_suffix"})
        assert result["key"] == "prefix__suffix"

    def test_step_output_reference(self):
        """Should substitute step output references"""
        player = self.create_player(
            steps=[{"step": 1, "tool": "mcp__t__t", "params": {}}],
            variables={}
        )

        # Simulate step output
        player.step_outputs["step1"] = {"number": 42, "url": "https://example.com"}

        result = player._substitute_variables({
            "text": "Issue #{{step1.number}} at {{step1.url}}"
        })
        assert result["text"] == "Issue #42 at https://example.com"

    def test_options_override_scenario_variables(self):
        """Options variables should override scenario variables"""
        player = self.create_player(
            steps=[{"step": 1, "tool": "mcp__t__t", "params": {}}],
            variables={"VAR": "original"},
            options=PlayerOptions(variables={"VAR": "overridden"})
        )

        result = player._substitute_variables({"key": "{{VAR}}"})
        assert result["key"] == "overridden"


class TestOutputExtraction:
    """Tests for output extraction"""

    def create_player(self):
        """Helper to create a player"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": {},
            "steps": [{"step": 1, "tool": "mcp__t__t", "params": {}}]
        })

        class MockConfig:
            servers = {}
            source = "test"

        return ScenarioPlayer(scenario, MockConfig(), PlayerOptions())

    def test_extract_top_level_field(self):
        """Should extract top-level field with $."""
        player = self.create_player()

        data = {"id": 123, "name": "test"}
        player._extract_output("step1", {"id_value": "$.id"}, data)

        assert player.step_outputs["step1"]["id_value"] == 123

    def test_extract_nested_field(self):
        """Should extract nested field"""
        player = self.create_player()

        data = {"data": {"user": {"name": "John"}}}
        player._extract_output("step1", {"user_name": "$.data.user.name"}, data)

        assert player.step_outputs["step1"]["user_name"] == "John"

    def test_extract_array_element(self):
        """Should extract array element"""
        player = self.create_player()

        data = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}
        player._extract_output("step1", {"first_id": "$.items[0].id"}, data)

        assert player.step_outputs["step1"]["first_id"] == 1

    def test_extract_full_result(self):
        """Should extract full result with $"""
        player = self.create_player()

        data = {"id": 123, "name": "test"}
        player._extract_output("step1", {"full": "$"}, data)

        assert player.step_outputs["step1"]["full"] == data

    def test_extract_missing_path(self):
        """Should return None for missing path"""
        player = self.create_player()

        data = {"id": 123}
        player._extract_output("step1", {"missing": "$.nonexistent.path"}, data)

        assert player.step_outputs["step1"]["missing"] is None


class TestConditionEvaluation:
    """Tests for condition evaluation"""

    def create_player(self, variables=None, step_outputs=None):
        """Helper to create a player"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": variables or {},
            "steps": [{"step": 1, "tool": "mcp__t__t", "params": {}}]
        })

        class MockConfig:
            servers = {}
            source = "test"

        player = ScenarioPlayer(scenario, MockConfig(), PlayerOptions())
        if step_outputs:
            player.step_outputs = step_outputs
        return player

    def test_equality_true(self):
        """Should evaluate equality as true"""
        player = self.create_player(variables={"VAR": "value"})
        assert player._evaluate_condition('{{VAR}} == "value"') is True

    def test_equality_false(self):
        """Should evaluate equality as false"""
        player = self.create_player(variables={"VAR": "value"})
        assert player._evaluate_condition('{{VAR}} == "other"') is False

    def test_inequality_true(self):
        """Should evaluate inequality as true"""
        player = self.create_player(variables={"VAR": "value"})
        assert player._evaluate_condition('{{VAR}} != "other"') is True

    def test_inequality_false(self):
        """Should evaluate inequality as false"""
        player = self.create_player(variables={"VAR": "value"})
        assert player._evaluate_condition('{{VAR}} != "value"') is False

    def test_non_empty_check(self):
        """Should evaluate non-empty as true"""
        player = self.create_player(step_outputs={"step1": {"value": "something"}})
        assert player._evaluate_condition("{{step1.value}}") is True

    def test_empty_check(self):
        """Should evaluate empty as false"""
        player = self.create_player(step_outputs={"step1": {"value": ""}})
        # Empty string after substitution evaluates to falsy
        assert player._evaluate_condition("{{step1.value}}") is False


class TestStepResult:
    """Tests for StepResult dataclass"""

    def test_step_result_creation(self):
        """Should create StepResult with all fields"""
        step_result = StepResult(
            step=1,
            tool="mcp__test__action",
            success=True,
            duration=1.5,
            params={"input": "test"},
            result={"key": "value"},
            description="Test step",
            error=None,
            retries=0,
            skipped=False
        )

        assert step_result.step == 1
        assert step_result.tool == "mcp__test__action"
        assert step_result.success is True
        assert step_result.duration == 1.5
        assert step_result.params == {"input": "test"}
        assert step_result.result == {"key": "value"}


class TestPlayResult:
    """Tests for PlayResult dataclass"""

    def test_play_result_summary_passed(self):
        """Should generate PASSED summary"""
        result = PlayResult(
            scenario_name="Test",
            success=True,
            total_steps=3,
            passed_steps=3,
            failed_step=None,
            duration=5.5,
            step_results=[]
        )

        assert "PASSED" in result.summary
        assert "3/3" in result.summary

    def test_play_result_summary_failed(self):
        """Should generate FAILED summary"""
        result = PlayResult(
            scenario_name="Test",
            success=False,
            total_steps=3,
            passed_steps=2,
            failed_step=3,
            duration=5.5,
            step_results=[]
        )

        assert "FAILED" in result.summary
        assert "2/3" in result.summary

    def test_play_result_backward_compatibility(self):
        """Should support 'steps' property for backward compatibility"""
        step = StepResult(step=1, tool="test", success=True, duration=1.0)
        result = PlayResult(
            scenario_name="Test",
            success=True,
            total_steps=1,
            passed_steps=1,
            failed_step=None,
            duration=1.0,
            step_results=[step]
        )

        # Backward compatibility: .steps should return step_results
        assert result.steps == result.step_results
        assert len(result.steps) == 1


class TestIncludeResultsPolicy:
    """Tests for include_results option"""

    def create_player(self, include_results=False):
        """Helper to create a player with include_results option"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": {},
            "steps": [{"step": 1, "tool": "mcp__t__t", "params": {}}]
        })

        class MockConfig:
            servers = {}
            source = "test"

        options = PlayerOptions(include_results=include_results)
        return ScenarioPlayer(scenario, MockConfig(), options)

    def test_include_results_false_clears_result(self):
        """Should clear result when include_results=False (default)"""
        player = self.create_player(include_results=False)

        result = StepResult(
            step=1,
            tool="mcp__test__action",
            success=True,
            duration=1.0,
            result={"key": "value"}  # MCP raw result
        )

        player._apply_result_policy(result)

        assert result.result is None

    def test_include_results_true_keeps_result(self):
        """Should keep result when include_results=True"""
        player = self.create_player(include_results=True)

        result = StepResult(
            step=1,
            tool="mcp__test__action",
            success=True,
            duration=1.0,
            result={"key": "value"}  # MCP raw result
        )

        player._apply_result_policy(result)

        assert result.result == {"key": "value"}

    def test_include_results_on_failure_clears_on_success(self):
        """Should clear result on success when include_results='on_failure'"""
        player = self.create_player(include_results="on_failure")

        result = StepResult(
            step=1,
            tool="mcp__test__action",
            success=True,
            duration=1.0,
            result={"key": "value"}
        )

        player._apply_result_policy(result)

        assert result.result is None

    def test_include_results_on_failure_keeps_on_failure(self):
        """Should keep result on failure when include_results='on_failure'"""
        player = self.create_player(include_results="on_failure")

        result = StepResult(
            step=1,
            tool="mcp__test__action",
            success=False,
            duration=1.0,
            result={"error_data": "details"},
            error="Something went wrong"
        )

        player._apply_result_policy(result)

        assert result.result == {"error_data": "details"}
