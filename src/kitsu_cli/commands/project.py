"""Project commands."""

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import (
    resolve_asset_type,
    resolve_department,
    resolve_person,
    resolve_project,
    resolve_task_status,
    resolve_task_type,
)


@click.group("project")
def group():
    """Manage projects."""
    pass


@group.command()
@click.pass_context
def list(ctx):
    """List all projects."""
    require_auth(ctx)
    results = gazu.project.all_projects()
    output(results, ctx)


@group.command()
@click.option("--open", "open_only", is_flag=True, help="Only open projects.")
@click.pass_context
def list_open(ctx, open_only):
    """List open projects."""
    require_auth(ctx)
    results = gazu.project.all_open_projects()
    output(results, ctx)


@group.command()
@click.argument("project")
@click.pass_context
def get(ctx, project):
    """Get a project by UUID or name."""
    require_auth(ctx)
    result = resolve_project(project)
    output(result, ctx)


@group.command()
@click.argument("name")
@click.option("--production-type", type=click.Choice(["short", "tvshow", "featurefilm"]), default="short")
@click.option("--production-style", type=click.Choice(["2d3d", "2d", "3d", "ar", "vfx", "stop-motion"]), default="2d3d")
@click.pass_context
def create(ctx, name, production_type, production_style):
    """Create a new project."""
    require_auth(ctx)
    result = gazu.project.new_project(
        name=name,
        production_type=production_type,
        production_style=production_style,
    )
    output(result, ctx)


@group.command()
@click.argument("project")
@click.option("--name", help="New name.")
@click.option("--data", "extra_data", type=str, help="JSON metadata to merge.")
@click.option(
    "--bot-collaboration/--no-bot-collaboration",
    "bot_collaboration",
    default=None,
    help="Allow AI-agent (bot) assignment and time logging on this project.",
)
@click.pass_context
def update(ctx, project, name, extra_data, bot_collaboration):
    """Update a project."""
    import json as json_mod

    require_auth(ctx)
    proj = resolve_project(project)
    if name:
        proj["name"] = name
    if extra_data:
        proj["data"] = {**(proj.get("data") or {}), **json_mod.loads(extra_data)}
    if bot_collaboration is not None:
        proj["is_bot_collaboration_enabled"] = bot_collaboration
    result = gazu.project.update_project(proj)
    output(result, ctx)


@group.command()
@click.argument("project")
@click.option("--force", is_flag=True, help="Force deletion.")
@click.pass_context
def delete(ctx, project, force):
    """Delete a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    gazu.project.remove_project(proj, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted project {proj['name']}.")


@group.command()
@click.argument("project")
@click.pass_context
def close(ctx, project):
    """Close a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.project.close_project(proj)
    output(result, ctx)


# --- Sub-entity commands ---


@group.group("task-type")
def task_type():
    """Manage project task types."""
    pass


@task_type.command("list")
@click.argument("project")
@click.pass_context
def task_type_list(ctx, project):
    """List task types for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.task.all_task_types_for_project(proj)
    output(results, ctx)


@task_type.command("add")
@click.argument("project")
@click.argument("task_type")
@click.option("--priority", default=1, help="Priority order.")
@click.option("--hd-bitrate", type=int, default=None, help="HD movie bitrate in Mbit/s.")
@click.option("--ld-bitrate", type=int, default=None, help="LD movie bitrate in Mbit/s.")
@click.option("--client-visible/--no-client-visible", default=None, help="Show the task type to clients.")
@click.pass_context
def task_type_add(ctx, project, task_type, priority, hd_bitrate, ld_bitrate, client_visible):
    """Add a task type to a project, or update its settings."""
    require_auth(ctx)
    proj = resolve_project(project)
    tt = resolve_task_type(task_type)
    result = gazu.project.add_task_type(
        proj,
        tt,
        priority,
        hd_bitrate_compression=hd_bitrate,
        ld_bitrate_compression=ld_bitrate,
        is_client_visible=client_visible,
    )
    output(result, ctx)


@task_type.command("remove")
@click.argument("project")
@click.argument("task_type")
@click.pass_context
def task_type_remove(ctx, project, task_type):
    """Remove a task type from a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    tt = resolve_task_type(task_type)
    gazu.project.remove_task_type(proj, tt)
    if not ctx.obj.get("quiet"):
        click.echo(f"Removed task type {tt.get('name', task_type)} from project.")


