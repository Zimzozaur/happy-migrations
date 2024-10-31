import importlib.util
import re
from pathlib import Path
from sqlite3 import connect, DatabaseError, Connection
from typing import Generator, Literal
import configparser
from contextlib import contextmanager


from happy_migrations import Migration
from happy_migrations._data_classes import HappyIni
from happy_migrations.constants import (
    GET_CURRENT_REVISION,
    CREATE_HAPPY_STATUS_TABLE,
    ADD_HAPPY_STATUS,
    CREATE_HAPPY_LOG_TABLE,
    HAPPY_STATUS,
    GET_PENDING_MIGRATIONS,
    UPDATE_HAPPY_STATUS,
    TEST_MIGRATION_FILE_TEMPLATE,
    GET_MIGRATIONS_UP_TO,
    GET_LAST_APPLIED,
)


class MigrationError(Exception):
    pass


class SQLiteBackend:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    @contextmanager
    def connect(self) -> Connection:
        conn = connect(self.db_path)

        try:
            yield conn
        finally:
            conn.close()


def migration_name_parser(string: str) -> str:
    """Converts a given string to a normalized migration name format."""
    return re.sub(
        r'[^a-zA-Z0-9_]',
        '_',
        string
    ).lower()


def db_exist(db_path: Path) -> None:
    """Checks if the database file exists at the specified path."""
    if not db_path.exists():
        raise DatabaseError(f"Database not found at: {db_path}")


def create_happy_status_table(db_path: Path) -> None:
    """Create the `_happy_status` table in the specified database
    if it does not already exist.
    """
    with connect(db_path) as conn:
        conn.execute(CREATE_HAPPY_STATUS_TABLE)


def create_happy_log_table(db_path: Path) -> None:
    """Create the `_happy_log` table in the specified database
    if it does not already exist.
    """
    with connect(db_path) as conn:
        conn.execute(CREATE_HAPPY_LOG_TABLE)


def happy_init(db_path: Path) -> None:
    """Initializes the Happy migration system by verifying the database exists
    and creating necessary tables if needed.
    """
    db_exist(db_path)
    create_happy_status_table(db_path)
    create_happy_log_table(db_path)


def get_current_revision_id(db_path: Path) -> int:
    """Retrieves the latest migration revision id from the database
    or return -1 if empty.
    """
    with connect(db_path) as conn:
        row = conn.execute(GET_CURRENT_REVISION).fetchone()
        if not row:
            return -1
        return row[0]


def create_migration_file(mig_dir: Path, mig_name: str, mig_id: int) -> None:
    """Create new boilerplate migration file."""
    name = f"{mig_id:04}_{mig_name}.py"
    with open(mig_dir / name, 'w') as file:
        file.write(TEST_MIGRATION_FILE_TEMPLATE)


def add_migration_to_db(db_path: Path, mig_id: int, mig_name: str) -> None:
    """Add new migration to db with status pending."""
    full_name = f"{mig_id:04}_{mig_name}"
    with connect(db_path) as conn:
        conn.execute(
            ADD_HAPPY_STATUS,
            (mig_id, mig_name, full_name, HAPPY_STATUS['P'])
        )


def create_migration(mig_dir: Path, db_path: Path, migration_name: str) -> None:
    """Create new migration."""
    mig_name = migration_name_parser(migration_name)
    mig_id: int = get_current_revision_id(db_path) + 1
    create_migration_file(
        mig_dir=mig_dir,
        mig_name=mig_name,
        mig_id=mig_id,
    )
    add_migration_to_db(
        db_path=db_path,
        mig_id=mig_id,
        mig_name=mig_name,
    )


def get_pending_migrations(db_path: Path) -> Generator[str, None, None]:
    """Retrieves the names of pending migrations from the database."""
    with connect(db_path) as conn:
        names = conn.execute(
            GET_PENDING_MIGRATIONS,
            (HAPPY_STATUS["P"],)
        ).fetchall()
    return (name[0] for name in names)


def apply_all_forward_step_from_migration(mig: Migration, db_path: Path) -> None:
    """Execute every forward Query from a Migration."""
    with connect(db_path) as conn:
        for query in mig.queries:
            conn.execute(query.forward)


def get_mig_path(mig_dir: Path, mig_name: str) -> Path:
    """Return full path to migration."""
    return mig_dir / (mig_name + ".py")


