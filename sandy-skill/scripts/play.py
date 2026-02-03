#!/usr/bin/env python3
"""
Sandy Play CLI

Execute MCP scenarios without LLM (deterministic replay).

Usage:
    python play.py scenario.json [options]

Examples:
    # Basic execution (looks in assets/examples/ by default)
    python play.py supabase-query.json

    # Full path
    python play.py /path/to/scenario.json

    # With variables
    python play.py scenario.json --var TITLE="Bug Fix" --var CHANNEL="#dev"

    # With environment file
    python play.py scenario.json --env .sandy.env

    # Resume from specific step
    python play.py scenario.json --resume-from 3

    # Partial execution (steps 2-4 only)
    python play.py scenario.json --start 2 --end 4

    # Dry run (validate without execution)
    python play.py scenario.json --dry-run

    # Debug mode
    python play.py scenario.json --debug

    # Include full MCP results (for debugging)
    python play.py scenario.json --include-results true

    # Include results only on failure (recommended for debugging)
    python play.py scenario.json --include-results on_failure
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# Default scenarios directory (relative to script)
DEFAULT_SCENARIOS_DIR = SCRIPT_DIR.parent / "assets" / "examples"

from scenario import load_scenario, get_required_variables, ScenarioValidationError
from config import detect_config, load_config_from_path, ConfigNotFoundError
from player import PlayerOptions, play_scenario
from reporter import create_reporter


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Sandy Play - Execute MCP scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "scenario",
        type=str,
        help="Path to scenario JSON file",
    )

    parser.add_argument(
        "--var",
        action="append",
        dest="variables",
        metavar="KEY=VALUE",
        help="Set variable (can be used multiple times)",
    )

    parser.add_argument(
        "--env",
        type=str,
        metavar="FILE",
        help="Load variables from env file",
    )

    parser.add_argument(
        "--config",
        type=str,
        metavar="FILE",
        help="Path to MCP config file",
    )

    parser.add_argument(
        "--start",
        type=int,
        metavar="N",
        help="Start execution from step N (inclusive)",
    )

    parser.add_argument(
        "--end",
        type=int,
        metavar="N",
        help="End execution at step N (inclusive)",
    )

    parser.add_argument(
        "--resume-from",
        type=int,
        metavar="N",
        dest="start",  # Alias for --start
        help="Alias for --start (backward compatibility)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate scenario without executing",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        metavar="FILE",
        help="Write result to file",
    )

    parser.add_argument(
        "--include-results",
        type=str,
        nargs="?",
        const="true",
        default="false",
        metavar="MODE",
        help="Include MCP raw results: true, false (default), or on_failure",
    )

    return parser.parse_args()


def parse_variables(var_args: list[str] | None) -> dict[str, str]:
    """Parse --var KEY=VALUE arguments"""
    variables = {}
    if var_args:
        for var in var_args:
            if "=" in var:
                key, value = var.split("=", 1)
                variables[key.strip()] = value.strip()
    return variables


def resolve_scenario_path(scenario_arg: str) -> Path:
    """
    Resolve scenario path with fallback to default directory.

    Search order:
    1. Exact path (absolute or relative to cwd)
    2. Default scenarios directory (assets/examples/)

    Args:
        scenario_arg: Scenario path from CLI argument

    Returns:
        Resolved Path object

    Raises:
        FileNotFoundError: If scenario not found in any location
    """
    # Try exact path first
    path = Path(scenario_arg)
    if path.exists():
        return path.resolve()

    # Try default scenarios directory
    default_path = DEFAULT_SCENARIOS_DIR / scenario_arg
    if default_path.exists():
        return default_path.resolve()

    # Also try with .json extension
    if not scenario_arg.endswith(".json"):
        default_path_json = DEFAULT_SCENARIOS_DIR / f"{scenario_arg}.json"
        if default_path_json.exists():
            return default_path_json.resolve()

    # Not found anywhere
    raise FileNotFoundError(
        f"Scenario not found: {scenario_arg}\n"
        f"Searched:\n"
        f"  - {path.resolve()}\n"
        f"  - {DEFAULT_SCENARIOS_DIR / scenario_arg}"
    )


def load_env_file(path: str) -> dict[str, str]:
    """Load variables from .env file using python-dotenv"""
    from dotenv import dotenv_values

    env_path = Path(path)
    if not env_path.exists():
        print(f"Warning: Env file not found: {path}", file=sys.stderr)
        return {}

    # dotenv_values returns dict with None for unset values, filter them out
    values = dotenv_values(env_path)
    return {k: v for k, v in values.items() if v is not None}


async def main() -> int:
    """Main entry point"""
    args = parse_args()

    # Resolve scenario path (with default directory fallback)
    try:
        scenario_path = resolve_scenario_path(args.scenario)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Load scenario
    try:
        scenario = load_scenario(scenario_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ScenarioValidationError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        return 1

    # Load config
    try:
        if args.config:
            config = load_config_from_path(args.config)
        else:
            config = detect_config()
    except (ConfigNotFoundError, FileNotFoundError) as e:
        print(f"Config Error: {e}", file=sys.stderr)
        return 1

    # Collect variables
    variables: dict[str, str] = {}

    # From env file
    if args.env:
        variables.update(load_env_file(args.env))

    # From command line
    variables.update(parse_variables(args.variables))

    # Check required variables
    required = get_required_variables(scenario)
    missing = [v for v in required if v not in variables and v not in scenario.variables]
    if missing:
        print(f"Error: Missing required variables: {', '.join(missing)}", file=sys.stderr)
        print("Use --var KEY=VALUE to provide them", file=sys.stderr)
        return 1

    # Setup reporter
    output_file = None
    try:
        if args.output:
            output_file = open(args.output, "w", encoding="utf-8")

        reporter = create_reporter(
            verbose=args.verbose or args.debug,
            json_output=args.json,
            output=output_file,
        )

        # Parse include_results option
        include_results: bool | str = False
        if args.include_results == "true":
            include_results = True
        elif args.include_results == "on_failure":
            include_results = "on_failure"
        # else: default False

        # Setup player options
        options = PlayerOptions(
            variables=variables,
            start=args.start,
            end=args.end,
            dry_run=args.dry_run,
            debug=args.debug,
            include_results=include_results,
            on_step_start=None if args.json else reporter.step_start,
            on_step_complete=None if args.json else reporter.step_complete,
        )

        # Print header
        if not args.json:
            print(f"\nSandy Play: {scenario.metadata.name}")
            print(f"Config: {config.source}")
            if args.dry_run:
                print("[DRY RUN MODE]")
            if args.start or args.end:
                range_str = f"steps {args.start or 1}" + (f"-{args.end}" if args.end else "+")
                print(f"[Partial execution: {range_str}]")
            print("-" * 60)
            print()

        # Execute scenario
        try:
            result = await play_scenario(scenario, config, options)
        except Exception as e:
            print(f"Execution Error: {e}", file=sys.stderr)
            if args.debug:
                import traceback
                traceback.print_exc()
            return 1

        # Print result
        if args.json:
            reporter.print_json(result)
        else:
            reporter.print_result(result)

        return 0 if result.success else 1

    finally:
        if output_file:
            output_file.close()


def run() -> None:
    """Entry point for script execution"""
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    run()
