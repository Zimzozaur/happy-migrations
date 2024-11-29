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

__steps__: tuple[Step, ...] = jedi_table, rogue_table