@group.group("task-status")
def task_status():
    """Manage project task statuses."""
    pass


@task_status.command("list")
@click.argument("project")
@click.pass_context
def task_status_list(ctx, project):
    """List task statuses for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.task.all_task_statuses_for_project(proj)
    output(results, ctx)


@task_status.command("add")
@click.argument("project")
@click.argument("task_status")
@click.pass_context
def task_status_add(ctx, project, task_status):
    """Add a task status to a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    ts = resolve_task_status(task_status)
    result = gazu.project.add_task_status(proj, ts)
    output(result, ctx)


@task_status.command("remove")
@click.argument("project")
@click.argument("task_status")
@click.pass_context
def task_status_remove(ctx, project, task_status):
    """Remove a task status from a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    ts = resolve_task_status(task_status)
    gazu.project.remove_task_status(proj, ts)
    if not ctx.obj.get("quiet"):
        click.echo(f"Removed task status {ts.get('name', task_status)} from project.")


@task_status.command("client-allowed")
@click.argument("project")
@click.argument("task_status")
@click.option("--allow/--deny", required=True, help="Let clients set this status.")
@click.pass_context
def task_status_client_allowed(ctx, project, task_status, allow):
    """Allow or deny a task status to the clients of a project."""
    require_auth(ctx)
    result = gazu.project.set_task_status_client_allowed(
        resolve_project(project), resolve_task_status(task_status), allow
    )
    output(result, ctx)


@group.group("asset-type")
def asset_type():
    """Manage project asset types."""
    pass


@asset_type.command("list")
@click.argument("project")
@click.pass_context
def asset_type_list(ctx, project):
    """List asset types for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.asset.all_asset_types_for_project(proj)
    output(results, ctx)


@asset_type.command("workflow")
@click.argument("project")
@click.argument("asset_type")
@click.option("--task-type", "task_types", multiple=True, help="Task type UUID or name (repeatable). Omit to restore the studio workflow.")
@click.pass_context
def asset_type_workflow(ctx, project, asset_type, task_types):
    """Set the task types of an asset type in a project."""
    require_auth(ctx)
    result = gazu.project.update_asset_type_workflow(
        resolve_project(project),
        resolve_asset_type(asset_type),
        [resolve_task_type(tt) for tt in task_types],
    )
    output(result, ctx)


@group.command()
@click.argument("project")
@click.option("--section", default="assets", help="Section to open (e.g. assets, shots).")
@click.pass_context
def url(ctx, project, section):
    """Get the web URL for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.project.get_project_url(proj, section=section)
    output(result, ctx)


@group.command("update-data")
@click.argument("project")
@click.option("--data", required=True, help="JSON string of metadata to merge.")
@click.pass_context
def update_data(ctx, project, data):
    """Update metadata on a project."""
    import json as json_mod

    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.project.update_project_data(proj, data=json_mod.loads(data))
    output(result, ctx)


# --- Team sub-group ---


@group.group("team")
def team():
    """Manage project team members."""
    pass


@team.command("list")
@click.argument("project")
@click.pass_context
def team_list(ctx, project):
    """List team members for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.project.get_team(proj)
    output(results, ctx)


@team.command("add")
@click.argument("project")
@click.argument("person")
@click.pass_context
def team_add(ctx, project, person):
    """Add a person to the project team."""
    require_auth(ctx)
    proj = resolve_project(project)
    pers = resolve_person(person)
    result = gazu.project.add_person_to_team(proj, pers)
    output(result, ctx)


@team.command("remove")
@click.argument("project")
@click.argument("person")
@click.pass_context
def team_remove(ctx, project, person):
    """Remove a person from the project team."""
    require_auth(ctx)
    proj = resolve_project(project)
    pers = resolve_person(person)
    gazu.project.remove_person_from_team(proj, pers)
    if not ctx.obj.get("quiet"):
        click.echo(f"Removed {pers.get('full_name', person)} from team.")


