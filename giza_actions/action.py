import os
from functools import partial, wraps
from pathlib import Path

os.environ["PREFECT_API_URL"] = f"{os.environ.get('REMOTE_SERVER')}/api"
os.environ["PREFECT_UI_URL"] = f"{os.environ.get('REMOTE_SERVER')}"

from prefect import Flow  # noqa: E402
from prefect import flow as _flow  # noqa: E402
from prefect.settings import (  # noqa: E402
    PREFECT_API_URL,
    PREFECT_LOGGING_SETTINGS_PATH,
    PREFECT_UI_URL,
    update_current_profile,
)
from prefect.utilities.asyncutils import sync_compatible  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402

from giza_actions.__init__ import __module_path__  # noqa: E402


class Action:
    def __init__(self, entrypoint: Flow, name: str):
        self.name = name
        self._flow = entrypoint
        self._set_settings()

    def _set_settings(self):
        update_current_profile(
            settings={PREFECT_API_URL: f"{os.environ.get('REMOTE_SERVER')}/api"}
        )
        update_current_profile(
            settings={PREFECT_LOGGING_SETTINGS_PATH: f"{__module_path__}/logging.yaml"}
        )

    def _update_api_url(self, api_url: str):
        update_current_profile(settings={PREFECT_API_URL: api_url})

    def get_flow(self):
        return self._flow

    @sync_compatible
    async def serve(
        self,
        name: str,
        print_starting_message: bool = True,
    ):
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
    if func is None:
        return partial(action, **task_init_kwargs)

    @wraps(func)
    def safe_func(**kwargs):
        return func(**kwargs)

    safe_func.__name__ = func.__name__
    return _flow(safe_func, **task_init_kwargs)
