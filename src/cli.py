"""CLI entry point for CareerOS."""

from __future__ import annotations

import json
from pathlib import Path

import click

from src.db import CareerDB
from src.extractor import extract_from_conversations
from src.importers.chatgpt import import_chatgpt
from src.importers.claude import import_claude
from src.models import Role


def _detect_and_import(path: Path) -> tuple[str, list]:
    """Detect export format and import conversations."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        raise click.ClickException(f"Expected non-empty JSON array in {path}")

    first = data[0]

    # ChatGPT exports have "mapping" dicts
    if "mapping" in first:
        return "chatgpt", import_chatgpt(path)

    # Claude exports have "chat_messages" or "uuid"
    if "chat_messages" in first or "uuid" in first:
        return "claude", import_claude(path)

    raise click.ClickException(
        f"Could not detect export format. Expected ChatGPT or Claude export."
    )


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


def _get_db(ctx: click.Context) -> CareerDB:
    db_path = ctx.obj.get("db_path")
    if db_path:
        return CareerDB(db_path)
    return CareerDB()


# ── Import command ──


@cli.command("import")
@click.argument("file", type=click.Path(exists=True))
@click.option("--skip-extract", is_flag=True, help="Import only, skip LLM extraction")
@click.pass_context
def import_cmd(ctx: click.Context, file: str, skip_extract: bool) -> None:
    """Import a ChatGPT or Claude conversation export."""
    path = Path(file)
    db = _get_db(ctx)

    try:
        click.echo(f"Detecting format for {path.name}...")
        source, conversations = _detect_and_import(path)
        click.echo(f"Found {len(conversations)} conversations ({source} format)")

        # Filter out already-imported conversations
        new_convs = []
        skipped = 0
        for conv in conversations:
            if db.conversation_exists(conv.id, conv.source):
                skipped += 1
            else:
                new_convs.append(conv)

        if skipped:
            click.echo(f"Skipping {skipped} already-imported conversations")

        if not new_convs:
            click.echo("No new conversations to import.")
            return

        # Store conversations
        for conv in new_convs:
            db.insert_conversation(conv, raw_path=str(path.resolve()))

        click.echo(f"Imported {len(new_convs)} conversations")

        if skip_extract:
            click.echo("Skipping extraction (--skip-extract)")
            return

        # Extract career data
        click.echo("Extracting career data (this may take a moment)...")
        results = extract_from_conversations(new_convs)

        work_count = 0
        total_projects = 0
        total_skills = 0
        total_achievements = 0

        for conv_id, result in results:
            db.store_extraction(conv_id, result)
            if result.is_work:
                work_count += 1
                total_projects += len(result.projects)
                total_skills += len(result.skills)
                total_achievements += len(result.achievements)

        click.echo(
            f"\nDone! {work_count}/{len(new_convs)} conversations were work-relevant"
        )
        click.echo(f"  Projects:     {total_projects}")
        click.echo(f"  Skills:       {total_skills}")
        click.echo(f"  Achievements: {total_achievements}")

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
    db = _get_db(ctx)
    try:
        projects = db.get_projects()
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
    db = _get_db(ctx)
    try:
        skills = db.get_skills()
        if not skills:
            click.echo("No skills found. Run 'careeros import' first.")
            return

        # Group by category
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
    db = _get_db(ctx)
    try:
        achievements = db.get_achievements()
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
    db = _get_db(ctx)
    try:
        roles = db.get_roles()
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
    db = _get_db(ctx)
    try:
        role = Role(title=title, company=company, started_at=start, ended_at=end)
        db.insert_role(role)
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
    db = _get_db(ctx)
    try:
        # Support short IDs — find full ID by prefix
        project = db.get_project_by_id(project_id)
        if not project:
            # Try prefix match
            rows = db.conn.execute(
                "SELECT id, name FROM projects WHERE id LIKE ?",
                (f"{project_id}%",),
            ).fetchall()
            if len(rows) == 1:
                project_id = rows[0]["id"]
                project = {"name": rows[0]["name"]}
            elif len(rows) > 1:
                click.echo(f"Ambiguous project ID '{project_id}'. Matches:")
                for r in rows:
                    click.echo(f"  {r['id'][:8]}  {r['name']}")
                return
            else:
                click.echo(f"Project '{project_id}' not found.")
                return

        role = db.get_role_by_id(role_id)
        if not role:
            # Try prefix match
            rows = db.conn.execute(
                "SELECT id, title FROM roles WHERE id LIKE ?",
                (f"{role_id}%",),
            ).fetchall()
            if len(rows) == 1:
                role_id = rows[0]["id"]
                role = {"title": rows[0]["title"]}
            elif len(rows) > 1:
                click.echo(f"Ambiguous role ID '{role_id}'. Matches:")
                for r in rows:
                    click.echo(f"  {r['id'][:8]}  {r['title']}")
                return
            else:
                click.echo(f"Role '{role_id}' not found.")
                return

        db.link_project_to_role(project_id, role_id)
        click.echo(
            f"Linked '{project['name']}' → '{role['title']}'"
        )
    finally:
        db.close()


# ── Export command ──


@cli.command("export")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def export_cmd(ctx: click.Context, as_json: bool) -> None:
    """Export all career data."""
    db = _get_db(ctx)
    try:
        data = db.export_all()
        if as_json:
            click.echo(json.dumps(data, indent=2, default=str))
        else:
            # Summary output
            click.echo(f"Projects:     {len(data['projects'])}")
            click.echo(f"Skills:       {len(data['skills'])}")
            click.echo(f"Achievements: {len(data['achievements'])}")
            click.echo(f"Roles:        {len(data['roles'])}")
            click.echo("\nUse --json for full export.")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
