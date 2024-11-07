"""
Document your migration
"""

from happy_migrations import Query

jedi_table = Query(
    forward="""
    CREATE TABLE jedi (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    """,
    backward="""
    DROP TABLE jedi;
    """
)

sith_table = Query(
    forward="""
    CREATE TABLE sith (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    """,
    backward="""
    DROP TABLE sith;
    """
)

rogue_table = Query(
    forward="""
    CREATE TABLE rogue (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    """,
    backward="""
    DROP TABLE rogue;
    """
)

__queries__: tuple = jedi_table, sith_table, rogue_table
