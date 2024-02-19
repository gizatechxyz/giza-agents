import sys
import time
from typing import Optional

import typer
from pydantic import ValidationError
from requests import HTTPError
from rich import print_json
from rich.live import Live

from giza import API_HOST
from giza.client import WorkspaceClient
from giza.options import DEBUG_OPTION
from giza.utils import echo, get_response_info

app = typer.Typer()


@app.command(
    short_help="📦 Retrieves information about a Giza Workspace.",
    help="""📦 Retrieves information about a Giza Workspace.

    This command will return the workspace URL if the workspace exist or an error otherwise.

    Until the verification is complete the user won't be able to log in nor user other CLI capabilities.

    """,
)
def get(
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    echo("Retrieving workspace information ✅ ")
    try:
        client = WorkspaceClient(API_HOST)
        workspace = client.get()
    except ValidationError as e:
        echo.error("Workspace validation error")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error("⛔️There is an error retrieving the workspace information")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
    if workspace.status == "FAILED":
        echo.error("⛔️Workspace creation failed⛔️")
        echo.error("⛔️Please delete the workspace and create a new one⛔️")
    else:
        echo.info(f"✅ Workspace URL: {workspace.url} ✅")
    print_json(workspace.json())


@app.command(
    short_help="🔥 Create a Giza Workspace.",
    help="""🔥 Create a Giza Workspace.

    This command will trigger the creation of a Giza Workspace if it does not exist.
    If the workspaces already exists, the command will return an error.
    """,
)
def create(
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    """
    Command to create a Giza Workspace.

    Args:
        debug (Optional[bool], optional): Whether to add debug information, will show requests, extra logs and traceback if there is an Exception. Defaults to DEBUG_OPTION (False).

    Raises:
        ValidationError: input fields are validated, if these are not suitable the exception is raised
        HTTPError: request error to the API, 4XX or 5XX
    """

    echo("Creating Workspace ✅ ")
    echo.warning("This process can take up to 10 minutes ⏳")
    try:
        client = WorkspaceClient(API_HOST)
        workspace = client.create()
        with Live() as live:
            live.update(echo.format_message("Waiting for workspace creation..."))
            while workspace.status not in ["COMPLETED", "FAILED"]:
                time.sleep(20)
                workspace = client.get()
                live.update(
                    echo.format_message(f"Workspace status is '{workspace.status}'")
                )
            if workspace.status == "FAILED":
                live.update(
                    echo.format_error(f"Workspace status is '{workspace.status}'")
                )
                sys.exit(1)
            live.update(echo.format_message("Worksace creation is successful ✅"))
    except ValidationError as e:
        echo.error("Workspace validation error")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error("⛔️Could not create the workspace")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
    echo.info(f"✅ Workspace URL: {workspace.url} ✅")


@app.command(
    short_help="❌ Delete a Giza Workspace.",
    help="""❌ Delete a Giza Workspace.

    This command will delete an existing Giza Workspace or throw an error otherwise.
    """,
)
def delete(
    debug: Optional[bool] = DEBUG_OPTION,
) -> None:
    echo.warning("THIS WILL ERASE ALL YOUR WORKSPACE DATA ❌")
    confirmation = typer.confirm(
        "Are you sure you want to delete the workspace?", default=False
    )
    if not confirmation:
        echo.info("Aborting ❌")
        sys.exit(0)
    echo("Deleting Workspace ✅ ")
    try:
        client = WorkspaceClient(API_HOST)
        client.delete()
    except ValidationError as e:
        echo.error("Workspace validation error")
        echo.error("Review the provided information")
        if debug:
            raise e
        echo.error(str(e))
        sys.exit(1)
    except HTTPError as e:
        info = get_response_info(e.response)
        echo.error("⛔️There is an error while deleting workspace")
        echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
        echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
        echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
        echo.error(
            f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
        ) if info.get("request_id") else None
        if debug:
            raise e
        sys.exit(1)
    echo.info("Workspace Deleted ✅")
