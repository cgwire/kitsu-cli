"""Casting commands (asset-to-shot/episode linking)."""

import json as json_mod

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project


@click.group("casting")
def group():
    """Manage casting (asset-to-entity linking)."""
    pass


@group.command("get-shot")
@click.argument("shot")
@click.pass_context
def get_shot(ctx, shot):
    """Get casting for a shot."""
    require_auth(ctx)
    result = gazu.casting.get_shot_casting(shot)
    output(result, ctx)


@group.command("get-asset")
@click.argument("asset")
@click.pass_context
def get_asset(ctx, asset):
    """Get casting for an asset."""
    require_auth(ctx)
    result = gazu.casting.get_asset_casting(asset)
    output(result, ctx)


@group.command("get-episode")
@click.argument("episode")
@click.pass_context
def get_episode(ctx, episode):
    """Get casting for an episode."""
    require_auth(ctx)
    result = gazu.casting.get_episode_casting(episode)
    output(result, ctx)


@group.command("get-sequence")
@click.argument("sequence")
@click.pass_context
def get_sequence(ctx, sequence):
    """Get casting for a sequence."""
    require_auth(ctx)
    result = gazu.casting.get_sequence_casting(sequence)
    output(result, ctx)


@group.command("cast-in")
@click.argument("asset")
@click.pass_context
def cast_in(ctx, asset):
    """Get entities an asset is cast in."""
    require_auth(ctx)
    result = gazu.casting.get_asset_cast_in(asset)
    output(result, ctx)


@group.command("update-shot")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("shot")
@click.argument("casting", metavar="CASTING_JSON")
@click.pass_context
def update_shot(ctx, project, shot, casting):
    """Update shot casting. CASTING_JSON: list of {asset_id, nb_occurences}."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.casting.update_shot_casting(proj, shot, json_mod.loads(casting))
    output(result, ctx)


@group.command("update-asset")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("asset")
@click.argument("casting", metavar="CASTING_JSON")
@click.pass_context
def update_asset(ctx, project, asset, casting):
    """Update asset casting. CASTING_JSON: list of {asset_id, nb_occurences}."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.casting.update_asset_casting(proj, asset, json_mod.loads(casting))
    output(result, ctx)


@group.command("update-episode")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("episode")
@click.argument("casting", metavar="CASTING_JSON")
@click.pass_context
def update_episode(ctx, project, episode, casting):
    """Update episode casting. CASTING_JSON: list of {asset_id, nb_occurences}."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.casting.update_episode_casting(proj, episode, json_mod.loads(casting))
    output(result, ctx)


@group.command("get-asset-type")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("asset_type")
@click.pass_context
def get_asset_type(ctx, project, asset_type):
    """Get casting for an asset type."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.casting.get_asset_type_casting(proj, asset_type)
    output(result, ctx)


@group.command("get-project-shots")
@click.option("--project", required=True, help="Project UUID or name.")
@click.pass_context
def get_project_shots(ctx, project):
    """Get casting for all shots in a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.casting.get_project_shots_casting(proj)
    output(result, ctx)


@group.command("get-episode-shots")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("episode")
@click.pass_context
def get_episode_shots(ctx, project, episode):
    """Get casting for all shots in an episode."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.casting.get_episode_shots_casting(proj, episode)
    output(result, ctx)


@group.command("get-sequence-shots")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("sequence")
@click.pass_context
def get_sequence_shots(ctx, project, sequence):
    """Get casting for all shots in a sequence."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.casting.get_sequence_shots_casting(proj, sequence)
    output(result, ctx)


@group.command("get-episodes")
@click.option("--project", required=True, help="Project UUID or name.")
@click.pass_context
def get_episodes(ctx, project):
    """Get casting for all episodes in a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.casting.get_episodes_casting(proj)
    output(result, ctx)


@group.command("delete-link")
@click.argument("entity_link")
@click.pass_context
def delete_link(ctx, entity_link):
    """Delete an entity link."""
    require_auth(ctx)
    result = gazu.casting.delete_entity_link(entity_link)
    output(result, ctx)


@group.command("entity-links")
@click.option("--project", required=True, help="Project UUID or name.")
@click.option("--page", type=int, default=None)
@click.option("--limit", type=int, default=None)
@click.pass_context
def entity_links(ctx, project, page, limit):
    """List all entity links for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    kwargs = {}
    if page is not None:
        kwargs["page"] = page
    if limit is not None:
        kwargs["limit"] = limit
    results = gazu.casting.all_entity_links_for_project(proj, **kwargs)
    output(results, ctx)
