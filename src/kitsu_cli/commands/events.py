"""Real-time event listener commands."""

import click


@click.group("events")
def group():
    """Listen to real-time events from Kitsu."""
    pass


@group.command()
@click.pass_context
def listen(ctx):
    """Listen to real-time events and print them as JSON."""
    import json

    from kitsu_cli.client import require_auth

    require_auth(ctx)

    try:
        import gazu.events as events
    except ImportError:
        raise click.ClickException("Events module requires python-socketio. Install with: pip install python-socketio[client]")

    import gazu

    host = gazu.get_host().replace("/api", "")
    token = gazu.client.default_client.tokens.get("access_token", "")

    def on_event(data):
        click.echo(json.dumps(data, default=str))

    event_client = events.init(host, token)
    events.add_listener(event_client, "*", on_event)

    if not ctx.obj.get("quiet"):
        click.echo("Listening for events... (Ctrl+C to stop)", err=True)

    try:
        events.run_client(event_client)
    except KeyboardInterrupt:
        pass
