"""File management commands (output files, working files, previews, software)."""

import json as json_mod

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project


@click.group("files")
def group():
    """Manage files, output types, and software."""
    pass


# --- Output File commands ---


@group.group("output")
def output_group():
    """Manage output files."""
    pass


@output_group.command("list")
@click.option("--entity", help="Entity UUID.")
@click.option("--project", help="Project UUID or name.")
@click.option("--output-type", help="Output type UUID.")
@click.option("--task-type", help="Task type UUID.")
@click.option("--name", default=None)
@click.option("--representation", default=None)
@click.pass_context
def output_list(ctx, entity, project, output_type, task_type, name, representation):
    """List output files."""
    require_auth(ctx)
    kwargs = {}
    if output_type:
        kwargs["output_type"] = output_type
    if task_type:
        kwargs["task_type"] = task_type
    if name:
        kwargs["name"] = name
    if representation:
        kwargs["representation"] = representation
    if entity:
        results = gazu.files.all_output_files_for_entity(entity, **kwargs)
    elif project:
        results = gazu.files.all_output_files_for_project(resolve_project(project), **kwargs)
    else:
        raise click.ClickException("Provide --entity or --project.")
    output(results, ctx)


@output_group.command("get")
@click.argument("output_file")
@click.pass_context
def output_get(ctx, output_file):
    """Get an output file by UUID."""
    require_auth(ctx)
    result = gazu.files.get_output_file(output_file)
    output(result, ctx)


@output_group.command("last")
@click.argument("entity")
@click.option("--output-type", default=None)
@click.option("--task-type", default=None)
@click.option("--name", default=None)
@click.option("--representation", default=None)
@click.pass_context
def output_last(ctx, entity, output_type, task_type, name, representation):
    """Get the last output files for an entity."""
    require_auth(ctx)
    kwargs = {}
    if output_type:
        kwargs["output_type"] = output_type
    if task_type:
        kwargs["task_type"] = task_type
    if name:
        kwargs["name"] = name
    if representation:
        kwargs["representation"] = representation
    results = gazu.files.get_last_output_files_for_entity(entity, **kwargs)
    output(results, ctx)


@output_group.command("new")
@click.argument("entity")
@click.option("--output-type", required=True, help="Output type UUID.")
@click.option("--task-type", required=True, help="Task type UUID.")
@click.option("--comment", default="", help="Comment for the output file.")
@click.option("--working-file", default=None, help="Working file UUID.")
@click.option("--person", default=None, help="Person UUID.")
@click.option("--name", default="main")
@click.option("--revision", default=0, type=int)
@click.option("--nb-elements", default=1, type=int)
@click.option("--representation", default="")
@click.option("--file-status-id", default=None, help="File status UUID.")
@click.pass_context
def output_new(
    ctx, entity, output_type, task_type, comment, working_file,
    person, name, revision, nb_elements, representation, file_status_id,
):
    """Create a new output file for an entity."""
    require_auth(ctx)
    kwargs = {}
    if working_file:
        kwargs["working_file"] = working_file
    if person:
        kwargs["person"] = person
    if file_status_id:
        kwargs["file_status_id"] = file_status_id
    result = gazu.files.new_entity_output_file(
        entity,
        output_type,
        task_type,
        comment,
        name=name,
        revision=revision,
        nb_elements=nb_elements,
        representation=representation,
        **kwargs,
    )
    output(result, ctx)


@output_group.command("build-path")
@click.argument("entity")
@click.option("--output-type", required=True, help="Output type UUID.")
@click.option("--task-type", required=True, help="Task type UUID.")
@click.option("--name", default="main")
@click.option("--representation", default="")
@click.option("--revision", default=0, type=int)
@click.option("--nb-elements", default=1, type=int)
@click.pass_context
def output_build_path(
    ctx, entity, output_type, task_type, name, representation, revision,
    nb_elements,
):
    """Build the output file path for an entity."""
    require_auth(ctx)
    result = gazu.files.build_entity_output_file_path(
        entity,
        output_type,
        task_type,
        name=name,
        representation=representation,
        revision=revision,
        nb_elements=nb_elements,
    )
    click.echo(result)


