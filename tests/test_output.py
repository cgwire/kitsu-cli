"""Test output formatting."""

import json
from unittest.mock import MagicMock

from kitsu_cli.output import output


def _ctx(fmt="json"):
    ctx = MagicMock()
    ctx.obj = {"format": fmt}
    return ctx


def test_json_output(capsys):
    data = [{"id": "1", "name": "test"}]
    output(data, _ctx("json"))
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed == data


def test_id_only_output(capsys):
    data = [{"id": "uuid-1"}, {"id": "uuid-2"}]
    output(data, _ctx("id-only"))
    captured = capsys.readouterr()
    assert "uuid-1" in captured.out
    assert "uuid-2" in captured.out


def test_csv_output(capsys):
    data = [{"id": "1", "name": "test"}]
    output(data, _ctx("csv"))
    captured = capsys.readouterr()
    assert "id,name" in captured.out
    assert "1,test" in captured.out


def test_json_single_dict(capsys):
    data = {"id": "1", "name": "test"}
    output(data, _ctx("json"))
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["name"] == "test"


def test_empty_list(capsys):
    output([], _ctx("table"))
    captured = capsys.readouterr()
    assert "No results" in captured.out
