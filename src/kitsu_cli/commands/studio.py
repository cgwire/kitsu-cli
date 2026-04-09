"""Studio/user-context commands."""

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project


@click.group("studio")
def group():
    """User context: personal tasks, notifications, filters."""
    pass


@group.command("todo")
@click.pass_context
def todo(ctx):
    """List tasks to do for the current user."""
    require_auth(ctx)
    results = gazu.user.all_tasks_to_do()
    output(results, ctx)


@group.command("done")
@click.pass_context
def done(ctx):
    """List done tasks for the current user."""
    require_auth(ctx)
    results = gazu.user.all_done_tasks()
    output(results, ctx)


@group.command("notifications")
@click.pass_context
def notifications(ctx):
    """List notifications for the current user."""
    require_auth(ctx)
    results = gazu.user.all_notifications()
    output(results, ctx)


@group.command("mark-all-read")
@click.pass_context
def mark_all_read(ctx):
    """Mark all notifications as read."""
    require_auth(ctx)
    gazu.user.mark_all_notifications_as_read()
    if not ctx.obj.get("quiet"):
        click.echo("All notifications marked as read.")


@group.command("context")
@click.pass_context
def user_context(ctx):
    """Get the current user context."""
    require_auth(ctx)
    result = gazu.user.get_context()
    output(result, ctx)


@group.command("tasks-requiring-feedback")
@click.pass_context
def tasks_requiring_feedback(ctx):
    """List tasks requiring feedback from the current user."""
    require_auth(ctx)
    results = gazu.user.all_tasks_requiring_feedback()
    output(results, ctx)


@group.command("subscribe")
@click.argument("task")
@click.pass_context
def subscribe(ctx, task):
    """Subscribe to a task."""
    require_auth(ctx)
    result = gazu.user.subscribe_to_task(task)
    output(result, ctx)


@group.command("unsubscribe")
@click.argument("task")
@click.pass_context
def unsubscribe(ctx, task):
    """Unsubscribe from a task."""
    require_auth(ctx)
    gazu.user.unsubscribe_from_task(task)
    if not ctx.obj.get("quiet"):
        click.echo(f"Unsubscribed from task {task}.")


@group.command("time-spents")
@click.option("--start", required=True, help="Start date (YYYY-MM-DD).")
@click.option("--end", required=True, help="End date (YYYY-MM-DD).")
@click.pass_context
def time_spents(ctx, start, end):
    """Get time spents for the current user in a date range."""
    require_auth(ctx)
    result = gazu.user.get_timespents_range(start, end)
    output(result, ctx)


@group.command("day-off")
@click.pass_context
def day_off(ctx):
    """Get day offs for the current user."""
    require_auth(ctx)
    result = gazu.user.get_day_off()
    output(result, ctx)


# --- Filter sub-group ---


@group.group("filter")
def filter_group():
    """Manage user filters."""
    pass


@filter_group.command("list")
@click.pass_context
def filter_list(ctx):
    """List all filters."""
    require_auth(ctx)
    results = gazu.user.all_filters()
    output(results, ctx)


@filter_group.command("create")
@click.argument("name")
@click.option("--query", required=True)
@click.option("--list-type", required=True, help="List type (e.g. 'asset', 'shot').")
@click.option("--project", default=None, help="Project UUID.")
@click.pass_context
def filter_create(ctx, name, query, list_type, project):
    """Create a new filter."""
    require_auth(ctx)
    kwargs = {}
    if project:
        kwargs["project"] = project
    result = gazu.user.new_filter(name, query, list_type, **kwargs)
    output(result, ctx)


@filter_group.command("update")
@click.argument("filter_id")
@click.option("--name", default=None)
@click.option("--query", default=None)
@click.pass_context
def filter_update(ctx, filter_id, name, query):
    """Update a filter."""
    require_auth(ctx)
    f = {"id": filter_id}
    if name:
        f["name"] = name
    if query:
        f["query"] = query
    result = gazu.user.update_filter(f)
    output(result, ctx)


@filter_group.command("delete")
@click.argument("filter_id")
@click.pass_context
def filter_delete(ctx, filter_id):
    """Delete a filter."""
    require_auth(ctx)
    gazu.user.remove_filter(filter_id)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted filter {filter_id}.")


# --- Filter group sub-group ---


@group.group("filter-group")
def filter_group_group():
    """Manage filter groups."""
    pass


@filter_group_group.command("list")
@click.pass_context
def filter_group_list(ctx):
    """List all filter groups."""
    require_auth(ctx)
    results = gazu.user.all_filter_groups()
    output(results, ctx)


@filter_group_group.command("create")
@click.argument("name")
@click.option("--project", default=None, help="Project UUID or name.")
@click.pass_context
def filter_group_create(ctx, name, project):
    """Create a new filter group."""
    require_auth(ctx)
    kwargs = {}
    if project:
        kwargs["project"] = resolve_project(project)
    result = gazu.user.new_filter_group(name, **kwargs)
    output(result, ctx)


@filter_group_group.command("update")
@click.argument("filter_group")
@click.option("--name", default=None)
@click.pass_context
def filter_group_update(ctx, filter_group, name):
    """Update a filter group."""
    require_auth(ctx)
    fg = {"id": filter_group}
    if name:
        fg["name"] = name
    result = gazu.user.update_filter_group(fg)
    output(result, ctx)


@filter_group_group.command("delete")
@click.argument("filter_group")
@click.pass_context
def filter_group_delete(ctx, filter_group):
    """Delete a filter group."""
    require_auth(ctx)
    gazu.user.remove_filter_group(filter_group)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted filter group {filter_group}.")
