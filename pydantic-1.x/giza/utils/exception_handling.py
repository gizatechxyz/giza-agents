import sys

from pydantic import ValidationError
from requests import HTTPError

from giza.exceptions import ScarbBuildError, ScarbNotFound
from giza.utils import echo, get_response_info


class ExceptionHandler:
    """
    Context manager to handle exceptions in the CLI.

    The main purpose of this class is to handle common exceptions in the CLI and
    provide a consistent way to handle them.

    The CLI commands should be wrapped with this context manager to handle exceptions
    and provide a consistent way to handle them.

    Example:
    ```python
    with ExceptionHandler():
        # Your command code here
        client = Client()
        client.get() # This will raise an exception if something goes wrong but will be handled in __exit__
    ```

    """

    def __init__(self, debug: bool = False) -> None:
        if debug is None:
            debug = False
        self.debug = debug

    def handle_exit(self):
        if self.debug:
            return False
        sys.exit(1)

    def __enter__(self):
        # Set up resources here
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        error = None
        if exc_type in [ScarbBuildError, ScarbNotFound]:
            error = True
            echo.error("⛔️Error building the scarb model⛔️")
            echo.error("⛔️Version could not be updated⛔️")
            echo.error("Check scarb documentation https://docs.swmansion.com/scarb/")
        elif exc_type == ValidationError:
            error = True
            echo.error("Resource validation error")
            echo.error("Review the provided information")
        elif exc_type == HTTPError:
            error = True
            info = get_response_info(exc_value.response)
            echo.error("⛔️Could not perform the action on the resource⛔️")
            echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
            echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
            echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
            echo.error(
                f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
            ) if info.get("request_id") else None
        elif isinstance(exc_value, Exception):
            error = True
            echo.error(f"⛔️An error occurred: {exc_value}⛔️")
        if error:
            return self.handle_exit()
