import click
from click import echo, style

from happy_migrations import (
    SQLiteBackend,
    parse_happy_ini,
    create_happy_ini
)
from happy_migrations._textual_app import StatusApp


class SQLiteBackendContext(click.Context):
    obj: SQLiteBackend


@click.group()
@click.pass_context
def happy(ctx) -> None:
    """Happy CLI."""
    happy_ini = parse_happy_ini()
    ctx.obj = SQLiteBackend(happy_ini)


@click.command()
@click.pass_context
def init(ctx: SQLiteBackendContext) -> None:
    """Initializes the Happy migration system."""
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


@click.command()
@click.pass_context
def log(ctx: SQLiteBackendContext) -> None:
    """Display _happy_log table."""


@click.command()
@click.pass_context
def status(ctx: SQLiteBackendContext) -> None:
    """Display _happy_status table."""
    status_data = ctx.obj.list_happy_status()
    StatusApp(
        headers=["Name", "Status", "Creation Date"],
        rows=status_data
    ).run(inline=True, inline_no_clear=True)


@click.command()
@click.pass_context
def fixture(ctx: SQLiteBackendContext):
    """Create 1000 migrations with names based on 孫子 quotes names."""
    from random import randint
    quotes = [
        "all_warfare_is_based_on_deception",
        "the_wise_warrior_avoids_the_battle",
        "in_the_midst_of_chaos_opportunity",
        "move_swift_as_the_wind",
        "strategy_without_tactics_is_slow",
        "let_your_plans_be_dark",
        "supreme_art_is_to_subdue",
        "opportunities_multiply_as_they_are_seized",
        "he_will_win_who_knows_when_to_fight",
        "quickness_is_the_essence_of_war"
    ]
    for _ in range(10**3):
        ctx.obj.create_mig(quotes[randint(0, 9)])


happy.add_command(init)
happy.add_command(cmig)
happy.add_command(config)
happy.add_command(log)
happy.add_command(status)
happy.add_command(fixture)
