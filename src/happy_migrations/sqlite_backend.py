import importlib.util
import re
from pathlib import Path
from sqlite3 import connect, DatabaseError, Connection, Cursor
from typing import Generator, Literal
import configparser

from happy_migrations import Migration
from happy_migrations._data_classes import HappyIni


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

__steps__: tuple = first_step,
"""

MIG_IS_NOT_TUPLE = "__steps__ is not a tuple inside migration: "


CREATE_HAPPY_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS _happy_status (
    id_mig_status integer primary key autoincrement,
    mig_id integer,
    mig_name varchar(255),
    mig_fname varchar(255),
    status varchar(255),
    created TIMESTAMP NOT NULL DEFAULT current_timestamp
);
"""

ADD_HAPPY_STATUS = """
INSERT INTO _happy_status (mig_id, mig_name, mig_fname, status)
VALUES (:mig_id, :mig_name, :mig_fname, :status)
"""

CREATE_HAPPY_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS _happy_log (
    id_happy_log integer primary key autoincrement,
    mig_id integer,
    operation varchar(255),
    username varchar(255),
    hostname varchar(255),
    created TIMESTAMP NOT NULL DEFAULT current_timestamp
);
"""

ADD_HAPPY_LOG = """
INSERT INTO _happy_log (mig_id, operation, username, hostname)
VALUES (:mig_id, :operation, :username, :hostname)
"""

GET_CURRENT_REVISION = """
SELECT mig_id
FROM _happy_status
ORDER BY mig_id DESC
LIMIT 1
"""

GET_PENDING_MIG = """
SELECT mig_fname
FROM _happy_status
WHERE status = :status
ORDER BY mig_id
"""

GET_MIGS_UP_TO = """
SELECT mig_fname
FROM _happy_status
WHERE mig_id {operator} ? AND status = ?
ORDER BY mig_id {order_direction}
"""

UPDATE_HAPPY_STATUS = """
UPDATE _happy_status
SET status = :status
WHERE mig_name = :mig_name
"""

GET_LAST_BY_STATUS = """
SELECT mig_fname
FROM _happy_status
WHERE status = ?
ORDER BY mig_id DESC
LIMIT 1
"""

LIST_HAPPY_STATUS = """
SELECT mig_id, mig_name, mig_fname, status, created
FROM _happy_status
"""

GET_HAPPY_STATUS_BY_FNAME = """
SELECT mig_id, mig_name, mig_fname, status, created
FROM _happy_status
WHERE mig_fname = :mig_fname
"""

LIST_HAPPY_LOG = """
SELECT mig_id, operation, username, hostname, created
FROM _happy_log
"""

HAPPY_STATUS = {
    "A": "Applied 🟢",
    "P": "Pending 🟡",
}

INI_TEMPLATE = """\
[HAPPY]
db_path = path\\to\\db
"""


class MigrationError(Exception):
    pass


def _mig_name_parser(string: str) -> str:
    """Converts a given string to a normalized migration name format."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', string).lower()


def parse_settings_ini() -> HappyIni:
    """Parse the 'happy.ini' configuration file
    and return a HappyIni dataclass instance.
    """
    config = configparser.ConfigParser()
    config.read('happy.ini')
    return HappyIni(db_path=config['Settings']['db_path'])


