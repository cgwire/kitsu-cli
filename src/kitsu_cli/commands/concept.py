"""Concept commands."""

import json as json_mod

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_project


@click.group("concept")
def group():
    """Manage concepts."""
    pass


@group.command()
@click.option("--project", help="Project UUID or name.")
@click.pass_context
def list(ctx, project):
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
@click.pass_context
def create(ctx, project, name, description, extra_data):
    """Create a new concept."""
    require_auth(ctx)
    proj = resolve_project(project)
    kwargs = {}
    if description:
        kwargs["description"] = description
    if extra_data:
        kwargs["data"] = json_mod.loads(extra_data)
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