# --- Metadata sub-group ---


@group.group("metadata")
def metadata():
    """Manage project metadata descriptors."""
    pass


@metadata.command("list")
@click.argument("project")
@click.pass_context
def metadata_list(ctx, project):
    """List metadata descriptors for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.project.all_metadata_descriptors(proj)
    output(results, ctx)


@metadata.command("get")
@click.argument("project")
@click.argument("descriptor")
@click.pass_context
def metadata_get(ctx, project, descriptor):
    """Get a metadata descriptor by UUID."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.project.get_metadata_descriptor(proj, descriptor)
    output(result, ctx)


@metadata.command("add")
@click.argument("project")
@click.argument("name")
@click.argument("entity_type", type=click.Choice(["asset", "shot", "scene"]))
@click.option("--data-type", default="string", help="Data type (default: string).")
@click.option("--choices", default=None, help="Comma-separated list of choices.")
@click.option("--for-client", is_flag=True, help="Display in Kitsu client.")
@click.option("--departments", default=None, help="Comma-separated department IDs.")
@click.pass_context
def metadata_add(ctx, project, name, entity_type, data_type, choices, for_client, departments):
    """Add a metadata descriptor to a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    choices_list = choices.split(",") if choices else []
    departments_list = departments.split(",") if departments else []
    result = gazu.project.add_metadata_descriptor(
        proj,
        name,
        entity_type,
        data_type=data_type,
        choices=choices_list,
        for_client=for_client,
        departments=departments_list,
    )
    output(result, ctx)


@metadata.command("delete")
@click.argument("project")
@click.argument("descriptor")
@click.option("--force", is_flag=True, help="Force deletion.")
@click.pass_context
def metadata_delete(ctx, project, descriptor, force):
    """Delete a metadata descriptor."""
    require_auth(ctx)
    proj = resolve_project(project)
    gazu.project.remove_metadata_descriptor(proj, descriptor, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted metadata descriptor {descriptor}.")


@metadata.command("update")
@click.argument("project")
@click.argument("descriptor")
@click.option("--name", "new_name", required=True, help="New name for the descriptor.")
@click.pass_context
def metadata_update(ctx, project, descriptor, new_name):
    """Update a metadata descriptor."""
    require_auth(ctx)
    proj = resolve_project(project)
    desc = gazu.project.get_metadata_descriptor(proj, descriptor)
    desc["name"] = new_name
    result = gazu.project.update_metadata_descriptor(proj, desc)
    output(result, ctx)


# --- Automation sub-group ---


@group.group("automation")
def automation():
    """Manage project status automations."""
    pass


@automation.command("list")
@click.argument("project")
@click.pass_context
def automation_list(ctx, project):
    """List status automations for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.project.all_status_automations(proj)
    output(results, ctx)


@automation.command("add")
@click.argument("project")
@click.argument("automation_id")
@click.pass_context
def automation_add(ctx, project, automation_id):
    """Add a status automation to a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.project.add_status_automation(
        proj, {"status_automation_id": automation_id}
    )
    output(result, ctx)


@automation.command("delete")
@click.argument("project")
@click.argument("automation_id")
@click.pass_context
def automation_delete(ctx, project, automation_id):
    """Remove a status automation from a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    gazu.project.remove_status_automation(proj, automation_id)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted status automation {automation_id}.")


# --- Budget sub-group ---


@group.group("budget")
def budget():
    """Manage project budgets."""
    pass


@budget.command("list")
@click.argument("project")
@click.pass_context
def budget_list(ctx, project):
    """List budgets for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.project.get_budgets(proj)
    output(results, ctx)


@budget.command("get")
@click.argument("project")
@click.argument("budget_id")
@click.pass_context
def budget_get(ctx, project, budget_id):
    """Get a specific budget."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.project.get_budget(proj, budget_id)
    output(result, ctx)


