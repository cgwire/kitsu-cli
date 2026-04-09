"""Test root CLI group and global options."""


def test_help(invoke):
    result = invoke("--help")
    assert result.exit_code == 0
    assert "Kitsu production tracker CLI" in result.output


def test_version(invoke):
    result = invoke("--version")
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_all_command_groups_listed(invoke):
    result = invoke("--help")
    assert result.exit_code == 0
    for group in [
        "auth", "project", "asset", "shot", "task", "person",
        "files", "casting", "playlist", "entity", "scene",
        "edit", "concept", "studio", "sync", "search", "cache", "events",
    ]:
        assert group in result.output, f"Missing command group: {group}"


def test_auth_help(invoke):
    result = invoke("auth", "--help")
    assert result.exit_code == 0
    assert "login" in result.output
    assert "logout" in result.output
    assert "status" in result.output


def test_project_help(invoke):
    result = invoke("project", "--help")
    assert result.exit_code == 0
    assert "list" in result.output
    assert "get" in result.output
    assert "create" in result.output


def test_shot_subgroups(invoke):
    result = invoke("shot", "--help")
    assert result.exit_code == 0
    assert "sequence" in result.output
    assert "episode" in result.output


def test_task_subgroups(invoke):
    result = invoke("task", "--help")
    assert result.exit_code == 0
    assert "comment" in result.output
    assert "preview" in result.output
    assert "time" in result.output
    assert "type" in result.output
    assert "status" in result.output
