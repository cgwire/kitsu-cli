"""Person and department commands."""

import click
import gazu

from kitsu_cli.client import require_auth
from kitsu_cli.output import output
from kitsu_cli.resolver import resolve_person


@click.group("person")
def group():
    """Manage people, departments, and organisations."""
    pass


@group.command("list")
@click.pass_context
def list_cmd(ctx):
    """List all persons."""
    require_auth(ctx)
    results = gazu.person.all_persons()
    output(results, ctx)


@group.command()
@click.argument("person")
@click.option("--relations", is_flag=True)
@click.pass_context
def get(ctx, person, relations):
    """Get a person by UUID, email, or full name."""
    require_auth(ctx)
    result = resolve_person(person)
    if relations:
        result = gazu.person.get_person(result["id"], relations=True)
    output(result, ctx)


@group.command()
@click.option("--first-name", required=True)
@click.option("--last-name", required=True)
@click.option("--email", required=True)
@click.option("--phone", default="")
@click.option("--role", default="user", type=click.Choice(["user", "admin", "manager", "client", "vendor"]))
@click.option("--desktop-login", default="")
@click.option("--department", "departments", multiple=True, help="Department UUID (repeatable).")
@click.option("--password", default=None, help="Initial password.")
@click.option("--active/--inactive", default=True)
@click.pass_context
def create(ctx, first_name, last_name, email, phone, role, desktop_login, departments, password, active):
    """Create a new person."""
    require_auth(ctx)
    kwargs = {}
    if departments:
        kwargs["departments"] = list(departments)
    if password:
        kwargs["password"] = password
    result = gazu.person.new_person(
        first_name, last_name, email,
        phone=phone, role=role, desktop_login=desktop_login,
        active=active, **kwargs
    )
    output(result, ctx)


@group.command()
@click.argument("person")
@click.option("--first-name", default=None)
@click.option("--last-name", default=None)
@click.option("--email", default=None)
@click.option("--phone", default=None)
@click.option("--role", default=None, type=click.Choice(["user", "admin", "manager", "client", "vendor"]))
@click.option("--active/--inactive", default=None)
@click.option("--current-password", default=None, help="Your password, to change your own email.")
@click.option("--totp", default=None, help="Your 2FA code, to change your own email.")
@click.pass_context
def update(ctx, person, first_name, last_name, email, phone, role, active, current_password, totp):
    """Update a person."""
    require_auth(ctx)
    # Send only the changed fields. Zou regenerates the token of a bot when
    # the body contains "expiration_date", even with the same value.
    p = {"id": resolve_person(person)["id"]}
    if first_name:
        p["first_name"] = first_name
    if last_name:
        p["last_name"] = last_name
    if email:
        p["email"] = email
    if phone is not None:
        p["phone"] = phone
    if role:
        p["role"] = role
    if active is not None:
        p["active"] = active
    if current_password:
        p["current_password"] = current_password
    if totp:
        p["totp"] = totp
    result = gazu.person.update_person(p)
    output(result, ctx)


