"""
Document your migration
"""

from happy_migrations import Query

separatist_table = Query(
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

__queries__: tuple = separatist_table,
