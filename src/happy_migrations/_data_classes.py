from dataclasses import dataclass
from datetime import datetime


@dataclass
class HappyIni:
    db_path: str


@dataclass
class Query:
    forward: str
    backward: str


@dataclass
class Migration:
    key: int
    name: str
    queries: tuple[Query, ...]


@dataclass
class MigrationStatus:
    id_migrations_status: int
    migration_id: int
    migration_name: str
    full_name: str
    applied: bool
    created: datetime


@dataclass
class HappyLog:
    id_happy_log: int
    migration_id: int
    operation: str
    username: str
    hostname: str
    created: datetime
