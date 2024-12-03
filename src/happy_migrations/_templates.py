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

_HAPPY_INI_TEMPLATE = """\
[Settings]
db_path =
migs_dir =
theme =
"""
