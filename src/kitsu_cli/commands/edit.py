"""Edit commands."""

import json as json_mod

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project


@click.group("edit")
def group():
    """Manage edits."""
    pass


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.pass_context
def list(ctx, project):
    """List edits for a project."""
    require_auth(ctx)
    results = gazu.edit.all_edits_for_project(resolve_project(project))
    output(results, ctx)


@group.command()
@click.argument("edit")
@click.pass_context
def get(ctx, edit):
    """Get an edit by UUID."""
    require_auth(ctx)
    result = gazu.edit.get_edit(edit)
    output(result, ctx)


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("name")
@click.option("--description", "-d", default=None)
@click.option("--data", "extra_data", default=None, help="JSON metadata.")
@click.option("--episode", default=None, help="Episode UUID.")
@click.option("--with-tasks", is_flag=True, help="Create default tasks for the edit.")
@click.pass_context
def create(ctx, project, name, description, extra_data, episode, with_tasks):
    """Create a new edit."""
    require_auth(ctx)
    proj = resolve_project(project)
    kwargs = {}
    if description:
        kwargs["description"] = description
    if extra_data:
        kwargs["data"] = json_mod.loads(extra_data)
    if episode:
        kwargs["episode"] = episode
    result = gazu.edit.new_edit(proj, name, **kwargs)
    if with_tasks:
        task_types = gazu.task.all_task_types_for_project(proj)
        gazu.task.create_edit_tasks(result, task_types)
        if not ctx.obj.get("quiet"):
            click.echo(f"Created {len(task_types)} task(s).", err=True)
    output(result, ctx)


@group.command()
@click.argument("edit")
@click.option("--name", help="New name.")
@click.option("--data", "extra_data", help="JSON metadata to merge.")
@click.pass_context
def update(ctx, edit, name, extra_data):
    """Update an edit."""
    require_auth(ctx)
    e = gazu.edit.get_edit(edit)
    if name:
        e["name"] = name
    if extra_data:
        gazu.edit.update_edit_data(e, json_mod.loads(extra_data))
    result = gazu.edit.update_edit(e)
    output(result, ctx)


@group.command()
@click.argument("edit")
@click.option("--force", is_flag=True)
@click.pass_context
def delete(ctx, edit, force):
    """Delete an edit."""
    require_auth(ctx)
    e = gazu.edit.get_edit(edit)
    gazu.edit.remove_edit(e, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted edit {e.get('name', edit)}.")


@group.command()
@click.argument("edit")
@click.pass_context
def url(ctx, edit):
    """Get the Kitsu URL for an edit."""
    require_auth(ctx)
    e = gazu.edit.get_edit(edit)
    click.echo(gazu.edit.get_edit_url(e))


@group.command()
@click.argument("edit")
@click.pass_context
def previews(ctx, edit):
    """List preview files for an edit."""
    require_auth(ctx)
    results = gazu.edit.all_previews_for_edit(edit)
    output(results, ctx)
