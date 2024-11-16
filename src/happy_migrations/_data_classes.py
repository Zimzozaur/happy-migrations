from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class HappyIni:
    db_path: Path | str
    migs_dir: Path

    def __post_init__(self):
        if isinstance(self.db_path, str) and self.db_path != ":memory:":
            self.db_path = Path(self.db_path)
        if isinstance(self.migs_dir, str):
            self.migs_dir = Path(self.migs_dir)


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
