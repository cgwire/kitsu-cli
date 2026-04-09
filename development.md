# Development Guide

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

## Setup

Clone and install in development mode:

```bash
git clone https://github.com/cgwire/kitsu-cli.git
cd kitsu-cli
uv sync
```

This creates a `.venv/` virtual environment and installs all dependencies including dev tools.

If you prefer pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Verify the install:

```bash
.venv/bin/kitsu --help
```

## Project structure

```
kitsu-cli/
├── pyproject.toml                  # Project metadata, dependencies, entry point
├── scripts/
│   └── generate_commands.py        # Coverage report: gazu functions vs CLI commands
├── src/kitsu_cli/
│   ├── __init__.py
│   ├── __main__.py                 # `python -m kitsu_cli` entry point
│   ├── cli.py                      # Root Click group, lazy-loading, global options
│   ├── config.py                   # Config file (~/.config/kitsu-cli/config.toml)
│   ├── client.py                   # Gazu client setup from resolved config
│   ├── output.py                   # JSON/table/CSV/id-only formatters
│   ├── resolver.py                 # UUID-or-name entity resolution
│   └── commands/
│       ├── auth.py                 # login, logout, status
│       ├── project.py              # Project CRUD + task-type/task-status/asset-type
│       ├── asset.py                # Asset CRUD + asset type management
│       ├── shot.py                 # Shot/sequence/episode CRUD, CSV import/export
│       ├── task.py                 # Tasks, comments, previews, time, types, statuses
│       ├── person.py               # People, departments, organisations
│       ├── files.py                # Output/working/preview files, software, output types
│       ├── casting.py              # Asset-to-entity casting
│       ├── playlist.py             # Playlist CRUD
│       ├── entity.py               # Generic entities and entity types
│       ├── scene.py                # Scenes and asset instances
│       ├── edit.py                 # Edit CRUD
│       ├── concept.py              # Concept CRUD
│       ├── studio.py               # User context (todo, notifications, filters, chats)
│       ├── sync.py                 # Event log and data import
│       ├── search.py               # Name-based entity search
│       ├── cache.py                # Client cache control
│       └── events.py               # Real-time event listener
└── tests/
    ├── conftest.py                 # Shared fixtures (runner, invoke)
    ├── test_cli.py                 # Root group and command structure tests
    ├── test_auth.py                # Auth command tests
    ├── test_config.py              # Config read/write/priority tests
    ├── test_output.py              # Output formatter tests
    ├── test_project.py             # Project command tests
    └── test_asset.py               # Asset command tests
```

## Running tests

```bash
# All tests
uv run pytest

# Verbose output
uv run pytest -v

# Single test file
uv run pytest tests/test_auth.py

# Single test function
uv run pytest tests/test_auth.py::test_login_with_token

# With coverage
uv run pytest --cov=kitsu_cli
```

Tests use Click's `CliRunner` and mock Gazu calls with `unittest.mock.patch`. No running Kitsu server is needed.

## Adding a new command

### 1. Identify the Gazu function

Find the function in the [Gazu source](https://github.com/cgwire/gazu) or run the coverage report:

```bash
uv run python scripts/generate_commands.py --module asset
```

This shows which Gazu functions are already covered and which are missing.

### 2. Write the command

Open the relevant `src/kitsu_cli/commands/<module>.py` and add a Click command. Follow the existing patterns:

```python
@group.command()
@click.argument("entity_id")
@click.option("--project", required=True, help="Project UUID or name.")
@click.pass_context
def my_command(ctx, entity_id, project):
    """Short description shown in --help."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.module.some_function(proj, entity_id)
    output(result, ctx)
```

Key conventions:

- Call `require_auth(ctx)` at the top of every command that hits the API.
- Use `resolve_*()` functions from `resolver.py` to accept both UUIDs and names.
- Pipe results through `output(result, ctx)` so all formats (JSON/table/CSV/id-only) work.
- Use `click.argument()` for required positional parameters (entity IDs).
- Use `click.option()` for filters and optional parameters.
- For delete commands, print a confirmation unless `--quiet` is set.

### 3. Register the command group (if new)

If you created a new module file, add it to `COMMAND_MODULES` in `cli.py`:

```python
COMMAND_MODULES = {
    ...
    "my_module": "kitsu_cli.commands.my_module",
}
```

### 4. Write tests

Add tests in `tests/test_<module>.py`. Mock Gazu and `require_auth`:

```python
from unittest.mock import patch

def test_my_command(invoke):
    with patch("kitsu_cli.commands.module.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.module.require_auth"), \
         patch("kitsu_cli.commands.module.resolve_project", return_value={"id": "p1"}):
        mock_gazu.module.some_function.return_value = {"id": "x1", "name": "result"}
        result = invoke("--format", "json", "module", "my-command", "entity-id", "--project", "p1")
        assert result.exit_code == 0
        assert "result" in result.output
```

### 5. Verify coverage

```bash
uv run python scripts/generate_commands.py --module asset
```

## Architecture notes

### Lazy loading

Command groups are loaded on demand via `LazyGroup` in `cli.py`. This keeps `kitsu --help` fast — only the requested command module is imported. Each command file exposes a `group` variable (a `click.Group`).

### Config priority

Authentication and host settings are resolved in this order (first wins):

1. CLI flags (`--host`, `--token`)
2. Environment variables (`KITSU_HOST`, `KITSU_TOKEN`)
3. Config file (`~/.config/kitsu-cli/config.toml`)

### Output pipeline

All commands call `output(data, ctx)` from `output.py`. The format is determined by `--format` or auto-detected (JSON when piped, table when interactive). The `output()` function handles all four formats:

- `json` — `json.dumps`, pretty-printed in TTY
- `table` — Rich table, falls back to JSON if Rich is unavailable
- `csv` — Standard CSV with header row
- `id-only` — One ID per line

### Entity resolution

`resolver.py` provides `resolve_*()` helpers that accept a string and return a Gazu dict. They check if the string is a UUID (regex match) and call the appropriate `get_*()` or `get_*_by_name()` Gazu function. This lets users pass either format on the command line.

## Coverage report

To see which Gazu functions have CLI commands and which are still missing:

```bash
uv run python scripts/generate_commands.py
```

To check a single module:

```bash
uv run python scripts/generate_commands.py --module task
```

Output shows `[OK]` or `[MISSING]` for each function, with per-module and total coverage percentages.
