import importlib.util
from pathlib import Path
from sqlite3 import connect, Connection, Cursor
from typing import Callable, Generator, Literal
from itertools import zip_longest

from happy_migrations import MigrationSQL
from happy_migrations._data_classes import HappyIni, MigData, HappyMsg
from happy_migrations._sql import (
    CREATE_HAPPY_STATUS_TABLE,
    HAPPY_STATUS_EXIST,
    GET_LAST_APPLIED_ID,
    ADD_HAPPY_STATUS,
    REMOVE_HAPPY_STATUS,
    LIST_HAPPY_STATUS,
)
from happy_migrations._templates import MIGRATION_FILE_TEMPLATE
from happy_migrations._utils import mig_name_parser

MIG_IS_NOT_TUPLE = "__steps__ is not a tuple inside migration: "

HAPPY_STATUS: dict[int, str] = {
    1: "Applied 🟢",
    0: "Pending 🟡",
}

MigDirection = Literal["up", "down"]


def _no_mig_to(direction: MigDirection) -> HappyMsg:
    """Create a warning message when no migrations are available
    to apply or roll back.
    """
    action = "apply" if direction == "up" else "roll back"
    return HappyMsg(
        status="warning", header="Warning: ", message=f"No migration to {action}."
    )


def _migration_done(mig_data: MigData, direction: MigDirection) -> HappyMsg:
    """Create a success message for a completed migration."""
    action = "Applied" if direction == "up" else "Rolled back"
    return HappyMsg(
        status="success", header=f"{action}: ", message=f"{mig_data.full_name}"
    )


def _all_migs_have_been(direction: MigDirection) -> HappyMsg:
    """Create an informational message when all migrations have been processed."""
    action = "applied" if direction == "up" else "rolled back"
    return HappyMsg(
        status="info", header=f"All migrations have been {action}!", message=""
    )


def _changed_up_to(direction: MigDirection, mig_id: int) -> HappyMsg:
    """Create an informational message for migrations processed up to a specific ID."""
    action = "Applied" if direction == "up" else "Rolled back"
    return HappyMsg(
        status="info", header=f"{action} all migrations up to {mig_id}.", message=""
    )


