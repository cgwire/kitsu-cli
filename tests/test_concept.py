"""Test concept commands."""

from unittest.mock import patch

MOCK_PROJECT = {"id": "project-uuid-1", "name": "Test Project"}
FOLDER_UUID = "6c74a1ed-451e-4cf1-aa1a-d737ab40d866"


def test_move_finds_the_folder_by_name(invoke):
    with patch("kitsu_cli.commands.concept.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.concept.require_auth"), \
         patch("kitsu_cli.commands.concept.resolve_project", return_value=MOCK_PROJECT):
        mock_gazu.concept.get_concept_folder_by_name.return_value = {"id": "f1", "name": "Props"}
        result = invoke("concept", "move", "--project", "P", "--folder", "Props", "c1", "c2")
        assert result.exit_code == 0
        mock_gazu.concept.move_concepts.assert_called_once_with(
            MOCK_PROJECT, ["c1", "c2"], {"id": "f1", "name": "Props"}
        )


def test_move_without_folder_moves_to_the_root(invoke):
    with patch("kitsu_cli.commands.concept.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.concept.require_auth"), \
         patch("kitsu_cli.commands.concept.resolve_project", return_value=MOCK_PROJECT):
        result = invoke("concept", "move", "--project", "P", "c1")
        assert result.exit_code == 0
        mock_gazu.concept.move_concepts.assert_called_once_with(MOCK_PROJECT, ["c1"], None)


def test_folder_rename_accepts_a_uuid(invoke):
    with patch("kitsu_cli.commands.concept.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.concept.require_auth"), \
         patch("kitsu_cli.commands.concept.resolve_project", return_value=MOCK_PROJECT):
        result = invoke("concept", "folder", "rename", "P", FOLDER_UUID, "Sets")
        assert result.exit_code == 0
        mock_gazu.concept.update_concept_folder.assert_called_once_with({"id": FOLDER_UUID, "name": "Sets"})


def test_unknown_folder_name_fails(runner):
    from kitsu_cli.cli import cli

    with patch("kitsu_cli.commands.concept.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.concept.require_auth"), \
         patch("kitsu_cli.commands.concept.resolve_project", return_value=MOCK_PROJECT):
        mock_gazu.concept.get_concept_folder_by_name.return_value = None
        result = runner.invoke(cli, ["concept", "folder", "delete", "P", "Nope"])
        assert result.exit_code == 1
        assert "Concept folder not found: Nope" in result.output
        mock_gazu.concept.remove_concept_folder.assert_not_called()
