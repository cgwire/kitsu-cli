"""Shared test fixtures."""

import pytest
from click.testing import CliRunner

from kitsu_cli.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def invoke(runner):
    """Helper to invoke CLI commands with default obj context."""
    def _invoke(*args, **kwargs):
        return runner.invoke(cli, args, catch_exceptions=False, **kwargs)
    return _invoke
