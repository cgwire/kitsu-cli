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


def test_project_update_enable_bot_collaboration(invoke):
    with patch("kitsu_cli.commands.project.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.project.require_auth"), \
         patch("kitsu_cli.commands.project.resolve_project", return_value=dict(MOCK_PROJECT)):
        mock_gazu.project.update_project.side_effect = lambda p: p
        result = invoke(
            "--format", "json", "project", "update",
            "project-uuid-1", "--bot-collaboration",
        )
        assert result.exit_code == 0
        sent = mock_gazu.project.update_project.call_args[0][0]
        assert sent["is_bot_collaboration_enabled"] is True


def test_project_update_disable_bot_collaboration(invoke):
    with patch("kitsu_cli.commands.project.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.project.require_auth"), \
         patch("kitsu_cli.commands.project.resolve_project", return_value=dict(MOCK_PROJECT)):
        mock_gazu.project.update_project.side_effect = lambda p: p
        result = invoke(
            "--format", "json", "project", "update",
            "project-uuid-1", "--no-bot-collaboration",
        )
        assert result.exit_code == 0
        sent = mock_gazu.project.update_project.call_args[0][0]
        assert sent["is_bot_collaboration_enabled"] is False


def test_project_update_leaves_bot_collaboration_untouched(invoke):
    with patch("kitsu_cli.commands.project.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.project.require_auth"), \
         patch("kitsu_cli.commands.project.resolve_project", return_value=dict(MOCK_PROJECT)):
        mock_gazu.project.update_project.side_effect = lambda p: p
        result = invoke("project", "update", "project-uuid-1", "--name", "Renamed")
        assert result.exit_code == 0
        sent = mock_gazu.project.update_project.call_args[0][0]
        assert "is_bot_collaboration_enabled" not in sent


def test_project_delete(invoke):
    with patch("kitsu_cli.commands.project.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.project.require_auth"), \
         patch("kitsu_cli.commands.project.resolve_project", return_value=MOCK_PROJECT):
        mock_gazu.project.remove_project.return_value = ""
        result = invoke("project", "delete", "project-uuid-1")
        assert result.exit_code == 0
        assert "Deleted project Test Project" in result.output


def test_budget_entry_create_sends_the_department_and_the_person(invoke):
    with patch("kitsu_cli.commands.project.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.project.require_auth"), \
         patch("kitsu_cli.commands.project.resolve_project", return_value={"id": "p1"}), \
         patch("kitsu_cli.commands.project.resolve_department", return_value={"id": "d1"}), \
         patch("kitsu_cli.commands.project.resolve_person", return_value={"id": "u1"}):
        mock_gazu.project.create_budget_entry.return_value = {"id": "e1"}
        result = invoke(
            "project", "budget-entry", "create", "p1", "b1",
            "--department", "Animation", "--person", "a@b.c",
            "--months-duration", "3", "--daily-salary", "350",
        )
        assert result.exit_code == 0
        mock_gazu.project.create_budget_entry.assert_called_once_with(
            {"id": "p1"}, "b1", {"id": "d1"}, person={"id": "u1"},
            position=None, seniority=None, start_date=None,
            months_duration=3, daily_salary=350.0,
        )
