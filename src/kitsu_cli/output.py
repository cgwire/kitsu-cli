"""Output formatting: JSON, table, CSV, id-only."""

import csv
import io
import json
import sys

import click


def output(data, ctx: click.Context, id_field: str = "id") -> None:
    """Format and print data according to the chosen output format."""
    fmt = ctx.obj.get("format", "json")

    if fmt == "id-only":
        _print_ids(data, id_field)
    elif fmt == "csv":
        _print_csv(data)
    elif fmt == "table":
        _print_table(data)
    else:
        _print_json(data)


def _print_json(data) -> None:
    indent = 2 if sys.stdout.isatty() else None
    click.echo(json.dumps(data, indent=indent, default=str))


def _print_ids(data, id_field: str = "id") -> None:
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                click.echo(item.get(id_field, ""))
            else:
                click.echo(item)
    elif isinstance(data, dict):
        click.echo(data.get(id_field, ""))
    else:
        click.echo(data)


def _print_csv(data) -> None:
    if isinstance(data, dict):
        data = [data]
    if not data:
        return

    buf = io.StringIO()
    fields = list(data[0].keys())
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in data:
        writer.writerow({k: _flatten(v) for k, v in row.items()})
    click.echo(buf.getvalue().rstrip())


_TABLE_COLUMNS = {
    "Project": ["name", "production_type", "production_style", "fps", "resolution", "start_date", "end_date", "id"],
    "Asset": ["name", "asset_type_name", "episode_name", "description", "id"],
    "Shot": ["name", "sequence_name", "episode_name", "nb_frames", "frame_in", "frame_out", "description", "id"],
    "Sequence": ["name", "episode_name", "id"],
    "Episode": ["name", "id"],
    "Task": ["task_type_name", "task_status_name", "entity_name", "assigner_name", "last_comment_date", "id"],
    "TaskType": ["name", "for_entity", "color", "id"],
    "TaskStatus": ["name", "short_name", "color", "is_done", "id"],
    "Person": ["full_name", "email", "role", "active", "departments", "id"],
    "AssetType": ["name", "id"],
    "OutputFile": ["name", "representation", "revision", "path", "id"],
    "WorkingFile": ["name", "revision", "software_name", "path", "id"],
    "PreviewFile": ["revision", "extension", "status", "id"],
    "OutputType": ["name", "short_name", "id"],
    "Software": ["name", "short_name", "file_extension", "id"],
    "Playlist": ["name", "for_entity", "created_at", "id"],
    "Comment": ["text", "task_status_name", "person_name", "created_at", "id"],
    "Edit": ["name", "description", "id"],
    "Concept": ["name", "description", "id"],
    "Scene": ["name", "id"],
    "Department": ["name", "color", "id"],
    "Organisation": ["name", "id"],
}


def _pick_columns(data: list[dict]) -> list[str]:
    """Choose the best columns for table display."""
    first = data[0]
    entity_type = first.get("type", "")

    if entity_type in _TABLE_COLUMNS:
        return [k for k in _TABLE_COLUMNS[entity_type] if k in first]

    # Fallback: prefer well-known fields, then fill up to 8 columns
    priority = ["name", "full_name", "id", "email", "role", "description",
                "status", "type", "created_at", "updated_at"]
    chosen = [k for k in priority if k in first]

    for k in first:
        if len(chosen) >= 8:
            break
        if k not in chosen and not isinstance(first.get(k), (dict, list)):
            val = first.get(k)
            if val is not None and val != "":
                chosen.append(k)

    return chosen or list(first.keys())[:6]


def _print_table(data) -> None:
    if isinstance(data, dict):
        data = [data]
    if not data:
        click.echo("No results.")
        return

    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        _print_json(data)
        return

    display_keys = _pick_columns(data)

    table = Table(show_lines=False)
    for key in display_keys:
        table.add_column(key)
    for row in data:
        table.add_row(*[_cell(row.get(k)) for k in display_keys])

    Console().print(table)


def _cell(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return str(value)


def _flatten(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return str(value) if value is not None else ""
