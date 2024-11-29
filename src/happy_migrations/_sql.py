CREATE_HAPPY_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS _happy_status (
    id_happy_status integer primary key autoincrement,
    mig_id integer not null,
    mig_name varchar(255) not null,
    applied TIMESTAMP NOT NULL DEFAULT current_timestamp
);
"""

HAPPY_STATUS_EXIST = """
SELECT name
FROM sqlite_master
WHERE type='table' AND name='_happy_status';
"""

ADD_HAPPY_STATUS = """
INSERT INTO _happy_status (mig_id, mig_name)
VALUES (:mig_id, :mig_name)
"""

REMOVE_HAPPY_STATUS = """
DELETE FROM _happy_status
WHERE mig_id = :mig_id
"""

GET_CURRENT_REVISION = """
SELECT mig_name
FROM _happy_status
ORDER BY mig_name DESC
LIMIT 1
"""

GET_LAST_APPLIED_NAME = """
SELECT mig_name
FROM _happy_status
ORDER BY mig_id DESC
LIMIT 1
"""

GET_LAST_APPLIED_ID = """
SELECT mig_id
FROM _happy_status
ORDER BY mig_id DESC
LIMIT 1
"""

LIST_HAPPY_STATUS = """
SELECT mig_id, mig_name
FROM _happy_status
"""
