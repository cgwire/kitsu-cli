"""Test task commands."""

import json
from unittest.mock import patch


MOCK_PROJECT = {"id": "project-uuid-1", "name": "Test Project"}
MOCK_ASSET = {"id": "asset-uuid-1", "name": "Kitsu UI"}
MOCK_TASK_TYPE = {"id": "tt-uuid-1", "name": "Specs"}
MOCK_PERSON = {"id": "person-uuid-1", "email": "bot@studio.test"}


def test_get_by_entity_finds_an_asset_by_name_in_a_project(invoke):
    with patch("kitsu_cli.commands.task.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.task.require_auth"), \
         patch("kitsu_cli.commands.task.resolve_task_type", return_value=MOCK_TASK_TYPE), \
         patch("kitsu_cli.resolver.resolve_project", return_value=MOCK_PROJECT), \
         patch("gazu.asset.get_asset_by_name", return_value=MOCK_ASSET) as by_name:
        mock_gazu.task.get_task_by_entity.return_value = {"id": "task-1"}
        result = invoke(
            "--format", "json", "task", "get-by-entity", "Kitsu UI",
            "--task-type", "Specs", "--project", "Test Project",
        )
        assert result.exit_code == 0
        by_name.assert_called_once_with(MOCK_PROJECT, "Kitsu UI")
        mock_gazu.task.get_task_by_entity.assert_called_once_with(
            MOCK_ASSET, MOCK_TASK_TYPE, name="main"
        )


def test_get_by_entity_still_accepts_a_uuid(invoke):
    uuid = "6c74a1ed-451e-4cf1-aa1a-d737ab40d866"
    with patch("kitsu_cli.commands.task.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.task.require_auth"), \
         patch("kitsu_cli.commands.task.resolve_task_type", return_value=MOCK_TASK_TYPE):
        mock_gazu.task.get_task_by_entity.return_value = {"id": "task-1"}
        result = invoke("task", "get-by-entity", uuid, "--task-type", "Specs")
        assert result.exit_code == 0
        assert mock_gazu.task.get_task_by_entity.call_args[0][0] == uuid


def test_get_by_entity_refuses_a_name_without_project(invoke):
    with patch("kitsu_cli.commands.task.require_auth"), \
         patch("kitsu_cli.commands.task.resolve_task_type", return_value=MOCK_TASK_TYPE):
        result = invoke("task", "get-by-entity", "Kitsu UI", "--task-type", "Specs")
        assert result.exit_code == 1
        assert "--project" in result.output


def test_assign_sends_a_list_of_task_ids(invoke):
    # gazu <= 1.3.1 sends a string, and Zou answers ParameterException.
    with patch("kitsu_cli.commands.task.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.task.require_auth"), \
         patch("kitsu_cli.commands.task.resolve_person", return_value=MOCK_PERSON):
        result = invoke("task", "assign", "task-1", "--person", "bot@studio.test")
        assert result.exit_code == 0
        mock_gazu.client.put.assert_called_once_with(
            "actions/persons/person-uuid-1/assign", {"task_ids": ["task-1"]}
        )


def test_batch_assign_uses_the_route_of_zou(invoke):
    # gazu <= 1.3.1 calls data/tasks/assign, which Zou does not have.
    with patch("kitsu_cli.commands.task.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.task.require_auth"), \
         patch("kitsu_cli.commands.task.resolve_person", return_value=MOCK_PERSON):
        result = invoke(
            "task", "batch-assign", "--person", "bot@studio.test", "task-1", "task-2"
        )
        assert result.exit_code == 0
        mock_gazu.client.put.assert_called_once_with(
            "actions/persons/person-uuid-1/assign",
            {"task_ids": ["task-1", "task-2"]},
        )


def test_create_tasks_on_an_asset_uses_the_route_of_zou(invoke):
    # gazu <= 1.3.1 posts to data/assets/<id>/tasks, which is GET only.
    with patch("kitsu_cli.commands.task.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.task.require_auth"), \
         patch("kitsu_cli.commands.task.resolve_task_type",
               side_effect=lambda name: {"id": f"tt-{name}"}):
        mock_gazu.client.post.return_value = [{"id": "task-1"}, {"id": "task-2"}]
        result = invoke(
            "task", "create-tasks", "asset-uuid-1", "--entity-type", "asset",
            "--task-type", "Specs", "--task-type", "Plan",
        )
        assert result.exit_code == 0
        mock_gazu.client.post.assert_called_once_with(
            "data/entities/asset-uuid-1/tasks",
            {"task_type_ids": ["tt-Specs", "tt-Plan"]},
        )


