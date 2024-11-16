import configparser
from pathlib import Path
from typing import cast

from happy_migrations._data_classes import HappyIni


def parse_happy_ini() -> HappyIni:
    """Parse the 'happy.ini' configuration file and return a HappyIni dataclass instance."""
    config = configparser.ConfigParser()
    config.read('happy.ini')
    return HappyIni(
        db_path=cast(Path, config['Settings']['db_path']),
        migs_dir=cast(Path, config['Settings']['migs_dir'])
    )
