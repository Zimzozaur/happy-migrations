from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from textual.theme import BUILTIN_THEMES

from happy_migrations._echo_msg import echo_msg


@dataclass
class HappyIni:
    db_path: Path | str
    migs_dir: Path
    theme: str

    def __post_init__(self) -> None:
        """Converts string paths to Path objects after initialization."""
        if isinstance(self.db_path, str) and self.db_path != ":memory:":
            self.db_path = Path(self.db_path)
        if isinstance(self.migs_dir, str):
            self.migs_dir = Path(self.migs_dir)
        if self.theme not in list(BUILTIN_THEMES.keys()):
            echo_msg(
                HappyMsg(
                    status="warning",
                    header="Invalid theme: ",
                    message=f"`{self.theme}` used textual-dark instead",
                )
            )
            self.theme = "textual-dark"


@dataclass
class HappyMsg:
    """Represents a message send to end user."""

    status: Literal["warning", "success", "error", "info"]
    header: str
    message: str

    @property
    def color(self) -> str:
        """Get the color associated with the status."""
        match self.status:
            case "success":
                return "green"
            case "warning":
                return "yellow"
            case "error":
                return "red"
            case "info":
                return "blue"


@dataclass
class MigData:
    """Represents information about a migration file."""

    path: Path

    @property
    def full_name(self) -> str:
        return self.path.stem

    @property
    def file_name(self) -> str:
        return self.path.name

    @property
    def id(self) -> int:
        return int(self.full_name.split("_", maxsplit=1)[0])

    @property
    def name(self) -> str:
        return self.full_name.split("_", maxsplit=1)[1]


@dataclass
class Step:
    """Represents a single step in a database migration."""

    forward: str
    backward: str


@dataclass
class MigrationSQL:
    """Represents a complete database migration."""

    steps: tuple[Step, ...]
