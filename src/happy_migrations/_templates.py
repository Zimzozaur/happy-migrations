MIGRATION_FILE_TEMPLATE = """\
\"\"\"
Document your migration
\"\"\"

from happy_migrations import Step

first_step = Step(
    forward=\"\"\"

    \"\"\",
    backward=\"\"\"

    \"\"\"
)

__steps__: tuple[Step, ...] = first_step,
"""

INI_TEMPLATE = """\
[HAPPY]
db_path = path\\to\\db
"""
