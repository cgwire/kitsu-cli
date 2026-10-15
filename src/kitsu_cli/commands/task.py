"""Task commands with comment, time, and preview sub-groups."""

import json as json_mod
import sys
import time as time_mod

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import (
    is_uuid,
    resolve_asset,
    resolve_department,
    resolve_person,
    resolve_project,
    resolve_task_status,
    resolve_task_type,
)


def _get_current_user():
    """Get the currently authenticated user."""
    result = gazu.client.get("auth/authenticated")
    return result.get("user", result)


def _filter_by_status(results, task_status_id):
    """Client-side filter on task_status_id."""
    return [t for t in results if t.get("task_status_id") == task_status_id]


@click.group("task")
def group():
    """Manage tasks, comments, and time tracking."""
    pass


# --- Task commands ---


@group.command("list")
@click.option("--project", help="Project UUID or name.")
@click.option("--asset", help="Asset UUID.")
@click.option("--shot", help="Shot UUID.")
@click.option("--sequence", help="Sequence UUID.")
@click.option("--episode", help="Episode UUID.")
@click.option("--concept", help="Concept UUID.")
@click.option("--edit", help="Edit UUID.")
@click.option("--scene", help="Scene UUID.")
@click.option("--person", help="Person UUID or email.")
@click.option("--assignee", help="Assignee UUID, email, or 'me'.")
@click.option("--task-type", "task_type", help="Task type UUID or name.")
@click.option("--task-status", "task_status", help="Task status UUID or name.")
@click.option("--relations", is_flag=True, help="Include related entities.")
@click.pass_context
def list_cmd(ctx, project, asset, shot, sequence, episode, concept, edit, scene, person, assignee, task_type, task_status, relations):
    """List tasks with various filters.

    Filters can be combined: --project with --task-type and/or --task-status,
    or --assignee me to list your own tasks.
    """
    require_auth(ctx)

    # Resolve --assignee
    if assignee == "me":
        me = _get_current_user()
        person = me["id"]
        assignee = None
    elif assignee:
        person = resolve_person(assignee)["id"]
        assignee = None

    # Fetch tasks
    if person and not project:
        # Use the user module for "me" tasks — includes todo context
        results = gazu.task.all_tasks_for_person(person)
    elif project and task_type and task_status:
        results = gazu.task.all_tasks_for_task_status(
            resolve_project(project), resolve_task_type(task_type), resolve_task_status(task_status)
        )
    elif project and task_type:
        results = gazu.task.all_tasks_for_task_type(resolve_project(project), resolve_task_type(task_type))
    elif project:
        results = gazu.task.all_tasks_for_project(resolve_project(project), task_type=resolve_task_type(task_type) if task_type else None)
    elif asset:
        results = gazu.task.all_tasks_for_asset(asset, relations=relations)
    elif shot:
        results = gazu.task.all_tasks_for_shot(shot, relations=relations)
    elif sequence:
        results = gazu.task.all_tasks_for_sequence(sequence, relations=relations)
    elif episode:
        results = gazu.task.all_tasks_for_episode(episode, relations=relations)
    elif concept:
        results = gazu.task.all_tasks_for_concept(concept, relations=relations)
    elif edit:
        results = gazu.task.all_tasks_for_edit(edit, relations=relations)
    elif scene:
        results = gazu.task.all_tasks_for_scene(scene, relations=relations)
    else:
        raise click.ClickException("Provide a filter: --project, --asset, --shot, --sequence, --episode, --concept, --edit, --scene, --person, or --assignee.")

    # Client-side filters when API couldn't handle the combination
    if task_status and not (project and task_type):
        ts = resolve_task_status(task_status)
        results = _filter_by_status(results, ts["id"])
    if task_type and person:
        tt = resolve_task_type(task_type)
        results = [t for t in results if t.get("task_type_id") == tt["id"]]

    output(results, ctx)


