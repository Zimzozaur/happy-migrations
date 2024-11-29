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
    """,
)

alter_jedi = Step(
    forward="""
    ALTER TABLE jedi
    ADD COLUMN new_column TEXT NOT NULL DEFAULT 'default_value';
    """,
    backward="""
    """,
)


__steps__: tuple[Step, ...] = (alter_jedi,)
