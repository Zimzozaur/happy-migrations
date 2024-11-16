import click
from click import echo, style

from happy_migrations import (
    SQLiteBackend,
    parse_happy_ini,
    create_happy_ini
)


class SQLiteBackendContext(click.Context):
    obj: SQLiteBackend


@click.group()
@click.pass_context
def happy(ctx) -> None:
    """A CLI tool for managing SQL migrations."""
    happy_ini = parse_happy_ini()
    ctx.obj = SQLiteBackend(happy_ini)


@click.command()
@click.pass_context
def init(ctx: SQLiteBackendContext) -> None:
    """Initializes the Happy migration system """
    ctx.obj.happy_init()
    ctx.obj.close_connection()


@click.command()
@click.argument("migration_name")
@click.pass_context
def cmig(ctx: SQLiteBackendContext, migration_name: str) -> None:
    """Create migration."""
    ctx.obj.create_mig(mig_name=migration_name)
    ctx.obj.close_connection()


@click.command()
def config():
    """Create happy.ini file in CWD."""
    message = "Happy.ini already exist."
    if create_happy_ini():
        echo(style("Warning: ", "yellow") + message)


happy.add_command(init)
happy.add_command(cmig)
happy.add_command(config)
