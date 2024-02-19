import typer

from giza.callbacks import debug_callback

DEBUG_OPTION = typer.Option(
    False,
    "--debug",
    is_flag=True,
    callback=debug_callback,
    help="""
    Enable debugging of HTTP calls.


    Disabled by default.""",
)
