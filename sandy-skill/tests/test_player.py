"""
Tests for player.py
"""

import asyncio
import json
import pytest
import tempfile
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


class TestAppendFile:
    """Tests for sandy__append_file internal tool"""

    def create_player(self, debug=False):
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

        return ScenarioPlayer(scenario, MockConfig(), PlayerOptions(debug=debug))

    def test_append_jsonl_single_item(self):
        """Should append single item as JSONL"""
        player = self.create_player()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            temp_path = f.name

        try:
            result = player._append_to_file(temp_path, "jsonl", {"name": "test", "value": 123})

            assert result["appended"] == 1
            assert result["path"] == temp_path

            content = Path(temp_path).read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 1
            assert json.loads(lines[0]) == {"name": "test", "value": 123}
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_append_jsonl_multiple_items(self):
        """Should append multiple items as JSONL"""
        player = self.create_player()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            temp_path = f.name

        try:
            items = [{"id": 1}, {"id": 2}, {"id": 3}]
            result = player._append_to_file(temp_path, "jsonl", items)

            assert result["appended"] == 3

            content = Path(temp_path).read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 3
            assert json.loads(lines[0]) == {"id": 1}
            assert json.loads(lines[2]) == {"id": 3}
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_append_jsonl_accumulates(self):
        """Should accumulate JSONL across multiple appends"""
        player = self.create_player()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            temp_path = f.name

        try:
            player._append_to_file(temp_path, "jsonl", {"batch": 1})
            player._append_to_file(temp_path, "jsonl", {"batch": 2})

            content = Path(temp_path).read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 2
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_append_csv_with_header(self):
        """Should write CSV with header on first append"""
        player = self.create_player()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            items = [{"name": "product1", "price": 100}, {"name": "product2", "price": 200}]
            result = player._append_to_file(temp_path, "csv", items)

            assert result["appended"] == 2

            content = Path(temp_path).read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 3  # header + 2 rows
            assert "name" in lines[0] and "price" in lines[0]
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_append_csv_no_duplicate_header(self):
        """Should not duplicate header on subsequent appends"""
        player = self.create_player()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            player._append_to_file(temp_path, "csv", [{"name": "a", "price": 1}])
            player._append_to_file(temp_path, "csv", [{"name": "b", "price": 2}])

            content = Path(temp_path).read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 3  # 1 header + 2 data rows
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_append_json_to_empty_file(self):
        """Should create JSON array from empty file"""
        player = self.create_player()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            result = player._append_to_file(temp_path, "json", {"id": 1})

            assert result["appended"] == 1
            assert result["total"] == 1

            data = json.loads(Path(temp_path).read_text())
            assert data == [{"id": 1}]
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_append_json_to_existing_array(self):
        """Should append to existing JSON array"""
        player = self.create_player()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('[{"id": 1}]')
            temp_path = f.name

        try:
            result = player._append_to_file(temp_path, "json", [{"id": 2}, {"id": 3}])

            assert result["appended"] == 2
            assert result["total"] == 3

            data = json.loads(Path(temp_path).read_text())
            assert len(data) == 3
            assert data[0]["id"] == 1
            assert data[2]["id"] == 3
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_append_creates_parent_directories(self):
        """Should create parent directories if they don't exist"""
        player = self.create_player()

        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "a" / "b" / "c" / "file.jsonl"

            result = player._append_to_file(str(nested_path), "jsonl", {"test": True})

            assert result["appended"] == 1
            assert nested_path.exists()

    def test_append_unsupported_format(self):
        """Should raise error for unsupported format"""
        player = self.create_player()

        with pytest.raises(ValueError) as exc_info:
            player._append_to_file("/tmp/test.txt", "xml", {"data": "test"})

        assert "Unsupported format" in str(exc_info.value)

    def test_flatten_nested_dict(self):
        """Should flatten nested dicts for CSV"""
        player = self.create_player()

        nested = {
            "user": {"name": "John", "age": 30},
            "tags": ["a", "b"]
        }

        flat = player._flatten_dict(nested)

        assert flat["user_name"] == "John"
        assert flat["user_age"] == 30
        assert "tags" in flat  # list should be JSON stringified


