from dataclasses import dataclass
from datetime import datetime


@dataclass
class HappyIni:
    db_path: str


@dataclass
class Step:
    forward: str
    backward: str


@dataclass
class Migration:
    mig_id: int
    mig_name: str
    mig_fname: str
    status: str
    created: datetime
    steps: tuple[Step, ...]


@dataclass
class MigrationStatus:
    id_mig_status: int
    mig_id: int
    mig_name: str
    mig_fname: str
    status: bool
    created: datetime


@dataclass
class HappyLog:
    id_happy_log: int
    mig_id: int
    operation: str
    username: str
    hostname: str
    created: datetime