@group.command("await")
@click.argument("task")
@click.option("--status", "target_status", required=True, help="Target status to wait for (UUID, name, or short name).")
@click.option("--timeout", "timeout_sec", type=int, default=0, help="Timeout in seconds (0 = no timeout).")
@click.option("--interval", type=int, default=30, help="Polling interval in seconds (default: 30).")
@click.pass_context
def await_cmd(ctx, task, target_status, timeout_sec, interval):
    """Wait for a task to reach a given status.

    Polls the task at regular intervals until its status matches the target.
    Exits 0 on match, 1 on timeout. Useful for agent orchestration.

    \b
    Examples:
      kitsu task await TASK_UUID --status approved
      kitsu task await TASK_UUID --status approved --timeout 3600 --interval 60
    """
    require_auth(ctx)
    ts = resolve_task_status(target_status)
    target_id = ts["id"]
    target_name = ts.get("short_name", ts.get("name", target_status))

    if not ctx.obj.get("quiet"):
        click.echo(f"Waiting for task {task} to reach status '{target_name}'...", err=True)

    start = time_mod.time()
    while True:
        t = gazu.task.get_task(task)
        current_status_id = t.get("task_status_id")
        if current_status_id == target_id:
            if not ctx.obj.get("quiet"):
                click.echo(f"Task reached status '{target_name}'.", err=True)
            output(t, ctx)
            return

        if timeout_sec > 0 and (time_mod.time() - start) >= timeout_sec:
            click.echo(f"Timeout after {timeout_sec}s. Current status: {t.get('task_status_name', current_status_id)}", err=True)
            ctx.exit(1)
            return

        time_mod.sleep(interval)


@group.command()
@click.argument("task")
@click.pass_context
def get(ctx, task):
    """Get a task by UUID."""
    require_auth(ctx)
    result = gazu.task.get_task(task)
    output(result, ctx)


@group.command()
@click.argument("entity", metavar="ENTITY_UUID")
@click.option("--task-type", "task_type", required=True, help="Task type UUID or name.")
@click.option("--name", default="main")
@click.option("--task-status", "task_status", help="Task status UUID or name.")
@click.option("--assigner", help="Assigner person UUID or email.")
@click.option("--assignee", "assignees", multiple=True, help="Assignee person UUID or email (repeatable).")
@click.pass_context
def create(ctx, entity, task_type, name, task_status, assigner, assignees):
    """Create a new task on an entity."""
    require_auth(ctx)
    tt = resolve_task_type(task_type)
    kwargs = {"name": name}
    if task_status:
        kwargs["task_status"] = resolve_task_status(task_status)
    if assigner:
        kwargs["assigner"] = resolve_person(assigner)
    if assignees:
        kwargs["assignees"] = [resolve_person(a) for a in assignees]
    entity_dict = gazu.entity.get_entity(entity)
    result = gazu.task.new_task(entity_dict, tt, **kwargs)
    output(result, ctx)


@group.command()
@click.argument("task")
@click.option("--name", help="New name.")
@click.option("--data", "extra_data", help="JSON metadata to merge.")
@click.pass_context
def update(ctx, task, name, extra_data):
    """Update a task."""
    require_auth(ctx)
    t = gazu.task.get_task(task)
    if name:
        t["name"] = name
    if extra_data:
        gazu.task.update_task_data(t, json_mod.loads(extra_data))
    result = gazu.task.update_task(t)
    output(result, ctx)


@group.command()
@click.argument("task")
@click.pass_context
def delete(ctx, task):
    """Delete a task."""
    require_auth(ctx)
    gazu.task.remove_task(task)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted task {task}.")


@group.command()
@click.argument("task")
@click.option("--person", help="Person UUID or email.")
@click.pass_context
def start(ctx, task, person):
    """Start a task (set to WIP status)."""
    require_auth(ctx)
    kwargs = {}
    if person:
        kwargs["person"] = resolve_person(person)
    result = gazu.task.start_task(task, **kwargs)
    output(result, ctx)


@group.command()
@click.argument("task")
@click.option("--person", required=True, help="Person UUID or email.")
@click.pass_context
def assign(ctx, task, person):
    """Assign a person to a task."""
    require_auth(ctx)
    # gazu <= 1.3.1 sends task_ids as a string: Zou refuses it.
    person_id = resolve_person(person)["id"]
    result = gazu.client.put(f"actions/persons/{person_id}/assign", {"task_ids": [task]})
    output(result, ctx)


@group.command()
@click.argument("task")
@click.option("--person", required=True, help="Person UUID or email.")
@click.option("--comment", "-m", required=True, help="Review comment.")
@click.option("--revision", type=int, default=1)
@click.pass_context
def review(ctx, task, person, comment, revision):
    """Submit a task for review."""
    require_auth(ctx)
    result = gazu.task.task_to_review(task, resolve_person(person), comment, revision=revision)
    output(result, ctx)


