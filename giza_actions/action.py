import os
from functools import partial, wraps
from pathlib import Path

from giza_actions.utils import get_workspace_uri  # noqa: E402

os.environ["PREFECT_API_URL"] = f"{get_workspace_uri()}/api"
os.environ["PREFECT_UI_URL"] = get_workspace_uri()

from prefect import Flow  # noqa: E402
from prefect import flow as _flow  # noqa: E402
from prefect.settings import PREFECT_API_URL  # noqa: E402
from prefect.settings import (  # noqa: E402
    PREFECT_LOGGING_SETTINGS_PATH,
    PREFECT_UI_URL,
    update_current_profile,
)
from prefect.utilities.asyncutils import sync_compatible  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402

from giza_actions.__init__ import __module_path__  # noqa: E402


class Action:
    """
    A class to represent an Action.

    Attributes:
        name (str): The name of the action.
        _flow (Flow): The Prefect flow that represents the action's entrypoint.

    Methods:
        _set_settings: Updates the current profile with API and logging settings.
        _update_api_url: Updates the API URL in the current profile.
        get_flow: Returns the Prefect flow.
        serve: Serves the action, making it ready to poll for scheduled runs.
    """

    def __init__(self, entrypoint: Flow, name: str):
        """
        Constructs all the necessary attributes for the Action object.

        Args:
            entrypoint (Flow): The Prefect flow that represents the action's entrypoint.
            name (str): The name of the action.
        """
        self.name = name
        self._flow = entrypoint
        self._set_settings()

    def _set_settings(self):
        """
        Updates the current profile with the workspace API URL and the path to the logging configuration.
        """
        update_current_profile(settings={PREFECT_API_URL: f"{get_workspace_uri()}/api"})
        update_current_profile(
            settings={PREFECT_LOGGING_SETTINGS_PATH: f"{__module_path__}/logging.yaml"}
        )

    def _update_api_url(self, api_url: str):
        """
        Updates the API URL in the current profile.

        Args:
            api_url (str): The new API URL to set in the profile.
        """
        update_current_profile(settings={PREFECT_API_URL: api_url})

    def get_flow(self):
        """
        Returns the Prefect flow associated with the action.

        Returns:
            Flow: The Prefect flow of the action.
        """
        return self._flow

    @sync_compatible
    async def serve(
        self,
        name: str,
        print_starting_message: bool = True,
    ):
        """
        Serves the action, making it ready to poll for scheduled runs.

        Args:
            name (str): The name to assign to the runner. If a file path is provided, it uses the file name without the extension.
            print_starting_message (bool, optional): Whether to print a starting message. Defaults to True.
        """
        from prefect.runner import Runner

        # Handling for my_flow.serve(__file__)
        # Will set name to name of file where my_flow.serve() without the extension
        # Non filepath strings will pass through unchanged
        name = Path(name).stem

        runner = Runner(name=name, pause_on_shutdown=False)
        deployment_id = await runner.add_flow(
            self._flow,
            name=name,
        )
        if print_starting_message:
            help_message = (
                f"[green]Your action {self.name!r} is being served and polling for"
                " scheduled runs!\n[/]"
            )
            if PREFECT_UI_URL:
                help_message += (
                    "\nYou can run your action via the Actions UI:"
                    f" [blue]{PREFECT_UI_URL.value()}/deployments/deployment/{deployment_id}[/]\n"
                )

            console = Console()
            console.print(Panel(help_message))
        await runner.start(webserver=False)


def action(func=None, **task_init_kwargs):
    """
    Decorator to convert a function into a Prefect flow.

    Args:
        func (Callable, optional): The function to convert into a flow. If None, returns a partial function.
        **task_init_kwargs: Arbitrary keyword arguments passed to the flow initialization.

    Returns:
        Flow: The Prefect flow created from the function.
    """
    if func is None:
        return partial(action, **task_init_kwargs)

    @wraps(func)
    def safe_func(**kwargs):
        """
        A wrapper function that calls the original function with its arguments.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the original function.

        Returns:
            The return value of the original function.
        """
        return func(**kwargs)

    safe_func.__name__ = func.__name__
    return _flow(safe_func, **task_init_kwargs)
