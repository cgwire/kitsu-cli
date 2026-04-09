# kitsu-cli Agent Specifications

This document describes how code agents (LLMs, automation scripts, CI bots) should interact with kitsu-cli.

## Principles

1. **JSON by default.** When stdout is not a TTY (pipes, subprocesses), output is JSON. Agents should always parse JSON output. Pass `--format json` explicitly if unsure.
2. **IDs for writes, names for reads.** Use human-readable names for lookups (`kitsu project get "My Project"`), but always pass UUIDs for mutating operations (create, update, delete). After creating an entity, extract its `id` from the JSON response and use that UUID in subsequent commands.
3. **One command, one action.** Each command maps to a single Gazu/Kitsu API call. Agents should compose multi-step workflows by chaining commands.
4. **Exit codes.** `0` = success, non-zero = error. Error messages go to stderr.

## Authentication for agents

Set environment variables rather than passing credentials on every call:

```bash
export KITSU_HOST=https://kitsu.mystudio.com
export KITSU_TOKEN=your-access-token
```

Or authenticate once and let kitsu-cli store the token:

```bash
kitsu auth login --host https://kitsu.mystudio.com --token YOUR_TOKEN
```

To verify credentials programmatically:

```bash
kitsu auth status --format json
# Exit code 0 = authenticated, non-zero = not authenticated
```

## Output parsing

### JSON mode

All list commands return a JSON array. All get/create/update commands return a JSON object.

```bash
# Get all project IDs
kitsu project list --format json | jq -r '.[].id'

# Get a specific field
kitsu project get "My Project" --format json | jq -r '.id'
```

### id-only mode

For simple scripting where you only need IDs:

```bash
PROJECT_ID=$(kitsu project get "My Project" --format id-only)
kitsu asset list --project "$PROJECT_ID" --format id-only
```

### CSV mode

For tabular data processing:

```bash
kitsu asset list --project "My Project" --format csv
```

First line is always the header row. Fields containing commas or newlines are quoted.

## Common workflows

### Create a full shot pipeline

```bash
# 1. Get project ID
PROJECT=$(kitsu project get "My Project" --format id-only)

# 2. Create episode (for TV shows)
EPISODE=$(kitsu shot episode create --project "$PROJECT" EP01 --format id-only)

# 3. Create sequence
SEQUENCE=$(kitsu shot sequence create --project "$PROJECT" --episode "$EPISODE" SQ010 --format id-only)

# 4. Create shot
SHOT=$(kitsu shot create --project "$PROJECT" --sequence "$SEQUENCE" SH0010 --nb-frames 120 --format id-only)

# 5. Create tasks
kitsu task create "$SHOT" --task-type Layout
kitsu task create "$SHOT" --task-type Animation
kitsu task create "$SHOT" --task-type Lighting
```

### Publish a preview with status change

```bash
TASK_UUID="..."
kitsu task preview publish "$TASK_UUID" \
  --status "Waiting For Approval" \
  --file /path/to/render.mp4 \
  -m "Animation pass 2" \
  --format json
```

### Batch-assign tasks

```bash
# Assign all animation tasks for a project to a person
kitsu task list --project "My Project" --task-type Animation --format id-only | \
  while read TASK_ID; do
    kitsu task assign "$TASK_ID" --person artist@example.com
  done
```

### Track time spent

```bash
kitsu task time add "$TASK_UUID" \
  --person artist@example.com \
  --date 2025-03-14 \
  --duration 90
```

### Import shots from CSV

```bash
kitsu shot import-csv --project "My Project" shots.csv
```

### Listen to events

```bash
# Stream events as newline-delimited JSON
kitsu events listen --format json
```

Each event is printed as a single JSON object per line, suitable for processing with `jq` or streaming parsers.

## Multi-agent development pipeline

This section describes how to orchestrate a sequential agent pipeline where each
phase is reviewed (first by an AI review agent, then by a human) before the next
phase starts. Token consumption is logged at each deliverable stage.

### Statuses used

| Status | Short name | Meaning |
|--------|-----------|---------|
| Todo | `todo` | Not started |
| Work In Progress | `wip` | Agent is working |
| Waiting For Approval | `wfa` | Deliverable ready — triggers review |
| Retake | `retake` | Reviewer rejected, agent must redo |
| Approved | `approved` | Human validated, next phase can start |
| Done | `done` | Fully complete |

### Pipeline phases

```
Specs → Unit Tests → Code → QA
```

Each phase follows the same cycle:

```
Worker agent ──► wfa ──► Review agent ──► wfa ──► Human ──► approved ──► next phase
                                │                   │
                                └── retake ◄────────┘
```

### 1. Setup: project and tasks

