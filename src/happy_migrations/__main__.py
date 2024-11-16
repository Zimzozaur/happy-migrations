import click

from happy_migrations import SQLiteBackend, parse_happy_ini


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
    """Initialize the SQLite backend."""
    ctx.obj.happy_init()
    ctx.obj.close_connection()


@click.command()
@click.argument("migration_name")
@click.pass_context
def cmig(ctx: SQLiteBackendContext, migration_name: str) -> None:
    """Create migration."""
    ctx.obj.create_mig(mig_name=migration_name)
    ctx.obj.close_connection()


happy.add_command(init)
happy.add_command(cmig)
