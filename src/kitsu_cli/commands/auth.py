"""Authentication commands."""

import click
import gazu

from kitsu_cli.config import get_host, store_credentials, clear_credentials, load_config
from kitsu_cli.output import output


@click.group("auth")
def group():
    """Authenticate with a Kitsu server."""
    pass


@group.command()
@click.option("--email", "-e", help="User email address.")
@click.option("--password", "-p", help="User password (prompted if not given).")
@click.option("--token", "-t", help="Use an existing API token instead of email/password.")
@click.option("--host", "-h", "login_host", help="Kitsu server URL.")
@click.pass_context
def login(ctx, email, password, token, login_host):
    """Log in to a Kitsu server."""
    host = login_host or get_host(ctx.obj.get("host"))
    if not host:
        host = click.prompt("Kitsu server URL")

    host = host.rstrip("/")
    if not host.endswith("/api"):
        api_host = host + "/api"
    else:
        api_host = host
        host = host[:-4]

    gazu.set_host(api_host)

    if token:
        gazu.set_token(token)
        # Verify token works
        try:
            result = gazu.client.get("auth/authenticated")
        except Exception as e:
            raise click.ClickException(f"Token authentication failed: {e}")
        store_credentials(host, token)
        if not ctx.obj.get("quiet"):
            user = result.get("user", {})
            click.echo(f"Logged in as {user.get('full_name', user.get('email', '?'))}.")
        return

    if not email:
        email = click.prompt("Email")
    if not password:
        password = click.prompt("Password", hide_input=True)

    try:
        result = gazu.log_in(email, password)
    except Exception as e:
        raise click.ClickException(f"Login failed: {e}")

    access_token = gazu.client.default_client.tokens["access_token"]
    store_credentials(host, access_token)
    user = result.get("user", {})
    if not ctx.obj.get("quiet"):
        click.echo(f"Logged in as {user.get('full_name', user.get('email', '?'))}.")


@group.command()
@click.pass_context
def status(ctx):
    """Show current authentication status."""
    from kitsu_cli.client import ensure_client

    try:
        ensure_client(ctx)
        result = gazu.client.get("auth/authenticated")
    except (SystemExit, Exception):
        click.echo("Not authenticated.")
        ctx.exit(1)
        return

    user = result.get("user", result)
    if ctx.obj.get("format", "table") == "json":
        output(user, ctx)
    else:
        click.echo(f"Host:  {gazu.get_host()}")
        click.echo(f"User:  {user.get('full_name', '?')}")
        click.echo(f"Email: {user.get('email', '?')}")
        click.echo(f"Role:  {user.get('role', '?')}")


@group.command()
@click.pass_context
def logout(ctx):
    """Clear stored credentials."""
    clear_credentials()
    if not ctx.obj.get("quiet"):
        click.echo("Credentials cleared.")
