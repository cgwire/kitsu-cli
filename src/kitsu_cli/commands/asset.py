"""Asset commands."""

import json as json_mod

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import (
    resolve_asset,
    resolve_asset_type,
    resolve_episode,
    resolve_project,
    resolve_shot,
    resolve_task_type,
)


@click.group("asset")
def group():
    """Manage assets."""
    pass


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.option("--asset-type", "asset_type", help="Filter by asset type UUID or name.")
@click.option("--episode", default=None, help="Filter by episode UUID.")
@click.option("--shot", default=None, help="Filter by shot UUID.")
@click.pass_context
def list(ctx, project, asset_type, episode, shot):
    """List assets for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    if episode:
        ep = resolve_episode(episode)
        results = gazu.asset.all_assets_for_episode(ep)
    elif shot:
        s = resolve_shot(shot)
        results = gazu.asset.all_assets_for_shot(s)
    elif asset_type:
        at = resolve_asset_type(asset_type)
        results = gazu.asset.all_assets_for_project_and_type(proj, at)
    else:
        results = gazu.asset.all_assets_for_project(proj)
    output(results, ctx)


@group.command()
@click.argument("asset")
@click.option("--project", help="Project UUID or name (required for name lookup).")
@click.option("--name", "by_name", help="Look up by name instead of UUID.")
@click.pass_context
def get(ctx, asset, project, by_name):
    """Get an asset by UUID, or by name with --project."""
    require_auth(ctx)
    if by_name or project:
        if not project:
            raise click.ClickException("--project is required for name lookup.")
        proj = resolve_project(project)
        result = gazu.asset.get_asset_by_name(proj, asset)
        if not result:
            raise click.ClickException(f"Asset not found: {asset}")
    else:
        result = resolve_asset(asset)
    output(result, ctx)


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.option("--type", "asset_type", required=True, help="Asset type UUID or name.")
@click.argument("name")
@click.option("--description", "-d", default=None)
@click.option("--episode", default=None, help="Episode UUID (for TV shows).")
@click.option("--data", "extra_data", default=None, help="JSON metadata.")
@click.option("--with-tasks", is_flag=True, help="Create default tasks for the asset.")
@click.option(
    "--task-type", "task_types", multiple=True,
    help="With --with-tasks: task type UUID or name (repeatable). Default: the asset task types of the project.",
)
@click.pass_context
def create(ctx, project, asset_type, name, description, episode, extra_data, with_tasks, task_types):
    """Create a new asset."""
    require_auth(ctx)
    proj = resolve_project(project)
    at = resolve_asset_type(asset_type)

    kwargs = {}
    if description:
        kwargs["description"] = description
    if extra_data:
        kwargs["extra_data"] = json_mod.loads(extra_data)
    if episode:
        kwargs["episode"] = episode

    result = gazu.asset.new_asset(proj, at, name, **kwargs)
    if with_tasks:
        if task_types:
            type_ids = [resolve_task_type(tt)["id"] for tt in task_types]
        else:
            type_ids = [
                tt["id"]
                for tt in gazu.task.all_task_types_for_project(proj)
                if tt.get("for_entity", "Asset") == "Asset"
            ]
        gazu.task.create_asset_tasks(result, type_ids)
        if not ctx.obj.get("quiet"):
            click.echo(f"Created {len(type_ids)} task(s).", err=True)
    output(result, ctx)


@group.command()
@click.argument("asset")
@click.option("--name", help="New name.")
@click.option("--description", "-d", help="New description.")
@click.option("--data", "extra_data", help="JSON metadata to merge.")
@click.pass_context
def update(ctx, asset, name, description, extra_data):
    """Update an asset."""
    require_auth(ctx)
    a = resolve_asset(asset)
    if name:
        a["name"] = name
    if description:
        a["description"] = description
    if extra_data:
        gazu.asset.update_asset_data(a, json_mod.loads(extra_data))
    result = gazu.asset.update_asset(a)
    output(result, ctx)


@group.command()
@click.argument("asset")
@click.option("--force", is_flag=True, help="Force deletion.")
@click.pass_context
def delete(ctx, asset, force):
    """Delete an asset."""
    require_auth(ctx)
    a = resolve_asset(asset)
    gazu.asset.remove_asset(a, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted asset {a.get('name', asset)}.")


@group.command()
@click.argument("asset")
@click.pass_context
def url(ctx, asset):
    """Get the URL of an asset."""
    require_auth(ctx)
    a = resolve_asset(asset)
    result = gazu.asset.get_asset_url(a)
    output(result, ctx)


@group.command("import-csv")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("csv_file", type=click.Path(exists=True))
@click.pass_context
def import_csv(ctx, project, csv_file):
    """Import assets from a CSV file."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.asset.import_assets_with_csv(proj, csv_file)
    output(result, ctx)


