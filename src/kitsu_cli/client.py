"""Gazu client setup from resolved config."""

import sys

import click
import gazu

from kitsu_cli.config import get_host, get_token


def ensure_client(ctx: click.Context) -> None:
    """Configure the gazu default client from CLI options, env vars, or config file."""
    host = get_host(ctx.obj.get("host"))
    if not host:
        click.echo("Error: No Kitsu host configured. Use --host, KITSU_HOST, or `kitsu auth login`.", err=True)
        sys.exit(1)

    host = host.rstrip("/")
    if not host.endswith("/api"):
        host += "/api"

    gazu.set_host(host)

    token = get_token(ctx.obj.get("token"))
    if token:
        gazu.set_token(token)


def require_auth(ctx: click.Context) -> None:
    """Ensure client is configured and authenticated."""
    ensure_client(ctx)
    try:
        gazu.client.get("auth/authenticated")
    except Exception:
        click.echo("Error: Not authenticated. Run `kitsu auth login` first.", err=True)
        sys.exit(1)
