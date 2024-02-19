import sys
from typing import Optional

import typer
from requests import HTTPError

from giza import API_HOST
from giza.client import UsersClient
from giza.exceptions import PasswordError
from giza.options import DEBUG_OPTION
from giza.utils import echo, get_response_info
from giza.utils.misc import _check_password_strength


def prompt_for_input(
    prompt_message: str, type: Optional[type] = str, hide_input: bool = False
) -> str:
    """
    Prompt the user for input.

    Args:
        prompt_message (str): The message to display when prompting the user.
        type (type, optional): The type of input to expect. Defaults to str.
        hide_input (bool, optional): Whether to hide the input (for passwords). Defaults to False.

    Returns:
        str: The user's input.
    """
    return typer.prompt(prompt_message, type=type, hide_input=hide_input)


def handle_http_error(
    e: HTTPError, error_msg: str, debug: Optional[bool] = DEBUG_OPTION
) -> None:
    """
    Handle an HTTP error.

    Args:
        e (HTTPError): The error to handle.
        debug (Optional[bool]): Whether to raise the error for debugging. Defaults to DEBUG_OPTION.
    """
    info = get_response_info(e.response)
    echo.error(f"⛔️{error_msg}⛔️")
    echo.error(f"⛔️Detail -> {info.get('detail')}⛔️")
    echo.error(f"⛔️Status code -> {info.get('status_code')}⛔️")
    echo.error(f"⛔️Error message -> {info.get('content')}⛔️")
    echo.error(
        f"⛔️Request ID: Give this to an administrator to trace the error -> {info.get('request_id')}⛔️"
    ) if info.get("request_id") else None
    if debug:
        raise e
    sys.exit(1)


def request_reset_password_token(
    email: str = typer.Option(None, "--email"),
    debug: Optional[bool] = DEBUG_OPTION,
) -> bool:
    """
    Request a password reset token for a given email.

    Args:
        email (str): The email to request a password reset for.
        debug (Optional[bool]): Whether to raise errors for debugging. Defaults to DEBUG_OPTION.

    Returns:
        bool: True if the request was successful, False if not.
    """
    if email is None:
        email = prompt_for_input("Please enter your email address 📧")

    api_client = UsersClient(API_HOST)
    try:
        echo(api_client.request_reset_password_token(email).msg)
    except HTTPError as e:
        handle_http_error(e, "Could not request the reset token", debug)

    echo("Please check your email for a password reset token 📬")

    return True


def reset_password(
    token: str = typer.Option(None, "--token"),
    debug: Optional[bool] = DEBUG_OPTION,
) -> bool:
    """
    Reset the password for a user using a reset token.

    Args:
        token (str): The reset token received by email.
        debug (Optional[bool]): Whether to raise errors for debugging. Defaults to DEBUG_OPTION.

    Returns:
        bool: True if the reset was successful, False if not.
    """
    if token is None:
        token = prompt_for_input("Please enter your reset token 🎟️")

    new_password = prompt_for_input("Please enter your new password 🔑", hide_input=True)
    confirm_password = prompt_for_input(
        "Please confirm your new password 🔑", hide_input=True
    )

    if new_password != confirm_password:
        echo.error("⛔️Passwords do not match⛔️")
        sys.exit(1)
    try:
        _check_password_strength(new_password)
    except PasswordError as e:
        echo.error("Password does not meet the requirements")
        echo.error(f"⛔️{e}⛔️")
        if debug:
            raise e
        sys.exit(1)

    api_client = UsersClient(API_HOST)
    try:
        echo(api_client.reset_password(token, new_password).msg)
    except HTTPError as e:
        handle_http_error(e, "Could not reset the password", debug)

    echo("Password reset was successful 🎉")

    return True
