from pathlib import Path

import pytest

from happy_migrations.sqlite_backend import (
    SQLiteBackend,
    _mig_name_parser,
    MIGRATION_FILE_TEMPLATE
)

ZERO_MIG_FNAME = "0000_jedi_sith_rogue_tables"
ONE_MIG_FNAME = "0001_separatist_table"

ZERO_MIG_NAME = "jedi_sith_rogue_tables"
ONE_MIG_NAME = "separatist_table"

GET_STATUS = """
    SELECT status
    FROM _happy_status
"""

GET_ZERO_MIG_TABLE_NAMES = """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name IN ('jedi', 'sith', 'rogue');
"""


@pytest.fixture
def db() -> SQLiteBackend:
    mig_dir = Path(__file__).parent.resolve() / "migrations"
    print(mig_dir)
    db_path = ":memory:"
    db = SQLiteBackend(db_path=db_path, mig_dir=mig_dir)
    db.happy_init()
    return db


@pytest.fixture
def db_temp(tmp_path) -> SQLiteBackend:
    db = SQLiteBackend(db_path=":memory:", mig_dir=tmp_path)
    db.happy_init()
    return db


def test_mig_incorrect_name():
    assert _mig_name_parser("Mar^&*io") == "mar___io"


def test_mig_parser(tmp_path):
    db = SQLiteBackend(db_path=":memory:", mig_dir=tmp_path)
    db.happy_init()
    db.create_mig("mar_io")
    res = db._parse_mig(tmp_path / "0000_mar_io.py")
    query_body = "\n\n    "
    query = res.steps[0]
    assert query.forward == query_body
    assert query.backward == query_body


def test_is_singleton(db, db_temp):
    assert db is db_temp
    assert db._connection is db_temp._connection


def test_happy_init(db):
    res = db._fetchall("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='_happy_log' OR name='_happy_status';
    """)
    assert res == [('_happy_status',), ('_happy_log',)]


def test_are_separated():
    mig_dir = Path().resolve().parent / "migrations"
    db_path = ":memory:"
    db = SQLiteBackend(db_path=db_path, mig_dir=mig_dir)
    res = db._fetchall("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='_happy_log' OR name='_happy_status';
    """)
    assert res == []


def test_get_mig_status_exist(db):
    db._add_mig_to_happy_status(mig_id=0, mig_name="mario")
    res = db._get_mig_status("0000_mario")[:-1]
    assert res == (0, 'mario', '0000_mario', 'Pending 🟡')


def test_get_mig_status_not_exist(db):
    db._add_mig_to_happy_status(mig_id=0, mig_name="mario")
    res = db._get_mig_status("0000_luigi")
    assert res is None


def test_create_mig(db_temp):
    db_temp._create_mig_file("mario", 0)
    assert len(tuple(db_temp._mig_dir.glob("0000_mario.py"))) == 1


def test_curren_revision_no_mig(db):
    assert db._get_current_revision_id() == -1


def test_current_revision_one_mig(db_temp):
    db_temp.create_mig("mario")
    assert db_temp._get_current_revision_id() == 0


def test_create_mig_file(db_temp):
    db_temp._create_mig_file(mig_name="mario", mig_id=0)
    with open(db_temp._mig_dir / "0000_mario.py", "r") as file:
        assert file.read() == MIGRATION_FILE_TEMPLATE


def test_add_mig_happy_status(db):
    db._add_mig_to_happy_status(mig_id=0, mig_name="mario")
    query = """
        SELECT mig_fname, status
        FROM _happy_status
        WHERE mig_id = 0
    """
    res = db._fetchone(query)
    assert res == ('0000_mario', 'Pending 🟡')


def test_get_pending_migs_names(db):
    db._add_mig_to_happy_status(mig_id=0, mig_name="mario")
    db._add_mig_to_happy_status(mig_id=1, mig_name="luigi")
    res = tuple(db._get_pending_migs_names())
    assert res == ('0000_mario', '0001_luigi')


