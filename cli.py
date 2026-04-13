# PATH: app/cli.py
import typer, os
from app.database import create_db_and_tables, get_cli_session, drop_all
from app.services.scraper_service import ScraperService
from app.repositories.event import EventRepository
from app.scraper.scheduler import run_all
from app.models.user import User
from app.utilities.security import encrypt_password

cli = typer.Typer(help="Caribbean Events Management CLI")

@cli.command()
def init_db():
    create_db_and_tables()
    typer.echo("Database tables created.")

@cli.command()
def reset_db(yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt"),):
    if not yes:
        typer.confirm("This will delete ALL data. Continue?", abort=True)
    with get_cli_session() as db:
        drop_all()
        create_db_and_tables()
    typer.echo("Database reset complete.")

@cli.command()
def create_admin(
    username: str = typer.Argument(..., help="Admin username"),
    email: str    = typer.Argument(..., help="Admin email"),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
):
    with get_cli_session() as db:
        user = User(
            username=username,
            email=email,
            password=encrypt_password(password),
            role="admin",
        )
        db.add(user)
        db.commit()
        
    typer.echo(f"Admin user '{username}' created.")

@cli.command()
def import_csv(
    path:    str  = typer.Argument(..., help="Path to CSV file"),
    publish: bool = typer.Option(False, "--publish", help="Auto-publish imported events"),
):
    if not os.path.exists(path):
        typer.echo(f"File not found: {path}", err=True)
        raise typer.Exit(1)

    with get_cli_session() as db:
        result = ScraperService(db).import_from_csv(path, auto_publish=publish)

    typer.echo(f"Created : {result['created']}")
    typer.echo(f"Skipped : {result['skipped']}")
    typer.echo(f"Errors  : {len(result['errors'])}")
    
    for err in result["errors"]:
        typer.echo(f"  {err}", err=True)

@cli.command()
def scrape(
    publish: bool = typer.Option(False, "--publish", help="Auto-publish scraped events"),
    only:    str  = typer.Option("", "--only", help="Run one scraper: ticketmaster, eventbrite, islandetickets, tjj, caribbeanevents"),
):
    run_all(auto_publish=publish, only=only)
    typer.echo("Scrape run complete.")

@cli.command()
def list_events(
    status: str = typer.Option("", help="Filter: draft / pending / published"),
    limit:  int = typer.Option(20, help="Max rows to show"),
):
    with get_cli_session() as db:
        repo   = EventRepository(db)
        events = repo.get_all_admin(limit=limit)
        if status:
            events = [e for e in events if e.status.value == status]

    if not events:
        typer.echo("No events found.")
        return
    for e in events:
        typer.echo(f"[{e.id:4}] {e.status.value:10} {e.island.value:20} {e.date.strftime('%d %b %Y')}  {e.title}")

if __name__ == "__main__":
    cli()