@group.command()
@click.argument("task")
@click.pass_context
def task_url(ctx, task):
    """Get the Kitsu URL for a task."""
    require_auth(ctx)
    t = gazu.task.get_task(task)
    click.echo(_task_url(t))


# gazu.task.get_task_url always gives a shots/ path. Same routes as getTaskPath
# in kitsu/src/lib/path.js.
_ROUTE_TYPES = {"Shot": "shots", "Edit": "edits", "Sequence": "sequences"}


def _task_url(t):
    base = f"{gazu.client.get_api_url_from_host()}/productions/{t['project_id']}"
    for_entity = (t.get("task_type") or {}).get("for_entity") or "Asset"
    if for_entity == "Episode":
        return f"{base}/episodes/{t['entity_id']}/tasks/{t['id']}/"
    route_type = _ROUTE_TYPES.get(for_entity, "assets")
    is_tv_show = (t.get("project") or {}).get("production_type") == "tvshow"
    if is_tv_show and for_entity == "Shot":
        episode_id = gazu.shot.get_shot(t["entity_id"]).get("episode_id")
        if episode_id:
            base = f"{base}/episodes/{episode_id}"
    return f"{base}/{route_type}/tasks/{t['id']}/"


@group.command("list-open")
@click.option("--person", help="Person UUID or email.")
@click.pass_context
def list_open(ctx, person):
    """List all open tasks, optionally filtered by person."""
    require_auth(ctx)
    if person:
        results = gazu.task.all_open_tasks_for_person(resolve_person(person))
    else:
        results = gazu.task.all_open_tasks()
    output(results, ctx)


@group.command("get-by-entity")
@click.argument("entity", metavar="ENTITY")
@click.option("--task-type", "task_type", required=True, help="Task type UUID or name.")
@click.option("--name", default="main", help="Task name.")
@click.option("--project", help="Project UUID or name, to find an asset by name.")
@click.pass_context
def get_by_entity(ctx, entity, task_type, name, project):
    """Get a task by entity (UUID, or asset name with --project), task type, and name."""
    require_auth(ctx)
    tt = resolve_task_type(task_type)
    if not is_uuid(entity):
        entity = resolve_asset(entity, project)
    result = gazu.task.get_task_by_entity(entity, tt, name=name)
    output(result, ctx)


@group.command("batch-assign")
@click.option("--person", required=True, help="Person UUID or email.")
@click.argument("tasks", nargs=-1, required=True, metavar="TASK_UUID...")
@click.pass_context
def batch_assign(ctx, person, tasks):
    """Assign multiple tasks to a person."""
    require_auth(ctx)
    # gazu <= 1.3.1 calls data/tasks/assign, a route that Zou does not have.
    person_id = resolve_person(person)["id"]
    result = gazu.client.put(f"actions/persons/{person_id}/assign", {"task_ids": list(tasks)})
    output(result, ctx)


@group.command("clear-assignations")
@click.argument("tasks", nargs=-1, required=True, metavar="TASK_UUID...")
@click.option("--person", help="Person UUID or email.")
@click.pass_context
def clear_assignations(ctx, tasks, person):
    """Clear assignations on tasks."""
    require_auth(ctx)
    kwargs = {}
    if person:
        kwargs["person"] = resolve_person(person)
    result = gazu.task.clear_assignations(list(tasks), **kwargs)
    output(result, ctx)


@group.command("create-tasks")
@click.argument("entity", metavar="ENTITY_UUID")
@click.option("--task-type", "task_types", multiple=True, required=True, help="Task type UUID or name (repeatable).")
@click.option("--entity-type", "entity_type", required=True, type=click.Choice(["shot", "asset", "entity"]), help="Entity type to pick the right creation function.")
@click.pass_context
def create_tasks(ctx, entity, task_types, entity_type):
    """Create tasks on an entity (batch by type)."""
    require_auth(ctx)
    tt_list = [resolve_task_type(tt) for tt in task_types]
    if entity_type == "shot":
        result = gazu.task.create_shot_tasks(entity, tt_list)
    else:
        # gazu <= 1.3.1 posts asset tasks to data/assets/<id>/tasks, which is
        # GET only. Zou creates the tasks of any entity on this route.
        result = gazu.client.post(
            f"data/entities/{entity}/tasks", {"task_type_ids": [tt["id"] for tt in tt_list]}
        )
    output(result, ctx)


