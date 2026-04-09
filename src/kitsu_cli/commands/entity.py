"""Generic entity commands."""

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output


@click.group("entity")
def group():
    """Manage generic entities and entity types."""
    pass


@group.command()
@click.pass_context
def list(ctx):
    """List all entities."""
    require_auth(ctx)
    results = gazu.entity.all_entities()
    output(results, ctx)


@group.command()
@click.argument("entity")
@click.pass_context
def get(ctx, entity):
    """Get an entity by UUID."""
    require_auth(ctx)
    result = gazu.entity.get_entity(entity)
    output(result, ctx)


@group.command()
@click.argument("entity")
@click.option("--force", is_flag=True)
@click.pass_context
def delete(ctx, entity, force):
    """Delete an entity."""
    require_auth(ctx)
    gazu.entity.remove_entity(entity, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted entity {entity}.")


@group.command()
@click.argument("entity")
@click.pass_context
def linked(ctx, entity):
    """List entities with tasks linked to this entity."""
    require_auth(ctx)
    results = gazu.entity.all_entities_with_tasks_linked_to_entity(entity)
    output(results, ctx)


# --- Entity Type sub-group ---


@group.group("type")
def type_group():
    """Manage entity types."""
    pass


@type_group.command("list")
@click.pass_context
def type_list(ctx):
    """List all entity types."""
    require_auth(ctx)
    results = gazu.entity.all_entity_types()
    output(results, ctx)


@type_group.command("get")
@click.argument("entity_type")
@click.pass_context
def type_get(ctx, entity_type):
    """Get an entity type by UUID or name."""
    require_auth(ctx)
    from kitsu_cli.resolver import is_uuid
    if is_uuid(entity_type):
        result = gazu.entity.get_entity_type(entity_type)
    else:
        result = gazu.entity.get_entity_type_by_name(entity_type)
    if not result:
        raise click.ClickException(f"Entity type not found: {entity_type}")
    output(result, ctx)


@type_group.command("create")
@click.argument("name")
@click.pass_context
def type_create(ctx, name):
    """Create a new entity type."""
    require_auth(ctx)
    result = gazu.entity.new_entity_type(name)
    output(result, ctx)


@type_group.command("delete")
@click.argument("entity_type")
@click.pass_context
def type_delete(ctx, entity_type):
    """Delete an entity type."""
    require_auth(ctx)
    gazu.entity.remove_entity_type(entity_type)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted entity type {entity_type}.")
