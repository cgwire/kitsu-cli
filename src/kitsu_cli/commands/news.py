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


@group.command("list")
@click.option("--project", default=None, help="Project UUID or name.")
@click.option("--limit", default=20, type=int, help="Number of results (default: 20).")
@click.option("--offset", default=0, type=int, help="Offset for pagination (default: 0).")
@click.option("--after", default=None, help="Only the news after this date (2026-10-08 or 2026-10-08T12:00:00).")
@click.option("--details", is_flag=True, help="Add the task type name, the status short name and the comment text.")
@click.pass_context
def list_cmd(ctx, project, limit, offset, after, details):
    """List recent news/activity."""
    require_auth(ctx)
    query = f"page_size={limit}&offset={offset}"
    if after:
        query += f"&after={after}"
    if project:
        proj = resolve_project(project)
        result = gazu.client.get(f"data/projects/{proj['id']}/news?{query}")
    else:
        result = gazu.client.get(f"data/projects/news?{query}")
    if details:
        _add_details(result.get("data", []) if isinstance(result, dict) else result)
    output(result, ctx)


def _add_details(news):
    """Give the names that a reader needs: the news have only ids."""
    task_types = {t["id"]: t["name"] for t in gazu.task.all_task_types()}
    statuses = {s["id"]: s["short_name"] for s in gazu.task.all_task_statuses()}
    for item in news:
        item["task_type_name"] = task_types.get(item.get("task_type_id"))
        item["task_status_short_name"] = statuses.get(item.get("task_status_id"))
        comment_id = item.get("comment_id")
        item["comment_text"] = (
            gazu.client.get(f"data/comments/{comment_id}").get("text") if comment_id else None
        )


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
