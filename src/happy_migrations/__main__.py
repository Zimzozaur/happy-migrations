from pathlib import Path

import click
from click import echo, style

from happy_migrations import (
    SQLiteBackend,
    parse_happy_ini,
    create_happy_ini
)
from happy_migrations._textual_app import StatusApp


@click.group()
def happy() -> None:
    """Happy CLI."""
    pass


@click.command()
def config():
    """Create happy.ini file inside CWD."""
    message = "Happy.ini already exist."
    path = Path().cwd() / "happy.ini"

    if create_happy_ini(path):
        echo(style("Warning: ", "yellow") + message)
    else:
        echo(style("Created: ", "green") + str(path))


@click.command()
def init() -> None:
    """Initializes the Happy migrations."""
    db = SQLiteBackend(parse_happy_ini())
    db.happy_init()
    db.close_connection()


@click.command()
@click.argument("migration_name")
def cmig(migration_name: str) -> None:
    """Create migration."""
    db = SQLiteBackend(parse_happy_ini())
    db.create_mig(mig_name=migration_name)
    db.close_connection()


@click.command()
def log() -> None:
    """Display _happy_log table."""
    pass


@click.command()
def status() -> None:
    """Display _happy_status table."""
    db = SQLiteBackend(parse_happy_ini())
    StatusApp(
        headers=["Name", "Status", "Creation Date"],
        rows=db.list_happy_status()
    ).run(inline=True, inline_no_clear=True)
    db.close_connection()


@click.command()
def fixture():
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
    db = SQLiteBackend(parse_happy_ini())
    for _ in range(10**3):
        db.create_mig(quotes[randint(0, 9)])
    db.close_connection()


happy.add_command(init)
happy.add_command(cmig)
happy.add_command(config)
happy.add_command(log)
happy.add_command(status)
happy.add_command(fixture)