@group.command("export-csv")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("csv_file", type=click.Path())
@click.option("--episode", default=None, help="Episode UUID.")
@click.option("--assigned-to-me", is_flag=True, help="Only the entities with tasks assigned to you.")
@click.pass_context
def export_csv(ctx, project, csv_file, episode, assigned_to_me):
    """Export assets to a CSV file."""
    require_auth(ctx)
    proj = resolve_project(project)
    kwargs = {}
    if episode:
        kwargs["episode"] = resolve_episode(episode)
    if assigned_to_me:
        kwargs["assigned_to_me"] = True
    result = gazu.asset.export_assets_with_csv(proj, csv_file, **kwargs)
    output(result, ctx)


# --- Asset Type sub-group ---


@group.group("type")
def type_group():
    """Manage asset types."""
    pass


@type_group.command("list")
@click.pass_context
def type_list(ctx):
    """List all asset types."""
    require_auth(ctx)
    results = gazu.asset.all_asset_types()
    output(results, ctx)


@type_group.command("get")
@click.argument("asset_type")
@click.pass_context
def type_get(ctx, asset_type):
    """Get an asset type by UUID or name."""
    require_auth(ctx)
    result = resolve_asset_type(asset_type)
    output(result, ctx)


@type_group.command("create")
@click.argument("name")
@click.pass_context
def type_create(ctx, name):
    """Create a new asset type."""
    require_auth(ctx)
    result = gazu.asset.new_asset_type(name)
    output(result, ctx)


@type_group.command("delete")
@click.argument("asset_type")
@click.pass_context
def type_delete(ctx, asset_type):
    """Delete an asset type."""
    require_auth(ctx)
    at = resolve_asset_type(asset_type)
    gazu.asset.remove_asset_type(at)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted asset type {at.get('name', asset_type)}.")


@type_group.command("update")
@click.argument("asset_type")
@click.option("--name", required=True, help="New name for the asset type.")
@click.pass_context
def type_update(ctx, asset_type, name):
    """Update an asset type."""
    require_auth(ctx)
    at = resolve_asset_type(asset_type)
    at["name"] = name
    result = gazu.asset.update_asset_type(at)
    output(result, ctx)


# --- Asset Instance sub-group ---


@group.group("instance")
def instance_group():
    """Manage asset instances."""
    pass


@instance_group.command("list")
@click.argument("asset")
@click.option("--shot", default=None, help="List instances for a shot UUID instead.")
@click.pass_context
def instance_list(ctx, asset, shot):
    """List asset instances for an asset."""
    require_auth(ctx)
    if shot:
        s = resolve_shot(shot)
        results = gazu.asset.all_asset_instances_for_shot(s)
    else:
        a = resolve_asset(asset)
        results = gazu.asset.all_asset_instances_for_asset(a)
    output(results, ctx)


@instance_group.command("get")
@click.argument("asset_instance")
@click.pass_context
def instance_get(ctx, asset_instance):
    """Get an asset instance by UUID."""
    require_auth(ctx)
    result = gazu.asset.get_asset_instance(asset_instance)
    output(result, ctx)


@instance_group.command("create")
@click.argument("asset")
@click.option("--scene", required=True, help="Scene UUID.")
@click.pass_context
def instance_create(ctx, asset, scene):
    """Create a new asset instance."""
    require_auth(ctx)
    a = resolve_asset(asset)
    result = gazu.asset.new_asset_asset_instance(a, scene)
    output(result, ctx)


@instance_group.command("enable")
@click.argument("asset_instance")
@click.pass_context
def instance_enable(ctx, asset_instance):
    """Enable an asset instance."""
    require_auth(ctx)
    result = gazu.asset.enable_asset_instance(asset_instance)
    output(result, ctx)


@instance_group.command("disable")
@click.argument("asset_instance")
@click.pass_context
def instance_disable(ctx, asset_instance):
    """Disable an asset instance."""
    require_auth(ctx)
    result = gazu.asset.disable_asset_instance(asset_instance)
    output(result, ctx)
