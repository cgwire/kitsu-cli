#!/usr/bin/env python3
"""
Introspect Gazu modules and report coverage against kitsu-cli commands.

This script compares the public functions in each Gazu module against the
CLI commands already implemented, helping identify missing coverage.

Usage:
    python scripts/generate_commands.py [--module MODULE]
"""

import importlib
import inspect
import sys
from pathlib import Path


# Mapping of gazu module names to CLI command module names
MODULE_MAP = {
    "asset": "asset",
    "shot": "shot",
    "task": "task",
    "project": "project",
    "person": "person",
    "files": "files",
    "casting": "casting",
    "playlist": "playlist",
    "entity": "entity",
    "scene": "scene",
    "edit": "edit",
    "concept": "concept",
    "sync": "sync",
    "user": "studio",
    "context": None,  # Merged into other modules
    "cache": "cache",
}

# Functions that are intentionally not exposed as CLI commands
SKIP_FUNCTIONS = {
    # Internal/helper functions
    "normalize_model_parameter",
    "normalize_list_of_models_for_links",
    "validate_date_format",
    "sanitize_filename",
    # Async variants
    "aio",
    # Functions better handled by other commands
    "get_host",
    "set_host",
    "set_token",
    "set_tokens",
    "log_in",
    "log_out",
    # Sync functions that need two clients
    "push_assets",
    "push_episodes",
    "push_sequences",
    "push_shots",
    "push_entity_links",
    "push_project_entities",
    "push_tasks",
    "push_tasks_comments",
    "push_task_comments",
    "push_task_comment",
    "convert_id_list",
    "get_model_list_diff",
    "get_link_list_diff",
    "get_id_map_by_name",
    "get_id_map_by_id",
    "is_changed",
    "get_sync_department_id_map",
    "get_sync_asset_type_id_map",
    "get_sync_project_id_map",
    "get_sync_task_type_id_map",
    "get_sync_task_status_id_map",
    "get_sync_person_id_map",
}


def get_public_functions(module_name: str) -> list[tuple[str, inspect.Signature]]:
    """Get all public functions from a gazu module."""
    try:
        mod = importlib.import_module(f"gazu.{module_name}")
    except ImportError:
        return []

    functions = []
    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith("_"):
            continue
        if name in SKIP_FUNCTIONS:
            continue
        if obj.__module__ != f"gazu.{module_name}":
            continue
        sig = inspect.signature(obj)
        functions.append((name, sig))

    return sorted(functions, key=lambda x: x[0])


def get_cli_commands(module_name: str) -> set[str]:
    """Extract command names from a CLI module source file."""
    cli_module = MODULE_MAP.get(module_name)
    if not cli_module:
        return set()

    cmd_file = Path(__file__).parent.parent / "src" / "kitsu_cli" / "commands" / f"{cli_module}.py"
    if not cmd_file.exists():
        return set()

    # Look for gazu function calls in the source
    source = cmd_file.read_text()
    covered = set()
    for line in source.splitlines():
        line = line.strip()
        if f"gazu.{module_name}." in line or f"gazu.{cli_module}." in line:
            # Extract function name
            for part in line.split(f"gazu.{module_name}."):
                if part and "(" in part:
                    fname = part.split("(")[0].strip()
                    covered.add(fname)
            if module_name != cli_module:
                for part in line.split(f"gazu.{cli_module}."):
                    if part and "(" in part:
                        fname = part.split("(")[0].strip()
                        covered.add(fname)
    return covered


def report(module_name: str | None = None):
    """Print a coverage report."""
    modules = [module_name] if module_name else sorted(MODULE_MAP.keys())

    total_funcs = 0
    total_covered = 0

    for mod in modules:
        functions = get_public_functions(mod)
        if not functions:
            continue

        covered = get_cli_commands(mod)
        # Also check other CLI modules that might call this gazu module
        for other_mod in MODULE_MAP.values():
            if other_mod and other_mod != MODULE_MAP.get(mod):
                cmd_file = Path(__file__).parent.parent / "src" / "kitsu_cli" / "commands" / f"{other_mod}.py"
                if cmd_file.exists():
                    source = cmd_file.read_text()
                    for line in source.splitlines():
                        if f"gazu.{mod}." in line:
                            for part in line.split(f"gazu.{mod}."):
                                if part and "(" in part:
                                    fname = part.split("(")[0].strip()
                                    covered.add(fname)

        print(f"\n{'='*60}")
        print(f"Module: gazu.{mod} -> kitsu {MODULE_MAP.get(mod, '(unmapped)')}")
        print(f"{'='*60}")

        mod_total = len(functions)
        mod_covered = 0

        for fname, sig in functions:
            status = "OK" if fname in covered else "MISSING"
            if status == "OK":
                mod_covered += 1
            params = str(sig).replace("client=<gazu.client.KitsuClient object>", "client=default")
            print(f"  [{status:7s}] {fname}{params}")

        print(f"\n  Coverage: {mod_covered}/{mod_total} ({100*mod_covered/mod_total:.0f}%)")
        total_funcs += mod_total
        total_covered += mod_covered

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_covered}/{total_funcs} ({100*total_covered/total_funcs:.0f}%)")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check kitsu-cli coverage of gazu functions")
    parser.add_argument("--module", "-m", help="Check a specific module")
    args = parser.parse_args()
    report(args.module)
