"""Concept commands."""

import json as json_mod

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import is_uuid, resolve_project


def _resolve_folder(proj, folder):
    """Return a concept folder dict from a UUID or a name in the project dict."""
    if is_uuid(folder):
        return {"id": folder}
    result = gazu.concept.get_concept_folder_by_name(proj, folder)
    if not result:
        raise click.ClickException(f"Concept folder not found: {folder}")
    return result


@click.group("concept")
def group():
    """Manage concepts."""
    pass


@group.command("list")
@click.option("--project", help="Project UUID or name.")
@click.pass_context
def list_cmd(ctx, project):
    """List concepts."""
    require_auth(ctx)
    if project:
        results = gazu.concept.all_concepts_for_project(resolve_project(project))
    else:
        results = gazu.concept.all_concepts()
    output(results, ctx)


@group.command()
@click.argument("concept")
@click.pass_context
def get(ctx, concept):
    """Get a concept by UUID."""
    require_auth(ctx)
    result = gazu.concept.get_concept(concept)
    output(result, ctx)


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.argument("name")
@click.option("--description", "-d", default=None)
@click.option("--data", "extra_data", default=None, help="JSON metadata.")
@click.option("--folder", default=None, help="Concept folder UUID or name.")
@click.pass_context
def create(ctx, project, name, description, extra_data, folder):
    """Create a new concept."""
    require_auth(ctx)
    proj = resolve_project(project)
    kwargs = {}
    if description:
        kwargs["description"] = description
    if extra_data:
        kwargs["data"] = json_mod.loads(extra_data)
    if folder:
        kwargs["concept_folder"] = _resolve_folder(proj, folder)
    result = gazu.concept.new_concept(proj, name, **kwargs)
    output(result, ctx)


@group.command()
@click.argument("concept")
@click.option("--name", help="New name.")
@click.pass_context
def update(ctx, concept, name):
    """Update a concept."""
    require_auth(ctx)
    c = gazu.concept.get_concept(concept)
    if name:
        c["name"] = name
    result = gazu.concept.update_concept(c)
    output(result, ctx)


@group.command()
@click.argument("concept")
@click.option("--force", is_flag=True)
@click.pass_context
def delete(ctx, concept, force):
    """Delete a concept."""
    require_auth(ctx)
    c = gazu.concept.get_concept(concept)
    gazu.concept.remove_concept(c, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted concept {c.get('name', concept)}.")


@group.command()
@click.argument("concept")
@click.pass_context
def previews(ctx, concept):
    """List preview files for a concept."""
    require_auth(ctx)
    results = gazu.concept.all_previews_for_concept(concept)
    output(results, ctx)


@group.command()
@click.option("--project", required=True, help="Project UUID or name.")
@click.option("--folder", default=None, help="Concept folder UUID or name. Omit to move to the root.")
@click.argument("concepts", nargs=-1, required=True, metavar="CONCEPT_UUID...")
@click.pass_context
def move(ctx, project, folder, concepts):
    """Move concepts to a concept folder."""
    require_auth(ctx)
    proj = resolve_project(project)
    target = _resolve_folder(proj, folder) if folder else None
    result = gazu.concept.move_concepts(proj, list(concepts), target)
    output(result, ctx)


@group.group("folder")
def folder_group():
    """Manage concept folders."""
    pass


@folder_group.command("list")
@click.argument("project")
@click.pass_context
def folder_list(ctx, project):
    """List the concept folders of a project."""
    require_auth(ctx)
    output(gazu.concept.all_concept_folders_for_project(resolve_project(project)), ctx)


@folder_group.command("create")
@click.argument("project")
@click.argument("name")
@click.pass_context
def folder_create(ctx, project, name):
    """Create a concept folder."""
    require_auth(ctx)
    output(gazu.concept.new_concept_folder(resolve_project(project), name), ctx)


@folder_group.command("rename")
@click.argument("project")
@click.argument("folder")
@click.argument("new_name")
@click.pass_context
def folder_rename(ctx, project, folder, new_name):
    """Rename a concept folder."""
    require_auth(ctx)
    f = {**_resolve_folder(resolve_project(project), folder), "name": new_name}
    output(gazu.concept.update_concept_folder(f), ctx)


@folder_group.command("delete")
@click.argument("project")
@click.argument("folder")
@click.pass_context
def folder_delete(ctx, project, folder):
    """Delete a concept folder."""
    require_auth(ctx)
    gazu.concept.remove_concept_folder(_resolve_folder(resolve_project(project), folder))
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted concept folder {folder}.")