@budget.command("create")
@click.argument("project")
@click.argument("name")
@click.option("--description", default=None, help="Budget description.")
@click.option("--currency", default=None, help="Currency code (e.g. USD, EUR).")
@click.option("--start-date", default=None, help="Start date (YYYY-MM-DD).")
@click.option("--end-date", default=None, help="End date (YYYY-MM-DD).")
@click.option("--amount", type=float, default=None, help="Overall budget amount.")
@click.pass_context
def budget_create(ctx, project, name, description, currency, start_date, end_date, amount):
    """Create a budget for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.project.create_budget(
        proj,
        name,
        description=description,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
        amount=amount,
    )
    output(result, ctx)


@budget.command("update")
@click.argument("project")
@click.argument("budget_id")
@click.option("--data", required=True, help="JSON string of fields to update.")
@click.pass_context
def budget_update(ctx, project, budget_id, data):
    """Update a budget."""
    import json as json_mod

    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.project.update_budget(proj, budget_id, json_mod.loads(data))
    output(result, ctx)


@budget.command("delete")
@click.argument("project")
@click.argument("budget_id")
@click.pass_context
def budget_delete(ctx, project, budget_id):
    """Delete a budget."""
    require_auth(ctx)
    proj = resolve_project(project)
    gazu.project.remove_budget(proj, budget_id)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted budget {budget_id}.")


# --- Budget-entry sub-group ---


@group.group("budget-entry")
def budget_entry():
    """Manage budget entries."""
    pass


@budget_entry.command("list")
@click.argument("project")
@click.argument("budget_id")
@click.pass_context
def budget_entry_list(ctx, project, budget_id):
    """List entries for a budget."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.project.get_budget_entries(proj, budget_id)
    output(results, ctx)


@budget_entry.command("create")
@click.argument("project")
@click.argument("budget_id")
@click.option("--department", required=True, help="Department UUID or name.")
@click.option("--person", default=None, help="Person UUID or email.")
@click.option("--position", default=None, help="Position of the person.")
@click.option("--seniority", default=None, help="Seniority of the person.")
@click.option("--start-date", default=None, help="Start date (YYYY-MM-DD).")
@click.option("--months-duration", type=int, default=None, help="Duration in months.")
@click.option("--daily-salary", type=float, default=None, help="Daily salary.")
@click.pass_context
def budget_entry_create(ctx, project, budget_id, department, person, position, seniority,
                        start_date, months_duration, daily_salary):
    """Create a budget entry."""
    require_auth(ctx)
    result = gazu.project.create_budget_entry(
        resolve_project(project),
        budget_id,
        resolve_department(department),
        person=resolve_person(person) if person else None,
        position=position,
        seniority=seniority,
        start_date=start_date,
        months_duration=months_duration,
        daily_salary=daily_salary,
    )
    output(result, ctx)


@budget_entry.command("update")
@click.argument("project")
@click.argument("budget_id")
@click.argument("entry_id")
@click.option("--data", required=True, help="JSON string of fields to update.")
@click.pass_context
def budget_entry_update(ctx, project, budget_id, entry_id, data):
    """Update a budget entry."""
    import json as json_mod

    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.project.update_budget_entry(
        proj, budget_id, entry_id, json_mod.loads(data)
    )
    output(result, ctx)


@budget_entry.command("delete")
@click.argument("project")
@click.argument("budget_id")
@click.argument("entry_id")
@click.pass_context
def budget_entry_delete(ctx, project, budget_id, entry_id):
    """Delete a budget entry."""
    require_auth(ctx)
    proj = resolve_project(project)
    gazu.project.remove_budget_entry(proj, budget_id, entry_id)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted budget entry {entry_id}.")


# --- Milestones command ---


@group.command()
@click.argument("project")
@click.pass_context
def milestones(ctx, project):
    """List milestones for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.project.get_milestones(proj)
    output(results, ctx)


# --- Schedule sub-group ---


@group.group("schedule")
def schedule():
    """Manage schedule items."""
    pass


@schedule.command("list")
@click.argument("project")
@click.pass_context
def schedule_list(ctx, project):
    """List schedule items for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    results = gazu.client.get(f"data/projects/{proj['id']}/schedule-items")
    output(results, ctx)