@group.command("batch-delete")
@click.argument("tasks", nargs=-1, required=True, metavar="TASK_UUID...")
@click.pass_context
def batch_delete(ctx, tasks):
    """Delete multiple tasks at once."""
    require_auth(ctx)
    gazu.task.remove_tasks_batch(list(tasks))
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted {len(tasks)} task(s).")


@group.command("batch-status")
@click.argument("tasks", nargs=-1, required=True, metavar="TASK_UUID...")
@click.option("--status", "task_status", required=True, help="Target task status UUID or name/short-name.")
@click.option("--message", "-m", "comment_text", default="", help="Comment to add with the status change.")
@click.option("--person", help="Author person UUID or email.")
@click.pass_context
def batch_status(ctx, tasks, task_status, comment_text, person):
    """Change the status of multiple tasks at once."""
    require_auth(ctx)
    ts = resolve_task_status(task_status)
    kwargs = {"comment": comment_text}
    if person:
        kwargs["person"] = resolve_person(person)
    results = []
    for task_id in tasks:
        result = gazu.task.add_comment(task_id, ts, **kwargs)
        results.append(result)
    if not ctx.obj.get("quiet"):
        click.echo(f"Updated {len(tasks)} task(s) to '{ts.get('name', task_status)}'.", err=True)
    output(results, ctx)


@group.command("batch-priority")
@click.argument("tasks", nargs=-1, required=True, metavar="TASK_UUID...")
@click.option("--priority", required=True, type=click.Choice(["0", "1", "2", "3"]), help="Priority level (0=normal, 1=high, 2=very high, 3=emergency).")
@click.pass_context
def batch_priority(ctx, tasks, priority):
    """Set priority on multiple tasks at once."""
    require_auth(ctx)
    priority_int = int(priority)
    results = []
    for task_id in tasks:
        t = gazu.task.get_task(task_id)
        t["priority"] = priority_int
        result = gazu.task.update_task(t)
        results.append(result)
    if not ctx.obj.get("quiet"):
        labels = {0: "normal", 1: "high", 2: "very high", 3: "emergency"}
        click.echo(f"Set {len(tasks)} task(s) to priority '{labels[priority_int]}'.", err=True)
    output(results, ctx)


# --- Comment sub-group ---


@group.group("comment")
def comment_group():
    """Manage task comments."""
    pass


@comment_group.command("list")
@click.argument("task")
@click.pass_context
def comment_list(ctx, task):
    """List comments for a task."""
    require_auth(ctx)
    results = gazu.task.all_comments_for_task(task)
    output(results, ctx)


@comment_group.command("get")
@click.argument("comment_id")
@click.pass_context
def comment_get(ctx, comment_id):
    """Get a comment by UUID."""
    require_auth(ctx)
    result = gazu.task.get_comment(comment_id)
    output(result, ctx)


@comment_group.command("add")
@click.argument("task")
@click.option("--status", "task_status", required=True, help="Task status UUID or name/short-name.")
@click.option("--message", "-m", "comment_text", default="", help="Comment text.")
@click.option("--person", help="Author person UUID or email.")
@click.option("--attachment", "attachments", multiple=True, type=click.Path(exists=True), help="File to attach (repeatable).")
@click.pass_context
def comment_add(ctx, task, task_status, comment_text, person, attachments):
    """Add a comment to a task."""
    require_auth(ctx)
    ts = resolve_task_status(task_status)
    kwargs = {"comment": comment_text}
    if person:
        kwargs["person"] = resolve_person(person)
    if attachments:
        kwargs["attachments"] = list(attachments)
    result = gazu.task.add_comment(task, ts, **kwargs)
    output(result, ctx)


@comment_group.command("delete")
@click.argument("comment_id")
@click.pass_context
def comment_delete(ctx, comment_id):
    """Delete a comment."""
    require_auth(ctx)
    gazu.task.remove_comment(comment_id)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted comment {comment_id}.")


