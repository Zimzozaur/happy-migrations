from functools import wraps
from pathlib import Path
from typing import cast

import click
from click import echo, style
from click import Group

from happy_migrations import SQLiteBackend, parse_happy_ini
from happy_migrations._data_classes import HappyMsg
from happy_migrations._echo_msg import echo_msg
from happy_migrations._textual_app import StatusApp
from happy_migrations._utils import create_happy_ini
from happy_migrations.cli import social, demo


def db_conn(func):
    """Decorator to handle SQLiteBackend connection setup and teardown."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        db = SQLiteBackend(parse_happy_ini())
        try:
            return func(db, *args, **kwargs)
        finally:
            db.close_connection()

    return wrapper


@click.group()
def happy() -> None:
    """Happy CLI."""
    pass


# Groups
happy.add_command(cast(Group, social))
happy.add_command(cast(Group, demo))


@happy.command()
def config():
    """Create happy.ini file inside CWD."""
    message = "Happy.ini already exist."
    path = Path().cwd() / "happy.ini"

    if create_happy_ini(path):
        echo(style("Warning: ", "yellow") + message)
    else:
        echo(style("Created: ", "green") + str(path))


@happy.command()
@db_conn
def init(db: SQLiteBackend) -> None:
    """Initializes the Happy migrations."""
    echo_msg(db.happy_init())


@happy.command()
@click.argument("migration_name")
@db_conn
def create(db: SQLiteBackend, migration_name: str) -> None:
    """Create migration file."""
    echo_msg(db.create_mig(mig_name=migration_name))


@happy.command()
@db_conn
def status(db: SQLiteBackend) -> None:
    """Display _happy_status table."""
    content = db.list_happy_status()
    if isinstance(content[0], str):
        headers = content[0]
        rows = []
    else:
        headers = content[0]
        rows = content[1:]
    StatusApp(headers=headers, rows=rows, theme=db.theme).run(
        inline=True, inline_no_clear=True
    )


@happy.command()
@click.option("--qty", default=10, type=int, help="Quantity of migrations")
@db_conn
def fixture(db: SQLiteBackend, qty: int):
    """Create 10 migrations with names based on 孫子 quotes."""
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
        "quickness_is_the_essence_of_war",
    ]
    for _ in range(qty):
        echo_msg(db.create_mig(quotes[randint(0, 9)]))
    echo_msg(
        HappyMsg(
            status="info",
            header="Done: ",
            message=f"Created {qty} migration{"" if qty == 1 else "s"}.",
        )
    )


@happy.command()
@db_conn
def up(db: SQLiteBackend):
    """Applies the next available migration."""
    echo_msg(db.up())


@happy.command()
@db_conn
def up_all(db: SQLiteBackend):
    """Applies all available migrations."""
    db.up_all(echo_msg)


@happy.command()
@db_conn
@click.argument("target", type=click.IntRange(min=0, max=1000))
def up_to(db: SQLiteBackend, target: int):
    """Applies migrations up to a specified target."""
    db.up_to(target, echo_msg)


@happy.command()
@db_conn
def down(db: SQLiteBackend):
    """Rolls back the most recent migration."""
    echo_msg(db.down())


@happy.command()
@db_conn
def down_all(db: SQLiteBackend):
    """Rolls back all applied migrations."""
    db.down_all(echo_msg)


@happy.command()
@db_conn
@click.argument("target", type=click.IntRange(min=0, max=1000))
def down_to(db: SQLiteBackend, target: int):
    """Rolls back migrations down to a specified target."""
    db.down_to(target, echo_msg)
