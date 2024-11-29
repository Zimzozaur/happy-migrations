from pathlib import Path

import pytest

from happy_migrations._data_classes import MigData
from happy_migrations.sqlite_backend import (
    SQLiteBackend,
    MIGRATION_FILE_TEMPLATE,
    HappyIni, _parse_mig,
)

ZERO_MIG_FILE = "0001_jedi_rogue_tables.py"
ONE_MIG_FILE = "0002_separatist_sith_tables"

ZERO_MIG_NAME = "jedi_rogue_tables"
ONE_MIG_NAME = "separatist_sith_tables"


GET_ZERO_MIG_TABLE_NAMES = """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name IN ('jedi', 'sith', 'rogue');
"""


@pytest.fixture
def happy_ini_memo_temp(tmp_path):
    return HappyIni(
        db_path=":memory:",
        migs_dir=tmp_path,
        theme="tokyo-night"
    )


@pytest.fixture
def db() -> SQLiteBackend:
    migs_dir = Path(__file__).parent.resolve() / "migrations"
    db_path = ":memory:"
    db = SQLiteBackend(HappyIni(
        db_path=db_path,
        migs_dir=migs_dir,
        theme="tokyo-night"
    ))
    db.happy_init()
    return db


@pytest.fixture
def db_temp(happy_ini_memo_temp) -> SQLiteBackend:
    db = SQLiteBackend(happy_ini_memo_temp)
    db.happy_init()
    return db


def test_mig_parser(tmp_path, happy_ini_memo_temp):
    db = SQLiteBackend(happy_ini_memo_temp)
    db.happy_init()
    db.create_mig("mar_io")
    res = _parse_mig(tmp_path / "0001_mar_io.py")
    query_body = "\n\n    "
    query = res.steps[0]
    assert query.forward == query_body
    assert query.backward == query_body


def test_happy_init(db):
    res = db._fetchall("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='_happy_status';
    """)
    assert res == [('_happy_status',)]


# When I started testing app I found that DB is not separated.
# So I have 2 similar tests to be sure that tests are not connected.
def test_are_separated():
    migs_dir = Path().resolve().parent / "migrations"
    db_path = ":memory:"
    db = SQLiteBackend(HappyIni(
        db_path=db_path,
        migs_dir=migs_dir,
        theme="tokyo-night"
    ))
    res = db._fetchall("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='_happy_status';
    """)
    assert res == []


def test_create_mig(db_temp, tmp_path):
    mig_data = MigData(tmp_path / "0001_mario.py")
    db_temp._create_mig_file(mig_data)
    assert len(tuple(db_temp._migs_dir.glob("0001_mario.py"))) == 1


def test_curren_revision_no_mig(db_temp):
    assert db_temp._get_latest_mig_id() == 0


def test_current_revision_one_mig(db_temp):
    db_temp.create_mig("mario")
    assert db_temp._get_latest_mig_id() == 1


def test_create_mig_file(db_temp):
    mig_data = MigData(db_temp._migs_dir / "0001_mario.py")
    db_temp._create_mig_file(mig_data)
    with open(db_temp._migs_dir / "0001_mario.py", "r") as file:
        assert file.read() == MIGRATION_FILE_TEMPLATE


def test_add_mig_happy_status(db):
    mig_data = MigData(db._migs_dir / ZERO_MIG_FILE)
    db._add_mig_to_happy_status(mig_data)
    query = """
        SELECT mig_id, mig_name
        FROM _happy_status
        WHERE mig_name = :mig_name
    """
    res = db._fetchone(query, {"mig_name":ZERO_MIG_NAME})
    assert res == (1, ZERO_MIG_NAME)


def test_exec_all_forward_steps(db):
    mig_path = db._migs_dir / ZERO_MIG_FILE
    db._add_mig_to_happy_status(MigData(mig_path))
    mig = _parse_mig(mig_path)
    db._exec_forward_steps(mig)
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name IN ('jedi', 'rogue');
    """
    res = db._fetchall(query)
    assert res == [('jedi',), ('rogue',)]


def test_apply_all_migs(db):
    db.up_all(lambda x: x)
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name IN ('jedi', 'sith', 'rogue', 'separatist');
    """
    res = set(db._fetchall(query))
    assert res == {('jedi',), ('sith',), ('rogue',), ('separatist',)}


def test_get_mig_with_number_no_mig(db_temp):
    assert not db_temp._get_mig_path_by_id(0)


def test_get_mig_with_number_mig_exist(db):
    res = db._get_mig_path_by_id(1)
    assert res.stem == "0001_jedi_rogue_tables"
