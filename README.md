# kitsu-cli

Command-line interface for the [Kitsu](https://www.cg-wire.com/kitsu) production tracker, built on top of the [Gazu](https://github.com/cgwire/gazu) Python SDK.

Kitsu-cli exposes Gazu's 260+ functions as structured CLI commands. Output defaults to JSON for easy piping into `jq` or consumption by scripts and AI agents, with optional table and CSV formats for human use.

## Install

Requires Python 3.10+.

```bash
pip install git+https://github.com/cgwire/kitsu-cli.git
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install git+https://github.com/cgwire/kitsu-cli.git
```

For development install, see [development.md](development.md).

## Quick start

### Authenticate

```bash
# Interactive login (prompts for email and password)
kitsu auth login --host https://kitsu.mystudio.com

# Login with email and password directly
kitsu auth login --host https://kitsu.mystudio.com --email admin@example.com --password secret

# Login with an API token
kitsu auth login --host https://kitsu.mystudio.com --token YOUR_TOKEN

# Check authentication status
kitsu auth status

# Logout (clears stored credentials)
kitsu auth logout
```

Credentials are stored in `~/.config/kitsu-cli/config.toml` (permissions `0600`).

### Environment variables

Instead of passing `--host` and `--token` every time, set environment variables:

```bash
export KITSU_HOST=https://kitsu.mystudio.com
export KITSU_TOKEN=your-access-token
```

Priority order: CLI flag > environment variable > config file.

### Browse projects

```bash
# List all projects
kitsu project list

# List open projects only
kitsu project list-open

# Get a specific project by name or UUID
kitsu project get "My Project"
kitsu project get a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Work with assets

```bash
# List assets in a project
kitsu asset list --project "My Project"

# Filter by asset type
kitsu asset list --project "My Project" --asset-type Character

# Create an asset
kitsu asset create --project "My Project" --type Character "Hero"

# Get an asset by UUID
kitsu asset get a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Work with shots

```bash
# List shots for a project
kitsu shot list --project "My Project"

# List shots in a specific sequence
kitsu shot list --sequence SEQUENCE_UUID

# Create a sequence, then a shot
kitsu shot sequence create --project "My Project" SQ010
kitsu shot create --project "My Project" --sequence SEQUENCE_UUID SH0010

# Manage episodes
kitsu shot episode list --project "My Project"
kitsu shot episode create --project "My Project" EP01
```

### Manage tasks

```bash
# List tasks for a shot
kitsu task list --shot SHOT_UUID

# List tasks assigned to someone
kitsu task list --person user@example.com

# Create a task
kitsu task create ENTITY_UUID --task-type Animation

# Start, assign, and review
kitsu task start TASK_UUID
kitsu task assign TASK_UUID --person artist@example.com
kitsu task review TASK_UUID --person lead@example.com --comment "Approved"

# Add a comment
kitsu task comment add TASK_UUID --status "Work In Progress" -m "Starting animation pass"

# Track time
kitsu task time add TASK_UUID --person artist@example.com --date 2025-03-14 --duration 120
```

### Publish previews

```bash
# Publish a preview file with a comment in one step
kitsu task preview publish TASK_UUID --status "Waiting For Approval" \
  --file /path/to/render.mp4 -m "First animation pass" --set-thumbnail
```

## Output formats

Default is `json` when piping, `table` when interactive.

```bash
# JSON (default for non-TTY)
kitsu project list --format json

# Pretty table (default for TTY)
kitsu project list --format table

# CSV
kitsu project list --format csv

# IDs only (useful for scripting)
kitsu project list --format id-only
```

Pipe JSON into `jq` for ad-hoc queries:

```bash
kitsu asset list --project "My Project" --format json | jq '.[].name'
```

## Command groups

| Group | Description |
|-------|-------------|
| `auth` | Login, logout, status |
| `project` | Projects and project settings |
| `asset` | Assets and asset types |
| `shot` | Shots, sequences, and episodes |
| `task` | Tasks, comments, previews, time tracking, task types/statuses |
| `person` | People, departments, organisations |
| `files` | Output files, working files, preview files, software |
| `casting` | Asset-to-shot/episode casting |
| `playlist` | Playlist management |
| `entity` | Generic entities and entity types |
| `scene` | Scenes and asset instances |
| `edit` | Edit entities |
| `concept` | Concept art |
| `studio` | Current user: tasks to do, notifications, filters, chats |
| `sync` | Event log and data import |
| `search` | Search entities by name |
| `cache` | Client-side cache control |
| `events` | Real-time event listener |

Use `kitsu <group> --help` to see available commands, and `kitsu <group> <command> --help` for options.

## Global options

```
--host TEXT                      Kitsu server URL (or KITSU_HOST env var)
--token TEXT                     API access token (or KITSU_TOKEN env var)
--format [json|table|csv|id-only] Output format
-v, --verbose                    Verbose output
-q, --quiet                      Suppress non-essential output
--version                        Show version
-h, --help                       Show help
```

## Entity resolution

Most commands accept both UUIDs and human-readable names where possible:

```bash
# These are equivalent
kitsu project get a1b2c3d4-e5f6-7890-abcd-ef1234567890
kitsu project get "My Project"

# Persons can be resolved by email or full name
kitsu task assign TASK_UUID --person artist@example.com
kitsu task assign TASK_UUID --person "Jane Doe"

# Task statuses accept name or short name
kitsu task comment add TASK_UUID --status wip -m "Working on it"
kitsu task comment add TASK_UUID --status "Work In Progress" -m "Working on it"
```

## About

kitsu-cli is developed by [CGWire](https://www.cg-wire.com), the creators of Kitsu. It is built on top of [Gazu](https://github.com/cgwire/gazu), the official Python client for the Kitsu API.

## License

See [LICENSE](LICENSE) for details.