def _parse_mig(mig_path: Path) -> MigrationSQL:
    """Parses a migration file and returns a `Migration` object."""
    spec = importlib.util.spec_from_file_location(mig_path.name, mig_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    queries = getattr(module, "__steps__")
    if not isinstance(queries, tuple):
        raise ValueError(MIG_IS_NOT_TUPLE + mig_path.name)
    return MigrationSQL(steps=queries)


class SQLiteBackend:
    """
    Only `_apply_mig()`, `_rollback_mig()`, `happy_init()` commit change.
    """

    def __init__(self, happy: HappyIni) -> None:
        self._config = happy
        self._migs_dir = happy.migs_dir
        self._db_path = happy.db_path
        self._connection: Connection = connect(self._db_path)
        self.theme = happy.theme

    def happy_boot(self, callback: Callable[[HappyMsg], None]) -> None:
        """Initializes Happy and applies all migrations.
        Required during app startup to integrate Happy into the app.
        """
        # TODO: Write test
        self.happy_init()
        self.up_all(callback)
        self.close_connection()

    def happy_init(self) -> HappyMsg:
        """Initializes the Happy migration system by verifying the migrations
        dir exist and create necessary tables if needed.
        """
        if not self._migs_dir.exists() or not self._fetchone(HAPPY_STATUS_EXIST):
            self._migs_dir.mkdir(parents=True, exist_ok=True)
            self._execute(CREATE_HAPPY_STATUS_TABLE)
            self._commit()
            return HappyMsg(
                status="success",
                header="Initialized: ",
                message="Hopefully no tears 🤗",
            )
        return HappyMsg(
            status="warning",
            header="Don't worry: ",
            message="Happy already initialized ☺️",
        )

    def create_mig(self, mig_name: str) -> HappyMsg:
        """Create new migration file."""
        mig_name = mig_name_parser(mig_name)
        mig_id: int = self._get_latest_mig_id() + 1
        file_name = f"{mig_id:04}_{mig_name}.py"
        path = self._migs_dir / file_name
        mig_data = MigData(path=path)
        self._create_mig_file(mig_data)
        return HappyMsg(
            status="success",
            header="Created: ",
            message=file_name,
        )

    def up(self) -> HappyMsg:
        """Apply the first available migration."""
        applied_id = self._fetchone(GET_LAST_APPLIED_ID)
        to_apply_path = self._get_mig_path_by_id(
            1 if not applied_id else applied_id[0] + 1
        )
        if not applied_id and not to_apply_path:
            return HappyMsg(
                status="error",
                header="Error: ",
                message=f"{self._migs_dir.resolve()} directory is empty.",
            )
        if not to_apply_path:
            return _no_mig_to("up")

        mig_data = MigData(path=to_apply_path)
        self._apply_mig(mig_data)
        return _migration_done(mig_data, "up")

    def up_all(self, callback: Callable[[HappyMsg], None]) -> None:
        """Apply all migrations until no further migrations are available."""
        msg = self.up()
        callback(msg)
        if msg.status in ["error", "warning"]:
            return

        while True:
            msg = self.up()
            if msg.status == "warning":
                break
            callback(msg)

        callback(_all_migs_have_been("up"))

    def up_to(self, mig_id: int, callback: Callable[[HappyMsg], None]) -> None:
        """Applies all pending migrations up to the specified migration ID."""
        total_migs = self._migs_qty
        total_applied = len(self._fetchall(LIST_HAPPY_STATUS))

        if total_applied == total_migs or total_applied == mig_id:
            callback(_no_mig_to("up"))
            return
        if mig_id <= total_migs:
            for _ in range(mig_id - total_applied):
                msg = self.up()
                callback(msg)
        else:
            while True:
                msg = self.up()
                if msg.status == "warning":
                    break
                callback(msg)
        last_id = mig_id if mig_id <= total_migs else total_migs
        callback(_changed_up_to("up", last_id))

    def down(self) -> HappyMsg:
        """Roll back the most recently applied migration.

        Returns:
            HappyMsg: An object representing the result of the rollback attempt.
                - "Warning" if no migrations are applied and nothing can be rolled back.
                - "Success" if the rollback is performed successfully.
        """
        applied_id = self._fetchone(GET_LAST_APPLIED_ID)
        if not applied_id:
            return _no_mig_to("down")
        path = self._get_mig_path_by_id(applied_id[0])
        mig_data = MigData(path=path)
        self._rollback_mig(mig_data)
        return _migration_done(mig_data, "down")

    def down_all(self, callback: Callable[[HappyMsg], None] | None = None) -> None:
        """Rollback all applied migrations up to the specified migration ID."""
        while True:
            msg = self.down()
            if msg.status == "warning":
                break
            callback(msg)
        callback(_all_migs_have_been("down"))

    def down_to(self, mig_id: int, callback: Callable[[HappyMsg], None]) -> None:
        """Roll back all applied migrations up to the specified migration ID."""
        total_applied = len(self._fetchall(LIST_HAPPY_STATUS))

        if mig_id > total_applied or total_applied == 0:
            callback(_no_mig_to("down"))
            return
        if mig_id > 0:
            for _ in range(abs(mig_id - total_applied) + 1):
                msg = self.down()
                callback(msg)
        else:
            while True:
                msg = self.down()
                if msg.status == "warning":
                    break
                callback(msg)

        last_id = mig_id if mig_id > 1 else 1
        callback(_changed_up_to("down", last_id))

    def list_happy_status(self) -> list[list[str]] | list[str]:
        """Generate a table showing the status of migrations."""
        migs = map(lambda p: MigData(p), self._migs_paths())
        applied = self._fetchall(LIST_HAPPY_STATUS)
        sorted_migs = sorted(migs, key=lambda mig: mig.id)
        if not sorted_migs:
            return [["Migrations directory is empty."]]

        zipped = zip_longest(sorted_migs, applied)
        migs_table: list[list[str | int]] = [
            ["ID", "Name", "Status"],
        ]

        transformed = [
            [mig.id, mig.name, "Applied 🟢" if status else "Pending 🟡"]
            for mig, status in zipped
        ]
        migs_table.extend(transformed)
        return migs_table

    def close_connection(self):
        """Close connection to DB."""
        self._connection.close()

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

    def _reconnect(self):
        """Reconnect connection to DB."""
        self._connection.close()
        self._connection = connect(self._db_path)

    @property
    def _migs_qty(self) -> int:
        """Return number of migrations inside migration directory"""
        return sum(1 for _ in self._migs_paths())

    def _migs_paths(self) -> Generator[Path, None, None]:
        """Retrieve paths to migration files."""
        return self._migs_dir.glob("????_*")

    def _get_mig_path_by_id(self, mig_id: id) -> Path | None:
        """Look for mig with chosen id."""
        res = tuple(self._migs_dir.glob(f"{mig_id:04}_*.py"))
        if not res:
            return None
        return res[0]

    def _get_latest_mig_id(self) -> int:
        """Retrieve the latest migration id from the migrations
        directory or return 0 if empty.
        """
        mig_paths: list[Path] | None = list(self._migs_paths())
        if not mig_paths:
            return 0
        max_id_path = max(mig_paths, key=lambda p: p.stem)
        return int(max_id_path.stem.split("_", maxsplit=1)[0])

    def _create_mig_file(self, mig_data: MigData) -> None:
        """Create new boilerplate migration file."""
        with open(self._migs_dir / mig_data.file_name, "w") as file:
            file.write(MIGRATION_FILE_TEMPLATE)

    def _add_mig_to_happy_status(self, mig_data: MigData) -> None:
        """Add migration to _happy_status."""
        params = {
            "mig_id": mig_data.id,
            "mig_name": mig_data.name,
        }
        self._connection.execute(ADD_HAPPY_STATUS, params)

    def _remove_mig_from_happy_status(self, mig_data: MigData) -> None:
        """Remove migrations from _happy_status."""
        params = {"mig_id": mig_data.id}
        self._connection.execute(REMOVE_HAPPY_STATUS, params)

    def _apply_mig(self, mig_data: MigData) -> None:
        """Apply a migration."""
        mig = _parse_mig(mig_data.path)
        self._exec_forward_steps(mig)
        self._add_mig_to_happy_status(mig_data)
        self._commit()

    def _rollback_mig(self, mig_data: MigData) -> None:
        """Roll back a migration."""
        mig = _parse_mig(mig_data.path)
        self._exec_backward_steps(mig)
        self._remove_mig_from_happy_status(mig_data)
        self._commit()

    def _exec_forward_steps(self, mig: MigrationSQL) -> None:
        """Execute every forward Query from a Migration."""
        for query in mig.steps:
            self._execute(query.forward)

    def _exec_backward_steps(self, mig: MigrationSQL) -> None:
        """Rolls back a migration by executing each backward SQL statement
        from the last Query to the first.
        """
        for query in mig.steps[::-1]:
            self._execute(query.backward)