def parse_migration(mig_path: Path, mig_name: str) -> Migration:
    """Parses a migration file and returns a `Migration` object."""
    key, name = mig_name.split('_')
    # Dynamically import the module to access `__queries__`
    spec = importlib.util.spec_from_file_location(name, mig_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    queries = getattr(module, "__queries__")
    if not isinstance(queries, tuple):
        raise ValueError(f"__queries__ is not a tuple inside migration: {mig_name}")
    return Migration(key=key, name=name, queries=queries)


def change_happy_status(
    mig_name: str,
    status: Literal["A", "P"],
    db_path: Path
) -> None:
    """Updates the `applied` status of a specific migration
    in the `_happy_status` database table.
    """
    with connect(db_path) as conn:
        conn.execute(
            UPDATE_HAPPY_STATUS,
            (HAPPY_STATUS[status], mig_name)
        )


def apply_migration_from_name(db_path: Path, mig_dir: Path, mig_name: str) -> None:
    mig_path = get_mig_path(mig_dir, mig_name)
    mig = parse_migration(mig_path, mig_name)
    apply_all_forward_step_from_migration(mig, db_path)
    change_happy_status(mig_name, "A", db_path)


def rollback_migration_from_name(db_path: Path, mig_dir: Path, mig_name: str) -> None:
    mig_path = get_mig_path(mig_dir, mig_name)
    mig = parse_migration(mig_path, mig_name)
    apply_all_backward_steps(mig, db_path)
    change_happy_status(mig_name, "P", db_path)


def apply_all_migrations(db_path: Path, mig_dir: Path):
    mig_names = get_pending_migrations(db_path)
    for mig_name in mig_names:
        apply_migration_from_name(db_path, mig_dir, mig_name)


def get_all_pending_up_to(
    max_id: int,
    status: Literal["A", "P"],
    order: Literal["ASC", "DESC"]
) -> Generator[str, None, None]:
    """Retrieves all pending migration names from
    the `_happy_status` table up to a specified migration ID.
    """
    if order == "ASC":
        operator = "<="
    else:
        operator = ">="

    query = GET_MIGRATIONS_UP_TO.format(
        operator=operator,
        order_direction=order
    )

    with connect(db_path) as conn:
        names = conn.execute(
            query,
            (max_id, HAPPY_STATUS[status])
        ).fetchall()
    return (name[0] for name in names)


def apply_migrations_up_to_chosen(max_id: int, db_path: Path, mig_dir: Path) -> None:
    """Applies all pending migrations up to the specified migration ID."""
    names = get_all_pending_up_to(max_id, "P", "ASC")
    for name in names:
        apply_migration_from_name(db_path, mig_dir, name)


def rollback_migration(db_path: Path, mig_dir: Path) -> None:
    """Rolls back the last applied migration. If no migration is available
    to roll back, logs a message indicating this.
    """
    with connect(db_path) as conn:
        name: tuple[str] | None = conn.execute(
            GET_LAST_APPLIED,
            (HAPPY_STATUS["A"],)
        ).fetchone()
        if name is None:
            print("No migration to roll back.")
        mig_path = get_mig_path(mig_dir, name[0])
        mig = parse_migration(mig_path, name[0])
        apply_all_backward_steps(mig, db_path)
        change_happy_status(name[0], "P", db_path)


def apply_all_backward_steps(mig: Migration, db_path: Path) -> None:
    """Rolls back a migration by executing each backward SQL statement
    from the last Query to the first.
    """
    with connect(db_path) as conn:
        for query in mig.queries[::-1]:
            conn.execute(query.backward)


def rollback_migrations_to_chosen(max_id: int, db_path: Path, mig_dir: Path) -> None:
    """Roll back all applied migrations up to the specified migration ID."""
    names = list(get_all_pending_up_to(max_id, "A", "DESC"))
    for name in names[::-1]:
        rollback_migration_from_name(db_path, mig_dir, name)


def list_happy_logs():
    pass


def list_happy_migrations():
    pass


def parse_settings_ini() -> HappyIni:
    """Parse the 'happy.ini' configuration file
    and return a HappyIni dataclass instance.
    """
    config = configparser.ConfigParser()
    config.read('happy.ini')
    return HappyIni(db_path=config['Settings']['db_path'])


def set_all_migrations_to_pending() -> None:
    UPDATE_ALL_PENDING = """
    UPDATE _happy_status
    SET applied = ?;
    """

    with connect(Path().resolve() / "happy.db") as conn:
        conn.execute(UPDATE_ALL_PENDING, (HAPPY_STATUS["P"],))


if __name__ == "__main__":
    mig_dir = Path().resolve().parent / "migrations"
    db_path = Path().resolve() / "happy.db"

    # happy_init(db_path)

    # create_migration(
    #     mig_dir=migrations,
    #     db_path=db_path,
    #     migration_name="mario"
    # )

    # set_all_migrations_to_pending()

    apply_migrations_up_to_chosen(0, db_path, mig_dir)
    # rollback_migration(db_path, mig_dir)

    import time
    time.sleep(5)

    rollback_migrations_to_chosen(0, db_path, mig_dir)

    # apply_all_migrations(db_path, mig_dir)