@schedule.command("create")
@click.argument("project")
@click.option("--task-type", required=True, help="Task type UUID or name.")
@click.option("--start-date", required=True, help="Start date (YYYY-MM-DD).")
@click.option("--end-date", required=True, help="End date (YYYY-MM-DD).")
@click.option("--man-days", type=int, default=None, help="Number of man-days.")
@click.pass_context
def schedule_create(ctx, project, task_type, start_date, end_date, man_days):
    """Create a schedule item for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    tt = resolve_task_type(task_type)
    body = {
        "project_id": proj["id"],
        "task_type_id": tt["id"],
        "start_date": start_date,
        "end_date": end_date,
    }
    if man_days is not None:
        body["man_days"] = man_days
    result = gazu.client.post("data/schedule-items", body)
    output(result, ctx)


@schedule.command("update")
@click.argument("schedule_item")
@click.option("--start-date", default=None, help="Start date (YYYY-MM-DD).")
@click.option("--end-date", default=None, help="End date (YYYY-MM-DD).")
@click.option("--man-days", type=int, default=None, help="Number of man-days.")
@click.pass_context
def schedule_update(ctx, schedule_item, start_date, end_date, man_days):
    """Update a schedule item."""
    require_auth(ctx)
    body = {}
    if start_date is not None:
        body["start_date"] = start_date
    if end_date is not None:
        body["end_date"] = end_date
    if man_days is not None:
        body["man_days"] = man_days
    result = gazu.client.put(f"data/schedule-items/{schedule_item}", body)
    output(result, ctx)


@schedule.command("delete")
@click.argument("schedule_item")
@click.pass_context
def schedule_delete(ctx, schedule_item):
    """Delete a schedule item."""
    require_auth(ctx)
    gazu.client.delete(f"data/schedule-items/{schedule_item}")
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted schedule item {schedule_item}.")


# --- Stats sub-group ---


@group.group("stats")
def stats():
    """Project statistics and quotas."""
    pass


@stats.command("episodes")
@click.argument("project")
@click.option("--task-type", default=None, help="Task type UUID or name.")
@click.pass_context
def stats_episodes(ctx, project, task_type):
    """Get episode statistics for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    url = f"data/projects/{proj['id']}/episodes/stats"
    if task_type:
        tt = resolve_task_type(task_type)
        url += f"?task_type_id={tt['id']}"
    result = gazu.client.get(url)
    output(result, ctx)


@stats.command("retakes")
@click.argument("project")
@click.pass_context
def stats_retakes(ctx, project):
    """Get retake statistics for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.client.get(
        f"data/projects/{proj['id']}/episodes/retake-stats"
    )
    output(result, ctx)


@stats.command("quotas")
@click.argument("project")
@click.option("--task-type", required=True, help="Task type UUID or name.")
@click.option("--person", default=None, help="Person UUID or email.")
@click.pass_context
def stats_quotas(ctx, project, task_type, person):
    """Get quota statistics for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    tt = resolve_task_type(task_type)
    if person:
        pers = resolve_person(person)
        result = gazu.client.get(
            f"data/projects/{proj['id']}/quotas/persons/{pers['id']}"
        )
    else:
        result = gazu.client.get(
            f"data/projects/{proj['id']}/quotas/{tt['id']}"
        )
    output(result, ctx)


@stats.command("sequences")
@click.argument("project")
@click.pass_context
def stats_sequences(ctx, project):
    """Get per-sequence task statistics for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.client.get(f"data/projects/{proj['id']}/sequences/stats")
    output(result, ctx)


@stats.command("asset-types")
@click.argument("project")
@click.pass_context
def stats_asset_types(ctx, project):
    """Get per-asset-type task statistics for a project."""
    require_auth(ctx)
    proj = resolve_project(project)
    result = gazu.client.get(f"data/projects/{proj['id']}/asset-types/stats")
    output(result, ctx)


@stats.command("open-tasks")
@click.pass_context
def stats_open_tasks(ctx):
    """Get open task statistics across all projects."""
    require_auth(ctx)
    result = gazu.client.get("data/tasks/open-tasks/stats")
    output(result, ctx)
