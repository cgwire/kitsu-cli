"""Shot, sequence, and episode commands."""

import json as json_mod

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project, resolve_sequence, resolve_episode


@click.group("shot")
def group():
    """Manage shots, sequences, and episodes."""
    pass


# --- Shot commands ---


@group.command()
@click.option("--project", help="Project UUID or name.")
@click.option("--sequence", help="Sequence UUID.")
@click.option("--episode", help="Episode UUID.")
@click.pass_context
def list(ctx, project, sequence, episode):
    """List shots (filtered by project, sequence, or episode)."""
    require_auth(ctx)
    if sequence:
        results = gazu.shot.all_shots_for_sequence(resolve_sequence(sequence))
    elif episode:
        results = gazu.shot.all_shots_for_episode(resolve_episode(episode))
    elif project:
        results = gazu.shot.all_shots_for_project(resolve_project(project))
    else:
        raise click.ClickException("Provide --project, --sequence, or --episode.")
    output(results, ctx)


@group.command()
@click.argument("shot")
@click.pass_context
def get(ctx, shot):
    """Get a shot by UUID."""
    require_auth(ctx)
    result = gazu.shot.get_shot(shot)
    output(result, ctx)


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.option("--sequence", required=True, help="Sequence UUID.")
@click.argument("name")
@click.option("--nb-frames", type=int, default=None)
@click.option("--frame-in", type=int, default=None)
@click.option("--frame-out", type=int, default=None)
@click.option("--description", "-d", default=None)
@click.option("--data", "extra_data", default=None, help="JSON metadata.")
@click.option("--with-tasks", is_flag=True, help="Create default tasks for the shot.")
@click.pass_context
def create(ctx, project, sequence, name, nb_frames, frame_in, frame_out, description, extra_data, with_tasks):
    """Create a new shot."""
    require_auth(ctx)
    proj = resolve_project(project)
    seq = resolve_sequence(sequence)
    kwargs = {}
    if nb_frames is not None:
        kwargs["nb_frames"] = nb_frames
    if frame_in is not None:
        kwargs["frame_in"] = frame_in
    if frame_out is not None:
        kwargs["frame_out"] = frame_out
    if description:
        kwargs["description"] = description
    if extra_data:
        kwargs["data"] = json_mod.loads(extra_data)
    result = gazu.shot.new_shot(proj, seq, name, **kwargs)
    if with_tasks:
        task_types = gazu.task.all_task_types_for_project(proj)
        gazu.task.create_shot_tasks(result, task_types)
        if not ctx.obj.get("quiet"):
            click.echo(f"Created {len(task_types)} task(s).", err=True)
    output(result, ctx)


@group.command()
@click.argument("shot")
@click.option("--name", help="New name.")
@click.option("--data", "extra_data", help="JSON metadata to merge.")
@click.pass_context
def update(ctx, shot, name, extra_data):
    """Update a shot."""
    require_auth(ctx)
    s = gazu.shot.get_shot(shot)
    if name:
        s["name"] = name
    if extra_data:
        gazu.shot.update_shot_data(s, json_mod.loads(extra_data))
    result = gazu.shot.update_shot(s)
    output(result, ctx)


