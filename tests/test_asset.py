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
