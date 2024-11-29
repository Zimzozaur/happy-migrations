import click

from happy_migrations._data_classes import HappyMsg
from happy_migrations._echo_msg import echo_msg


@click.group()
def social() -> None:
    """Social commands group."""
    pass


@social.command()
def github() -> None:
    """Display the link to the GitHub repository."""
    msg = HappyMsg(
        status="info",
        header="Github: ",
        message="https://github.com/Zimzozaur/happy-migrations/",
    )
    echo_msg(msg)


@social.command()
def issue() -> None:
    """Display the link to the GitHub issues page."""
    msg = HappyMsg(
        status="info",
        header="Github Issue: ",
        message="https://github.com/Zimzozaur/happy-migrations/issues",
    )
    echo_msg(msg)


@social.command()
def discord() -> None:
    """Display the link to the official Discord server."""
    msg = HappyMsg(
        status="info",
        header="Server Invitation: ",
        message="https://discord.gg/JF44rr67Ng",
    )
    echo_msg(msg)


@social.command()
def x() -> None:
    """Display the link to the Simon's X profile."""
    msg = HappyMsg(status="info", header="X: ", message="https://x.com/zimzozaur")
    echo_msg(msg)