@comment_group.command("reply")
@click.argument("comment_id")
@click.option("--text", "-m", required=True, help="Reply text.")
@click.option("--person", help="Author person UUID or email.")
@click.pass_context
def comment_reply(ctx, comment_id, text, person):
    """Reply to a comment."""
    require_auth(ctx)
    kwargs = {"text": text}
    if person:
        kwargs["person"] = resolve_person(person)
    result = gazu.task.reply_to_comment(comment_id, **kwargs)
    output(result, ctx)


@comment_group.command("acknowledge")
@click.argument("task")
@click.argument("comment_id")
@click.pass_context
def comment_acknowledge(ctx, task, comment_id):
    """Acknowledge a comment."""
    require_auth(ctx)
    result = gazu.task.acknowledge_comment(task, comment_id)
    output(result, ctx)


@comment_group.command("update")
@click.argument("comment_id")
@click.option("--text", "-m", required=True, help="New comment text.")
@click.pass_context
def comment_update(ctx, comment_id, text):
    """Update a comment."""
    require_auth(ctx)
    result = gazu.task.update_comment(comment_id, text=text)
    output(result, ctx)


@comment_group.command("last")
@click.argument("task")
@click.pass_context
def comment_last(ctx, task):
    """Get the last comment for a task."""
    require_auth(ctx)
    result = gazu.task.get_last_comment_for_task(task)
    output(result, ctx)


@comment_group.command("add-attachment")
@click.argument("task")
@click.argument("comment_id")
@click.option("--file", "file_paths", multiple=True, required=True, type=click.Path(exists=True), help="File to attach (repeatable).")
@click.pass_context
def comment_add_attachment(ctx, task, comment_id, file_paths):
    """Add attachment files to a comment."""
    require_auth(ctx)
    result = gazu.task.add_attachment_files_to_comment(task, comment_id, list(file_paths))
    output(result, ctx)


@comment_group.command("delete-attachment")
@click.argument("comment_id")
@click.argument("attachment_file")
@click.pass_context
def comment_delete_attachment(ctx, comment_id, attachment_file):
    """Delete an attachment from a comment."""
    require_auth(ctx)
    gazu.task.delete_comment_attachment(comment_id, attachment_file)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted attachment {attachment_file} from comment {comment_id}.")


@comment_group.command("delete-reply")
@click.argument("comment_id")
@click.argument("reply")
@click.pass_context
def comment_delete_reply(ctx, comment_id, reply):
    """Delete a reply from a comment."""
    require_auth(ctx)
    gazu.task.delete_comment_reply(comment_id, reply)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted reply {reply} from comment {comment_id}.")


# --- Preview sub-group ---


@group.group("preview")
def preview_group():
    """Manage task previews."""
    pass


@preview_group.command("list")
@click.argument("task")
@click.pass_context
def preview_list(ctx, task):
    """List preview files for a task."""
    require_auth(ctx)
    results = gazu.task.all_previews_for_task(task)
    output(results, ctx)


@preview_group.command("add")
@click.argument("task")
@click.argument("comment_id")
@click.option("--file", "file_path", type=click.Path(exists=True), help="Preview file to upload.")
@click.option("--url", "file_url", help="Preview file URL.")
@click.option("--revision", type=int, default=None)
@click.pass_context
def preview_add(ctx, task, comment_id, file_path, file_url, revision):
    """Add a preview to a task comment."""
    require_auth(ctx)
    kwargs = {}
    if file_path:
        kwargs["preview_file_path"] = file_path
    if file_url:
        kwargs["preview_file_url"] = file_url
    if revision is not None:
        kwargs["revision"] = revision
    result = gazu.task.add_preview(task, comment_id, **kwargs)
    output(result, ctx)


@preview_group.command("publish")
@click.argument("task")
@click.option("--status", "task_status", required=True, help="Task status UUID or name.")
@click.option("--message", "-m", "comment_text", default="", help="Comment text.")
@click.option("--file", "file_path", type=click.Path(exists=True), help="Preview file.")
@click.option("--url", "file_url", help="Preview file URL.")
@click.option("--set-thumbnail", is_flag=True)
@click.option("--person", help="Author person UUID or email.")
@click.pass_context
def preview_publish(ctx, task, task_status, comment_text, file_path, file_url, set_thumbnail, person):
    """Publish a preview (comment + preview in one step)."""
    require_auth(ctx)
    ts = resolve_task_status(task_status)
    kwargs = {"comment": comment_text, "set_thumbnail": set_thumbnail}
    if file_path:
        kwargs["preview_file_path"] = file_path
    if file_url:
        kwargs["preview_file_url"] = file_url
    if person:
        kwargs["person"] = resolve_person(person)
    comment_result, preview_result = gazu.task.publish_preview(task, ts, **kwargs)
    output({"comment": comment_result, "preview": preview_result}, ctx)


