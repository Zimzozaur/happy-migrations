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

__steps__: tuple = separatist_table,
