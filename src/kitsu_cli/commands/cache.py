"""Cache management commands."""

import click
import gazu


@click.group("cache")
def group():
    """Manage the Gazu client cache."""
    pass


@group.command()
def enable():
    """Enable the Gazu cache."""
    gazu.cache.enable()
    click.echo("Cache enabled.")


@group.command()
def disable():
    """Disable the Gazu cache."""
    gazu.cache.disable()
    click.echo("Cache disabled.")


@group.command()
def clear():
    """Clear the Gazu cache."""
    gazu.cache.clear_all()
    click.echo("Cache cleared.")
