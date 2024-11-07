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
    fname: str
    status: str
    created: datetime
    steps: tuple[Step, ...]


@dataclass
class HappyLog:
    id_happy_log: int
    mig_id: int
    operation: str
    username: str
    hostname: str
    created: datetime
