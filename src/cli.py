"""CLI entry point for CareerOS.

Thin wrapper over the service layer — all business logic lives in service.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from src.db import CareerDB
from src.service import AmbiguousIDError, CareerService, NotFoundError, ServiceError


@click.group()
@click.option(
    "--db",
    type=click.Path(),
    default=None,
    help="Path to SQLite database (default: ~/.careeros/career.db)",
)
@click.pass_context
def cli(ctx: click.Context, db: str | None) -> None:
    """CareerOS — Extract career data from AI conversations."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = db


def _get_service(ctx: click.Context) -> tuple[CareerService, CareerDB]:
    db_path = ctx.obj.get("db_path")
    db = CareerDB(db_path) if db_path else CareerDB()
    return CareerService(db), db


# ── Import command ──


@cli.command("import")
@click.argument("file", type=click.Path(exists=True))
@click.option("--skip-extract", is_flag=True, help="Import only, skip LLM extraction")
@click.pass_context
def import_cmd(ctx: click.Context, file: str, skip_extract: bool) -> None:
    """Import a ChatGPT or Claude conversation export."""
    svc, db = _get_service(ctx)
    try:
        result = svc.import_file(file, skip_extract=skip_extract)

        click.echo(
            f"Found {result.total_conversations} conversations ({result.source} format)"
        )
        if result.skipped_conversations:
            click.echo(
                f"Skipping {result.skipped_conversations} already-imported conversations"
            )
        click.echo(f"Imported {result.new_conversations} conversations")

        if not result.extracted:
            if skip_extract:
                click.echo("Skipping extraction (--skip-extract)")
            return

        click.echo(
            f"\nDone! {result.work_conversations}/{result.new_conversations} "
            f"conversations were work-relevant"
        )
        click.echo(f"  Projects:     {result.projects_extracted}")
        click.echo(f"  Skills:       {result.skills_extracted}")
        click.echo(f"  Achievements: {result.achievements_extracted}")

    except ServiceError as e:
        raise click.ClickException(str(e))
    finally:
        db.close()


# ── Show commands ──


@cli.group("show")
def show() -> None:
    """Display extracted career data."""


@show.command("projects")
@click.pass_context
def show_projects(ctx: click.Context) -> None:
    """List all extracted projects."""
    svc, db = _get_service(ctx)
    try:
        projects = svc.get_projects()
        if not projects:
            click.echo("No projects found. Run 'careeros import' first.")
            return

        for p in projects:
            role_info = ""
            if p.get("role_title"):
                role_info = f" [{p['role_title']}"
                if p.get("role_company"):
                    role_info += f" @ {p['role_company']}"
                role_info += "]"
            dates = ""
            if p.get("started_at"):
                dates = f" ({p['started_at']}"
                if p.get("ended_at"):
                    dates += f" → {p['ended_at']}"
                dates += ")"

            click.echo(f"  {p['id'][:8]}  {p['name']}{role_info}{dates}")
            if p.get("summary"):
                click.echo(f"           {p['summary']}")
    finally:
        db.close()


@show.command("skills")
@click.pass_context
def show_skills(ctx: click.Context) -> None:
    """List all extracted skills."""
    svc, db = _get_service(ctx)
    try:
        skills = svc.get_skills()
        if not skills:
            click.echo("No skills found. Run 'careeros import' first.")
            return

        by_category: dict[str, list[str]] = {}
        for s in skills:
            by_category.setdefault(s["category"], []).append(s["name"])

        for category, names in sorted(by_category.items()):
            click.echo(f"  {category}: {', '.join(names)}")
    finally:
        db.close()


@show.command("achievements")
@click.pass_context
def show_achievements(ctx: click.Context) -> None:
    """List all extracted achievements."""
    svc, db = _get_service(ctx)
    try:
        achievements = svc.get_achievements()
        if not achievements:
            click.echo("No achievements found. Run 'careeros import' first.")
            return

        for a in achievements:
            impact = f" ({a['impact']})" if a.get("impact") else ""
            date = f" [{a['achieved_at']}]" if a.get("achieved_at") else ""
            click.echo(f"  {a['id'][:8]}  {a['summary']}{impact}{date}")
    finally:
        db.close()


@show.command("roles")
@click.pass_context
def show_roles(ctx: click.Context) -> None:
    """List all roles with linked projects."""
    svc, db = _get_service(ctx)
    try:
        roles = svc.get_roles()
        if not roles:
            click.echo("No roles found. Use 'careeros add role' to add one.")
            return

        for r in roles:
            company = f" @ {r['company']}" if r.get("company") else ""
            dates = ""
            if r.get("started_at"):
                dates = f" ({r['started_at']}"
                if r.get("ended_at"):
                    dates += f" → {r['ended_at']}"
                else:
                    dates += " → present"
                dates += ")"

            click.echo(f"  {r['id'][:8]}  {r['title']}{company}{dates}")
            for p in r.get("projects", []):
                click.echo(f"           └─ {p['name']}: {p.get('summary', '')}")
    finally:
        db.close()


# ── Add command ──


@cli.group("add")
def add() -> None:
    """Manually add career data."""


@add.command("role")
@click.option("--title", required=True, help="Role title")
@click.option("--company", default=None, help="Company name")
@click.option("--start", default=None, help="Start date (YYYY-MM)")
@click.option("--end", default=None, help="End date (YYYY-MM)")
@click.pass_context
def add_role(
    ctx: click.Context,
    title: str,
    company: str | None,
    start: str | None,
    end: str | None,
) -> None:
    """Add a role (job title + company)."""
    svc, db = _get_service(ctx)
    try:
        role = svc.add_role(title=title, company=company, started_at=start, ended_at=end)
        company_str = f" @ {company}" if company else ""
        click.echo(f"Added role: {title}{company_str} (id: {role.id[:8]})")
    finally:
        db.close()


# ── Link command ──


@cli.group("link")
def link() -> None:
    """Link entities together."""


@link.command("project")
@click.argument("project_id")
@click.option("--role", "role_id", required=True, help="Role ID to link to")
@click.pass_context
def link_project(ctx: click.Context, project_id: str, role_id: str) -> None:
    """Link a project to a role."""
    svc, db = _get_service(ctx)
    try:
        result = svc.link_project_to_role(project_id, role_id)
        click.echo(f"Linked '{result.project_name}' → '{result.role_title}'")
    except AmbiguousIDError as e:
        click.echo(str(e) + ". Matches:")
        for m in e.matches:
            label = m.get("name") or m.get("title")
            click.echo(f"  {m['id'][:8]}  {label}")
    except NotFoundError as e:
        click.echo(str(e))
    finally:
        db.close()


# ── Export command ──


@cli.command("export")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def export_cmd(ctx: click.Context, as_json: bool) -> None:
    """Export all career data."""
    svc, db = _get_service(ctx)
    try:
        data = svc.export_all()
        if as_json:
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            click.echo(f"Projects:     {len(data['projects'])}")
            click.echo(f"Skills:       {len(data['skills'])}")
            click.echo(f"Achievements: {len(data['achievements'])}")
            click.echo(f"Roles:        {len(data['roles'])}")
            click.echo("\nUse --json for full export.")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
