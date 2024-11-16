import configparser
from pathlib import Path
from typing import cast

from happy_migrations._data_classes import HappyIni


_HAPPY_INI_TEMPLATE = """\
[Settings]
db_path =
migs_dir =
theme = dark
"""


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
    config.read('happy.ini')
    return HappyIni(
        db_path=cast(Path, config['Settings']['db_path']),
        migs_dir=cast(Path, config['Settings']['migs_dir'])
    )
