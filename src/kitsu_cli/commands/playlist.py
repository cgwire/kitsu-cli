"""Playlist commands."""

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project


@click.group("playlist")
def group():
    """Manage playlists."""
    pass


@group.command()
@click.option("--project", help="Project UUID or name.")
@click.option("--episode", help="Episode UUID.")
@click.pass_context
def list(ctx, project, episode):
    """List playlists."""
    require_auth(ctx)
    if episode:
        results = gazu.playlist.all_playlists_for_episode(episode)
    elif project:
        results = gazu.playlist.all_playlists_for_project(resolve_project(project))
    else:
        results = gazu.playlist.all_playlists()
    output(results, ctx)


@group.command()
@click.argument("playlist")
@click.pass_context
def get(ctx, playlist):
    """Get a playlist by UUID."""
    require_auth(ctx)
    result = gazu.playlist.get_playlist(playlist)
    output(result, ctx)


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("name")
@click.option("--episode", default=None, help="Episode UUID.")
@click.option("--for-entity", default="shot", type=click.Choice(["shot", "asset", "edit"]))
@click.option("--for-client", is_flag=True)
@click.pass_context
def create(ctx, project, name, episode, for_entity, for_client):
    """Create a new playlist."""
    require_auth(ctx)
    proj = resolve_project(project)
    kwargs = {"for_entity": for_entity, "for_client": for_client}
    if episode:
        kwargs["episode"] = episode
    result = gazu.playlist.new_playlist(proj, name, **kwargs)
    output(result, ctx)


@group.command()
@click.argument("playlist")
@click.option("--name", help="New name.")
@click.pass_context
def update(ctx, playlist, name):
    """Update a playlist."""
    require_auth(ctx)
    p = gazu.playlist.get_playlist(playlist)
    if name:
        p["name"] = name
    result = gazu.playlist.update_playlist(p)
    output(result, ctx)


@group.command("shots")
@click.argument("playlist")
@click.pass_context
def shots(ctx, playlist):
    """List all shots for a playlist."""
    require_auth(ctx)
    results = gazu.playlist.all_shots_for_playlist(playlist)
    output(results, ctx)


@group.command("update-entity-preview")
@click.argument("playlist")
@click.argument("entity")
@click.argument("preview_file")
@click.pass_context
def update_entity_preview(ctx, playlist, entity, preview_file):
    """Update the preview file for an entity in a playlist."""
    require_auth(ctx)
    p = gazu.playlist.get_playlist(playlist)
    result = gazu.playlist.update_entity_preview(p, entity, preview_file)
    output(result, ctx)


@group.command()
@click.argument("playlist")
@click.pass_context
def delete(ctx, playlist):
    """Delete a playlist."""
    require_auth(ctx)
    gazu.playlist.delete_playlist(playlist)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted playlist {playlist}.")


@group.command("add-entity")
@click.argument("playlist")
@click.argument("entity")
@click.option("--preview-file", default=None, help="Preview file UUID.")
@click.pass_context
def add_entity(ctx, playlist, entity, preview_file):
    """Add an entity to a playlist."""
    require_auth(ctx)
    kwargs = {}
    if preview_file:
        kwargs["preview_file"] = preview_file
    result = gazu.playlist.add_entity_to_playlist(playlist, entity, **kwargs)
    output(result, ctx)


@group.command("remove-entity")
@click.argument("playlist")
@click.argument("entity")
@click.pass_context
def remove_entity(ctx, playlist, entity):
    """Remove an entity from a playlist."""
    require_auth(ctx)
    result = gazu.playlist.remove_entity_from_playlist(playlist, entity)
    output(result, ctx)


@group.command("build-movie")
@click.argument("playlist")
@click.pass_context
def build_movie(ctx, playlist):
    """Build a movie from a playlist."""
    require_auth(ctx)
    result = gazu.playlist.build_playlist_movie(playlist)
    output(result, ctx)


@group.command("download-zip")
@click.argument("playlist")
@click.argument("file_path", type=click.Path())
@click.pass_context
def download_zip(ctx, playlist, file_path):
    """Download a playlist as a ZIP file."""
    require_auth(ctx)
    gazu.playlist.download_playlist_zip(playlist, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")


# --- Build job sub-group ---


@group.group("build-job")
def build_job_group():
    """Manage playlist build jobs."""
    pass


@build_job_group.command("list")
@click.option("--project", required=True, help="Project UUID or name.")
@click.pass_context
def build_job_list(ctx, project):
    """List all build jobs for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.playlist.all_build_jobs_for_project(proj)
    output(results, ctx)


@build_job_group.command("get")
@click.argument("build_job")
@click.pass_context
def build_job_get(ctx, build_job):
    """Get a build job by UUID."""
    require_auth(ctx)
    result = gazu.playlist.get_build_job(build_job)
    output(result, ctx)


@build_job_group.command("delete")
@click.argument("build_job")
@click.pass_context
def build_job_delete(ctx, build_job):
    """Delete a build job."""
    require_auth(ctx)
    gazu.playlist.remove_build_job(build_job)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted build job {build_job}.")


@build_job_group.command("download")
@click.argument("playlist")
@click.argument("build_job")
@click.argument("file_path", type=click.Path())
@click.pass_context
def build_job_download(ctx, playlist, build_job, file_path):
    """Download a playlist build."""
    require_auth(ctx)
    gazu.playlist.download_playlist_build(playlist, build_job, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")
