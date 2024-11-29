from pathlib import Path
from time import sleep

import click

from happy_migrations._data_classes import HappyMsg, HappyIni
from happy_migrations._echo_msg import echo_msg
from happy_migrations._sql import CREATE_HAPPY_STATUS_TABLE
from happy_migrations.sqlite_backend import SQLiteBackend

_file_1 = """\
\"\"\"
Migration: "A New Table"

This is the demo you're looking for! 🛠️

- jedi_table: Creates a table where you can store legendary Jedi like Obi-Wan Kenobi or Luminara Unduli.
- rogue_table: Creates a table to store daring rogues like Cassian Andor or Han Solo.

Use this migration to showcase your database Jedi skills! 🌌
\"\"\"

from happy_migrations import Step

jedi_table = Step(
    forward=\"\"\"
    CREATE TABLE jedi (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    \"\"\",
    backward=\"\"\"
    DROP TABLE jedi;
    \"\"\"
)

rogue_table = Step(
    forward=\"\"\"
    CREATE TABLE rogue (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    \"\"\",
    backward=\"\"\"
    DROP TABLE rogue;
    \"\"\"
)

__steps__: tuple[Step, ...] = jedi_table, rogue_table\n
"""

_file_2 = """\
\"\"\"
Migration: "The Dark Side and The Separatists"

This migration creates tables for those who walk on the dark side of the galaxy! 🌌

- `separatist_table`: Creates a table to store separatist leaders like Count Dooku or General Grievous.
- `sith_table`: Creates a table to store Sith Lords like Darth Vader or Darth Maul.
- **Backward**: Drops these tables faster than a TIE fighter closing in on a Rebel.

Use this migration to demonstrate your control over both the Separatists and the Sith! ⚔️
\"\"\"

from happy_migrations import Step

separatist_table = Step(
    forward=\"\"\"
    CREATE TABLE separatist (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    \"\"\",
    backward=\"\"\"
    DROP TABLE separatist;
    \"\"\"
)

sith_table = Step(
    forward=\"\"\"
    CREATE TABLE sith (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    \"\"\",
    backward=\"\"\"
    DROP TABLE sith;
    \"\"\"
)

__steps__: tuple[Step, ...] = separatist_table, sith_table
"""

_files = _file_1, _file_2
_names = ["0001_jedi_rogue_tables.py", "0002_separatist_sith_tables.py"]
_migs_dir = Path("./demo_happy_migrations/")
_ini = Path("happy.ini")
_db = Path("demo_happy.db")
_theme = "tokyo-night"


_happy_ini = """\
[Settings]
db_path = ./demo_happy.db
migs_dir = ./demo_happy_migrations
theme = tokyo-night
"""


@click.group()
def demo():
    """CLI entry point to try out Happy."""


@demo.command()
def run():
    """Sets up everything needed for testing."""
    if not _migs_dir.exists():
        _migs_dir.mkdir()
        for name, file in zip(_names, _files):
            with open(_migs_dir / name, "w") as f:
                f.write(file)
        echo_msg(
            HappyMsg(
                status="success",
                header="Success: ",
                message="Created Migration folder with migrations.",
            )
        )
        sleep(2)
    if not _ini.exists():
        with open(_ini, "w") as f:
            f.write(_happy_ini)
        echo_msg(
            HappyMsg(
                status="warning",
                header="Created ini: ",
                message="Don't forget to update in production!",
            )
        )
        sleep(2)
    if not _db.exists():
        _backend = SQLiteBackend(
            HappyIni(db_path=_db, migs_dir=_migs_dir, theme=_theme)
        )
        sleep(5)
        _backend._execute(CREATE_HAPPY_STATUS_TABLE)
        echo_msg(
            HappyMsg(
                status="error",
                header="Just Kidding 😅: ",
                message="This time DB was setup successfully.",
            )
        )
        sleep(3)
    echo_msg(
        HappyMsg(
            status="info",
            header="Ahoy Hoy! 🎉 ",
            message="Now you are ready to run `happy up` 🔥",
        )
    )
