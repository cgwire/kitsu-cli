"""Sync commands."""

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project


@click.group("sync")
def group():
    """Data synchronization and event log."""
    pass


@group.command("last-events")
@click.option("--limit", type=int, default=100, help="Number of events to fetch.")
@click.option("--project", default=None, help="Project UUID or name.")
@click.option("--after", default=None, help="Datetime (ISO format).")
@click.option("--before", default=None, help="Datetime (ISO format).")
@click.option("--only-files", is_flag=True, help="Only file-related events.")
@click.option("--name", default=None, help="Event name filter.")
@click.pass_context
def last_events(ctx, limit, project, after, before, only_files, name):
    """Get the last events from the server."""
    require_auth(ctx)
    kwargs = {"limit": limit, "only_files": only_files}
    if project:
        kwargs["project"] = resolve_project(project)
    if after:
        kwargs["after"] = after
    if before:
        kwargs["before"] = before
    if name:
        kwargs["name"] = name
    results = gazu.sync.get_last_events(**kwargs)
    output(results, ctx)


@group.command("import-entities")
@click.argument("json_file", type=click.Path(exists=True))
@click.pass_context
def import_entities(ctx, json_file):
    """Import entities from a JSON file."""
    import json as json_mod

    require_auth(ctx)
    with open(json_file) as f:
        entities = json_mod.load(f)
    result = gazu.sync.import_entities(entities)
    output(result, ctx)


@group.command("import-tasks")
@click.argument("json_file", type=click.Path(exists=True))
@click.pass_context
def import_tasks(ctx, json_file):
    """Import tasks from a JSON file."""
    import json as json_mod

    require_auth(ctx)
    with open(json_file) as f:
        tasks = json_mod.load(f)
    result = gazu.sync.import_tasks(tasks)
    output(result, ctx)
