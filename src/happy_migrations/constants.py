import re

MIGRATION_FILE_FORMAT = re.compile(r'^(\d{4})_([a-zA-Z0-9_]+)\.py$')

TEST_MIGRATION_FILE_TEMPLATE = """\
\"\"\"
Document your migration
\"\"\"

from happy_migrations import Query

first_step = Query(
    forward=\"\"\"
    CREATE TABLE jedi (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    );
    \"\"\",
    backward=\"\"\"
    DROP TABLE jedi;
    \"\"\"
)

__queries__: tuple = first_step,
"""

MIGRATION_FILE_TEMPLATE = """\
\"\"\"
Document your migration
\"\"\"

from happy_migrations import Query

first_step = Query(
    forward=\"\"\"

    \"\"\",
    backward=\"\"\"

    \"\"\"
)

__queries__: tuple = first_step,
"""


CREATE_HAPPY_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS _happy_status (
    id_migrations_status integer primary key autoincrement,
    migration_id integer,
    migration_name varchar(255),
    full_name varchar(255),
    applied integer,
    created TIMESTAMP NOT NULL DEFAULT current_timestamp
);
"""

ADD_HAPPY_STATUS = """
INSERT INTO _happy_status (migration_id, migration_name, full_name, applied)
VALUES (?, ?, ?, ?)
"""

CREATE_HAPPY_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS _happy_log (
    id_happy_log integer primary key autoincrement,
    migration_id integer,
    operation varchar(255),
    username varchar(255),
    hostname varchar(255),
    created TIMESTAMP NOT NULL DEFAULT current_timestamp
);
"""

GET_CURRENT_REVISION = """
SELECT migration_id
FROM _happy_status
ORDER BY migration_id DESC
LIMIT 1
"""

GET_PENDING_MIGRATIONS = """
SELECT full_name
FROM _happy_status
WHERE applied = ?
ORDER BY migration_id
"""

GET_MIGRATIONS_UP_TO = """
SELECT full_name
FROM _happy_status
WHERE migration_id {operator} ? AND applied = ?
ORDER BY migration_id {order_direction}
"""

UPDATE_HAPPY_STATUS = """
UPDATE _happy_status
SET applied = ?
WHERE full_name = ?
"""

GET_LAST_APPLIED = """
SELECT full_name
FROM _happy_status
WHERE applied = ?
ORDER BY migration_id DESC
LIMIT 1
"""

HAPPY_STATUS = {
    "A": "Applied 🟢",
    "P": "Pending 🟡",
}

INI_TEMPLATE = """\
[HAPPY]
db_path = path\\to\\db
"""