def test_exec_all_forward_steps(db):
    mig_path = db._mig_dir / (ZERO_MIG_FNAME + ".py")
    db._add_mig_to_happy_status(0, "jedi_sith_rogue_tables")
    mig = db._parse_mig(mig_path)
    db._exec_all_forward_steps(mig)
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name IN ('jedi', 'sith', 'rogue');
    """
    res = db._fetchall(query)
    assert res == [('jedi',), ('sith',), ('rogue',)]


def test_change_happy_status(db):
    db._add_mig_to_happy_status(mig_id=0, mig_name="mario")
    name = "mario"
    db._change_happy_status(name, "A")
    query = """
        SELECT status
        FROM _happy_status
        WHERE mig_name = :mig_name
    """
    res = db._fetchall(query, {"mig_name": name})
    assert res == [("Applied 🟢",)]
    db._change_happy_status(name, "P")
    res = db._fetchall(query, {"mig_name": name})
    assert res == [("Pending 🟡",)]


def test__get_mig_path(db_temp):
    mig_dir = db_temp._mig_dir
    mig_name = "mario"
    res = db_temp._get_mig_path(mig_name)
    assert res == mig_dir / (mig_name + ".py")


def test_apply_mig_from_name(db):
    db._add_mig_to_happy_status(0, "jedi_sith_rogue_tables")
    db._apply_mig_from_name(ZERO_MIG_FNAME)
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name IN ('jedi', 'sith', 'rogue');
    """
    res = db._fetchall(query)
    assert res == [('jedi',), ('sith',), ('rogue',)]


def test_apply_all_migs(db):
    db._add_mig_to_happy_status(0, ZERO_MIG_NAME)
    db._add_mig_to_happy_status(1, ONE_MIG_NAME)
    db._apply_all_migs()
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name IN ('jedi', 'sith', 'rogue', 'separatist');
    """
    res = db._fetchall(query)
    assert res == [('jedi',), ('sith',), ('rogue',), ('separatist',)]


# TODO: Refactor SQL

def test_get_all_migs_up_to_pending(db):
    db._add_mig_to_happy_status(0, ZERO_MIG_NAME)
    db._add_mig_to_happy_status(1, ONE_MIG_NAME)
    res = tuple(db._get_all_migs_names_up_to(max_id=0, status="P", order="ASC"))
    assert res == ('0000_jedi_sith_rogue_tables',)


def test_get_all_migs_up_to_applied(db):
    for id, mig_name in enumerate((ZERO_MIG_NAME, ONE_MIG_NAME)):
        db._add_mig_to_happy_status(id, mig_name)
        db._change_happy_status(mig_name, "A")

    res = tuple(db._get_all_migs_names_up_to(max_id=0, status="A", order="DESC"))
    assert res == ('0001_separatist_table', '0000_jedi_sith_rogue_tables')


@pytest.mark.parametrize(
    ("up_to", "result"),
    (
        (0, [('Applied 🟢',), ('Pending 🟡',)]),
        (1, [('Applied 🟢',), ('Applied 🟢',)])
    )
)
def test_apply_migs_up_to_0(db, up_to, result):
    db._add_mig_to_happy_status(0, ZERO_MIG_NAME)
    db._add_mig_to_happy_status(1, ONE_MIG_NAME)
    db._apply_migs_up_to(up_to)
    query = """
        SELECT status
        FROM _happy_status
    """
    res = db._fetchall(query)
    assert res == result


@pytest.mark.parametrize(
    ("up_to", "result"),
    (
            (0, [('Pending 🟡',), ('Pending 🟡',)]),
            (1, [('Applied 🟢',), ('Pending 🟡',)])
    )
)
def test_rollback_migs_up_to(db, up_to, result):
    db._add_mig_to_happy_status(0, ZERO_MIG_NAME)
    db._add_mig_to_happy_status(1, ONE_MIG_NAME)
    db._apply_all_migs()
    db._rollback_migs_up_to(up_to)
    query = """
        SELECT status
        FROM _happy_status
    """
    res = db._fetchall(query)
    assert res == result


def test_rollback_mig_true(db):
    db._add_mig_to_happy_status(0, ZERO_MIG_NAME)
    db._apply_all_migs()
    assert db._fetchall(GET_STATUS) == [('Applied 🟢',)]
    assert db._rollback_last_mig()
    res = db._fetchall(GET_STATUS)
    assert res == [('Pending 🟡',)]


def test_rollback_mig_false(db):
    assert not db._rollback_last_mig()


def test_exec_all_backward_steps(db):
    mig_path = db._mig_dir / (ZERO_MIG_FNAME + ".py")
    db._add_mig_to_happy_status(0, "jedi_sith_rogue_tables")
    mig = db._parse_mig(mig_path)
    db._exec_all_forward_steps(mig)
    db._exec_all_backward_steps(mig)
    res = db._fetchall(GET_ZERO_MIG_TABLE_NAMES)
    assert res == []