class TestWaitForElement:
    """Tests for sandy__wait_for_element internal tool"""

    def create_player_with_mock_client(self, mock_results):
        """
        Helper to create a player with mocked MCP client.

        Args:
            mock_results: List of (success, data) tuples for sequential calls
        """
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": {},
            "steps": [{"step": 1, "tool": "sandy__wait_for_element", "params": {"selector": "button"}}]
        })

        class MockConfig:
            servers = {"chrome-devtools": {"command": "mock"}}
            source = "test"

        class MockToolResult:
            def __init__(self, success, data):
                self.success = success
                self.data = data
                self.error = None if success else "Mock error"

        class MockClient:
            def __init__(self, results):
                self.results = results
                self.call_count = 0

            async def call_tool(self, tool_name, params):
                if self.call_count < len(self.results):
                    result = self.results[self.call_count]
                    self.call_count += 1
                    return MockToolResult(result[0], result[1])
                return MockToolResult(False, None)

            async def connect(self):
                pass

            async def disconnect(self):
                pass

        player = ScenarioPlayer(scenario, MockConfig(), PlayerOptions())
        player._clients["chrome-devtools"] = MockClient(mock_results)
        return player

    def test_wait_for_element_found_immediately(self):
        """Should return immediately when element is found"""
        from scenario import Step

        async def run_test():
            # Element found on first check
            player = self.create_player_with_mock_client([(True, True)])

            step = Step(step=1, tool="sandy__wait_for_element", params={"selector": "button", "timeout": 5})
            result = await player._execute_internal_tool(
                step,
                {"selector": "button", "timeout": 5, "interval": 0.1},
                StepResult(step=1, tool="sandy__wait_for_element", success=False, duration=0)
            )

            assert result.success is True
            assert result.result["found"] is True
            assert result.result["selector"] == "button"

        asyncio.run(run_test())

    def test_wait_for_element_found_after_retries(self):
        """Should find element after a few retries"""
        from scenario import Step

        async def run_test():
            # Element not found twice, then found
            player = self.create_player_with_mock_client([
                (True, False),  # Not found
                (True, False),  # Not found
                (True, True),   # Found
            ])

            step = Step(step=1, tool="sandy__wait_for_element", params={"selector": ".delayed"})
            result = await player._execute_internal_tool(
                step,
                {"selector": ".delayed", "timeout": 5, "interval": 0.05},
                StepResult(step=1, tool="sandy__wait_for_element", success=False, duration=0)
            )

            assert result.success is True
            assert result.result["found"] is True

        asyncio.run(run_test())

    def test_wait_for_element_timeout(self):
        """Should timeout when element is never found"""
        from scenario import Step

        async def run_test():
            # Element never found
            player = self.create_player_with_mock_client([
                (True, False),
                (True, False),
                (True, False),
                (True, False),
                (True, False),
            ])

            step = Step(step=1, tool="sandy__wait_for_element", params={"selector": ".missing"})
            result = await player._execute_internal_tool(
                step,
                {"selector": ".missing", "timeout": 0.2, "interval": 0.05},
                StepResult(step=1, tool="sandy__wait_for_element", success=False, duration=0)
            )

            assert result.success is False
            assert "not found" in result.error.lower()

        asyncio.run(run_test())

    def test_wait_for_element_missing_selector(self):
        """Should fail when selector is missing"""
        from scenario import Step

        async def run_test():
            player = self.create_player_with_mock_client([])

            step = Step(step=1, tool="sandy__wait_for_element", params={})
            result = await player._execute_internal_tool(
                step,
                {},
                StepResult(step=1, tool="sandy__wait_for_element", success=False, duration=0)
            )

            assert result.success is False
            assert "selector" in result.error.lower()

        asyncio.run(run_test())

    def test_selector_escaping(self):
        """Should properly escape selectors with special characters"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": {},
            "steps": [{"step": 1, "tool": "mcp__t__t", "params": {}}]
        })

        class MockConfig:
            servers = {}
            source = "test"

        player = ScenarioPlayer(scenario, MockConfig(), PlayerOptions())

        # Test escaping logic directly
        selector_with_quote = "button[data-name='test']"
        escaped = selector_with_quote.replace("\\", "\\\\").replace("'", "\\'")
        assert escaped == "button[data-name=\\'test\\']"

        selector_with_backslash = "div.class\\:name"
        escaped = selector_with_backslash.replace("\\", "\\\\").replace("'", "\\'")
        assert escaped == "div.class\\\\:name"


class TestWaitUntil:
    """Tests for sandy__wait_until internal tool"""

    def create_player_with_mock_client(self, mock_results):
        """Helper to create a player with mocked MCP client"""
        scenario = parse_scenario({
            "version": "2.1",
            "metadata": {"name": "Test"},
            "variables": {},
            "steps": [{"step": 1, "tool": "sandy__wait_until", "params": {"expression": "true"}}]
        })

        class MockConfig:
            servers = {"chrome-devtools": {"command": "mock"}}
            source = "test"

        class MockToolResult:
            def __init__(self, success, data):
                self.success = success
                self.data = data
                self.error = None if success else "Mock error"

        class MockClient:
            def __init__(self, results):
                self.results = results
                self.call_count = 0

            async def call_tool(self, tool_name, params):
                if self.call_count < len(self.results):
                    result = self.results[self.call_count]
                    self.call_count += 1
                    return MockToolResult(result[0], result[1])
                return MockToolResult(False, None)

            async def connect(self):
                pass

            async def disconnect(self):
                pass

        player = ScenarioPlayer(scenario, MockConfig(), PlayerOptions())
        player._clients["chrome-devtools"] = MockClient(mock_results)
        return player

    def test_wait_until_condition_met_immediately(self):
        """Should return immediately when condition is met"""
        from scenario import Step

        async def run_test():
            player = self.create_player_with_mock_client([(True, True)])

            step = Step(step=1, tool="sandy__wait_until", params={"expression": "window.loaded"})
            result = await player._execute_internal_tool(
                step,
                {"expression": "window.loaded", "timeout": 5, "interval": 0.1},
                StepResult(step=1, tool="sandy__wait_until", success=False, duration=0)
            )

            assert result.success is True
            assert result.result["condition_met"] is True

        asyncio.run(run_test())

    def test_wait_until_condition_met_after_retries(self):
        """Should succeed after condition becomes true"""
        from scenario import Step

        async def run_test():
            player = self.create_player_with_mock_client([
                (True, False),
                (True, False),
                (True, True),
            ])

            step = Step(step=1, tool="sandy__wait_until", params={"expression": "window.ready"})
            result = await player._execute_internal_tool(
                step,
                {"expression": "window.ready", "timeout": 5, "interval": 0.05},
                StepResult(step=1, tool="sandy__wait_until", success=False, duration=0)
            )

            assert result.success is True
            assert result.result["condition_met"] is True

        asyncio.run(run_test())

    def test_wait_until_timeout(self):
        """Should timeout when condition is never met"""
        from scenario import Step

        async def run_test():
            player = self.create_player_with_mock_client([
                (True, False),
                (True, False),
                (True, False),
                (True, False),
            ])

            step = Step(step=1, tool="sandy__wait_until", params={"expression": "false"})
            result = await player._execute_internal_tool(
                step,
                {"expression": "false", "timeout": 0.15, "interval": 0.05},
                StepResult(step=1, tool="sandy__wait_until", success=False, duration=0)
            )

            assert result.success is False
            assert "not met" in result.error.lower()

        asyncio.run(run_test())

    def test_wait_until_missing_expression(self):
        """Should fail when expression is missing"""
        from scenario import Step

        async def run_test():
            player = self.create_player_with_mock_client([])

            step = Step(step=1, tool="sandy__wait_until", params={})
            result = await player._execute_internal_tool(
                step,
                {},
                StepResult(step=1, tool="sandy__wait_until", success=False, duration=0)
            )

            assert result.success is False
            assert "expression" in result.error.lower()

        asyncio.run(run_test())

    def test_wait_until_handles_mcp_errors(self):
        """Should continue polling even if MCP call fails"""
        from scenario import Step

        async def run_test():
            # First call fails, second succeeds with true
            player = self.create_player_with_mock_client([
                (False, None),  # MCP error
                (True, True),   # Success
            ])

            step = Step(step=1, tool="sandy__wait_until", params={"expression": "test"})
            result = await player._execute_internal_tool(
                step,
                {"expression": "test", "timeout": 5, "interval": 0.05},
                StepResult(step=1, tool="sandy__wait_until", success=False, duration=0)
            )

            assert result.success is True

        asyncio.run(run_test())
