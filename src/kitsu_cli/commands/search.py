"""Search commands."""

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project


@click.group("search")
def group():
    """Search entities."""
    pass


@group.command()
@click.argument("query")
@click.option("--limit", default=3, type=int, help="Max results per index (default: 3).")
@click.option("--project", default=None, help="Project UUID or name to scope the search.")
@click.pass_context
def query(ctx, query, limit, project):
    """Global search across assets, shots, persons, edits, and sequences."""
    require_auth(ctx)
    body = {
        "query": query,
        "limit": limit,
        "index_names": ["assets", "shots", "persons", "edits", "sequences"],
    }
    if project:
        proj = resolve_project(project)
        body["project_id"] = proj["id"]
    result = gazu.client.post("data/search", body)
    output(result, ctx)


@group.command()
@click.argument("query")
@click.option("--project", required=True, help="Project UUID or name.")
@click.pass_context
def asset(ctx, query, project):
    """Search for an asset by name in a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.asset.get_asset_by_name(proj, query)
    if result:
        output(result, ctx)
    else:
        click.echo("No results found.", err=True)


@group.command()
@click.argument("query")
@click.option("--project", required=True, help="Project UUID or name.")
@click.pass_context
def shot_cmd(ctx, query, project):
    """Search for a shot by name (requires --project and sequence context)."""
    require_auth(ctx)
    # Shot lookup requires sequence, so search through all sequences
    proj = resolve_project(project)
    sequences = gazu.shot.all_sequences_for_project(proj)
    for seq in sequences:
        result = gazu.shot.get_shot_by_name(seq, query)
        if result:
            output(result, ctx)
            return
    click.echo("No results found.", err=True)
