"""Entity chat and messaging commands."""

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output


@click.group("chat")
def group():
    """Entity chat and messaging."""
    pass


@group.command("messages")
@click.argument("entity")
@click.pass_context
def messages(ctx, entity):
    """List messages for an entity chat."""
    require_auth(ctx)
    results = gazu.client.get(f"data/entities/{entity}/chat/messages")
    output(results, ctx)


@group.command("send")
@click.argument("entity")
@click.option("--message", "-m", required=True, help="Message text.")
@click.pass_context
def send(ctx, entity, message):
    """Send a message to an entity chat."""
    require_auth(ctx)
    result = gazu.client.post(
        f"data/entities/{entity}/chat/messages", {"text": message}
    )
    output(result, ctx)


@group.command("delete-message")
@click.argument("entity")
@click.argument("message")
@click.pass_context
def delete_message(ctx, entity, message):
    """Delete a message from an entity chat."""
    require_auth(ctx)
    gazu.client.delete(f"data/entities/{entity}/chat/messages/{message}")
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted message {message}.")


@group.command("list")
@click.pass_context
def list_chats(ctx):
    """List chats the current user has joined."""
    require_auth(ctx)
    results = gazu.client.get("data/user/chats")
    output(results, ctx)


@group.command("join")
@click.argument("entity")
@click.pass_context
def join(ctx, entity):
    """Join an entity chat."""
    require_auth(ctx)
    result = gazu.client.post(f"actions/user/chats/{entity}/join", {})
    output(result, ctx)


@group.command("leave")
@click.argument("entity")
@click.pass_context
def leave(ctx, entity):
    """Leave an entity chat."""
    require_auth(ctx)
    gazu.client.delete(f"actions/user/chats/{entity}/join")
    if not ctx.obj.get("quiet"):
        click.echo(f"Left chat for entity {entity}.")
