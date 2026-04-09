"""Test auth commands."""

import pytest
from unittest.mock import patch, MagicMock


def test_logout(invoke, tmp_path):
    with patch("kitsu_cli.commands.auth.clear_credentials") as mock_clear:
        result = invoke("auth", "logout")
        assert result.exit_code == 0
        assert "Credentials cleared" in result.output
        mock_clear.assert_called_once()


def test_login_with_token(invoke):
    mock_user = {"full_name": "Test User", "email": "test@example.com"}

    with patch("kitsu_cli.commands.auth.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.auth.store_credentials") as mock_store:
        mock_gazu.client.get.return_value = {"authenticated": True, "user": mock_user}
        result = invoke("--host", "http://localhost", "auth", "login", "--token", "test-token")
        assert result.exit_code == 0
        assert "Test User" in result.output
        mock_store.assert_called_once_with("http://localhost", "test-token")


def test_login_with_email_password(invoke):
    mock_user = {"full_name": "Test User", "email": "test@example.com"}
    mock_client = MagicMock()
    mock_client.tokens = {"access_token": "generated-token"}

    with patch("kitsu_cli.commands.auth.gazu") as mock_gazu, \
         patch("kitsu_cli.commands.auth.store_credentials") as mock_store:
        mock_gazu.log_in.return_value = {"user": mock_user}
        mock_gazu.client.default_client = mock_client
        result = invoke(
            "--host", "http://localhost",
            "auth", "login",
            "--email", "test@example.com",
            "--password", "secret"
        )
        assert result.exit_code == 0
        assert "Test User" in result.output
        mock_gazu.log_in.assert_called_once_with("test@example.com", "secret")