@group.command()
@click.argument("shot")
@click.option("--force", is_flag=True)
@click.pass_context
def delete(ctx, shot, force):
    """Delete a shot."""
    require_auth(ctx)
    s = gazu.shot.get_shot(shot)
    gazu.shot.remove_shot(s, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted shot {s.get('name', shot)}.")


@group.command()
@click.argument("shot")
@click.pass_context
def restore(ctx, shot):
    """Restore a deleted shot."""
    require_auth(ctx)
    result = gazu.shot.restore_shot(shot)
    output(result, ctx)


@group.command()
@click.argument("shot")
@click.pass_context
def url(ctx, shot):
    """Get the Kitsu URL for a shot."""
    require_auth(ctx)
    s = gazu.shot.get_shot(shot)
    click.echo(gazu.shot.get_shot_url(s))


@group.command()
@click.argument("shot")
@click.pass_context
def previews(ctx, shot):
    """List preview files for a shot."""
    require_auth(ctx)
    s = gazu.shot.get_shot(shot)
    results = gazu.shot.all_previews_for_shot(s)
    output(results, ctx)


@group.command("asset-instances")
@click.argument("shot")
@click.pass_context
def asset_instances(ctx, shot):
    """List asset instances for a shot."""
    require_auth(ctx)
    results = gazu.shot.all_asset_instances_for_shot(shot)
    output(results, ctx)


@group.command("add-asset-instance")
@click.argument("shot")
@click.argument("asset_instance")
@click.pass_context
def add_asset_instance(ctx, shot, asset_instance):
    """Add an asset instance to a shot."""
    require_auth(ctx)
    result = gazu.shot.add_asset_instance_to_shot(shot, asset_instance)
    output(result, ctx)


@group.command("remove-asset-instance")
@click.argument("shot")
@click.argument("asset_instance")
@click.pass_context
def remove_asset_instance(ctx, shot, asset_instance):
    """Remove an asset instance from a shot."""
    require_auth(ctx)
    gazu.shot.remove_asset_instance_from_shot(shot, asset_instance)
    if not ctx.obj.get("quiet"):
        click.echo(f"Removed asset instance {asset_instance} from shot {shot}.")


@group.command("import-otio")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("otio_file", type=click.Path(exists=True))
@click.option("--episode", default=None, help="Episode UUID.")
@click.option("--naming-convention", default=None, help="Naming convention.")
@click.option("--match-case/--no-match-case", default=True)
@click.pass_context
def import_otio(ctx, project, otio_file, episode, naming_convention, match_case):
    """Import shots from an OpenTimelineIO file."""
    require_auth(ctx)
    proj = resolve_project(project)
    kwargs = {}
    if episode:
        kwargs["episode"] = resolve_episode(episode)
    if naming_convention:
        kwargs["naming_convention"] = naming_convention
    result = gazu.shot.import_otio(proj, otio_file, match_case=match_case, **kwargs)
    output(result, ctx)


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("csv_file", type=click.Path(exists=True))
@click.pass_context
def import_csv(ctx, project, csv_file):
    """Import shots from a CSV file."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.shot.import_shots_with_csv(proj, csv_file)
    output(result, ctx)


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("csv_file", type=click.Path())
@click.option("--episode", default=None, help="Episode UUID.")
@click.option("--assigned-to", default=None, help="Person UUID.")
@click.pass_context
def export_csv(ctx, project, csv_file, episode, assigned_to):
    """Export shots to a CSV file."""
    require_auth(ctx)
    proj = resolve_project(project)
    kwargs = {}
    if episode:
        kwargs["episode"] = resolve_episode(episode)
    if assigned_to:
        kwargs["assigned_to"] = assigned_to
    gazu.shot.export_shots_with_csv(proj, csv_file, **kwargs)
    if not ctx.obj.get("quiet"):
        click.echo(f"Exported to {csv_file}.")


# --- Sequence sub-group ---


@group.group("sequence")
def sequence_group():
    """Manage sequences."""
    pass


@sequence_group.command("list")
@click.option("--project", help="Project UUID or name.")
@click.option("--episode", help="Episode UUID.")
@click.pass_context
def sequence_list(ctx, project, episode):
    """List sequences."""
    require_auth(ctx)
    if episode:
        results = gazu.shot.all_sequences_for_episode(resolve_episode(episode))
    elif project:
        results = gazu.shot.all_sequences_for_project(resolve_project(project))
    else:
        raise click.ClickException("Provide --project or --episode.")
    output(results, ctx)


@sequence_group.command("get")
@click.argument("sequence")
@click.pass_context
def sequence_get(ctx, sequence):
    """Get a sequence by UUID."""
    require_auth(ctx)
    result = gazu.shot.get_sequence(sequence)
    output(result, ctx)


@sequence_group.command("create")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("name")
@click.option("--episode", default=None, help="Episode UUID.")
@click.option("--with-tasks", is_flag=True, help="Create default tasks for the sequence.")
@click.pass_context
def sequence_create(ctx, project, name, episode, with_tasks):
    """Create a new sequence."""
    require_auth(ctx)
    proj = resolve_project(project)
    kwargs = {}
    if episode:
        kwargs["episode"] = resolve_episode(episode)
    result = gazu.shot.new_sequence(proj, name, **kwargs)
    if with_tasks:
        task_types = gazu.task.all_task_types_for_project(proj)
        gazu.task.create_entity_tasks(result, task_types)
        if not ctx.obj.get("quiet"):
            click.echo(f"Created {len(task_types)} task(s).", err=True)
    output(result, ctx)


@sequence_group.command("update")
@click.argument("sequence")
@click.option("--name", help="New name.")
@click.option("--data", "extra_data", help="JSON metadata to merge.")
@click.pass_context
def sequence_update(ctx, sequence, name, extra_data):
    """Update a sequence."""
    require_auth(ctx)
    seq = gazu.shot.get_sequence(sequence)
    if name:
        seq["name"] = name
    if extra_data:
        gazu.shot.update_sequence_data(seq, json_mod.loads(extra_data))
    result = gazu.shot.update_sequence(seq)
    output(result, ctx)


@sequence_group.command("delete")
@click.argument("sequence")
@click.option("--force", is_flag=True)
@click.pass_context
def sequence_delete(ctx, sequence, force):
    """Delete a sequence."""
    require_auth(ctx)
    seq = gazu.shot.get_sequence(sequence)
    gazu.shot.remove_sequence(seq, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted sequence {seq.get('name', sequence)}.")


# --- Episode sub-group ---


@group.group("episode")
def episode_group():
    """Manage episodes."""
    pass


@episode_group.command("list")
@click.option("--project", required=True, help="Project UUID or name.")
@click.pass_context
def episode_list(ctx, project):
    """List episodes for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.shot.all_episodes_for_project(proj)
    output(results, ctx)


@episode_group.command("get")
@click.argument("episode")
@click.pass_context
def episode_get(ctx, episode):
    """Get an episode by UUID."""
    require_auth(ctx)
    result = gazu.shot.get_episode(episode)
    output(result, ctx)


@episode_group.command("create")
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("name")
@click.option("--with-tasks", is_flag=True, help="Create default tasks for the episode.")
@click.pass_context
def episode_create(ctx, project, name, with_tasks):
    """Create a new episode."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.shot.new_episode(proj, name)
    if with_tasks:
        task_types = gazu.task.all_task_types_for_project(proj)
        gazu.task.create_entity_tasks(result, task_types)
        if not ctx.obj.get("quiet"):
            click.echo(f"Created {len(task_types)} task(s).", err=True)
    output(result, ctx)


@episode_group.command("update")
@click.argument("episode")
@click.option("--name", help="New name.")
@click.option("--data", "extra_data", help="JSON metadata to merge.")
@click.pass_context
def episode_update(ctx, episode, name, extra_data):
    """Update an episode."""
    require_auth(ctx)
    ep = gazu.shot.get_episode(episode)
    if name:
        ep["name"] = name
    if extra_data:
        gazu.shot.update_episode_data(ep, json_mod.loads(extra_data))
    result = gazu.shot.update_episode(ep)
    output(result, ctx)


@episode_group.command("url")
@click.argument("episode")
@click.pass_context
def episode_url(ctx, episode):
    """Get the Kitsu URL for an episode."""
    require_auth(ctx)
    ep = gazu.shot.get_episode(episode)
    click.echo(gazu.shot.get_episode_url(ep))


@episode_group.command("delete")
@click.argument("episode")
@click.option("--force", is_flag=True)
@click.pass_context
def episode_delete(ctx, episode, force):
    """Delete an episode."""
    require_auth(ctx)
    ep = gazu.shot.get_episode(episode)
    gazu.shot.remove_episode(ep, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted episode {ep.get('name', episode)}.")
