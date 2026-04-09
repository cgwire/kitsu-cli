# Plan: Write MCP Server Specs for All 20 Modules

## Context

We're building an MCP (Model Context Protocol) server for Kitsu/Zou that mirrors the features of kitsu-cli. A "MCP Server" project exists in the local Kitsu instance (localhost:8080) with:

- **20 feature assets** (one per CLI module)
- **4 task types** per asset: Specs, Unit Tests, Code, Functional Tests (= 80 tasks total)
- **4 AI agent bots** assigned by feature (not round-robin)
- **Current phase:** Write Specs for all 20 modules

## Agent Assignments (by feature)

| Agent | Bot ID | Features (5 each) |
|-------|--------|-------------------|
| Agent 1 | `6b3bd192` | asset, auth, chat, events, scene |
| Agent 2 | `2ab9068e` | files, news, person, studio, sync |
| Agent 3 | `32d52212` | cache, concept, entity, playlist, project |
| Agent 4 | `59aa46d8` | casting, edit, search, shot, task |

## All 20 Specs Tasks

| Module | Task ID | Assigned To | Source File |
|--------|---------|-------------|-------------|
| asset | `3713ece3-0ada-4627-bd7f-2fb119b8c04d` | Agent 1 | `commands/asset.py` |
| auth | `8156170f-5cd9-4646-9825-2a092763f46d` | Agent 1 | `commands/auth.py` |
| chat | `f01fe29e-2b92-4f4a-bee2-060c65ca0062` | Agent 1 | `commands/chat.py` |
| events | `14d5d937-9295-41f4-8168-e18df4d5a5b3` | Agent 1 | `commands/events.py` |
| scene | `b43c478e-9730-4bf9-b98c-ccfde0830830` | Agent 1 | `commands/scene.py` |
| files | `d58104e8-ec62-4cc3-8ef5-500487bc9a12` | Agent 2 | `commands/files.py` |
| news | `d92c95a1-de0d-49f6-99a6-9071ffb1beeb` | Agent 2 | `commands/news.py` |
| person | `98bf7944-d069-4500-953e-31c5a21f7eba` | Agent 2 | `commands/person.py` |
| studio | `ba83d5af-d036-49ac-94b2-e33dcb95f72f` | Agent 2 | `commands/studio.py` |
| sync | `6c6edc79-96e2-494d-b413-15092971834b` | Agent 2 | `commands/sync.py` |
| cache | `a22bf156-175a-465b-81d7-2d9409de92dc` | Agent 3 | `commands/cache.py` |
| concept | `5d5b0d98-64a6-43f3-ab0e-f225204911a3` | Agent 3 | `commands/concept.py` |
| entity | `062969a7-d314-4094-9964-4e1d72a4b469` | Agent 3 | `commands/entity.py` |
| playlist | `b4bb32dc-2791-40cc-baef-617d081a6eea` | Agent 3 | `commands/playlist.py` |
| project | `9f5ee938-eae4-4b52-9db1-2de71f82662d` | Agent 3 | `commands/project.py` |
| casting | `fc90474d-ac62-4062-8371-6a742c6ff5c8` | Agent 4 | `commands/casting.py` |
| edit | `da4f9aed-5e05-4256-a5c8-f180cb25d7ce` | Agent 4 | `commands/edit.py` |
| search | `93bcd5bc-faee-4891-bb0c-7f46c8508dc2` | Agent 4 | `commands/search.py` |
| shot | `831f44b0-4ebd-46ce-a8f4-870fa835c342` | Agent 4 | `commands/shot.py` |
| task | `965cfb89-6999-4130-831c-fb537c442214` | Agent 4 | `commands/task.py` |

## What Each Spec Should Contain

An MCP tool specification in markdown for each CLI command in the module:

- **Tool name** — namespaced: `kitsu_<module>_<action>` (e.g., `kitsu_search_query`, `kitsu_shot_create`)
- **Description** — what the tool does
- **Input parameters** — name, type, required/optional, description
- **Return value** — what the tool returns
- Group related tools under headings matching CLI sub-groups

## Deliverables

Each module gets a spec file at `specs/<module>.md` (local working copy) that is **published to Kitsu storage** as a preview file via `kitsu task preview publish`. On retakes, the revised `.md` and a `.diff` file are both uploaded as new revisions.

## Workflow Per Task

Each agent, for each of its 5 assigned modules:

1. **Set task to WIP** via CLI:
   ```bash
   .venv/bin/kitsu task comment add <task-id> "Starting specs for <module> module" --status wip
   ```
2. **Read the CLI source** — `src/kitsu_cli/commands/<module>.py`
3. **Write MCP spec** — save to `specs/<module>.md`
4. **Publish the spec to Kitsu** — uploads the file to Kitsu storage as a preview revision with WFA status:
   ```bash
   .venv/bin/kitsu task preview publish <task-id> --status wfa --file specs/<module>.md -m "Specs written: specs/<module>.md\n\nTokens: <in> in / <out> out"
   ```
   This creates a comment + preview file in one step. Token counts come from the agent's API usage stats.

## Retake Loop

After posting specs with WFA status, each agent polls for retakes:

1. **Poll** the task status every 30 seconds:
   ```bash
   .venv/bin/kitsu --format json task get <task-id>
   ```
   Check if `task_status_id` == `9cc5019e-7a7a-4480-a792-ab5e97be55f6` (retake).

2. **On retake**, read the latest comment to get the reviewer's feedback:
   ```bash
   .venv/bin/kitsu --format json task comment last <task-id>
   ```

