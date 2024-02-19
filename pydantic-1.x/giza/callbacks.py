from http import client

import typer

from giza import __version__
from giza.utils import echo


def version_callback(value: bool) -> None:
    """
    Prints the current version when `--version` flag is added to a call.

    Args:
        value (bool): represents if the flag has been added or not to the call.

    Raises:
        Exit: exit the CLI execution
    """
    if value:
        echo(
            f"🚀 [orange3]Giza[/orange3] CLI, "
            f"version ~> [green]{__version__}[/green]",
        )
        raise typer.Exit()


def debug_callback(_, value: bool):
    """
    If a call adds the `--debug` flag debugging mode is activated for external requests and API Clients.

    Args:
        _ (_type_): discarded value
        value (bool): represents if the flag has been added to the call or not

    Returns:
        bool: pass the value back so it can be used in the clients
    """
    if value:
        echo(":bug: Debugging mode is [red]on[/red]")
        client.HTTPConnection.debuglevel = 1

    return value
