"""Root Click group with lazy-loading command groups."""

import os
import sys

import click

COMMAND_MODULES = {
    "auth": "kitsu_cli.commands.auth",
    "project": "kitsu_cli.commands.project",
    "asset": "kitsu_cli.commands.asset",
    "shot": "kitsu_cli.commands.shot",
    "task": "kitsu_cli.commands.task",
    "person": "kitsu_cli.commands.person",
    "files": "kitsu_cli.commands.files",
    "casting": "kitsu_cli.commands.casting",
    "playlist": "kitsu_cli.commands.playlist",
    "entity": "kitsu_cli.commands.entity",
    "scene": "kitsu_cli.commands.scene",
    "edit": "kitsu_cli.commands.edit",
    "concept": "kitsu_cli.commands.concept",
    "studio": "kitsu_cli.commands.studio",
    "sync": "kitsu_cli.commands.sync",
    "search": "kitsu_cli.commands.search",
    "cache": "kitsu_cli.commands.cache",
    "events": "kitsu_cli.commands.events",
    "chat": "kitsu_cli.commands.chat",
    "news": "kitsu_cli.commands.news",
}


class LazyGroup(click.Group):
    """Click group that lazily loads subcommand modules."""

    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        base = super().list_commands(ctx)
        lazy = sorted(self._lazy_subcommands.keys())
        return base + lazy

    def get_command(self, ctx, cmd_name):
        if cmd_name in self._lazy_subcommands:
            return self._load_lazy(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _load_lazy(self, cmd_name):
        module_path = self._lazy_subcommands[cmd_name]
        try:
            mod = __import__(module_path, fromlist=["group"])
        except ImportError:
            return None
        return getattr(mod, "group", None)


@click.group(
    cls=LazyGroup,
    lazy_subcommands=COMMAND_MODULES,
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--host",
    envvar="KITSU_HOST",
    help="Kitsu server URL.",
)
@click.option(
    "--token",
    envvar="KITSU_TOKEN",
    help="API access token.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table", "csv", "id-only"]),
    default=None,
    help="Output format (default: json).",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output.")
@click.version_option(package_name="kitsu-cli")
@click.pass_context
def cli(ctx, host, token, output_format, verbose, quiet):
    """Kitsu production tracker CLI."""
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["token"] = token
    ctx.obj["format"] = output_format or ("json" if not sys.stdout.isatty() else "table")
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


def main():
    cli()


if __name__ == "__main__":
    main()