@group.command()
@click.argument("person")
@click.option("--force", is_flag=True)
@click.pass_context
def delete(ctx, person, force):
    """Delete a person."""
    require_auth(ctx)
    p = resolve_person(person)
    gazu.person.remove_person(p, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted person {p.get('full_name', person)}.")


@group.command()
@click.argument("person")
@click.pass_context
def url(ctx, person):
    """Get the Kitsu URL for a person."""
    require_auth(ctx)
    p = resolve_person(person)
    click.echo(gazu.person.get_person_url(p))


@group.command("change-password")
@click.argument("person")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.pass_context
def change_password(ctx, person, password):
    """Change the password for a person."""
    require_auth(ctx)
    p = resolve_person(person)
    result = gazu.person.change_password_for_person(p, password)
    output(result, ctx)


@group.command("clear-avatar")
@click.argument("person")
@click.pass_context
def clear_avatar(ctx, person):
    """Clear a person's avatar."""
    require_auth(ctx)
    p = resolve_person(person)
    gazu.person.clear_person_avatar(p)
    if not ctx.obj.get("quiet"):
        click.echo(f"Avatar cleared for {p.get('full_name', person)}.")


@group.command()
@click.argument("person")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.pass_context
def set_avatar(ctx, person, file_path):
    """Set a person's avatar image."""
    require_auth(ctx)
    p = resolve_person(person)
    gazu.person.set_avatar(p, file_path)
    if not ctx.obj.get("quiet"):
        click.echo(f"Avatar set for {p.get('full_name', person)}.")


@group.command()
@click.argument("person")
@click.pass_context
def invite(ctx, person):
    """Send an invitation email to a person."""
    require_auth(ctx)
    p = resolve_person(person)
    result = gazu.person.invite_person(p)
    output(result, ctx)


@group.command()
@click.argument("person")
@click.option("--start", required=True, help="Start date (YYYY-MM-DD).")
@click.option("--end", required=True, help="End date (YYYY-MM-DD).")
@click.pass_context
def time_spents(ctx, person, start, end):
    """Get time spent by a person in a date range."""
    require_auth(ctx)
    p = resolve_person(person)
    result = gazu.person.get_time_spents_range(p["id"], start, end)
    output(result, ctx)


@group.command("time-spents-by-date")
@click.argument("person")
@click.option("--date", required=True, help="Date (YYYY-MM-DD).")
@click.pass_context
def time_spents_by_date(ctx, person, date):
    """Get time spents for a person on a specific date."""
    require_auth(ctx)
    p = resolve_person(person)
    result = gazu.person.get_time_spents_by_date(p, date)
    output(result, ctx)


@group.command("week-time-spents")
@click.argument("person")
@click.option("--year", required=True, type=int)
@click.option("--week", required=True, type=int)
@click.pass_context
def week_time_spents(ctx, person, year, week):
    """Get time spents for a person for a specific week."""
    require_auth(ctx)
    p = resolve_person(person)
    result = gazu.person.get_week_time_spents(p, year, week)
    output(result, ctx)


@group.command("year-time-spents")
@click.argument("person")
@click.option("--year", required=True, type=int)
@click.pass_context
def year_time_spents(ctx, person, year):
    """Get time spents for a person for a specific year."""
    require_auth(ctx)
    p = resolve_person(person)
    result = gazu.person.get_year_time_spents(p, year)
    output(result, ctx)


@group.command()
@click.argument("person")
@click.pass_context
def day_offs(ctx, person):
    """Get day offs for a person."""
    require_auth(ctx)
    p = resolve_person(person)
    results = gazu.person.get_day_offs(p)
    output(results, ctx)


@group.command("create-day-off")
@click.option("--date", required=True, help="Day off date (YYYY-MM-DD).")
@click.option("--end-date", default=None, help="End date for a range (YYYY-MM-DD).")
@click.option("--person", default=None, help="Person UUID, email, or name (admin only).")
@click.pass_context
def create_day_off(ctx, date, end_date, person):
    """Create a day off."""
    require_auth(ctx)
    body = {"date": date}
    if end_date is not None:
        body["end_date"] = end_date
    if person is not None:
        p = resolve_person(person)
        body["person_id"] = p["id"]
    result = gazu.client.post("data/day-offs", body)
    output(result, ctx)


@group.command("delete-day-off")
@click.argument("day_off")
@click.pass_context
def delete_day_off(ctx, day_off):
    """Delete a day off."""
    require_auth(ctx)
    gazu.client.delete(f"data/day-offs/{day_off}")
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted day off {day_off}.")


@group.command("month-timesheet")
@click.option("--year", required=True, type=int, help="Year.")
@click.option("--month", required=True, type=int, help="Month (1-12).")
@click.pass_context
def month_timesheet(ctx, year, month):
    """Get monthly timesheet table for all persons."""
    require_auth(ctx)
    result = gazu.client.get(
        f"data/persons/time-spents/month-table/{year}/{month}"
    )
    output(result, ctx)


@group.command("week-timesheet")
@click.option("--year", required=True, type=int, help="Year.")
@click.pass_context
def week_timesheet(ctx, year):
    """Get weekly timesheet table for all persons."""
    require_auth(ctx)
    result = gazu.client.get(f"data/persons/time-spents/week-table/{year}")
    output(result, ctx)


@group.command("day-timesheet")
@click.option("--year", required=True, type=int, help="Year.")
@click.option("--month", required=True, type=int, help="Month (1-12).")
@click.pass_context
def day_timesheet(ctx, year, month):
    """Get daily timesheet table for all persons."""
    require_auth(ctx)
    result = gazu.client.get(
        f"data/persons/time-spents/day-table/{year}/{month}"
    )
    output(result, ctx)


# --- Department sub-group ---


@group.group("department")
def department_group():
    """Manage departments."""
    pass


@department_group.command("list")
@click.pass_context
def department_list(ctx):
    """List all departments."""
    require_auth(ctx)
    results = gazu.person.all_departments()
    output(results, ctx)


@department_group.command("get")
@click.argument("department")
@click.pass_context
def department_get(ctx, department):
    """Get a department by UUID."""
    require_auth(ctx)
    result = gazu.person.get_department(department)
    output(result, ctx)


@department_group.command("create")
@click.argument("name")
@click.option("--color", default="")
@click.pass_context
def department_create(ctx, name, color):
    """Create a new department."""
    require_auth(ctx)
    result = gazu.person.new_department(name, color=color)
    output(result, ctx)


@department_group.command("update")
@click.argument("department")
@click.option("--name", default=None, help="New name.")
@click.option("--color", default=None, help="New color.")
@click.pass_context
def department_update(ctx, department, name, color):
    """Update a department."""
    require_auth(ctx)
    d = gazu.person.get_department(department)
    if name:
        d["name"] = name
    if color is not None:
        d["color"] = color
    result = gazu.person.update_department(d)
    output(result, ctx)


@department_group.command("add-to-department")
@click.argument("person")
@click.argument("department")
@click.pass_context
def department_add_person(ctx, person, department):
    """Add a person to a department."""
    require_auth(ctx)
    p = resolve_person(person)
    result = gazu.person.add_person_to_department(p, department)
    output(result, ctx)


@department_group.command("remove-from-department")
@click.argument("person")
@click.argument("department")
@click.pass_context
def department_remove_person(ctx, person, department):
    """Remove a person from a department."""
    require_auth(ctx)
    p = resolve_person(person)
    gazu.person.remove_person_from_department(p, department)
    if not ctx.obj.get("quiet"):
        click.echo(f"Removed {p.get('full_name', person)} from department.")


@department_group.command("delete")
@click.argument("department")
@click.option("--force", is_flag=True)
@click.pass_context
def department_delete(ctx, department, force):
    """Delete a department."""
    require_auth(ctx)
    d = gazu.person.get_department(department)
    gazu.person.remove_department(d, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted department {d.get('name', department)}.")


# --- Bot sub-group ---


@group.group("bot")
def bot_group():
    """Manage bots."""
    pass


@bot_group.command("create")
@click.argument("name")
@click.option("--email", required=True)
@click.option("--role", default="user", type=click.Choice(["user", "admin", "manager", "client", "vendor"]))
@click.option("--department", "departments", multiple=True, help="Department UUID (repeatable).")
@click.option("--active/--inactive", default=True)
@click.option("--expiration-date", default=None, help="Expiration date (YYYY-MM-DD).")
@click.pass_context
def bot_create(ctx, name, email, role, departments, active, expiration_date):
    """Create a new bot."""
    require_auth(ctx)
    kwargs = {}
    if departments:
        kwargs["departments"] = list(departments)
    if expiration_date:
        kwargs["expiration_date"] = expiration_date
    result = gazu.person.new_bot(name, email, role=role, active=active, **kwargs)
    output(result, ctx)


@bot_group.command("update")
@click.argument("bot")
@click.option("--first-name", default=None)
@click.option("--last-name", default=None)
@click.option("--email", default=None)
@click.option("--active/--inactive", default=None)
@click.pass_context
def bot_update(ctx, bot, first_name, last_name, email, active):
    """Update a bot."""
    require_auth(ctx)
    b = gazu.person.get_person(bot)
    if first_name:
        b["first_name"] = first_name
    if last_name:
        b["last_name"] = last_name
    if email:
        b["email"] = email
    if active is not None:
        b["active"] = active
    result = gazu.person.update_bot(b)
    output(result, ctx)


@bot_group.command("delete")
@click.argument("bot")
@click.option("--force", is_flag=True)
@click.pass_context
def bot_delete(ctx, bot, force):
    """Delete a bot."""
    require_auth(ctx)
    b = gazu.person.get_person(bot)
    gazu.person.remove_bot(b, force=force)
    if not ctx.obj.get("quiet"):
        click.echo(f"Deleted bot {b.get('full_name', bot)}.")


# --- Organisation sub-group ---


@group.group("organisation")
def organisation_group():
    """Manage organisations."""
    pass


@organisation_group.command("list")
@click.pass_context
def organisation_list(ctx):
    """List all organisations."""
    require_auth(ctx)
    results = gazu.person.all_organisations()
    output(results, ctx)


@organisation_group.command("get")
@click.pass_context
def organisation_get(ctx):
    """Get the current organisation."""
    require_auth(ctx)
    result = gazu.person.get_organisation()
    output(result, ctx)
