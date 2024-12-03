import configparser
from pathlib import Path
from typing import cast
import re

from happy_migrations._data_classes import HappyIni
from happy_migrations._templates import _HAPPY_INI_TEMPLATE


def create_happy_ini(path: Path) -> bool:
    """Create happy.ini file in CWD."""
    if path.exists():
        return True

    with open(path, "w") as file:
        file.write(_HAPPY_INI_TEMPLATE)

    return False


def parse_happy_ini() -> HappyIni:
    """Parse the 'happy.ini' configuration file and return a HappyIni dataclass instance."""
    config = configparser.ConfigParser()
    config.read("happy.ini")
    return HappyIni(
        db_path=cast(Path, config["Settings"]["db_path"]),
        migs_dir=cast(Path, config["Settings"]["migs_dir"]),
        theme=config["Settings"].get("theme", "textual-dark"),
    )


def mig_name_parser(string: str) -> str:
    """Converts a given string to a normalized migration name format."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", string).lower()


def _mig_path_to_id_n_name(mig_path: Path) -> list[str, str]:
    """Return migration id and name from path."""
    return cast(list[str, str], mig_path.stem.split("_", maxsplit=1))
