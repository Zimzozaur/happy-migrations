"""
Document your migration
"""

from happy_migrations import Step

separatist_table = Step(
    forward="""
    CREATE TABLE separatist (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    """,
    backward="""
    DROP TABLE separatist;
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


__steps__: tuple[Step, ...] = separatist_table, sith_table