```bash
PROJECT=$(kitsu -q project create "API Refactor" --format id-only)

# Create the feature as an asset
FEATURE=$(kitsu -q asset create --project "$PROJECT" --type Feature "auth-endpoints" \
  --format id-only)

# Create one task per phase
SPECS_TASK=$(kitsu -q task create "$FEATURE" --task-type Specs --format id-only)
TESTS_TASK=$(kitsu -q task create "$FEATURE" --task-type "Unit Tests" --format id-only)
CODE_TASK=$(kitsu -q task create "$FEATURE"  --task-type Code --format id-only)
QA_TASK=$(kitsu -q task create "$FEATURE"    --task-type QA --format id-only)
```

### 2. Worker agent: Specs

The specs agent picks up its task, works, then submits its deliverable with
token consumption logged in the comment.

```bash
# Start working
kitsu -q task start "$SPECS_TASK"
kitsu -q task comment add "$SPECS_TASK" --status wip \
  -m "Analysing codebase for auth endpoint inventory"

# ... agent works, tracks token usage ...
TOKENS_IN=12450
TOKENS_OUT=8230

# Submit deliverable with token cost
kitsu -q task preview publish "$SPECS_TASK" \
  --status wfa \
  --file specs/auth-endpoints.md \
  -m "Specs complete: 12 endpoints, 4 models.
Tokens: ${TOKENS_IN} in / ${TOKENS_OUT} out (cost: \$0.42)"
```

### 3. Review agent: automated review

A review agent polls for tasks in `wfa` status and reviews them.

```bash
# Poll for tasks waiting for approval
PENDING=$(kitsu -q task list --project "$PROJECT" --task-type Specs \
  --task-status wfa --format json)

TASK_ID=$(echo "$PENDING" | jq -r '.[0].id')

# Review agent reads the deliverable, analyses it
kitsu -q task start "$TASK_ID"  # status → wip (review in progress)

# ... review agent analyses the specs ...
REVIEW_TOKENS_IN=8200
REVIEW_TOKENS_OUT=3100

# Decision: approve or retake
# Case 1: Review passes → submit for human approval
kitsu -q task comment add "$TASK_ID" --status wfa \
  -m "Auto-review PASSED. All 12 endpoints documented, schemas valid.
No issues found. Ready for human review.
Review tokens: ${REVIEW_TOKENS_IN} in / ${REVIEW_TOKENS_OUT} out (cost: \$0.15)"

# Case 2: Review fails → request retake
kitsu -q task comment add "$TASK_ID" --status retake \
  -m "Auto-review FAILED: 3 endpoints missing error schemas.
See checklist below.
Review tokens: ${REVIEW_TOKENS_IN} in / ${REVIEW_TOKENS_OUT} out (cost: \$0.15)"
```

### 4. Human review

The human sees the task in `wfa` status in Kitsu's web UI. The comment thread
shows both the worker agent's deliverable and the review agent's analysis.
They can:

```bash
# Approve → next phase can start
kitsu task comment add "$SPECS_TASK" --status approved \
  -m "LGTM, proceed to tests"

# Or request retake with feedback
kitsu task comment add "$SPECS_TASK" --status retake \
  -m "Missing rate-limiting specs for /auth/token endpoint"
```

### 5. Orchestrator: gate between phases

The orchestrator waits for human approval before launching the next agent.

```bash
wait_for_approval() {
  TASK_ID=$1
  while true; do
    STATUS=$(kitsu -q task get "$TASK_ID" --format json | jq -r '.task_status_short_name')
    case "$STATUS" in
      approved|done) return 0 ;;
      retake)        return 1 ;;  # signal worker to retry
    esac
    sleep 30
  done
}

# Run the full pipeline
run_agent specs "$SPECS_TASK"
wait_for_approval "$SPECS_TASK" || { run_agent specs "$SPECS_TASK"; }

run_agent tests "$TESTS_TASK"
wait_for_approval "$TESTS_TASK" || { run_agent tests "$TESTS_TASK"; }

run_agent code "$CODE_TASK"
wait_for_approval "$CODE_TASK" || { run_agent code "$CODE_TASK"; }

run_agent qa "$QA_TASK"
wait_for_approval "$QA_TASK"
```

### 6. Token tracking convention

Every comment that sets status to `wfa` (deliverable submitted) must include
a token line so costs are traceable per deliverable:

```
Tokens: <input_tokens> in / <output_tokens> out (cost: $<amount>)
```

This produces a full audit trail visible in the Kitsu comment thread:

