"""Test news commands."""

import json
from unittest.mock import patch


MOCK_PROJECT = {"id": "project-uuid-1", "name": "Test Project"}

NEWS = {
    "data": [
        {
            "id": "news-1",
            "comment_id": "comment-1",
            "task_type_id": "tt-1",
            "task_status_id": "ts-1",
            "full_entity_name": "Module / Two-Factor Login",
        },
        {
            "id": "news-2",
            "comment_id": None,
            "task_type_id": "tt-1",
            "task_status_id": "ts-1",
            "full_entity_name": "Module / Two-Factor Login",
        },
    ]
}


def test_news_list_after_a_date(invoke):
    with patch("kitsu_cli.commands.news.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.news.require_auth"), \
         patch("kitsu_cli.commands.news.resolve_project", return_value=MOCK_PROJECT):
        mock_gazu.client.get.return_value = {"data": []}
        result = invoke(
            "news", "list", "--project", "Test Project", "--after", "2026-10-08T12:09:00"
        )
        assert result.exit_code == 0
        mock_gazu.client.get.assert_called_once_with(
            "data/projects/project-uuid-1/news?page_size=20&offset=0&after=2026-10-08T12:09:00"
        )


def test_news_list_with_details(invoke):
    def get(path):
        if path.startswith("data/projects/"):
            return json.loads(json.dumps(NEWS))
        return {"comment-1": {"text": "Should be in scope."}}[path.split("/")[-1]]

    with patch("kitsu_cli.commands.news.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.news.require_auth"), \
         patch("kitsu_cli.commands.news.resolve_project", return_value=MOCK_PROJECT):
        mock_gazu.client.get.side_effect = get
        mock_gazu.task.all_task_types.return_value = [{"id": "tt-1", "name": "Specs"}]
        mock_gazu.task.all_task_statuses.return_value = [{"id": "ts-1", "short_name": "retake"}]
        result = invoke(
            "--format", "json", "news", "list", "--project", "Test Project", "--details"
        )
        assert result.exit_code == 0
        first, second = json.loads(result.output)["data"]
        assert first["task_type_name"] == "Specs"
        assert first["task_status_short_name"] == "retake"
        assert first["comment_text"] == "Should be in scope."
        assert second["comment_text"] is None
