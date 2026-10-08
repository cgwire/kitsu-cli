"""Test asset commands."""

from unittest.mock import patch


MOCK_ASSET = {
    "id": "asset-uuid-1",
    "name": "Character01",
    "asset_type_name": "Character",
}

MOCK_PROJECT = {
    "id": "project-uuid-1",
    "name": "Test Project",
}


def test_asset_list(invoke):
    with patch("kitsu_cli.commands.asset.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.asset.require_auth"), \
         patch("kitsu_cli.commands.asset.resolve_project", return_value=MOCK_PROJECT):
        mock_gazu.asset.all_assets_for_project.return_value = [MOCK_ASSET]
        result = invoke("--format", "json", "asset", "list", "--project", "Test Project")
        assert result.exit_code == 0
        assert "Character01" in result.output


def test_asset_create(invoke):
    with patch("kitsu_cli.commands.asset.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.asset.require_auth"), \
         patch("kitsu_cli.commands.asset.resolve_project", return_value=MOCK_PROJECT), \
         patch("kitsu_cli.commands.asset.resolve_asset_type", return_value={"id": "type-1", "name": "Character"}):
        mock_gazu.asset.new_asset.return_value = MOCK_ASSET
        result = invoke(
            "--format", "json",
            "asset", "create",
            "--project", "Test Project",
            "--type", "Character",
            "Character01"
        )
        assert result.exit_code == 0
        mock_gazu.asset.new_asset.assert_called_once()


def test_asset_delete(invoke):
    with patch("kitsu_cli.commands.asset.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.asset.require_auth"), \
         patch("kitsu_cli.commands.asset.resolve_asset", return_value=MOCK_ASSET):
        mock_gazu.asset.remove_asset.return_value = ""
        result = invoke("asset", "delete", "asset-uuid-1")
        assert result.exit_code == 0
        assert "Deleted asset Character01" in result.output


def test_asset_type_list(invoke):
    with patch("kitsu_cli.commands.asset.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.asset.require_auth"):
        mock_gazu.asset.all_asset_types.return_value = [{"id": "type-1", "name": "Character"}]
        result = invoke("--format", "json", "asset", "type", "list")
        assert result.exit_code == 0
        assert "Character" in result.output


def test_asset_create_with_tasks_uses_the_route_of_zou(invoke):
    # gazu <= 1.3.1 posts to data/assets/<id>/tasks, which is GET only.
    with patch("kitsu_cli.commands.asset.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.asset.require_auth"), \
         patch("kitsu_cli.commands.asset.resolve_project", return_value=MOCK_PROJECT), \
         patch("kitsu_cli.commands.asset.resolve_asset_type", return_value={"id": "type-1", "name": "Module"}), \
         patch("kitsu_cli.commands.asset.resolve_task_type",
               side_effect=lambda name: {"id": f"tt-{name}"}):
        mock_gazu.asset.new_asset.return_value = MOCK_ASSET
        result = invoke(
            "asset", "create", "--project", "Test Project", "--type", "Module",
            "--with-tasks", "--task-type", "Specs", "--task-type", "Plan",
            "Character01",
        )
        assert result.exit_code == 0
        mock_gazu.client.post.assert_called_once_with(
            "data/entities/asset-uuid-1/tasks",
            {"task_type_ids": ["tt-Specs", "tt-Plan"]},
        )


def test_asset_create_with_tasks_defaults_to_the_task_types_of_the_project(invoke):
    with patch("kitsu_cli.commands.asset.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.asset.require_auth"), \
         patch("kitsu_cli.commands.asset.resolve_project", return_value=MOCK_PROJECT), \
         patch("kitsu_cli.commands.asset.resolve_asset_type", return_value={"id": "type-1", "name": "Module"}):
        mock_gazu.asset.new_asset.return_value = MOCK_ASSET
        mock_gazu.task.all_task_types_for_project.return_value = [
            {"id": "tt-1", "for_entity": "Asset"},
            {"id": "tt-2", "for_entity": "Shot"},
        ]
        result = invoke(
            "asset", "create", "--project", "Test Project", "--type", "Module",
            "--with-tasks", "Character01",
        )
        assert result.exit_code == 0
        mock_gazu.client.post.assert_called_once_with(
            "data/entities/asset-uuid-1/tasks", {"task_type_ids": ["tt-1"]}
        )