class SQLiteBackend:
    _instance = None

    def __new__(cls, *args, **kwargs) -> "SQLiteBackend":
        """Creates a new instance if one does not already exist; otherwise,
        returns the existing instance.
        Ensures the class follows the Singleton pattern.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_path: Path | str, mig_dir: Path | str) -> None:
        self._mig_dir = mig_dir
        self._db_path = db_path
        self._connection: Connection = connect(db_path)

    def _execute(self, query: str, params: dict | tuple = ()) -> Cursor:
        """Execute a SQL query with optional parameters and return a cursor."""
        return self._connection.execute(query, params)

    def _fetchone(self, query: str, params: dict | tuple = ()) -> tuple | None:
        """Execute a SQL query and fetches the first row of the result."""
        return self._execute(query=query, params=params).fetchone()

    def _fetchall(self, query: str, params: dict | tuple = ()) -> list:
        """Execute a SQL query and fetches all rows of the result."""
        return self._execute(query=query, params=params).fetchall()

    def _commit(self):
        """Commit the current transaction to the database."""
        self._connection.commit()

    def _get_mig_status(self, mig_fname: str) -> list | None:
        """Return mig status row if mig exist."""
        params = {"mig_fname": mig_fname}
        return self._fetchone(GET_HAPPY_STATUS_BY_FNAME, params)

    def _parse_mig(self, mig_path: Path) -> Migration:
        """Parses a migration file and returns a `Migration` object."""
        spec = importlib.util.spec_from_file_location(
            mig_path.name, mig_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        queries = getattr(module, "__steps__")
        if not isinstance(queries, tuple):
            raise ValueError(MIG_IS_NOT_TUPLE + mig_path.name)
        return Migration(*self._get_mig_status(mig_path.stem), steps=queries)

    def happy_init(self) -> None:
        """Initializes the Happy migration system by verifying the database exists
        and creating necessary tables if needed.
        """
        if not self._db_path == ":memory:" and not self._db_path.exists():
            raise DatabaseError(f"Database not found at: {self._db_path}")
        self._execute(CREATE_HAPPY_STATUS_TABLE)
        self._execute(CREATE_HAPPY_LOG_TABLE)
        self._connection.commit()

    def happy_boot(self) -> None:
        """Initializes Happy and applies all migrations.
        Required during app startup to integrate Happy into the app.
        """
        self.happy_init()
        self._apply_all_migs()

    def _get_current_revision_id(self) -> int:
        """Retrieves the latest migration revision id from the database
        or return -1 if empty.
        """
        row = self._fetchone(GET_CURRENT_REVISION)
        if not row:
            return -1
        return row[0]

    def create_mig(self, mig_name: str) -> None:
        """Create new migration."""
        mig_name = _mig_name_parser(mig_name)
        mig_id: int = self._get_current_revision_id() + 1
        self._create_mig_file(mig_name=mig_name, mig_id=mig_id)
        self._add_mig_to_happy_status(mig_id=mig_id, mig_name=mig_name)

    def _create_mig_file(self, mig_name: str, mig_id: int) -> None:
        """Create new boilerplate migration file."""
        name = f"{mig_id:04}_{mig_name}.py"
        with open(self._mig_dir / name, 'w') as file:
            file.write(MIGRATION_FILE_TEMPLATE)

    def _add_mig_to_happy_status(self, mig_id: int, mig_name: str) -> None:
        """Add new migration to db with status pending."""
        mig_fname = f"{mig_id:04}_{mig_name}"
        params = {
            "mig_id": mig_id,
            "mig_name": mig_name,
            "mig_fname": mig_fname,
            "status": HAPPY_STATUS['P'],
        }
        self._connection.execute(ADD_HAPPY_STATUS, params)
        self._commit()

    def _get_pending_migs_names(self) -> Generator[str, None, None]:
        """Return all pending migrations' names."""
        params = {"status": HAPPY_STATUS["P"]}
        names = self._fetchall(GET_PENDING_MIG, params)
        return (name[0] for name in names)

    def _exec_all_forward_steps(self, mig: Migration) -> None:
        """Execute every forward Query from a Migration."""
        for query in mig.steps:
            self._execute(query.forward)

    def _get_mig_path(self, mig_fname: str) -> Path:
        """Return full path to migration."""
        return self._mig_dir / (mig_fname + ".py")

    def _change_happy_status(self, mig_name: str, status: Literal["A", "P"]) -> None:
        """Updates the `applied` status of a specific migration
        in the `_happy_status` database table.
        """
        params = {"status": HAPPY_STATUS[status], "mig_name": mig_name}
        self._execute(UPDATE_HAPPY_STATUS, params)

    def _apply_mig_from_name(self, mig_fname: str) -> None:
        mig_path = self._get_mig_path(mig_fname)
        mig = self._parse_mig(mig_path)
        self._exec_all_forward_steps(mig)
        # TODO: Unify
        self._change_happy_status(mig_fname.split("_", maxsplit=1)[1], "A")
        self._commit()

    def _rollback_mig_from_name(self, mig_fname: str) -> None:
        mig_path = self._get_mig_path(mig_fname)
        mig = self._parse_mig(mig_path)
        self._exec_all_backward_steps(mig)
        self._change_happy_status(mig_fname.split('_', maxsplit=1)[1], "P")
        self._commit()

    def _apply_all_migs(self) -> None:
        mig_names = self._get_pending_migs_names()
        for mig_name in mig_names:
            self._apply_mig_from_name(mig_name)

    def _get_all_migs_names_up_to(
        self,
        max_id: int,
        status: Literal["A", "P"],
        order: Literal["ASC", "DESC"]
    ) -> list[str]:
        """Retrieves all pending migration names from
        the `_happy_status` table up to a specified migration ID.
        """
        if order == "ASC":
            operator = "<="
        else:
            operator = ">="

        query = GET_MIGS_UP_TO.format(
            operator=operator,
            order_direction=order
        )
        names = self._fetchall(
            query,
            (max_id, HAPPY_STATUS[status])
        )
        return [name[0] for name in names]

    def _apply_migs_up_to(self, max_id: int) -> None:
        """Applies all pending migrations up to the specified migration ID."""
        names = self._get_all_migs_names_up_to(max_id, "P", "ASC")
        for name in names:
            self._apply_mig_from_name(name)

    def _rollback_migs_up_to(self, max_id: int) -> None:
        """Roll back all applied migrations up to the specified migration ID."""
        fnames = self._get_all_migs_names_up_to(max_id, "A", "DESC")
        for fname in fnames:
            self._rollback_mig_from_name(fname)

    def _rollback_last_mig(self) -> bool:
        """Roll back the last applied migration and return True.
        If no migration is available to roll back return False.
        """
        name = self._fetchone(
            GET_LAST_BY_STATUS,
            (HAPPY_STATUS["A"],)
        )
        if name is None:
            return False
        mig_path = self._get_mig_path(name[0])
        mig = self._parse_mig(mig_path)
        self._exec_all_backward_steps(mig)
        self._change_happy_status(name[0].split("_", maxsplit=1)[1], "P")
        self._commit()
        return True

    def _exec_all_backward_steps(self, mig: Migration) -> None:
        """Rolls back a migration by executing each backward SQL statement
        from the last Query to the first.
        """
        for query in mig.steps[::-1]:
            self._execute(query.backward)

    def list_happy_logs(self) -> list:
        """Return list of all logs from _happy_log."""
        # TODO: Test when table is ok
        return self._fetchall(LIST_HAPPY_LOG)

    def list_happy_status(self) -> list:
        """Return list of all statuses from _happy_status."""
        # TODO: Test when table is ok
        return self._fetchall(LIST_HAPPY_STATUS)


if __name__ == "__main__":
    db = SQLiteBackend(
        db_path=":memory:",
        mig_dir=Path().resolve() / "migrations"
    )
