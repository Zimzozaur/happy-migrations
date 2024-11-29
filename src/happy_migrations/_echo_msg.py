from typing import TYPE_CHECKING

from click import echo, style


if TYPE_CHECKING:
    from happy_migrations._data_classes import HappyMsg


def echo_msg(msg: "HappyMsg") -> None:
    """Display a styled message to the console."""
    header = style(f"{msg.header}", f"{msg.color}")
    echo(header + msg.message)