@preview_group.command("tokens")
@click.argument("preview_file")
@click.option("--in", "token_in", type=click.IntRange(min=0), required=True, help="Input tokens to add.")
@click.option("--out", "token_out", type=click.IntRange(min=0), required=True, help="Output tokens to add.")
@click.pass_context
def preview_tokens(ctx, preview_file, token_in, token_out):
    """Add token counts to a preview, and to the data of its entity.

    The entity keeps the sum of the counts of its previews.
    """
    require_auth(ctx)
    preview = gazu.client.get(f"data/preview-files/{preview_file}")
    counts = {
        "token_in": (preview.get("token_in") or 0) + token_in,
        "token_out": (preview.get("token_out") or 0) + token_out,
    }
    gazu.client.put(f"data/preview-files/{preview_file}", counts)

    task = gazu.client.get(f"data/tasks/{preview['task_id']}")
    entity = gazu.client.get(f"data/entities/{task['entity_id']}")
    data = dict(entity.get("data") or {})
    data["token_in"] = (data.get("token_in") or 0) + token_in
    data["token_out"] = (data.get("token_out") or 0) + token_out
    gazu.client.put(f"data/entities/{task['entity_id']}", {"data": data})

    output(
        {
            "preview": counts,
            "entity": {"token_in": data["token_in"], "token_out": data["token_out"]},
        },
        ctx,
    )


@preview_group.command("set-main")
@click.argument("preview_file")
@click.option("--frame", type=int, default=None, help="Frame number.")
@click.pass_context
def preview_set_main(ctx, preview_file, frame):
    """Set a preview as main preview."""
    require_auth(ctx)
    kwargs = {}
    if frame is not None:
        kwargs["frame_number"] = frame
    result = gazu.task.set_main_preview(preview_file, **kwargs)
    output(result, ctx)


@preview_group.command("upload")
@click.argument("preview_file")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def preview_upload(ctx, preview_file, file_path):
    """Upload a file to an existing preview."""
    require_auth(ctx)
    result = gazu.task.upload_preview_file(preview_file, file_path)
    output(result, ctx)


# --- Time sub-group ---


@group.group("time")
def time_group():
    """Manage time tracking."""
    pass


@time_group.command("get")
@click.argument("task")
@click.option("--date", default=None, help="Date (YYYY-MM-DD).")
@click.pass_context
def time_get(ctx, task, date):
    """Get time spent on a task."""
    require_auth(ctx)
    result = gazu.task.get_time_spent(task, date=date)
    output(result, ctx)


@time_group.command("set")
@click.argument("task")
@click.option("--person", required=True, help="Person UUID or email.")
@click.option("--date", required=True, help="Date (YYYY-MM-DD).")
@click.option("--duration", required=True, type=int, help="Duration in minutes.")
@click.pass_context
def time_set(ctx, task, person, date, duration):
    """Set time spent on a task."""
    require_auth(ctx)
    result = gazu.task.set_time_spent(task, resolve_person(person), date, duration)
    output(result, ctx)


@time_group.command("add")
@click.argument("task")
@click.option("--person", required=True, help="Person UUID or email.")
@click.option("--date", required=True, help="Date (YYYY-MM-DD).")
@click.option("--duration", required=True, type=int, help="Duration in minutes.")
@click.pass_context
def time_add(ctx, task, person, date, duration):
    """Add time spent on a task."""
    require_auth(ctx)
    result = gazu.task.add_time_spent(task, resolve_person(person), date, duration)
    output(result, ctx)


@time_group.command("delete")
@click.argument("time_spent")
@click.pass_context
def time_delete(ctx, time_spent):
    """Delete a time spent entry."""
    require_auth(ctx)
    gazu.task.remove_time_spent(time_spent)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted time spent {time_spent}.")