@output_group.command("next-revision")
@click.argument("entity")
@click.option("--output-type", required=True, help="Output type UUID.")
@click.option("--task-type", required=True, help="Task type UUID.")
@click.option("--name", default="main")
@click.pass_context
def output_next_revision(ctx, entity, output_type, task_type, name):
    """Get the next output revision number for an entity."""
    require_auth(ctx)
    result = gazu.files.get_next_entity_output_revision(
        entity, output_type, task_type, name=name
    )
    click.echo(result)


@output_group.command("last-revision")
@click.argument("entity")
@click.option("--output-type", required=True, help="Output type UUID.")
@click.option("--task-type", required=True, help="Task type UUID.")
@click.option("--name", default="main")
@click.pass_context
def output_last_revision(ctx, entity, output_type, task_type, name):
    """Get the last output revision number for an entity."""
    require_auth(ctx)
    result = gazu.files.get_last_entity_output_revision(
        entity, output_type, task_type, name=name
    )
    click.echo(result)


# --- Working File commands ---


@group.group("working")
def working_group():
    """Manage working files."""
    pass


@working_group.command("list")
@click.argument("entity")
@click.option("--task", default=None, help="Task UUID.")
@click.option("--name", default=None)
@click.pass_context
def working_list(ctx, entity, task, name):
    """List working files for an entity."""
    require_auth(ctx)
    kwargs = {}
    if task:
        kwargs["task"] = task
    if name:
        kwargs["name"] = name
    results = gazu.files.get_all_working_files_for_entity(entity, **kwargs)
    output(results, ctx)


@working_group.command("get")
@click.argument("working_file")
@click.pass_context
def working_get(ctx, working_file):
    """Get a working file by UUID."""
    require_auth(ctx)
    result = gazu.files.get_working_file(working_file)
    output(result, ctx)


@working_group.command("upload")
@click.argument("working_file")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def working_upload(ctx, working_file, file_path):
    """Upload a working file."""
    require_auth(ctx)
    result = gazu.files.upload_working_file(working_file, file_path)
    output(result, ctx)


