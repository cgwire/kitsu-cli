"""Activity feed and news commands."""

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project


@click.group("news")
def group():
    """Activity feed and news."""
    pass


@group.command()
@click.option("--project", default=None, help="Project UUID or name.")
@click.option("--limit", default=20, type=int, help="Number of results (default: 20).")
@click.option("--offset", default=0, type=int, help="Offset for pagination (default: 0).")
@click.pass_context
def list(ctx, project, limit, offset):
    """List recent news/activity."""
    require_auth(ctx)
    if project:
        proj = resolve_project(project)
        result = gazu.client.get(
            f"data/projects/{proj['id']}/news?page_size={limit}&offset={offset}"
        )
    else:
        result = gazu.client.get(
            f"data/projects/news?page_size={limit}&offset={offset}"
        )
    output(result, ctx)


@group.command("entity")
@click.argument("entity")
@click.option("--limit", default=20, type=int, help="Number of results (default: 20).")
@click.option("--offset", default=0, type=int, help="Offset for pagination (default: 0).")
@click.pass_context
def entity_news(ctx, entity, limit, offset):
    """List news for a specific entity (by UUID)."""
    require_auth(ctx)
    result = gazu.client.get(
        f"data/entities/{entity}/news?page_size={limit}&offset={offset}"
    )
    output(result, ctx)


@group.command("get")
@click.argument("project")
@click.argument("news_id")
@click.pass_context
def get_news(ctx, project, news_id):
    """Get a specific news item from a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.client.get(
        f"data/projects/{proj['id']}/news/{news_id}"
    )
    output(result, ctx)
