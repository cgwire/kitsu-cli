"""Test person commands."""

from unittest.mock import patch


MOCK_BOT = {
    "id": "bot-uuid-1",
    "first_name": "MCP",
    "last_name": "",
    "is_bot": True,
    "expiration_date": None,
}


def test_person_update_sends_only_the_changed_fields(invoke):
    # Zou regenerates the token of a bot when "expiration_date" is in the
    # body, even with the same value: the old token stops working.
    with patch("kitsu_cli.commands.person.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.person.require_auth"), \
         patch("kitsu_cli.commands.person.resolve_person", return_value=dict(MOCK_BOT)):
        mock_gazu.person.update_person.side_effect = lambda p: p
        result = invoke(
            "person", "update", "bot-uuid-1", "--first-name", "Dev", "--last-name", "Agent"
        )
        assert result.exit_code == 0
        mock_gazu.person.update_person.assert_called_once_with(
            {"id": "bot-uuid-1", "first_name": "Dev", "last_name": "Agent"}
        )
