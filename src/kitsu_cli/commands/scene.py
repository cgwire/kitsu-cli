"""Scene commands."""

import json as json_mod

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project, resolve_sequence


@click.group("scene")
def group():
    """Manage scenes and asset instances."""
    pass


@group.command()
@click.option("--project", help="Project UUID or name.")
@click.option("--sequence", help="Sequence UUID.")
@click.pass_context
def list(ctx, project, sequence):
    """List scenes."""
    require_auth(ctx)
    if sequence:
        results = gazu.scene.all_scenes_for_sequence(resolve_sequence(sequence))
    elif project:
        results = gazu.scene.all_scenes_for_project(resolve_project(project))
    else:
        results = gazu.scene.all_scenes()
    output(results, ctx)


@group.command()
@click.argument("scene")
@click.pass_context
def get(ctx, scene):
    """Get a scene by UUID."""
    require_auth(ctx)
    result = gazu.scene.get_scene(scene)
    output(result, ctx)


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.option("--sequence", required=True, help="Sequence UUID.")
@click.argument("name")
@click.pass_context
def create(ctx, project, sequence, name):
    """Create a new scene."""
    require_auth(ctx)
    proj = resolve_project(project)
    seq = resolve_sequence(sequence)
    result = gazu.scene.new_scene(proj, seq, name)
    output(result, ctx)


@group.command()
@click.argument("scene")
@click.option("--name", help="New name.")
@click.pass_context
def update(ctx, scene, name):
    """Update a scene."""
    require_auth(ctx)
    s = gazu.scene.get_scene(scene)
    if name:
        s["name"] = name
    result = gazu.scene.update_scene(s)
    output(result, ctx)


@group.command("asset-instances")
@click.argument("scene")
@click.pass_context
def asset_instances(ctx, scene):
    """List asset instances for a scene."""
    require_auth(ctx)
    results = gazu.scene.all_asset_instances_for_scene(scene)
    output(results, ctx)


@group.command("add-asset")
@click.argument("scene")
@click.argument("asset")
@click.option("--description", "-d", default=None)
@click.pass_context
def add_asset(ctx, scene, asset, description):
    """Add an asset instance to a scene."""
    require_auth(ctx)
    kwargs = {}
    if description:
        kwargs["description"] = description
    result = gazu.scene.new_scene_asset_instance(scene, asset, **kwargs)
    output(result, ctx)


@group.command("shots")
@click.argument("scene")
@click.pass_context
def shots(ctx, scene):
    """List shots for a scene."""
    require_auth(ctx)
    results = gazu.scene.all_shots_for_scene(scene)
    output(results, ctx)


@group.command("add-shot")
@click.argument("scene")
@click.argument("shot")
@click.pass_context
def add_shot(ctx, scene, shot):
    """Link a shot to a scene."""
    require_auth(ctx)
    result = gazu.scene.add_shot_to_scene(scene, shot)
    output(result, ctx)


@group.command("camera-instances")
@click.argument("scene")
@click.pass_context
def camera_instances(ctx, scene):
    """List camera instances for a scene."""
    require_auth(ctx)
    results = gazu.scene.all_camera_instances_for_scene(scene)
    output(results, ctx)


@group.command("update-asset-instance")
@click.argument("asset_instance")
@click.option("--name", default=None, help="New name.")
@click.option("--data", "extra_data", default=None, help="JSON metadata.")
@click.pass_context
def update_asset_instance(ctx, asset_instance, name, extra_data):
    """Update an asset instance name and/or data."""
    require_auth(ctx)
    if name:
        result = gazu.scene.update_asset_instance_name(asset_instance, name)
        output(result, ctx)
    if extra_data:
        result = gazu.scene.update_asset_instance_data(asset_instance, json_mod.loads(extra_data))
        output(result, ctx)


@group.command("remove-shot")
@click.argument("scene")
@click.argument("shot")
@click.pass_context
def remove_shot(ctx, scene, shot):
    """Unlink a shot from a scene."""
    require_auth(ctx)
    result = gazu.scene.remove_shot_from_scene(scene, shot)
    output(result, ctx)