3. **Revise the spec** — incorporate the feedback, save updated `specs/<module>.md`.

4. **Generate a diff** of the changes:
   ```bash
   diff specs/<module>.md.prev specs/<module>.md > specs/<module>.diff
   ```
   (Agent keeps a copy of the previous version before editing.)

5. **Publish both files to Kitsu** — the revised spec as a new preview revision:
   ```bash
   .venv/bin/kitsu task preview publish <task-id> --status wfa --file specs/<module>.md -m "Specs revised (see diff)\n\nTokens: <in> in / <out> out"
   .venv/bin/kitsu task preview upload <task-id> <comment-id> --file specs/<module>.diff
   ```

6. **Repeat** until the task reaches `approved` or `done` status, or a max of 3 retakes.

## Unit Tests Phase

After the Specs phase (including retakes) settles, each agent monitors its Unit Tests tasks.

### Unit Tests Task IDs

| Module | Task ID | Assigned To |
|--------|---------|-------------|
| asset | `ab383eea-e4c7-4a88-b794-5e1b8a54e03c` | Agent 1 |
| auth | `6f42164c-f85b-4250-8071-698ddc307d15` | Agent 1 |
| chat | `406ce3cb-95ad-4907-866c-a5016228dcd2` | Agent 1 |
| events | `3b539f8f-a982-491c-b29c-fd5015fcd973` | Agent 1 |
| scene | `b23ec88e-ccc5-4ac7-8169-756b8ea282dd` | Agent 1 |
| files | `1e147142-2b0d-47a0-be6f-b6e7c565ddf0` | Agent 2 |
| news | `a4cb88f2-8043-4627-940d-a68d9436fe9e` | Agent 2 |
| person | `c644859c-dde7-42cd-8c24-e456b4067e47` | Agent 2 |
| studio | `4ae06ac3-1e53-4baf-b7ed-d420b9452d96` | Agent 2 |
| sync | `4016fee5-05fc-4af0-9a0e-25976e9950a8` | Agent 2 |
| cache | `a250803d-c59f-406b-b391-142b1df11013` | Agent 3 |
| concept | `2cf1e0f0-2180-4b51-9dc3-f16fc914c70e` | Agent 3 |
| entity | `b69e00bc-2b7c-4559-a9c2-0f07f753c698` | Agent 3 |
| playlist | `8a1e6d93-c1a7-466e-b9b1-f14da4f7cec3` | Agent 3 |
| project | `3ec99c93-9a44-4b2a-bd55-ec18a8150e9f` | Agent 3 |
| casting | `17fa253c-7e25-4203-9ab1-14cbee814735` | Agent 4 |
| edit | `61bef06b-5c46-4fc8-82db-1bb0aeba5d74` | Agent 4 |
| search | `8f072d2a-0a90-4419-8083-a4f50dbab2f2` | Agent 4 |
| shot | `6c7534b6-76db-4bf7-92d8-05e45f640806` | Agent 4 |
| task | `c0a7a010-b3ac-4e5d-8956-72a6a2260143` | Agent 4 |

### Trigger

Each agent polls its 5 Unit Tests tasks every 30 seconds. When a task reaches `ready` status (`0081eedc-4c31-4a31-9da6-2b91a1b19cf4`), work begins.

### Workflow Per Unit Tests Task

1. **Set task to WIP**:
   ```bash
   .venv/bin/kitsu task comment add <ut-task-id> "Starting unit tests for <module> module" --status wip
   ```

2. **Read the approved spec** — `specs/<module>.md`

3. **Write unit tests** — save to `tests/test_<module>.py`, based on the MCP tool definitions from the spec.

4. **Publish the tests to Kitsu** — uploads the file as a preview revision with WFA status:
   ```bash
   .venv/bin/kitsu task preview publish <ut-task-id> --status wfa --file tests/test_<module>.py -m "Unit tests written: tests/test_<module>.py\n\nTokens: <in> in / <out> out"
   ```

### Unit Tests Retake Loop

Same pattern as Specs retakes:

1. **Poll** for retake status every 30 seconds.
2. **On retake**, read the latest comment for reviewer feedback.
3. **Revise tests**, save updated `tests/test_<module>.py`.
4. **Generate diff**:
   ```bash
   diff tests/test_<module>.py.prev tests/test_<module>.py > tests/test_<module>.diff
   ```
5. **Publish both files to Kitsu** as a new revision:
   ```bash
   .venv/bin/kitsu task preview publish <ut-task-id> --status wfa --file tests/test_<module>.py -m "Unit tests revised (see diff)\n\nTokens: <in> in / <out> out"
   .venv/bin/kitsu task preview upload <ut-task-id> <comment-id> --file tests/test_<module>.diff
   ```
6. **Repeat** up to 3 retakes or until approved/done.

## Execution Strategy

### Step 1: Create `specs/` directory

```bash
mkdir -p specs
```

### Step 2: Spawn 4 parallel agents (one per bot)

Each agent handles 5 modules sequentially. All 4 agents run in parallel.

### Step 3: Verify

Confirm all 20 Specs tasks are in WFA status:
```bash
.venv/bin/kitsu --format json task list --project "MCP Server" --task-type Specs
```

## Module Sizes (for reference)

| Size | Modules |
|------|---------|
| Small (~3-7 tools) | auth, cache, events, search, edit, concept, news, chat, sync |
| Medium (~10-15 tools) | casting, scene, entity, playlist, studio |
| Large (~20-30 tools) | asset, shot, project, person |
| XL (~40-60 tools) | task, files |