@time_group.command("get-for-date")
@click.argument("task")
@click.option("--date", required=True, help="Date (YYYY-MM-DD).")
@click.pass_context
def time_get_for_date(ctx, task, date):
    """Get time spent on a task for a specific date."""
    require_auth(ctx)
    result = gazu.task.get_task_time_spent_for_date(task, date)
    output(result, ctx)


# --- Task Type sub-group ---


@group.group("type")
def type_group():
    """Manage task types."""
    pass


@type_group.command("list")
@click.option("--project", help="Project UUID or name.")
@click.pass_context
def type_list(ctx, project):
    """List task types."""
    require_auth(ctx)
    if project:
        results = gazu.task.all_task_types_for_project(resolve_project(project))
    else:
        results = gazu.task.all_task_types()
    output(results, ctx)


@type_group.command("get")
@click.argument("task_type")
@click.pass_context
def type_get(ctx, task_type):
    """Get a task type by UUID or name."""
    require_auth(ctx)
    result = resolve_task_type(task_type)
    output(result, ctx)


@type_group.command("create")
@click.argument("name")
@click.option("--color", default="#000000")
@click.option("--for-entity", default="Asset", type=click.Choice(["Asset", "Shot", "Sequence", "Episode", "Edit"]))
@click.pass_context
def type_create(ctx, name, color, for_entity):
    """Create a new task type."""
    require_auth(ctx)
    result = gazu.task.new_task_type(name, color=color, for_entity=for_entity)
    output(result, ctx)


@type_group.command("update")
@click.argument("task_type")
@click.option("--name", help="New name.")
@click.option("--color", help="New hex color code.")
@click.option("--department", help="Department name or UUID.")
@click.pass_context
def type_update(ctx, task_type, name, color, department):
    """Update a task type."""
    require_auth(ctx)
    tt = resolve_task_type(task_type)
    if name:
        tt["name"] = name
    if color:
        tt["color"] = color
    if department:
        dept = resolve_department(department)
        tt["department_id"] = dept["id"]
    result = gazu.task.update_task_type(tt)
    output(result, ctx)


@type_group.command("delete")
@click.argument("task_type")
@click.pass_context
def type_delete(ctx, task_type):
    """Delete a task type."""
    require_auth(ctx)
    tt = resolve_task_type(task_type)
    gazu.task.remove_task_type(tt)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted task type {tt.get('name', task_type)}.")


# --- Task Status sub-group ---


@group.group("status")
def status_group():
    """Manage task statuses."""
    pass


@status_group.command("list")
@click.option("--project", help="Project UUID or name.")
@click.pass_context
def status_list(ctx, project):
    """List task statuses."""
    require_auth(ctx)
    if project:
        results = gazu.task.all_task_statuses_for_project(resolve_project(project))
    else:
        results = gazu.task.all_task_statuses()
    output(results, ctx)


@status_group.command("get")
@click.argument("task_status")
@click.pass_context
def status_get(ctx, task_status):
    """Get a task status by UUID or name."""
    require_auth(ctx)
    result = resolve_task_status(task_status)
    output(result, ctx)


@status_group.command("create")
@click.argument("name")
@click.option("--short-name", required=True)
@click.option("--color", required=True, help="Hex color code.")
@click.pass_context
def status_create(ctx, name, short_name, color):
    """Create a new task status."""
    require_auth(ctx)
    result = gazu.task.new_task_status(name, short_name, color)
    output(result, ctx)


@status_group.command("update")
@click.argument("task_status")
@click.option("--name", help="New name.")
@click.option("--color", help="New hex color code.")
@click.pass_context
def status_update(ctx, task_status, name, color):
    """Update a task status."""
    require_auth(ctx)
    ts = resolve_task_status(task_status)
    kwargs = {}
    if name:
        kwargs["name"] = name
    if color:
        kwargs["color"] = color
    result = gazu.task.update_task_status(ts, **kwargs)
    output(result, ctx)


@status_group.command("default")
@click.pass_context
def status_default(ctx):
    """Get the default task status."""
    require_auth(ctx)
    result = gazu.task.get_default_task_status()
    output(result, ctx)


@status_group.command("delete")
@click.argument("task_status")
@click.pass_context
def status_delete(ctx, task_status):
    """Delete a task status."""
    require_auth(ctx)
    ts = resolve_task_status(task_status)
    gazu.task.remove_task_status(ts)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted task status {ts.get('name', task_status)}.")