def test_preview_tokens_adds_to_the_preview_and_to_the_asset(invoke):
    store = {
        "data/preview-files/pf-1": {"id": "pf-1", "task_id": "task-1", "token_in": 10, "token_out": None},
        "data/tasks/task-1": {"id": "task-1", "entity_id": "asset-uuid-1"},
        "data/entities/asset-uuid-1": {"id": "asset-uuid-1", "data": {"token_in": 100, "other": "kept"}},
    }
    with patch("kitsu_cli.commands.task.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.task.require_auth"):
        mock_gazu.client.get.side_effect = lambda path: store[path]
        result = invoke(
            "--format", "json", "task", "preview", "tokens", "pf-1",
            "--in", "5", "--out", "7",
        )
        assert result.exit_code == 0
        mock_gazu.client.put.assert_any_call(
            "data/preview-files/pf-1", {"token_in": 15, "token_out": 7}
        )
        mock_gazu.client.put.assert_any_call(
            "data/entities/asset-uuid-1",
            {"data": {"token_in": 105, "token_out": 7, "other": "kept"}},
        )
        assert json.loads(result.output) == {
            "preview": {"token_in": 15, "token_out": 7},
            "entity": {"token_in": 105, "token_out": 7},
        }


def test_preview_tokens_refuses_a_negative_count(invoke):
    with patch("kitsu_cli.commands.task.require_auth"):
        result = invoke("task", "preview", "tokens", "pf-1", "--in", "-5", "--out", "7")
        assert result.exit_code == 2


def test_clear_assignations_passes_the_task_list(invoke):
    # A command named "list" hid the list() builtin in this module.
    with patch("kitsu_cli.commands.task.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.task.require_auth"):
        mock_gazu.task.clear_assignations.return_value = []
        result = invoke("task", "clear-assignations", "task-1", "task-2")
        assert result.exit_code == 0
        mock_gazu.task.clear_assignations.assert_called_once_with(["task-1", "task-2"])


def _full_task(for_entity, production_type="featurefilm", entity_id="entity-1"):
    return {
        "id": "task-1",
        "project_id": "project-1",
        "entity_id": entity_id,
        "task_type": {"for_entity": for_entity},
        "project": {"production_type": production_type},
    }


def test_task_url_follows_the_entity_type_of_the_task(invoke):
    host = "https://kitsu.test"
    cases = [
        ("Asset", f"{host}/productions/project-1/assets/tasks/task-1/"),
        ("Shot", f"{host}/productions/project-1/shots/tasks/task-1/"),
        ("Edit", f"{host}/productions/project-1/edits/tasks/task-1/"),
        ("Sequence", f"{host}/productions/project-1/sequences/tasks/task-1/"),
        ("Episode", f"{host}/productions/project-1/episodes/entity-1/tasks/task-1/"),
    ]
    for for_entity, expected in cases:
        with patch("kitsu_cli.commands.task.gazu") as mock_gazu, \
             patch("kitsu_cli.commands.task.require_auth"):
            mock_gazu.task.get_task.return_value = _full_task(for_entity)
            mock_gazu.client.get_api_url_from_host.return_value = host
            result = invoke("task", "task-url", "task-1")
            assert result.exit_code == 0, result.output
            assert result.output.strip() == expected, for_entity


def test_task_url_gives_the_episode_of_a_shot_in_a_tv_show(invoke):
    host = "https://kitsu.test"
    with patch("kitsu_cli.commands.task.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.task.require_auth"):
        mock_gazu.task.get_task.return_value = _full_task("Shot", "tvshow")
        mock_gazu.shot.get_shot.return_value = {"episode_id": "episode-1"}
        mock_gazu.client.get_api_url_from_host.return_value = host
        result = invoke("task", "task-url", "task-1")
        assert result.output.strip() == (
            f"{host}/productions/project-1/episodes/episode-1/shots/tasks/task-1/"
        )
