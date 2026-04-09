"""Test project commands."""

from unittest.mock import patch


MOCK_PROJECT = {
    "id": "project-uuid-1",
    "name": "Test Project",
    "production_type": "short",
}


def test_project_list(invoke):
    with patch("kitsu_cli.commands.project.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.project.require_auth"):
        mock_gazu.project.all_projects.return_value = [MOCK_PROJECT]
        result = invoke("--format", "json", "project", "list")
        assert result.exit_code == 0
        assert "Test Project" in result.output


def test_project_get_by_uuid(invoke):
    with patch("kitsu_cli.commands.project.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.project.require_auth"), \
         patch("kitsu_cli.commands.project.resolve_project", return_value=MOCK_PROJECT):
        result = invoke("--format", "json", "project", "get", "project-uuid-1")
        assert result.exit_code == 0
        assert "Test Project" in result.output


def test_project_create(invoke):
    with patch("kitsu_cli.commands.project.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.project.require_auth"):
        mock_gazu.project.new_project.return_value = MOCK_PROJECT
        result = invoke("--format", "json", "project", "create", "Test Project")
        assert result.exit_code == 0
        mock_gazu.project.new_project.assert_called_once_with(
            name="Test Project",
            production_type="short",
            production_style="2d3d",
        )


def test_project_delete(invoke):
    with patch("kitsu_cli.commands.project.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.project.require_auth"), \
         patch("kitsu_cli.commands.project.resolve_project", return_value=MOCK_PROJECT):
        mock_gazu.project.remove_project.return_value = ""
        result = invoke("project", "delete", "project-uuid-1")
        assert result.exit_code == 0
        assert "Deleted project Test Project" in result.output
