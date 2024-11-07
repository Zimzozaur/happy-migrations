"""
Document your migration
"""

from happy_migrations import Step

jedi_table = Step(
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

sith_table = Step(
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

rogue_table = Step(
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

__steps__: tuple = jedi_table, sith_table, rogue_table
