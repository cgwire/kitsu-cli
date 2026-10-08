"""Entity resolution: accept UUID or name, return dict with 'id'."""

import re
import sys

import click

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def is_uuid(value: str) -> bool:
    return bool(UUID_RE.match(value))


def resolve_project(value: str) -> dict:
    """Resolve a project by UUID or name."""
    import gazu

    if is_uuid(value):
        return gazu.project.get_project(value)
    result = gazu.project.get_project_by_name(value)
    if not result:
        click.echo(f"Error: Project not found: {value}", err=True)
        sys.exit(1)
    return result


def resolve_asset(value: str, project: str | None = None) -> dict:
    """Resolve an asset by UUID, or by name inside a project."""
    import gazu

    if is_uuid(value):
        return gazu.asset.get_asset(value)
    if not project:
        click.echo("Error: Asset lookup by name requires --project. Use UUID instead.", err=True)
        sys.exit(1)
    result = gazu.asset.get_asset_by_name(resolve_project(project), value)
    if not result:
        click.echo(f"Error: Asset not found in {project}: {value}", err=True)
        sys.exit(1)
    return result


def resolve_asset_type(value: str) -> dict:
    import gazu

    if is_uuid(value):
        return gazu.asset.get_asset_type(value)
    result = gazu.asset.get_asset_type_by_name(value)
    if not result:
        click.echo(f"Error: Asset type not found: {value}", err=True)
        sys.exit(1)
    return result


def resolve_task_type(value: str) -> dict:
    import gazu

    if is_uuid(value):
        return gazu.task.get_task_type(value)
    result = gazu.task.get_task_type_by_name(value)
    if not result:
        click.echo(f"Error: Task type not found: {value}", err=True)
        sys.exit(1)
    return result


def resolve_task_status(value: str) -> dict:
    import gazu

    if is_uuid(value):
        return gazu.task.get_task_status(value)
    # Try by name first, then short name
    result = gazu.task.get_task_status_by_name(value)
    if not result:
        result = gazu.task.get_task_status_by_short_name(value)
    if not result:
        click.echo(f"Error: Task status not found: {value}", err=True)
        sys.exit(1)
    return result


def resolve_person(value: str) -> dict:
    import gazu

    if is_uuid(value):
        result = gazu.person.get_person(value)
        if not result:
            click.echo(f"Error: Person not found: {value}", err=True)
            sys.exit(1)
        return result
    # Try by email
    result = gazu.person.get_person_by_email(value)
    if not result:
        result = gazu.person.get_person_by_full_name(value)
    if not result:
        click.echo(f"Error: Person not found: {value}", err=True)
        sys.exit(1)
    return result


def resolve_sequence(value: str) -> dict:
    import gazu

    if is_uuid(value):
        return gazu.shot.get_sequence(value)
    click.echo("Error: Sequence lookup by name requires --project. Use UUID instead.", err=True)
    sys.exit(1)


def resolve_shot(value: str) -> dict:
    import gazu

    if is_uuid(value):
        return gazu.shot.get_shot(value)
    click.echo("Error: Shot lookup by name requires --project. Use UUID instead.", err=True)
    sys.exit(1)


def resolve_episode(value: str) -> dict:
    import gazu

    if is_uuid(value):
        return gazu.shot.get_episode(value)
    click.echo("Error: Episode lookup by name requires --project. Use UUID instead.", err=True)
    sys.exit(1)


def resolve_department(value: str) -> dict:
    import gazu

    if is_uuid(value):
        return gazu.person.get_department(value)
    for dept in gazu.person.all_departments():
        if dept["name"].lower() == value.lower():
            return dept
    click.echo(f"Error: Department not found: {value}", err=True)
    sys.exit(1)