```
┌─────────────────────────────────────────────────────────┐
│ Task: Specs for auth-endpoints                          │
├──────────┬──────────────────────────────────────────────┤
│ specs-agent  │ wip  │ Analysing codebase...             │
│ specs-agent  │ wfa  │ Specs complete: 12 endpoints.     │
│              │      │ Tokens: 12450 in / 8230 out ($0.42)│
│ review-agent │ wfa  │ Auto-review PASSED.               │
│              │      │ Tokens: 8200 in / 3100 out ($0.15)│
│ human        │ approved │ LGTM, proceed to tests        │
├──────────┬──────────────────────────────────────────────┤
│ tests-agent  │ wip  │ Writing test cases...             │
│ tests-agent  │ wfa  │ 34 tests, all green.              │
│              │      │ Tokens: 18900 in / 22100 out ($0.89)│
│ review-agent │ retake │ 3 tests missing edge cases.     │
│              │      │ Tokens: 9400 in / 4200 out ($0.19)│
│ tests-agent  │ wfa  │ Fixed. 37 tests, all green.       │
│              │      │ Tokens: 6200 in / 8400 out ($0.31)│
│ review-agent │ wfa  │ Auto-review PASSED.               │
│              │      │ Tokens: 9800 in / 3600 out ($0.18)│
│ human        │ approved │ Good coverage, go ahead       │
└──────────┴──────────────────────────────────────────────┘

Total tokens: 65150 in / 49630 out
Total cost:   $2.14
```

### Summary: agent checklist

Each worker/review agent should:

1. `kitsu task start $TASK` — set status to `wip`
2. `kitsu task comment add $TASK --status wip -m "..."` — log progress
3. Work on the deliverable, counting tokens consumed
4. `kitsu task preview publish $TASK --status wfa --file <deliverable> -m "...Tokens: X in / Y out (cost: $Z)"` — submit with cost
5. If status comes back as `retake`, read the review comments, fix, and re-submit to `wfa`

## Command reference

The CLI follows this structure:

```
kitsu <group> [sub-group] <command> [ARGUMENTS] [--options]
```

### Groups and their sub-groups

| Group | Sub-groups | Notes |
|-------|-----------|-------|
| `auth` | | login, logout, status |
| `project` | `task-type`, `task-status`, `asset-type` | Project CRUD + project-scoped types |
| `asset` | `type` | Asset CRUD + asset type management |
| `shot` | `sequence`, `episode` | Shot/sequence/episode CRUD |
| `task` | `comment`, `preview`, `time`, `type`, `status` | Full task lifecycle |
| `person` | `department`, `organisation` | People and departments |
| `files` | `output`, `working`, `preview`, `output-type`, `software` | File management |
| `casting` | | Asset-to-entity linking |
| `playlist` | | Playlist CRUD and entity management |
| `entity` | `type` | Generic entity access |
| `scene` | | Scene and asset instance management |
| `edit` | | Edit CRUD |
| `concept` | | Concept CRUD |
| `studio` | `filter`, `chat` | Current-user context (todo, notifications) |
| `sync` | | Event log and data import |
| `search` | | Name-based entity search |
| `cache` | | Client cache enable/disable/clear |
| `events` | | Real-time event streaming |

### Standard CRUD pattern

Most entity groups follow this pattern:

```bash
kitsu <group> list [--filters]      # List entities (returns JSON array)
kitsu <group> get <ID_OR_NAME>      # Get single entity (returns JSON object)
kitsu <group> create [--options] NAME # Create entity (returns JSON object with id)
kitsu <group> update <UUID> [--options] # Update entity (returns JSON object)
kitsu <group> delete <UUID> [--force]   # Delete entity (prints confirmation)
```

### Entity resolution rules

| Entity | Accepted formats |
|--------|-----------------|
| Project | UUID, name |
| Asset | UUID (name requires `--project`) |
| Shot | UUID |
| Sequence | UUID |
| Episode | UUID |
| Person | UUID, email, full name |
| Task type | UUID, name |
| Task status | UUID, name, short name |
| Asset type | UUID, name |

## Error handling

Errors are printed to stderr and the process exits with a non-zero code. Agents should check exit codes:

```bash
if kitsu project get "Nonexistent" --format json 2>/dev/null; then
  echo "Project found"
else
  echo "Project not found"
fi
```

Common error patterns:
- `Error: No Kitsu host configured` — set `KITSU_HOST` or run `kitsu auth login`
- `Error: Not authenticated` — token expired or invalid, re-authenticate
- `Error: Project not found: X` — entity does not exist
- `ClickException` — invalid arguments, missing required options

## Quiet mode

Use `--quiet` / `-q` to suppress informational messages (e.g., "Deleted project X"). Only structured output (JSON/CSV) and errors are printed. This is recommended for agents.

```bash
kitsu -q project delete "$PROJECT_UUID"
```
