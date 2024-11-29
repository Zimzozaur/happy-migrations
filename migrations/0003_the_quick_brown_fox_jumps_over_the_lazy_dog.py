"""
Document your migration
"""

from happy_migrations import Step

fox_table = Step(
    forward="""
    CREATE TABLE fox (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    """,
    backward="""
    DROP TABLE fox;
    """,
)

dog_table = Step(
    forward="""
    CREATE TABLE dog (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    """,
    backward="""
    DROP TABLE dog;
    """,
)

__steps__: tuple[Step, ...] = fox_table, dog_table