@working_group.command("download")
@click.argument("working_file")
@click.argument("file_path", type=click.Path())
@click.pass_context
def working_download(ctx, working_file, file_path):
    """Download a working file."""
    require_auth(ctx)
    gazu.files.download_working_file(working_file, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")


@working_group.command("new")
@click.argument("task")
@click.option("--name", default="main")
@click.option("--software", default=None, help="Software UUID.")
@click.option("--comment", default="")
@click.option("--revision", default=0, type=int)
@click.pass_context
def working_new(ctx, task, name, software, comment, revision):
    """Create a new working file for a task."""
    require_auth(ctx)
    result = gazu.files.new_working_file(
        task, name=name, software=software, comment=comment, revision=revision
    )
    output(result, ctx)


@working_group.command("for-task")
@click.argument("task")
@click.pass_context
def working_for_task(ctx, task):
    """List working files for a task."""
    require_auth(ctx)
    results = gazu.files.get_working_files_for_task(task)
    output(results, ctx)


@working_group.command("last")
@click.argument("task")
@click.pass_context
def working_last(ctx, task):
    """Get the last working files for a task."""
    require_auth(ctx)
    result = gazu.files.get_last_working_files(task)
    output(result, ctx)


@working_group.command("build-path")
@click.argument("task")
@click.option("--name", default="main")
@click.option("--software", default=None, help="Software UUID.")
@click.option("--revision", default=1, type=int)
@click.pass_context
def working_build_path(ctx, task, name, software, revision):
    """Build the working file path for a task."""
    require_auth(ctx)
    result = gazu.files.build_working_file_path(
        task, name=name, software=software, revision=revision
    )
    click.echo(result)


# --- Preview File commands ---


@group.group("preview")
def preview_group():
    """Manage preview files."""
    pass


@preview_group.command("get")
@click.argument("preview_file")
@click.pass_context
def preview_get(ctx, preview_file):
    """Get a preview file by UUID."""
    require_auth(ctx)
    result = gazu.files.get_preview_file(preview_file)
    output(result, ctx)


@preview_group.command("download")
@click.argument("preview_file")
@click.argument("file_path", type=click.Path())
@click.pass_context
def preview_download(ctx, preview_file, file_path):
    """Download a preview file."""
    require_auth(ctx)
    gazu.files.download_preview_file(preview_file, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")


@preview_group.command("download-thumbnail")
@click.argument("preview_file")
@click.argument("file_path", type=click.Path())
@click.pass_context
def preview_download_thumbnail(ctx, preview_file, file_path):
    """Download a preview file thumbnail."""
    require_auth(ctx)
    gazu.files.download_preview_file_thumbnail(preview_file, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")


@preview_group.command("url")
@click.argument("preview_file")
@click.pass_context
def preview_url(ctx, preview_file):
    """Get the URL of a preview file."""
    require_auth(ctx)
    pf = gazu.files.get_preview_file(preview_file)
    click.echo(gazu.files.get_preview_file_url(pf))


@preview_group.command("delete")
@click.argument("preview_file")
@click.option("--force", is_flag=True)
@click.pass_context
def preview_delete(ctx, preview_file, force):
    """Delete a preview file."""
    require_auth(ctx)
    gazu.files.remove_preview_file(preview_file, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted preview file {preview_file}.")


@preview_group.command("download-movie")
@click.argument("preview_file")
@click.argument("file_path", type=click.Path())
@click.pass_context
def preview_download_movie(ctx, preview_file, file_path):
    """Download a preview movie file."""
    require_auth(ctx)
    gazu.files.download_preview_movie(preview_file, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")


@preview_group.command("movie-url")
@click.argument("preview_file")
@click.pass_context
def preview_movie_url(ctx, preview_file):
    """Get the URL of a preview movie file."""
    require_auth(ctx)
    click.echo(gazu.files.get_preview_movie_url(preview_file))


@preview_group.command("download-cover")
@click.argument("preview_file")
@click.argument("file_path", type=click.Path())
@click.pass_context
def preview_download_cover(ctx, preview_file, file_path):
    """Download a preview file cover."""
    require_auth(ctx)
    gazu.files.download_preview_file_cover(preview_file, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")


@preview_group.command("update")
@click.argument("preview_file")
@click.option("--data", required=True, help="JSON data to update.")
@click.pass_context
def preview_update(ctx, preview_file, data):
    """Update a preview file."""
    require_auth(ctx)
    parsed = json_mod.loads(data)
    result = gazu.files.update_preview(preview_file, parsed)
    output(result, ctx)


@preview_group.command("running")
@click.pass_context
def preview_running(ctx):
    """List preview files currently being processed."""
    require_auth(ctx)
    results = gazu.files.get_running_preview_files()
    output(results, ctx)


# --- Output Type commands ---


@group.group("output-type")
def output_type_group():
    """Manage output types."""
    pass


@output_type_group.command("list")
@click.pass_context
def output_type_list(ctx):
    """List all output types."""
    require_auth(ctx)
    results = gazu.files.all_output_types()
    output(results, ctx)


@output_type_group.command("get")
@click.argument("output_type")
@click.pass_context
def output_type_get(ctx, output_type):
    """Get an output type by UUID or name."""
    require_auth(ctx)
    from kitsu_cli.resolver import is_uuid
    if is_uuid(output_type):
        result = gazu.files.get_output_type(output_type)
    else:
        result = gazu.files.get_output_type_by_name(output_type)
    if not result:
        raise click.ClickException(f"Output type not found: {output_type}")
    output(result, ctx)


@output_type_group.command("create")
@click.argument("name")
@click.option("--short-name", required=True)
@click.pass_context
def output_type_create(ctx, name, short_name):
    """Create a new output type."""
    require_auth(ctx)
    result = gazu.files.new_output_type(name, short_name)
    output(result, ctx)


@output_type_group.command("for-entity")
@click.argument("entity")
@click.pass_context
def output_type_for_entity(ctx, entity):
    """List all output types for an entity."""
    require_auth(ctx)
    results = gazu.files.all_output_types_for_entity(entity)
    output(results, ctx)


# --- Software commands ---


@group.group("software")
def software_group():
    """Manage software entries."""
    pass


@software_group.command("list")
@click.pass_context
def software_list(ctx):
    """List all software."""
    require_auth(ctx)
    results = gazu.files.all_softwares()
    output(results, ctx)


@software_group.command("get")
@click.argument("software")
@click.pass_context
def software_get(ctx, software):
    """Get a software by UUID or name."""
    require_auth(ctx)
    from kitsu_cli.resolver import is_uuid
    if is_uuid(software):
        result = gazu.files.get_software(software)
    else:
        result = gazu.files.get_software_by_name(software)
    if not result:
        raise click.ClickException(f"Software not found: {software}")
    output(result, ctx)


@software_group.command("create")
@click.argument("name")
@click.option("--short-name", required=True)
@click.option("--file-extension", required=True)
@click.pass_context
def software_create(ctx, name, short_name, file_extension):
    """Create a new software entry."""
    require_auth(ctx)
    result = gazu.files.new_software(name, short_name, file_extension)
    output(result, ctx)


@software_group.command("update")
@click.argument("software")
@click.option("--name", default=None)
@click.option("--short-name", default=None)
@click.option("--file-extension", default=None)
@click.pass_context
def software_update(ctx, software, name, short_name, file_extension):
    """Update a software entry."""
    require_auth(ctx)
    data = {"id": software}
    if name:
        data["name"] = name
    if short_name:
        data["short_name"] = short_name
    if file_extension:
        data["file_extension"] = file_extension
    result = gazu.files.update_software(data)
    output(result, ctx)


# --- Attachment File commands ---


@group.group("attachment")
def attachment_group():
    """Manage attachment files."""
    pass


@attachment_group.command("list")
@click.option("--task", default=None, help="Task UUID.")
@click.option("--project", default=None, help="Project UUID or name.")
@click.pass_context
def attachment_list(ctx, task, project):
    """List attachment files for a task or project."""
    require_auth(ctx)
    if task:
        results = gazu.files.get_all_attachment_files_for_task(task)
    elif project:
        results = gazu.files.get_all_attachment_files_for_project(
            resolve_project(project)
        )
    else:
        raise click.ClickException("Provide --task or --project.")
    output(results, ctx)


@attachment_group.command("get")
@click.argument("attachment")
@click.pass_context
def attachment_get(ctx, attachment):
    """Get an attachment file by UUID."""
    require_auth(ctx)
    result = gazu.files.get_attachment_file(attachment)
    output(result, ctx)


@attachment_group.command("download")
@click.argument("attachment")
@click.argument("file_path", type=click.Path())
@click.pass_context
def attachment_download(ctx, attachment, file_path):
    """Download an attachment file."""
    require_auth(ctx)
    gazu.files.download_attachment_file(attachment, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")


# --- File Status commands ---


@group.group("file-status")
def file_status_group():
    """Manage file statuses."""
    pass


@file_status_group.command("get")
@click.argument("status")
@click.pass_context
def file_status_get(ctx, status):
    """Get a file status by UUID or name."""
    require_auth(ctx)
    from kitsu_cli.resolver import is_uuid
    if is_uuid(status):
        result = gazu.files.get_file_status(status)
    else:
        result = gazu.files.get_file_status_by_name(status)
    if not result:
        raise click.ClickException(f"File status not found: {status}")
    output(result, ctx)


@file_status_group.command("create")
@click.argument("name")
@click.option("--color", required=True, help="Hex color string, e.g. #00FF00.")
@click.pass_context
def file_status_create(ctx, name, color):
    """Create a new file status."""
    require_auth(ctx)
    result = gazu.files.new_file_status(name, color)
    output(result, ctx)


# --- Avatar commands ---


@group.group("avatar")
def avatar_group():
    """Manage avatars for persons and projects."""
    pass


@avatar_group.command("upload-person")
@click.argument("person")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def avatar_upload_person(ctx, person, file_path):
    """Upload an avatar for a person."""
    require_auth(ctx)
    result = gazu.files.upload_person_avatar(person, file_path)
    output(result, ctx)


@avatar_group.command("download-person")
@click.argument("person")
@click.argument("file_path", type=click.Path())
@click.pass_context
def avatar_download_person(ctx, person, file_path):
    """Download a person's avatar."""
    require_auth(ctx)
    gazu.files.download_person_avatar(person, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")


@avatar_group.command("upload-project")
@click.argument("project")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def avatar_upload_project(ctx, project, file_path):
    """Upload an avatar for a project."""
    require_auth(ctx)
    result = gazu.files.upload_project_avatar(project, file_path)
    output(result, ctx)


@avatar_group.command("download-project")
@click.argument("project")
@click.argument("file_path", type=click.Path())
@click.pass_context
def avatar_download_project(ctx, project, file_path):
    """Download a project's avatar."""
    require_auth(ctx)
    gazu.files.download_project_avatar(project, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Downloaded to {file_path}.")
